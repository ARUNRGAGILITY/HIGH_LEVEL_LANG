# modules/parsers/method_parser.py
"""
Method parser for the Pseudo Java Parser
"""

import re
from typing import List, Tuple, Optional

from core.data_structures import Method, AccessModifier, Template
from utils.exceptions import PseudoJavaError


class MethodParser:
    """Parser for method declarations"""
    
    def __init__(self, synonym_config, type_mapping):
        self.synonym_config = synonym_config
        self.type_mapping = type_mapping
        self.statement_parser = None  # Will be set to avoid circular import
    
    def set_statement_parser(self, statement_parser):
        """Set statement parser to avoid circular imports"""
        self.statement_parser = statement_parser
    
    def _parse_method_body(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Parse method body - delegate to statement parser if available"""
        if self.statement_parser:
            return self.statement_parser.parse_method_body(lines, start_idx)
        else:
            # Fallback simple implementation
            body = []
            i = start_idx
            expected_indent = None
            
            while i < len(lines):
                line = lines[i]
                stripped_line = line.strip()
                
                if not stripped_line:
                    i += 1
                    continue
                
                current_indent = len(line) - len(line.lstrip())
                
                if expected_indent is None:
                    expected_indent = current_indent
                
                if current_indent < expected_indent:
                    break
                
                # Simple statement conversion
                if not stripped_line.endswith(';') and not stripped_line.endswith('{') and not stripped_line.endswith('}'):
                    stripped_line += ';'
                
                body.append(stripped_line)
                i += 1
            
            return body, i
    
    def parse_method(self, lines: List[str], start_idx: int, is_static: bool = False, 
                    is_constructor: bool = False, template: Template = None) -> Tuple[Optional[Method], int]:
        """Parse a method definition with enhanced syntax"""
        line = lines[start_idx].strip()
        
        if not line or line.startswith('//'):
            return None, start_idx + 1
        
        # Parse access modifier
        access_char = line[0] if line[0] in ['*', '-', '+'] else ''
        if access_char:
            line = line[1:].strip()
        
        access = AccessModifier(access_char)
        
        # Handle constructor syntax
        if is_constructor:
            return self._parse_constructor(lines, start_idx, line, access, template)
        else:
            return self._parse_regular_method(lines, start_idx, line, access, is_static, template)
    
    def _parse_constructor(self, lines: List[str], start_idx: int, line: str, 
                          access: AccessModifier, template: Template) -> Tuple[Optional[Method], int]:
        """Parse constructor with simplified or explicit syntax"""
        # Check for simplified constructor syntax: "param1, param2:"
        if ':' in line and not line.endswith(')') and not re.match(r'.*\w+\s*\([^)]*\)\s*:', line):
            # Simplified syntax
            params_str = line.rstrip(':').strip()
            method_name = template.name if template else "Constructor"
            
            # Parse parameters and generate automatic assignments
            if template:
                parameters = self._parse_parameters_from_declared_types(params_str, template)
            else:
                parameters = self._parse_method_parameters(params_str)
            
            # Generate automatic assignments
            auto_body = []
            for param_name, param_type in parameters:
                auto_body.append(f"this.{param_name} = {param_name};")
            
            # Parse any additional custom body
            if self.statement_parser:
                custom_body, end_idx = self.statement_parser.parse_method_body(lines, start_idx + 1)
            else:
                custom_body, end_idx = self._parse_method_body(lines, start_idx + 1)
            
            full_body = auto_body + custom_body
            
            return Method(
                name=method_name,
                parameters=parameters,
                return_type="void",
                access=access,
                body=full_body,
                is_static=False,
                is_constructor=True
            ), end_idx
        else:
            # Explicit constructor syntax
            line_for_parsing = line.rstrip(':') if line.endswith(':') else line
            match = re.match(r'(\w+)\s*\((.*?)\)', line_for_parsing)
            if not match:
                return None, start_idx + 1
            
            method_name = match.group(1)
            params_str = match.group(2)
            
            if template:
                parameters = self._parse_parameters_from_declared_types(params_str, template)
            else:
                parameters = self._parse_method_parameters(params_str)
            
            if self.statement_parser:
                body, end_idx = self.statement_parser.parse_method_body(lines, start_idx + 1)
            else:
                body, end_idx = self._parse_method_body(lines, start_idx + 1)
            
            return Method(
                name=method_name,
                parameters=parameters,
                return_type="void",
                access=access,
                body=body,
                is_static=False,
                is_constructor=True
            ), end_idx
    
    def _parse_regular_method(self, lines: List[str], start_idx: int, line: str,
                             access: AccessModifier, is_static: bool, template: Template) -> Tuple[Optional[Method], int]:
        """Parse regular method definition"""
        # Parse return type
        if ' returns ' in line:
            method_part, return_type = line.split(' returns ', 1)
            return_type = return_type.strip()
        elif ' -> ' in line:
            method_part, return_type = line.split(' -> ', 1)
            return_type = return_type.strip()
        else:
            method_part = line
            return_type = "void"
        
        # Parse method name and parameters
        match = re.match(r'(\w+)\s*\((.*?)\)', method_part)
        if not match:
            return None, start_idx + 1
        
        method_name = match.group(1)
        params_str = match.group(2)
        
        # Parse parameters
        if template:
            parameters = self._parse_parameters_from_declared_types(params_str, template)
        else:
            parameters = self._parse_method_parameters(params_str)
        
        # Parse method body
        if self.statement_parser:
            body, end_idx = self.statement_parser.parse_method_body(lines, start_idx + 1)
        else:
            body, end_idx = self._parse_method_body(lines, start_idx + 1)
        
        return Method(
            name=method_name,
            parameters=parameters,
            return_type=self.type_mapping.map_type(return_type),
            access=access,
            body=body,
            is_static=is_static,
            is_constructor=False
        ), end_idx
    
    def parse_abstract_method(self, lines: List[str], start_idx: int, 
                            template: Template = None) -> Tuple[Optional[Method], int]:
        """Parse an abstract method definition (no body)"""
        line = lines[start_idx].strip()
        
        if not line or line.startswith('//'):
            return None, start_idx + 1
        
        # Parse access modifier
        access_char = line[0] if line[0] in ['*', '-', '+'] else ''
        if access_char:
            line = line[1:].strip()
        
        access = AccessModifier(access_char)
        
        # Parse method signature
        if ' returns ' in line:
            method_part, return_type = line.split(' returns ', 1)
            return_type = return_type.strip()
        elif ' -> ' in line:
            method_part, return_type = line.split(' -> ', 1)
            return_type = return_type.strip()
        else:
            method_part = line
            return_type = "void"
        
        match = re.match(r'(\w+)\s*\((.*?)\)', method_part)
        if not match:
            return None, start_idx + 1
        
        method_name = match.group(1)
        params_str = match.group(2)
        
        # Parse parameters
        if template:
            parameters = self._parse_parameters_from_declared_types(params_str, template)
        else:
            parameters = self._parse_method_parameters(params_str)
        
        return Method(
            name=method_name,
            parameters=parameters,
            return_type=self.type_mapping.map_type(return_type),
            access=access,
            body=[],  # No body for abstract methods
            is_static=False,
            is_constructor=False
        ), start_idx + 1
    
    def parse_standalone_method(self, lines: List[str], start_idx: int) -> Tuple[Optional[Method], int]:
        """Parse a standalone method (outside of templates)"""
        line = lines[start_idx].strip()
        
        # Remove 'method' keyword
        if line.startswith('method '):
            line = line[7:].strip()
        else:
            return None, start_idx + 1
        
        # Parse as a static method
        return self._parse_regular_method(lines, start_idx, line, AccessModifier.PUBLIC, True, None)
    
    def _parse_parameters_from_declared_types(self, params_str: str, template: Template) -> List[Tuple[str, str]]:
        """Parse parameters using declared variable types from template"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if ' ' in param:
                # Explicit type given
                type_, name = param.split(' ', 1)
                params.append((name.strip(), self.type_mapping.map_type(type_.strip())))
            else:
                # Look up type from declared variables or infer
                param_name = param.strip()
                param_type = self._lookup_or_infer_parameter_type(param_name, template)
                params.append((param_name, param_type))
        
        return params
    
    def _parse_method_parameters(self, params_str: str) -> List[Tuple[str, str]]:
        """Parse method parameters with explicit typing"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if ' ' in param:
                parts = param.split()
                if len(parts) >= 2:
                    type_ = parts[0]
                    name = ' '.join(parts[1:])
                    params.append((name.strip(), self.type_mapping.map_type(type_.strip())))
                else:
                    raise PseudoJavaError(f"Parameter '{param}' requires explicit type. Use 'type name' syntax.")
            else:
                raise PseudoJavaError(f"Parameter '{param}' requires explicit type. Use 'type name' syntax (e.g., 'string {param}').")
        
        return params
    
    def _lookup_or_infer_parameter_type(self, param_name: str, template: Template) -> str:
        """Look up parameter type from declared variables or infer from patterns"""
        # First check exact match
        for var in template.instance_vars + template.template_vars:
            if var.name == param_name:
                return var.type_
        
        # Check collection element patterns
        for var in template.instance_vars + template.template_vars:
            var_name_lower = var.name.lower()
            param_name_lower = param_name.lower()
            
            if var.type_.startswith('ArrayList<'):
                element_type = var.type_[10:-1]
                
                # Common plural/singular patterns
                if ((var_name_lower == 'grades' and param_name_lower == 'grade') or
                    (var_name_lower == 'courses' and param_name_lower == 'course') or
                    (var_name_lower == 'scores' and param_name_lower == 'score') or
                    (var_name_lower == 'names' and param_name_lower == 'name') or
                    (var_name_lower == 'items' and param_name_lower == 'item') or
                    (var_name_lower == 'values' and param_name_lower == 'value') or
                    (var_name_lower.endswith('s') and var_name_lower[:-1] == param_name_lower)):
                    
                    return element_type
        
        # Infer from parameter name patterns for utility classes
        if len(template.instance_vars) == 0 and len(template.template_vars) == 0:
            return self._infer_type_from_name(param_name)
        
        # If all else fails, require explicit type
        raise PseudoJavaError(
            f"Parameter '{param_name}' type cannot be determined. "
            f"Either declare '{param_name}' as a variable in the template, "
            f"or use explicit type syntax: 'type {param_name}' (e.g., 'string {param_name}')"
        )
    
    def _infer_type_from_name(self, param_name: str) -> str:
        """Infer type from parameter name patterns"""
        param_lower = param_name.lower()
        
        # Mathematical parameter names
        if param_name in ['a', 'b', 'x', 'y', 'z', 'n', 'm']:
            return "double"
        elif param_lower in ['base', 'exponent', 'power']:
            return "double" if param_lower != 'exponent' else "int"
        elif any(word in param_lower for word in ['num', 'number', 'value', 'result']):
            return "double"
        elif any(word in param_lower for word in ['count', 'size', 'index', 'length']):
            return "int"
        elif any(word in param_lower for word in ['name', 'text', 'message', 'title']):
            return "String"
        elif any(word in param_lower for word in ['flag', 'enabled', 'active', 'valid']):
            return "boolean"
        
        return "String"  # Default fallback