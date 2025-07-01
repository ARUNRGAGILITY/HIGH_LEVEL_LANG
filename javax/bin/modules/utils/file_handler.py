# modules/utils/file_handler.py
"""
File handling utilities for the Pseudo Java Parser
"""

import os
from pathlib import Path
from typing import Optional

from utils.exceptions import PseudoJavaError


class FileHandler:
    """Handles file I/O operations"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def read_file(self, file_path: str) -> str:
        """Read content from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if self.verbose:
                print(f"Successfully read file: {file_path}")
            
            return content
        except FileNotFoundError:
            raise PseudoJavaError(f"Input file '{file_path}' not found")
        except UnicodeDecodeError:
            raise PseudoJavaError(f"Cannot decode file '{file_path}'. Please ensure it's a valid text file")
        except PermissionError:
            raise PseudoJavaError(f"Permission denied reading file '{file_path}'")
        except Exception as e:
            raise PseudoJavaError(f"Error reading file '{file_path}': {e}")
    
    def write_file(self, file_path: str, content: str) -> None:
        """Write content to a file"""
        try:
            # Create directory if it doesn't exist and path has a directory component
            dir_path = os.path.dirname(file_path)
            if dir_path:  # Only create directory if there's actually a directory path
                os.makedirs(dir_path, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if self.verbose:
                print(f"Successfully wrote file: {file_path}")
        
        except PermissionError:
            raise PseudoJavaError(f"Permission denied writing file '{file_path}'")
        except Exception as e:
            raise PseudoJavaError(f"Error writing file '{file_path}': {e}")
    
    def determine_output_file(self, input_file: str, program_name: str, 
                            output_file: Optional[str], output_dir: Optional[str]) -> str:
        """Determine the output file path based on various options"""
        if output_file:
            return output_file
        elif output_dir:
            # Use program name with specified directory
            return os.path.join(output_dir, f"{program_name}.java")
        else:
            # Default: use program name in current directory
            return f"{program_name}.java"
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        return os.path.exists(file_path)
    
    def get_file_extension(self, file_path: str) -> str:
        """Get file extension"""
        return Path(file_path).suffix
    
    def get_file_name_without_extension(self, file_path: str) -> str:
        """Get filename without extension"""
        return Path(file_path).stem
    
    def ensure_directory_exists(self, directory: str) -> None:
        """Ensure a directory exists, create if necessary"""
        try:
            os.makedirs(directory, exist_ok=True)
            if self.verbose:
                print(f"Directory ensured: {directory}")
        except PermissionError:
            raise PseudoJavaError(f"Permission denied creating directory '{directory}'")
        except Exception as e:
            raise PseudoJavaError(f"Error creating directory '{directory}': {e}")