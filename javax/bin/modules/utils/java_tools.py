# modules/utils/java_tools.py
"""
Java compilation and execution tools
"""

import os
import subprocess
import shutil
from pathlib import Path

from utils.exceptions import PseudoJavaError


class JavaTools:
    """Tools for compiling and running Java code"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def check_java_availability(self) -> dict:
        """Check if Java tools are available"""
        tools = {}
        
        # Check javac
        tools['javac'] = shutil.which('javac') is not None
        
        # Check java
        tools['java'] = shutil.which('java') is not None
        
        if self.verbose:
            for tool, available in tools.items():
                status = "✓" if available else "✗"
                print(f"{status} {tool}: {'Available' if available else 'Not found'}")
        
        return tools
    
    def compile(self, java_file: str) -> bool:
        """Compile Java file"""
        tools = self.check_java_availability()
        
        if not tools['javac']:
            raise PseudoJavaError(
                "Java compiler (javac) not found. Please install JDK and add it to your PATH."
            )
        
        try:
            if self.verbose:
                print(f"Compiling: {java_file}")
            
            # Run javac
            result = subprocess.run(
                ['javac', java_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if self.verbose:
                    print("Compilation successful!")
                return True
            else:
                print("Compilation errors:")
                if result.stderr:
                    print(result.stderr)
                if result.stdout:
                    print(result.stdout)
                return False
        
        except subprocess.TimeoutExpired:
            raise PseudoJavaError("Compilation timed out after 30 seconds")
        except FileNotFoundError:
            raise PseudoJavaError("Java compiler not found")
        except Exception as e:
            raise PseudoJavaError(f"Compilation error: {e}")
    
    def run(self, java_file: str) -> bool:
        """Run compiled Java program"""
        tools = self.check_java_availability()
        
        if not tools['java']:
            raise PseudoJavaError(
                "Java runtime (java) not found. Please install JRE/JDK and add it to your PATH."
            )
        
        try:
            # Extract class name and directory
            java_path = Path(java_file)
            class_name = java_path.stem
            class_dir = java_path.parent or Path(".")
            
            # Check if .class file exists
            class_file = class_dir / f"{class_name}.class"
            if not class_file.exists():
                raise PseudoJavaError(f"Compiled class file not found: {class_file}")
            
            if self.verbose:
                print(f"Running: {class_name}")
            
            # Run java
            result = subprocess.run(
                ['java', '-cp', str(class_dir), class_name],
                timeout=60
            )
            
            return result.returncode == 0
        
        except subprocess.TimeoutExpired:
            raise PseudoJavaError("Program execution timed out after 60 seconds")
        except FileNotFoundError:
            raise PseudoJavaError("Java runtime not found")
        except KeyboardInterrupt:
            print("\nProgram interrupted by user")
            return True
        except Exception as e:
            raise PseudoJavaError(f"Runtime error: {e}")
    
    def clean_class_files(self, java_file: str) -> None:
        """Remove generated .class files"""
        try:
            java_path = Path(java_file)
            class_name = java_path.stem
            class_dir = java_path.parent or Path(".")
            
            # Remove main class file
            class_file = class_dir / f"{class_name}.class"
            if class_file.exists():
                class_file.unlink()
                if self.verbose:
                    print(f"Removed: {class_file}")
            
            # Remove inner class files (if any)
            for inner_class in class_dir.glob(f"{class_name}$*.class"):
                inner_class.unlink()
                if self.verbose:
                    print(f"Removed: {inner_class}")
        
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not clean class files: {e}")
    
    def get_java_version(self) -> str:
        """Get Java version information"""
        try:
            result = subprocess.run(
                ['java', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Java version is typically in stderr
                version_output = result.stderr or result.stdout
                # Extract first line which usually contains version
                first_line = version_output.split('\n')[0]
                return first_line
            else:
                return "Unknown"
        
        except Exception:
            return "Not available"
    
    def validate_java_environment(self) -> bool:
        """Validate Java development environment"""
        tools = self.check_java_availability()
        
        if not tools['javac']:
            print("❌ Java compiler (javac) not found")
            print("   Please install JDK and add it to your PATH")
            return False
        
        if not tools['java']:
            print("❌ Java runtime (java) not found")
            print("   Please install JRE/JDK and add it to your PATH")
            return False
        
        if self.verbose:
            version = self.get_java_version()
            print(f"✅ Java environment validated")
            print(f"   Version: {version}")
        
        return True