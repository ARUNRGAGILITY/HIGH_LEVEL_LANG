# modules/utils/exceptions.py
"""
Custom exceptions for the Pseudo Java Parser
"""


class PseudoJavaError(Exception):
    """Base exception for Pseudo Java Parser errors"""
    pass


class ParseError(PseudoJavaError):
    """Exception raised for parsing errors"""
    
    def __init__(self, message: str, line_number: int = None, line_content: str = None):
        self.line_number = line_number
        self.line_content = line_content
        
        if line_number is not None:
            message = f"Line {line_number}: {message}"
            if line_content:
                message += f"\n  --> {line_content.strip()}"
        
        super().__init__(message)


class SyntaxError(ParseError):
    """Exception raised for syntax errors in pseudo-Java code"""
    pass


class TypeMismatchError(ParseError):
    """Exception raised for type-related errors"""
    pass


class VariableError(ParseError):
    """Exception raised for variable declaration/usage errors"""
    pass


class MethodError(ParseError):
    """Exception raised for method definition/usage errors"""
    pass


class TemplateError(ParseError):
    """Exception raised for template/class definition errors"""
    pass


class FileError(PseudoJavaError):
    """Exception raised for file I/O errors"""
    pass


class CompilationError(PseudoJavaError):
    """Exception raised for Java compilation errors"""
    pass


class RuntimeError(PseudoJavaError):
    """Exception raised for Java runtime errors"""
    pass