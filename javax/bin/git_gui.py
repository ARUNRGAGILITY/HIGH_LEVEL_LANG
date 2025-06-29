import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import threading
from pathlib import Path

class GitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Git GUI Frontend")
        self.root.geometry("800x600")
        
        self.repo_path = tk.StringVar()
        self.setup_ui()
        
    def setup_ui(self):
        # Repository selection frame
        repo_frame = ttk.Frame(self.root, padding="10")
        repo_frame.pack(fill=tk.X)
        
        ttk.Label(repo_frame, text="Repository:").pack(side=tk.LEFT)
        ttk.Entry(repo_frame, textvariable=self.repo_path, width=50).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(repo_frame, text="Browse", command=self.browse_repo).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(repo_frame, text="Refresh", command=self.refresh_status).pack(side=tk.LEFT, padx=(5, 0))
        
        # Main content frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File status frame
        status_frame = ttk.LabelFrame(main_frame, text="File Status", padding="5")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # File tree with scrollbar
        tree_frame = ttk.Frame(status_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_tree = ttk.Treeview(tree_frame, columns=("Status", "File"), show="tree headings")
        self.file_tree.heading("#0", text="")
        self.file_tree.heading("Status", text="Status")
        self.file_tree.heading("File", text="File Path")
        self.file_tree.column("#0", width=30)
        self.file_tree.column("Status", width=100)
        self.file_tree.column("File", width=400)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Stage Selected", command=self.stage_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Unstage Selected", command=self.unstage_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Stage All", command=self.stage_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Discard Changes", command=self.discard_changes).pack(side=tk.LEFT, padx=(0, 5))
        
        # Commit frame
        commit_frame = ttk.LabelFrame(main_frame, text="Commit", padding="5")
        commit_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(commit_frame, text="Commit Message:").pack(anchor=tk.W)
        self.commit_message = scrolledtext.ScrolledText(commit_frame, height=4, width=70)
        self.commit_message.pack(fill=tk.X, pady=(5, 5))
        
        commit_button_frame = ttk.Frame(commit_frame)
        commit_button_frame.pack(fill=tk.X)
        
        ttk.Button(commit_button_frame, text="Commit", command=self.commit_changes).pack(side=tk.LEFT)
        ttk.Button(commit_button_frame, text="Commit & Push", command=self.commit_and_push).pack(side=tk.LEFT, padx=(10, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to stage/unstage
        self.file_tree.bind("<Double-1>", self.toggle_stage)
        
    def browse_repo(self):
        folder = filedialog.askdirectory()
        if folder:
            self.repo_path.set(folder)
            self.refresh_status()
    
    def run_git_command(self, command, cwd=None):
        """Run git command and return output"""
        if not cwd:
            cwd = self.repo_path.get()
        if not cwd or not os.path.exists(cwd):
            return None, "No repository selected or path doesn't exist"
        
        try:
            result = subprocess.run(
                command, 
                cwd=cwd, 
                capture_output=True, 
                text=True, 
                shell=True
            )
            return result.stdout, result.stderr
        except Exception as e:
            return None, str(e)
    
    def refresh_status(self):
        """Refresh the git status and update the tree"""
        if not self.repo_path.get():
            return
            
        self.status_var.set("Refreshing...")
        self.root.update()
        
        # Clear current items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Get git status
        stdout, stderr = self.run_git_command("git status --porcelain")
        
        if stderr and "not a git repository" in stderr.lower():
            self.status_var.set("Error: Not a git repository")
            return
        
        if stdout:
            lines = stdout.strip().split('\n')
            for line in lines:
                if len(line) >= 3:
                    status_code = line[:2]
                    file_path = line[3:]
                    
                    # Determine status text and color
                    status_text, tag = self.parse_status_code(status_code)
                    
                    item = self.file_tree.insert("", tk.END, values=(status_text, file_path))
                    self.file_tree.set(item, "Status", status_text)
                    self.file_tree.set(item, "File", file_path)
                    
                    # Add tags for coloring
                    if tag:
                        self.file_tree.item(item, tags=(tag,))
        
        # Configure tags for colors
        self.file_tree.tag_configure("modified", foreground="orange")
        self.file_tree.tag_configure("staged", foreground="green")
        self.file_tree.tag_configure("untracked", foreground="red")
        self.file_tree.tag_configure("deleted", foreground="red")
        
        self.status_var.set("Ready")
    
    def parse_status_code(self, code):
        """Parse git status code to human readable text"""
        if code[0] == 'M':
            return "Modified (Staged)", "staged"
        elif code[1] == 'M':
            return "Modified", "modified"
        elif code == 'A ':
            return "Added (Staged)", "staged"
        elif code == '??':
            return "Untracked", "untracked"
        elif code[0] == 'D':
            return "Deleted (Staged)", "staged"
        elif code[1] == 'D':
            return "Deleted", "deleted"
        elif code == 'R ':
            return "Renamed (Staged)", "staged"
        elif code[1] == 'R':
            return "Renamed", "modified"
        else:
            return f"Status: {code}", None
    
    def get_selected_files(self):
        """Get list of selected files in the tree"""
        selected_items = self.file_tree.selection()
        files = []
        for item in selected_items:
            file_path = self.file_tree.set(item, "File")
            files.append(file_path)
        return files
    
    def stage_selected(self):
        """Stage selected files"""
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("No Selection", "Please select files to stage")
            return
        
        for file in files:
            stdout, stderr = self.run_git_command(f"git add \"{file}\"")
            if stderr:
                messagebox.showerror("Error", f"Failed to stage {file}: {stderr}")
                return
        
        self.refresh_status()
        self.status_var.set(f"Staged {len(files)} file(s)")
    
    def unstage_selected(self):
        """Unstage selected files"""
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("No Selection", "Please select files to unstage")
            return
        
        for file in files:
            stdout, stderr = self.run_git_command(f"git reset HEAD \"{file}\"")
            if stderr and "fatal:" in stderr:
                messagebox.showerror("Error", f"Failed to unstage {file}: {stderr}")
                return
        
        self.refresh_status()
        self.status_var.set(f"Unstaged {len(files)} file(s)")
    
    def stage_all(self):
        """Stage all changes"""
        stdout, stderr = self.run_git_command("git add .")
        if stderr and "fatal:" in stderr:
            messagebox.showerror("Error", f"Failed to stage all files: {stderr}")
            return
        
        self.refresh_status()
        self.status_var.set("Staged all changes")
    
    def discard_changes(self):
        """Discard changes for selected files"""
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("No Selection", "Please select files to discard changes")
            return
        
        if not messagebox.askyesno("Confirm", f"Are you sure you want to discard changes for {len(files)} file(s)? This cannot be undone."):
            return
        
        for file in files:
            stdout, stderr = self.run_git_command(f"git checkout -- \"{file}\"")
            if stderr and "fatal:" in stderr:
                messagebox.showerror("Error", f"Failed to discard changes for {file}: {stderr}")
                return
        
        self.refresh_status()
        self.status_var.set(f"Discarded changes for {len(files)} file(s)")
    
    def toggle_stage(self, event):
        """Toggle staging for double-clicked file"""
        item = self.file_tree.selection()[0]
        status = self.file_tree.set(item, "Status")
        file_path = self.file_tree.set(item, "File")
        
        if "Staged" in status:
            # Unstage the file
            stdout, stderr = self.run_git_command(f"git reset HEAD \"{file_path}\"")
        else:
            # Stage the file
            stdout, stderr = self.run_git_command(f"git add \"{file_path}\"")
        
        if stderr and "fatal:" in stderr:
            messagebox.showerror("Error", f"Git operation failed: {stderr}")
            return
        
        self.refresh_status()
    
    def commit_changes(self):
        """Commit staged changes"""
        message = self.commit_message.get(1.0, tk.END).strip()
        if not message:
            messagebox.showwarning("No Message", "Please enter a commit message")
            return
        
        stdout, stderr = self.run_git_command(f"git commit -m \"{message}\"")
        
        if "nothing to commit" in stdout:
            messagebox.showinfo("Nothing to Commit", "No staged changes to commit")
        elif stderr and "fatal:" in stderr:
            messagebox.showerror("Error", f"Commit failed: {stderr}")
        else:
            messagebox.showinfo("Success", "Changes committed successfully")
            self.commit_message.delete(1.0, tk.END)
            self.refresh_status()
    
    def commit_and_push(self):
        """Commit changes and push to remote"""
        self.commit_changes()
        
        # Push to remote
        self.status_var.set("Pushing to remote...")
        self.root.update()
        
        stdout, stderr = self.run_git_command("git push")
        
        if stderr and "fatal:" in stderr:
            messagebox.showerror("Error", f"Push failed: {stderr}")
        else:
            messagebox.showinfo("Success", "Changes committed and pushed successfully")
        
        self.status_var.set("Ready")

def main():
    root = tk.Tk()
    app = GitGUI(root)
    
    # Try to detect current directory as git repo
    current_dir = os.getcwd()
    if os.path.exists(os.path.join(current_dir, ".git")):
        app.repo_path.set(current_dir)
        app.refresh_status()
    
    root.mainloop()

if __name__ == "__main__":
    main()