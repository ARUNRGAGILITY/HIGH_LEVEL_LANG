import re
import textwrap
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class AccessModifier(Enum):
    PUBLIC = "*"
    PRIVATE = "-"
    PROTECTED = "+"
    PACKAGE_PRIVATE = ""

@dataclass
class Variable:
    name: str
    type_: str
    access: AccessModifier
    initial_value: Optional[str] = None
    is_static: bool = False

@dataclass
class Method:
    name: str
    parameters: List[Tuple[str, str]]  # (name, type)
    return_type: str
    access: AccessModifier
    body: List[str]
    is_static: bool = False
    is_constructor: bool = False

@dataclass
class Template:
    name: str
    template_vars: List[Variable]
    instance_vars: List[Variable]
    constructors: List[Method]
    template_methods: List[Method]
    instance_methods: List[Method]
    getters_setters: List[Tuple[str, AccessModifier]]

class PseudoJavaParser:
    def __init__(self):
        self.access_modifiers = {
            '*': 'public',
            '-': 'private',
            '+': 'protected',
            '': ''  # package-private
        }
        
        self.type_mapping = {
            'string': 'String',
            'int': 'int',
            'byte': 'byte',
            'short': 'short',
            'long': 'long',
            'float': 'float',
            'double': 'double',
            'boolean': 'boolean',
            'char': 'char',
            'arraylist': 'ArrayList',
            'list': 'List',
            'map': 'Map',
            'hashmap': 'HashMap',
            'set': 'Set',
            'hashset': 'HashSet'
        }
        
        self.object_creation_verbs = ['create', 'make', 'spawn', 'build', 'initialize']
    
    def parse_program(self, source_code: str) -> str:
        """Parse the entire pseudo-Java program and convert to Java"""
        lines = source_code.strip().split('\n')
        
        # Check what type of syntax we're dealing with
        first_line = lines[0].strip()
        
        if first_line.startswith('template '):
            # Template-only syntax - use template name as program name
            template_name = re.match(r'template\s+(\w+)', first_line).group(1)
            program_name = template_name
            start_idx = 0
        elif first_line.startswith('program '):
            # Traditional syntax with program declaration
            program_name = self._extract_program_name(first_line)
            start_idx = 1
        elif first_line == 'main':
            # Main-only syntax - use default name
            program_name = "MainProgram"
            start_idx = 0
        else:
            # Try to find the first significant line
            program_name = "DefaultProgram"
            start_idx = 0
            
            # Look for main or template to determine the structure
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped == 'main':
                    program_name = "MainProgram"
                    start_idx = 0
                    break
                elif stripped.startswith('template '):
                    template_name = re.match(r'template\s+(\w+)', stripped).group(1)
                    program_name = template_name
                    start_idx = 0
                    break
        
        # Parse templates and main method
        templates = []
        main_method_body = []
        standalone_methods = []  # For methods outside of templates
        
        i = start_idx
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('template '):
                template, i = self._parse_template(lines, i)
                templates.append(template)
            elif line == 'main':
                main_method_body, i = self._parse_main_method(lines, i + 1)
            elif line.startswith('method '):
                # Handle standalone methods (outside of templates)
                method, i = self._parse_standalone_method(lines, i)
                if method:
                    standalone_methods.append(method)
            else:
                i += 1
        
        # Generate Java code
        return self._generate_java_code(program_name, templates, main_method_body, standalone_methods)
    
    def _extract_program_name(self, line: str) -> str:
        """Extract program name from 'program ProgramName'"""
        match = re.match(r'program\s+(\w+)', line)
        return match.group(1) if match else "DefaultProgram"
    
    def _get_indentation(self, line: str) -> int:
        """Get the indentation level of a line"""
        return len(line) - len(line.lstrip())
    
    def _parse_template(self, lines: List[str], start_idx: int) -> Tuple[Template, int]:
        """Parse a template definition"""
        template_line = lines[start_idx].strip()
        template_name = re.match(r'template\s+(\w+)', template_line).group(1)
        
        template = Template(
            name=template_name,
            template_vars=[],
            instance_vars=[],
            constructors=[],
            template_methods=[],
            instance_methods=[],
            getters_setters=[]
        )
        
        i = start_idx + 1
        current_section = None
        
        while i < len(lines):
            line = lines[i].strip()
            original_line = lines[i]
            
            if not line or line.startswith('//'):
                i += 1
                continue
            
            # Check if we've reached the end of the template
            if original_line and not original_line.startswith('    ') and not original_line.startswith('\t'):
                if line.startswith('template ') or line == 'main':
                    break
            
            # Determine current section (these are at 4-space indentation level)
            if line.endswith(':') and self._get_indentation(original_line) == 4:
                current_section = line[:-1].strip()
                i += 1
                continue
            
            # Parse based on current section (content at 8-space indentation level)
            if current_section == 'template vars' and self._get_indentation(original_line) >= 8:
                var, i = self._parse_variable(lines, i, is_static=True)
                if var:
                    template.template_vars.append(var)
            elif current_section == 'instance vars' and self._get_indentation(original_line) >= 8:
                var, i = self._parse_variable(lines, i, is_static=False)
                if var:
                    template.instance_vars.append(var)
            elif current_section == 'constructor' and self._get_indentation(original_line) >= 8:
                method, i = self._parse_method(lines, i, is_constructor=True, template=template)
                if method:
                    template.constructors.append(method)
            elif current_section == 'template methods' and self._get_indentation(original_line) >= 8:
                method, i = self._parse_method(lines, i, is_static=True, template=template)
                if method:
                    template.template_methods.append(method)
            elif current_section == 'instance methods' and self._get_indentation(original_line) >= 8:
                method, i = self._parse_method(lines, i, is_static=False, template=template)
                if method:
                    template.instance_methods.append(method)
            elif current_section == 'getters setters' and self._get_indentation(original_line) >= 8:
                getter_setter, i = self._parse_getter_setter(lines, i)
                if getter_setter:
                    template.getters_setters.append(getter_setter)
            else:
                i += 1
        
        return template, i
    
    def _parse_variable(self, lines: List[str], start_idx: int, is_static: bool) -> Tuple[Optional[Variable], int]:
        """Parse a variable declaration requiring explicit type syntax"""
        line = lines[start_idx].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('//'):
            return None, start_idx + 1
        
        # Parse access modifier (* - +)
        access_char = line[0] if line[0] in ['*', '-', '+'] else ''
        if access_char:
            line = line[1:].strip()
        
        access = AccessModifier(access_char)
        
        # Parse variable declaration - require explicit "name as type" syntax
        initial_value = None
        
        if ' with ' in line:
            # New syntax: name as type with value
            var_part, initial_value = line.split(' with ', 1)
            var_part = var_part.strip()
            initial_value = initial_value.strip()
        elif ' = ' in line:
            # Old syntax: name as type = value
            var_part, initial_value = line.split(' = ', 1)
            var_part = var_part.strip()
            initial_value = initial_value.strip()
        else:
            var_part = line.strip()
            initial_value = None
        
        # Require "name as type" syntax
        if ' as ' not in var_part:
            raise ValueError(f"Variable declaration '{line}' must use 'name as type' syntax. "
                           f"Example: 'studentId as int' or 'name as string'")
        
        name_part, type_part = var_part.split(' as ', 1)
        name = name_part.strip()
        type_ = type_part.strip()
        
        # Handle special array syntax like "arraylist/double" or "list/string"
        if '/' in type_:
            container_type, element_type = type_.split('/', 1)
            container_type = container_type.strip().lower()
            element_type = element_type.strip()
            
            # Map container types
            mapped_container = self._map_type(container_type)
            mapped_element = self._map_type(element_type)
            
            # Convert primitive types to wrapper types for generics
            if mapped_element == 'int':
                mapped_element = 'Integer'
            elif mapped_element == 'double':
                mapped_element = 'Double'
            elif mapped_element == 'float':
                mapped_element = 'Float'
            elif mapped_element == 'boolean':
                mapped_element = 'Boolean'
            elif mapped_element == 'byte':
                mapped_element = 'Byte'
            elif mapped_element == 'short':
                mapped_element = 'Short'
            elif mapped_element == 'long':
                mapped_element = 'Long'
            elif mapped_element == 'char':
                mapped_element = 'Character'
            
            if container_type in ['arraylist', 'list']:
                type_ = f"ArrayList<{mapped_element}>"
                # Auto-initialize collections if no initial value provided
                if not initial_value or initial_value == 'arraylist':
                    initial_value = f"new ArrayList<{mapped_element}>()"
            elif container_type in ['map', 'hashmap']:
                # For maps, assume String key if only one type specified
                type_ = f"HashMap<String, {mapped_element}>"
                if not initial_value or initial_value == 'hashmap':
                    initial_value = f"new HashMap<String, {mapped_element}>()"
            elif container_type in ['set', 'hashset']:
                type_ = f"HashSet<{mapped_element}>"
                if not initial_value or initial_value == 'hashset':
                    initial_value = f"new HashSet<{mapped_element}>()"
            else:
                type_ = f"{mapped_container}<{mapped_element}>"
        else:
            type_ = self._map_type(type_)
        
        return Variable(
            name=name,
            type_=type_,
            access=access,
            initial_value=initial_value,
            is_static=is_static
        ), start_idx + 1
    
    def _parse_method(self, lines: List[str], start_idx: int, is_static: bool = False, is_constructor: bool = False, template: Template = None) -> Tuple[Optional[Method], int]:
        """Parse a method definition with enhanced syntax"""
        line = lines[start_idx].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('//'):
            return None, start_idx + 1
        
        # Parse access modifier (* - +)
        access_char = line[0] if line[0] in ['*', '-', '+'] else ''
        if access_char:
            line = line[1:].strip()
        
        access = AccessModifier(access_char)
        
        # Parse method signature
        if is_constructor:
            # Constructor: * ClassName(params)
            match = re.match(r'(\w+)\s*\((.*?)\)', line)
            if not match:
                return None, start_idx + 1
            
            method_name = match.group(1)
            params_str = match.group(2)
            return_type = "void"
        else:
            # Method: * methodName(params) returns returnType OR * methodName(params) -> returnType
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
        
        # Parse parameters using declared types for both constructors and methods
        if template:
            parameters = self._parse_parameters_from_declared_types(params_str, template)
        else:
            parameters = self._parse_method_parameters(params_str)
        
        # Parse method body
        body, end_idx = self._parse_method_body(lines, start_idx + 1)
        
        return Method(
            name=method_name,
            parameters=parameters,
            return_type=self._map_type(return_type),
            access=access,
            body=body,
            is_static=is_static,
            is_constructor=is_constructor
        ), end_idx
    
    def _parse_parameters_from_declared_types(self, params_str: str, template: Template) -> List[Tuple[str, str]]:
        """Parse parameters using declared variable types from template"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if ' ' in param:
                # Explicit type given: "type name"
                type_, name = param.split(' ', 1)
                params.append((name.strip(), self._map_type(type_.strip())))
            else:
                # Look up type from declared variables or infer from name
                param_name = param.strip()
                param_type = self._lookup_or_infer_parameter_type(param_name, template)
                params.append((param_name, param_type))
        
        return params
    
    def _lookup_or_infer_parameter_type(self, param_name: str, template: Template) -> str:
        """Look up parameter type from declared variables or infer from collection types"""
        
        # First check if parameter matches a declared variable exactly
        for var in template.instance_vars + template.template_vars:
            if var.name == param_name:
                return var.type_
        
        # If not found, check if parameter name matches collection element type
        # For example: grades is ArrayList<Double>, so 'grade' parameter should be Double
        for var in template.instance_vars + template.template_vars:
            var_name_lower = var.name.lower()
            param_name_lower = param_name.lower()
            
            # Handle plural to singular mapping
            if var.type_.startswith('ArrayList<'):
                element_type = var.type_[10:-1]  # Extract type from ArrayList<Type>
                
                # Check common plural/singular patterns
                if ((var_name_lower == 'grades' and param_name_lower == 'grade') or
                    (var_name_lower == 'courses' and param_name_lower == 'course') or
                    (var_name_lower == 'scores' and param_name_lower == 'score') or
                    (var_name_lower == 'names' and param_name_lower == 'name') or
                    (var_name_lower == 'items' and param_name_lower == 'item') or
                    (var_name_lower == 'values' and param_name_lower == 'value') or
                    (var_name_lower.endswith('s') and var_name_lower[:-1] == param_name_lower)):
                    
                    return element_type
        
        # For utility templates with no instance variables, use common parameter name patterns
        if len(template.instance_vars) == 0 and len(template.template_vars) == 0:
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
        
        # If still not found, require explicit type
        raise ValueError(f"Parameter '{param_name}' type cannot be determined. "
                        f"Either declare '{param_name}' as a variable in the template, "
                        f"or use explicit type syntax: 'type {param_name}' (e.g., 'string {param_name}')")
    
    def _parse_constructor_parameters(self, params_str: str, template: Template) -> List[Tuple[str, str]]:
        """Parse constructor parameters using actual variable types from template"""
        return self._parse_parameters_from_declared_types(params_str, template)
    
    def _parse_constructor_parameters(self, params_str: str, template: Template) -> List[Tuple[str, str]]:
        """Parse constructor parameters using actual variable types from template"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if ' ' in param:
                # Explicit type given: "int studentId"
                type_, name = param.split(' ', 1)
                params.append((name.strip(), self._map_type(type_.strip())))
            else:
                # No explicit type - look up from template variables
                param_name = param.strip()
                param_type = self._lookup_variable_type(param_name, template)
                params.append((param_name, param_type))
        
        return params
    
    def _lookup_variable_type(self, var_name: str, template: Template) -> str:
        """Look up the actual type of a variable from the template - only declared types"""
        # Check instance variables first
        for var in template.instance_vars:
            if var.name == var_name:
                return var.type_
        
        # Check template variables (static)
        for var in template.template_vars:
            if var.name == var_name:
                return var.type_
        
        # If not found, this is an error - require explicit declaration
        raise ValueError(f"Constructor parameter '{var_name}' does not match any declared variable. "
                        f"Either declare '{var_name}' as an instance/template variable, "
                        f"or use explicit type syntax: 'type {var_name}' (e.g., 'string {var_name}')")
    

    

    
    def _parse_method_body(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Parse method body with proper brace handling"""
        body = []
        i = start_idx
        expected_indent = None
        brace_stack = []  # Track opening braces to ensure proper closing
        indent_stack = []  # Track indentation levels for closing braces
        
        while i < len(lines):
            line = lines[i]
            
            # Determine expected indentation from first non-empty line
            if line.strip() and expected_indent is None:
                expected_indent = self._get_indentation(line)
            
            # If line is not indented enough, we've reached the end of the method
            if line.strip():
                current_indent = self._get_indentation(line)
                if expected_indent is not None and current_indent < expected_indent:
                    break
                
                # Check if we need to close braces due to decreased indentation
                while indent_stack and current_indent <= indent_stack[-1]:
                    body.append('}')
                    indent_stack.pop()
                    if brace_stack:
                        brace_stack.pop()
            
            if line.strip():  # Skip empty lines
                # Convert pseudo-Java to Java
                java_line = self._convert_statement_to_java(line.strip())
                body.append(java_line)
                
                # Track braces for proper closing
                if java_line.endswith('{'):
                    brace_stack.append('open')
                    indent_stack.append(self._get_indentation(line))
            
            i += 1
        
        # Close any remaining open braces
        while brace_stack:
            body.append('}')
            brace_stack.pop()
        
        return body, i
    
    def _parse_standalone_method(self, lines: List[str], start_idx: int) -> Tuple[Optional[Method], int]:
        """Parse a standalone method (outside of templates)"""
        line = lines[start_idx].strip()
        
        # Remove 'method' keyword
        if line.startswith('method '):
            line = line[7:].strip()
        else:
            return None, start_idx + 1
        
        # Parse as a static method
        return self._parse_method_signature_and_body(lines, start_idx, line, is_static=True)
    
    def _parse_method_signature_and_body(self, lines: List[str], start_idx: int, signature_line: str, is_static: bool = False) -> Tuple[Optional[Method], int]:
        """Parse method signature and body from a signature line"""
        
        # Parse access modifier (* - +)
        access_char = signature_line[0] if signature_line[0] in ['*', '-', '+'] else ''
        if access_char:
            signature_line = signature_line[1:].strip()
        
        access = AccessModifier(access_char)
        
        # Parse method signature - handle both 'returns' and '->' syntax
        if ' returns ' in signature_line:
            method_part, return_type = signature_line.split(' returns ', 1)
            return_type = return_type.strip()
        elif ' -> ' in signature_line:
            method_part, return_type = signature_line.split(' -> ', 1)
            return_type = return_type.strip()
        else:
            method_part = signature_line
            return_type = "void"
        
        match = re.match(r'(\w+)\s*\((.*?)\)', method_part)
        if not match:
            return None, start_idx + 1
        
        method_name = match.group(1)
        params_str = match.group(2)
        
        # Parse parameters
        parameters = self._parse_parameters(params_str, return_type)
        
        # Parse method body
        body, end_idx = self._parse_method_body(lines, start_idx + 1)
        
        return Method(
            name=method_name,
            parameters=parameters,
            return_type=self._map_type(return_type),
            access=access,
            body=body,
            is_static=is_static,
            is_constructor=False
        ), end_idx
    
    def _parse_getter_setter(self, lines: List[str], start_idx: int) -> Tuple[Optional[Tuple[str, AccessModifier]], int]:
        """Parse getter/setter specification"""
        line = lines[start_idx].strip()
        
        if not line or line.startswith('//'):
            return None, start_idx + 1
        
        # Parse access modifier (* - +)
        access_char = line[0] if line[0] in ['*', '-', '+'] else ''
        if access_char:
            line = line[1:].strip()
        
        access = AccessModifier(access_char)
        variable_name = line.strip()
        
        return (variable_name, access), start_idx + 1
    
    def _parse_main_method(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Parse main method body with proper brace handling"""
        body = []
        i = start_idx
        brace_stack = []
        indent_stack = []
        
        while i < len(lines):
            line = lines[i]
            
            # If line is not indented, we've reached the end of main
            if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                break
            
            if line.strip():  # Skip empty lines
                current_indent = self._get_indentation(line)
                
                # Check if we need to close braces due to decreased indentation
                while indent_stack and current_indent <= indent_stack[-1]:
                    body.append('}')
                    indent_stack.pop()
                    if brace_stack:
                        brace_stack.pop()
                
                # Convert pseudo-Java to Java
                java_line = self._convert_statement_to_java(line.strip())
                body.append(java_line)
                
                # Track braces for proper closing
                if java_line.endswith('{'):
                    brace_stack.append('open')
                    indent_stack.append(current_indent)
            
            i += 1
        
        # Close any remaining open braces
        while brace_stack:
            body.append('}')
            brace_stack.pop()
        
        return body, i
    
    def _convert_statement_to_java(self, statement: str) -> str:
        """Convert a pseudo-Java statement to Java"""
        statement = statement.strip()
        
        # Handle object creation with natural language - using string concatenation to avoid f-string issues
        for verb in self.object_creation_verbs:
            # Pattern for: create alice as Student with "args"
            pattern = verb + r'\s+(\w+)\s+as\s+(\w+)\s+with\s+(.*)'
            match = re.match(pattern, statement)
            if match:
                var_name = match.group(1)
                class_name = match.group(2)
                args = match.group(3)
                return f"{class_name} {var_name} = new {class_name}({args});"
        
        # Handle object creation without arguments
        for verb in self.object_creation_verbs:
            # Pattern for: create alice as Student with
            pattern = verb + r'\s+(\w+)\s+as\s+(\w+)\s+with\s*$'
            match = re.match(pattern, statement)
            if match:
                var_name = match.group(1)
                class_name = match.group(2)
                return f"{class_name} {var_name} = new {class_name}();"
        
        # Handle arraylist initialization in assignment statements
        if '=' in statement and 'arraylist' in statement and not any(op in statement for op in ['==', '!=', '<=', '>=']):
            return self._convert_arraylist_assignment(statement)
        
        # Handle print statements - both old f-string style and new simple style
        if statement.startswith('print f"'):
            return self._convert_fstring_print(statement)
        elif statement.startswith('print '):
            content = statement[6:].strip()
            if content.startswith('"') and content.endswith('"'):
                # Traditional quoted string
                return f"System.out.println({content});"
            else:
                # New simple print syntax: print Hello {name}, you are {age} years old
                return self._convert_simple_print(content)
        
        # Handle variable declarations with enhanced syntax (only for NEW variables with 'as' keyword)
        if ' as ' in statement and '=' in statement and not any(op in statement for op in ['==', '!=', '<=', '>=']):
            return self._convert_variable_declaration(statement)
        
        # Handle simple assignments (this.field = value, field = value, etc.)
        if '=' in statement and not any(op in statement for op in ['==', '!=', '<=', '>=']):
            return self._convert_simple_assignment(statement)
        
        # Handle if statements
        if statement.startswith('if '):
            return self._convert_if_statement(statement)
        elif statement.startswith('elif '):
            return self._convert_elif_statement(statement)
        elif statement == 'else:':
            return 'else {'
        
        # Handle for loops with enhanced syntax
        if statement.startswith('for '):
            return self._convert_for_loop(statement)
        
        # Handle while loops
        if statement.startswith('while '):
            return self._convert_while_loop(statement)
        
        # Handle switch statements
        if statement.startswith('switch '):
            return self._convert_switch_statement(statement)
        
        # Handle return statements
        if statement.startswith('return '):
            return statement + ';'
        
        # Handle method calls and other statements
        if not statement.endswith(';') and not statement.endswith('{') and not statement.endswith('}'):
            return statement + ';'
        
        return statement
    
    def _convert_simple_assignment(self, statement: str) -> str:
        """Convert simple assignment statements (not variable declarations)"""
        # This handles assignments like: this.field = value, field = value, etc.
        return statement + ';'
    
    def _convert_arraylist_assignment(self, statement: str) -> str:
        """Convert arraylist assignments like 'this.grades = arraylist' to proper Java"""
        parts = statement.split('=', 1)
        if len(parts) == 2:
            left_side = parts[0].strip()
            right_side = parts[1].strip()
            
            if right_side == 'arraylist':
                # We need to infer the generic type from the variable name
                # Look for common patterns in variable names
                var_name = left_side.split('.')[-1] if '.' in left_side else left_side
                
                if 'grade' in var_name.lower():
                    return f"{left_side} = new ArrayList<Double>();"
                elif 'course' in var_name.lower():
                    return f"{left_side} = new ArrayList<String>();"
                elif 'name' in var_name.lower() or 'title' in var_name.lower():
                    return f"{left_side} = new ArrayList<String>();"
                elif 'score' in var_name.lower() or 'point' in var_name.lower():
                    return f"{left_side} = new ArrayList<Double>();"
                elif 'id' in var_name.lower() or 'num' in var_name.lower():
                    return f"{left_side} = new ArrayList<Integer>();"
                else:
                    # Default to String for unknown cases
                    return f"{left_side} = new ArrayList<String>();"
            
        # If not an arraylist assignment, this is a simple assignment
        return statement + ";"
    
    def _convert_simple_print(self, content: str) -> str:
        """Convert simple print syntax: print Hello {name}, you are {age} years old"""
        
        # Find variables in {variable} format, including format specifiers
        variables = re.findall(r'\{([^}]+)\}', content)
        
        # Replace {variable} with appropriate format specifiers
        format_str = content
        args = []
        
        for var in variables:
            # Check for format specifiers like {var:.2f}
            if ':' in var:
                var_name, format_spec = var.split(':', 1)
                var_name = var_name.strip()
                format_spec = format_spec.strip()
                
                # Convert format specifiers
                if format_spec.endswith('f'):
                    # Floating point format
                    if '.' in format_spec:
                        precision = format_spec.split('.')[1][:-1]
                        format_placeholder = f"%.{precision}f"
                    else:
                        format_placeholder = "%f"
                elif format_spec == 'd':
                    format_placeholder = "%d"
                else:
                    format_placeholder = "%s"
                
                format_str = format_str.replace(f'{{{var}}}', format_placeholder)
                args.append(var_name)
            else:
                # Check if it's a simple variable or expression
                if any(op in var for op in ['+', '-', '*', '/', '.', '(']):
                    # It's an expression, use %s and parentheses
                    format_str = format_str.replace(f'{{{var}}}', '%s')
                    args.append(f"({var})")
                else:
                    # Simple variable
                    format_str = format_str.replace(f'{{{var}}}', '%s')
                    args.append(var)
        
        if args:
            args_str = ', ' + ', '.join(args)
            return f'System.out.println(String.format("{format_str}"{args_str}));'
        else:
            return f'System.out.println("{format_str}");'
        """Convert f-string print to Java String.format"""
        # Extract the f-string content
        match = re.match(r'print f"(.*?)"', statement)
        if not match:
            return statement + ';'
        
        content = match.group(1)
        
        # Find variables in {variable} format, including format specifiers
        variables = re.findall(r'\{([^}]+)\}', content)
        
        # Replace {variable} with appropriate format specifiers
        format_str = content
        args = []
        
        for var in variables:
            # Check for format specifiers like {var:.2f}
            if ':' in var:
                var_name, format_spec = var.split(':', 1)
                var_name = var_name.strip()
                format_spec = format_spec.strip()
                
                # Convert format specifiers
                if format_spec.endswith('f'):
                    # Floating point format
                    if '.' in format_spec:
                        precision = format_spec.split('.')[1][:-1]
                        format_placeholder = f"%.{precision}f"
                    else:
                        format_placeholder = "%f"
                elif format_spec == 'd':
                    format_placeholder = "%d"
                else:
                    format_placeholder = "%s"
                
                format_str = format_str.replace(f'{{{var}}}', format_placeholder)
                args.append(var_name)
            else:
                # Check if it's a simple variable or expression
                if any(op in var for op in ['+', '-', '*', '/', '.', '(']):
                    # It's an expression, use %s and parentheses
                    format_str = format_str.replace(f'{{{var}}}', '%s')
                    args.append(f"({var})")
                else:
                    # Simple variable
                    format_str = format_str.replace(f'{{{var}}}', '%s')
                    args.append(var)
        
        if args:
            args_str = ', ' + ', '.join(args)
            return f'System.out.println(String.format("{format_str}"{args_str}));'
        else:
            return f'System.out.println("{format_str}");'
    
    def _convert_variable_declaration(self, statement: str) -> str:
        """Convert variable declaration requiring explicit syntax"""
        if statement.startswith('var '):
            # Type inference not allowed for safety
            raise ValueError(f"Variable declaration '{statement}' must use explicit type syntax. "
                           f"Use 'name as type' instead of 'var name = value'")
        elif ' as ' in statement:
            # New syntax: name as type = value OR name as type with value
            if ' = ' in statement:
                var_part, value = statement.split(' = ', 1)
                var_part = var_part.strip()
                value = value.strip()
            else:
                var_part = statement.strip()
                value = None
            
            if ' as ' in var_part:
                name_part, type_part = var_part.split(' as ', 1)
                name = name_part.strip()
                type_ = type_part.strip()
                
                # Handle special array syntax like "arraylist/double"
                if '/' in type_:
                    container_type, element_type = type_.split('/', 1)
                    container_type = container_type.strip().lower()
                    element_type = element_type.strip()
                    
                    mapped_container = self._map_type(container_type)
                    mapped_element = self._map_type(element_type)
                    
                    # Convert primitive types to wrapper types for generics
                    if mapped_element == 'int':
                        mapped_element = 'Integer'
                    elif mapped_element == 'double':
                        mapped_element = 'Double'
                    elif mapped_element == 'float':
                        mapped_element = 'Float'
                    elif mapped_element == 'boolean':
                        mapped_element = 'Boolean'
                    elif mapped_element == 'byte':
                        mapped_element = 'Byte'
                    elif mapped_element == 'short':
                        mapped_element = 'Short'
                    elif mapped_element == 'long':
                        mapped_element = 'Long'
                    elif mapped_element == 'char':
                        mapped_element = 'Character'
                    
                    if container_type in ['arraylist', 'list']:
                        java_type = f"ArrayList<{mapped_element}>"
                        if not value:
                            value = f"new ArrayList<{mapped_element}>()"
                    elif container_type in ['map', 'hashmap']:
                        java_type = f"HashMap<String, {mapped_element}>"
                        if not value:
                            value = f"new HashMap<String, {mapped_element}>()"
                    elif container_type in ['set', 'hashset']:
                        java_type = f"HashSet<{mapped_element}>"
                        if not value:
                            value = f"new HashSet<{mapped_element}>()"
                    else:
                        java_type = f"{mapped_container}<{mapped_element}>"
                else:
                    java_type = self._map_type(type_)
                
                if value:
                    # Fix for arraylist initialization in constructor body
                    if value == 'arraylist' and java_type.startswith('ArrayList'):
                        generic_type = java_type[10:-1]  # Extract type from ArrayList<Type>
                        value = f"new ArrayList<{generic_type}>()"
                    return f"{java_type} {name} = {value};"
                else:
                    return f"{java_type} {name};"
            
        else:
            # Old syntax - require explicit types
            if '=' in statement and not any(op in statement for op in ['==', '!=', '<=', '>=']):
                raise ValueError(f"Variable declaration '{statement}' must use explicit type syntax. "
                               f"Use 'name as type = value' instead of implicit typing")
            return statement + ';'
    
    def _convert_if_statement(self, statement: str) -> str:
        """Convert if statement"""
        condition = statement[3:].rstrip(':')
        # Convert logical operators
        condition = condition.replace(' and ', ' && ')
        condition = condition.replace(' or ', ' || ')
        condition = condition.replace(' not ', ' !')
        return f"if ({condition}) {{"
    
    def _convert_elif_statement(self, statement: str) -> str:
        """Convert elif statement"""
        condition = statement[5:].rstrip(':')
        condition = condition.replace(' and ', ' && ')
        condition = condition.replace(' or ', ' || ')
        condition = condition.replace(' not ', ' !')
        return f"}} else if ({condition}) {{"
    
    def _convert_for_loop(self, statement: str) -> str:
        """Convert for loop with enhanced syntax"""
        # Handle different for loop patterns
        if ' in range(' in statement:
            # for i in range(start, end) OR for i in range(expression)
            pattern = r'for\s+(\w+)\s+in\s+range\((.*?)\):'
            match = re.match(pattern, statement)
            if match:
                var = match.group(1)
                range_expr = match.group(2).strip()
                
                # Handle range(expression) where expression might be a method call
                if ',' not in range_expr:
                    # Single argument: range(end)
                    return f"for (int {var} = 0; {var} < {range_expr}; {var}++) {{"
                else:
                    # Two arguments: range(start, end)
                    range_args = range_expr.split(',')
                    start = range_args[0].strip()
                    end = range_args[1].strip()
                    return f"for (int {var} = {start}; {var} < {end}; {var}++) {{"
        elif ' in ' in statement:
            # Enhanced for loop
            match = re.match(r'for\s+(\w+)\s+in\s+([^:]+):', statement)
            if match:
                var = match.group(1)
                collection = match.group(2).strip()
                return f"for (var {var} : {collection}) {{"
        
        return statement
    
    def _convert_while_loop(self, statement: str) -> str:
        """Convert while loop"""
        condition = statement[6:].rstrip(':')
        condition = condition.replace(' and ', ' && ')
        condition = condition.replace(' or ', ' || ')
        condition = condition.replace(' not ', ' !')
        return f"while ({condition}) {{"
    
    def _convert_switch_statement(self, statement: str) -> str:
        """Convert switch statement"""
        variable = statement[7:].rstrip(':')
        return f"switch ({variable}) {{"
    
    def _map_type(self, type_str: str) -> str:
        """Map pseudo-Java types to Java types"""
        return self.type_mapping.get(type_str.lower(), type_str)
    
    def _generate_java_code(self, program_name: str, templates: List[Template], main_body: List[str], standalone_methods: List[Method] = None) -> str:
        """Generate complete Java code with smart template merging"""
        if standalone_methods is None:
            standalone_methods = []
            
        java_code = []
        
        # Generate imports
        java_code.append("import java.util.*;")
        java_code.append("import java.util.Scanner;")
        java_code.append("")
        
        # Case 1: Template with main method - merge into single class
        if len(templates) == 1 and templates[0].name == program_name and main_body:
            template = templates[0]
            java_code.extend(self._generate_single_class_with_main(template, main_body, standalone_methods))
        
        # Case 2: Template only (no main method) - generate just the template class
        elif len(templates) == 1 and not main_body:
            template = templates[0]
            java_code.extend(self._generate_template_class(template))
        
        # Case 3: Main method with separate template classes
        elif main_body:
            java_code.extend(self._generate_main_class_with_separate_templates(program_name, templates, main_body, standalone_methods))
        
        # Case 4: Just standalone methods (no templates, no main)
        else:
            java_code.append(f"public class {program_name} {{")
            
            for method in standalone_methods:
                lines = self._generate_method_code(method)
                for line in lines:
                    java_code.append(line)
                java_code.append("")
            
            java_code.append("}")
        
        return '\n'.join(java_code)
    
    def _generate_single_class_with_main(self, template: Template, main_body: List[str], standalone_methods: List[Method]) -> List[str]:
        """Generate a single class that contains everything including main method"""
        lines = []
        
        lines.append(f"public class {template.name} {{")
        
        # Generate template variables (static)
        for var in template.template_vars:
            access_str = self.access_modifiers[var.access.value]
            initial = f" = {var.initial_value}" if var.initial_value else ""
            
            if access_str:
                lines.append(f"    {access_str} static {var.type_} {var.name}{initial};")
            else:
                lines.append(f"    static {var.type_} {var.name}{initial};")
        
        if template.template_vars:
            lines.append("")
        
        # Generate instance variables
        for var in template.instance_vars:
            access_str = self.access_modifiers[var.access.value]
            initial = f" = {var.initial_value}" if var.initial_value else ""
            
            if access_str:
                lines.append(f"    {access_str} {var.type_} {var.name}{initial};")
            else:
                lines.append(f"    {var.type_} {var.name}{initial};")
        
        if template.instance_vars:
            lines.append("")
        
        # Generate constructors
        for constructor in template.constructors:
            constructor_lines = self._generate_method_code(constructor, template.name)
            for line in constructor_lines:
                lines.append(line)
            lines.append("")
        
        # Generate template methods (static)
        for method in template.template_methods:
            method_lines = self._generate_method_code(method)
            for line in method_lines:
                lines.append(line)
            lines.append("")
        
        # Generate instance methods
        for method in template.instance_methods:
            method_lines = self._generate_method_code(method)
            for line in method_lines:
                lines.append(line)
            lines.append("")
        
        # Generate getters and setters
        for var_name, access in template.getters_setters:
            var = self._find_variable(template, var_name)
            if var:
                getter_setter_lines = self._generate_getter_setter(var, access)
                for line in getter_setter_lines:
                    lines.append(line)
                lines.append("")
        
        # Generate standalone methods
        for method in standalone_methods:
            method_lines = self._generate_method_code(method)
            for line in method_lines:
                lines.append(line)
            lines.append("")
        
        # Generate main method
        lines.append("    public static void main(String[] args) {")
        for line in main_body:
            lines.append(f"        {line}")
        lines.append("    }")
        
        lines.append("}")
        
        return lines
    
    def _generate_main_class_with_separate_templates(self, program_name: str, templates: List[Template], main_body: List[str], standalone_methods: List[Method]) -> List[str]:
        """Generate main class with separate template classes"""
        lines = []
        
        # Check for utility templates that should be merged into main class
        main_class_methods = []
        regular_templates = []
        
        for template in templates:
            # Check if this is a utility template (only static methods, no instance data)
            is_utility_template = (
                len(template.instance_vars) == 0 and 
                len(template.constructors) == 0 and 
                len(template.getters_setters) == 0 and
                len(template.instance_methods) == 0 and
                len(template.template_methods) > 0
            )
            
            # If it's a utility template with the same name as the program, merge it
            if is_utility_template and template.name == program_name:
                main_class_methods.extend(template.template_methods)
            else:
                # This is a regular template - create separate class
                regular_templates.append(template)
        
        # Add standalone methods to main class
        main_class_methods.extend(standalone_methods)
        
        # Generate main class
        lines.append(f"public class {program_name} {{")
        
        # Add merged utility methods and standalone methods to main class
        for method in main_class_methods:
            method_lines = self._generate_method_code(method)
            for line in method_lines:
                lines.append(line)
            lines.append("")
        
        # Generate main method
        lines.append("    public static void main(String[] args) {")
        for line in main_body:
            lines.append(f"        {line}")
        lines.append("    }")
        
        lines.append("}")
        lines.append("")
        
        # Generate regular template classes (if any)
        for template in regular_templates:
            template_lines = self._generate_template_class(template)
            lines.extend(template_lines)
            lines.append("")
        
        return lines
    
    def _generate_template_class(self, template: Template) -> List[str]:
        """Generate Java class from template"""
        lines = []
        
        lines.append(f"class {template.name} {{")
        
        # Generate template variables (static)
        for var in template.template_vars:
            access_str = self.access_modifiers[var.access.value]
            initial = f" = {var.initial_value}" if var.initial_value else ""
            
            if access_str:
                lines.append(f"    {access_str} static {var.type_} {var.name}{initial};")
            else:
                lines.append(f"    static {var.type_} {var.name}{initial};")
        
        if template.template_vars:
            lines.append("")
        
        # Generate instance variables
        for var in template.instance_vars:
            access_str = self.access_modifiers[var.access.value]
            initial = f" = {var.initial_value}" if var.initial_value else ""
            
            if access_str:
                lines.append(f"    {access_str} {var.type_} {var.name}{initial};")
            else:
                lines.append(f"    {var.type_} {var.name}{initial};")
        
        if template.instance_vars:
            lines.append("")
        
        # Generate constructors
        for constructor in template.constructors:
            lines.extend(self._generate_method_code(constructor, template.name))
            lines.append("")
        
        # Generate template methods (static)
        for method in template.template_methods:
            lines.extend(self._generate_method_code(method))
            lines.append("")
        
        # Generate instance methods
        for method in template.instance_methods:
            lines.extend(self._generate_method_code(method))
            lines.append("")
        
        # Generate getters and setters
        for var_name, access in template.getters_setters:
            var = self._find_variable(template, var_name)
            if var:
                lines.extend(self._generate_getter_setter(var, access))
                lines.append("")
        
        lines.append("}")
        
        return lines
    
    def _generate_method_code(self, method: Method, class_name: str = None) -> List[str]:
        """Generate Java method code"""
        lines = []
        
        access_str = self.access_modifiers[method.access.value]
        static_keyword = "static " if method.is_static else ""
        
        # Build parameter list
        params = ", ".join([f"{param_type} {param_name}" for param_name, param_type in method.parameters])
        
        # Build method signature
        if method.is_constructor:
            if access_str:
                signature = f"{access_str} {class_name}({params})"
            else:
                signature = f"{class_name}({params})"
        else:
            return_type = method.return_type if method.return_type != "void" else "void"
            if access_str:
                signature = f"{access_str} {static_keyword}{return_type} {method.name}({params})"
            else:
                signature = f"{static_keyword}{return_type} {method.name}({params})"
        
        lines.append(f"    {signature} {{")
        
        # Add method body
        for line in method.body:
            lines.append(f"        {line}")
        
        lines.append("    }")
        
        return lines
    
    def _generate_getter_setter(self, var: Variable, access: AccessModifier) -> List[str]:
        """Generate getter and setter methods"""
        lines = []
        access_str = self.access_modifiers[access.value]
        
        # Getter
        getter_name = f"get{var.name.capitalize()}"
        if access_str:
            lines.append(f"    {access_str} {var.type_} {getter_name}() {{")
        else:
            lines.append(f"    {var.type_} {getter_name}() {{")
        lines.append(f"        return {var.name};")
        lines.append("    }")
        lines.append("")
        
        # Setter
        setter_name = f"set{var.name.capitalize()}"
        if access_str:
            lines.append(f"    {access_str} void {setter_name}({var.type_} {var.name}) {{")
        else:
            lines.append(f"    void {setter_name}({var.type_} {var.name}) {{")
        lines.append(f"        this.{var.name} = {var.name};")
        lines.append("    }")
        
        return lines
    
    def _find_variable(self, template: Template, var_name: str) -> Optional[Variable]:
        """Find variable in template by name"""
        for var in template.instance_vars + template.template_vars:
            if var.name == var_name:
                return var
        return None


def main():
    """Command line interface for the parser"""
    import argparse
    import sys
    import os
    
    parser = argparse.ArgumentParser(
        description='Pseudo Java Language Parser - Convert pseudo-Java to Java',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python pseudo_java_parser.py input.pj -o output.java
  python pseudo_java_parser.py input.pj --output-dir src/main/java
  python pseudo_java_parser.py input.pj --compile
  python pseudo_java_parser.py --test
        '''
    )
    
    parser.add_argument('input', nargs='?', help='Input pseudo-Java file (.pj)')
    parser.add_argument('-o', '--output', help='Output Java file')
    parser.add_argument('--output-dir', help='Output directory for Java files')
    parser.add_argument('-c', '--compile', action='store_true', help='Compile generated Java code')
    parser.add_argument('-r', '--run', action='store_true', help='Compile and run the generated Java code')
    parser.add_argument('--test', action='store_true', help='Run built-in test')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version='Pseudo Java Parser 1.0')
    
    args = parser.parse_args()
    
    # Handle test mode
    if args.test:
        test_parser()
        return
    
    # Validate input
    if not args.input:
        parser.print_help()
        sys.exit(1)
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Read input file
        with open(args.input, 'r', encoding='utf-8') as f:
            pseudo_code = f.read()
        
        if args.verbose:
            print(f"Reading pseudo-Java file: {args.input}")
        
        # Parse the code
        pj_parser = PseudoJavaParser()
        java_code = pj_parser.parse_program(pseudo_code)
        
        # Extract program name - handle all syntax types
        first_line = pseudo_code.strip().split('\n')[0]
        if first_line.startswith('template '):
            # Template-only syntax - use template name
            program_name = re.match(r'template\s+(\w+)', first_line).group(1)
        elif first_line.startswith('program '):
            # Traditional syntax with program declaration
            program_name = pj_parser._extract_program_name(first_line)
        elif first_line == 'main':
            # Main-only syntax - use default name
            program_name = "MainProgram"
        else:
            # Look for main or template in the file
            program_name = "DefaultProgram"
            for line in pseudo_code.split('\n'):
                stripped = line.strip()
                if stripped == 'main':
                    program_name = "MainProgram"
                    break
                elif stripped.startswith('template '):
                    template_match = re.match(r'template\s+(\w+)', stripped)
                    if template_match:
                        program_name = template_match.group(1)
                        break
        
        # Determine output file
        if args.output:
            output_file = args.output
        elif args.output_dir:
            # Use program name with specified directory
            output_file = os.path.join(args.output_dir, f"{program_name}.java")
        else:
            # Default: use program name in current directory
            output_file = f"{program_name}.java"
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            if args.verbose:
                print(f"Created directory: {output_dir}")
        
        # Write Java code
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(java_code)
        
        print(f"Generated Java code: {output_file}")
        
        # Compile if requested
        if args.compile or args.run:
            if args.verbose:
                print("Compiling Java code...")
            
            compile_result = os.system(f"javac {output_file}")
            if compile_result == 0:
                print("Compilation successful!")
                
                # Run if requested
                if args.run:
                    if args.verbose:
                        print("Running Java program...")
                    
                    # Extract class name
                    class_name = os.path.splitext(os.path.basename(output_file))[0]
                    class_dir = os.path.dirname(output_file) or "."
                    
                    run_result = os.system(f"cd {class_dir} && java {class_name}")
                    if run_result != 0:
                        print("Runtime error occurred.", file=sys.stderr)
                        sys.exit(1)
            else:
                print("Compilation failed!", file=sys.stderr)
                sys.exit(1)
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def test_parser():
    """Test the parser with enhanced syntax"""
    
    sample_code = '''template Student
    template vars:
        * totalStudents as int with 0
        - schoolName as string with "Tech University"
        
    instance vars:
        * studentId as int
        * name as string
        - grades as arraylist/double
        + courses as arraylist/string
        gpa as double
        
    constructor:
        * Student(studentId, name)
            this.studentId = studentId
            this.name = name
            this.grades = arraylist
            this.courses = arraylist
            this.gpa = 0.0
            totalStudents += 1
            
    template methods:
        * getTotalStudents() returns int
            return totalStudents
            
        * getSchoolName() returns string
            return schoolName
            
    instance methods:
        * addGrade(string course, double grade)
            courses.add(course)
            grades.add(grade)
            updateGPA()
            print f"Added grade {grade} for course {course}"
            
        * getGPA() returns double
            return gpa
            
        - updateGPA()
            if grades.size() == 0:
                gpa = 0.0
                return
                
            total as double = 0.0
            for grade in grades:
                total += grade
                
            gpa = total / grades.size()
            
        * printTranscript()
            print f"=== TRANSCRIPT ==="
            print f"Student: {name} (ID: {studentId})"
            print f"School: {getSchoolName()}"
            print f"Courses: {courses.size()}"
            print f"GPA: {gpa:.2f}"
            
            for i in range(courses.size()):
                courseName as string = courses.get(i)
                grade as double = grades.get(i)
                print f"{courseName}: {grade}"
    
    getters setters:
        * name
        + studentId

main
    print f"Welcome to {Student.getSchoolName()}"
    
    create alice as Student with "S001", "Alice Johnson"
    make bob as Student with "S002", "Bob Smith"
    
    alice.addGrade("Math", 92.5)
    alice.addGrade("Science", 88.0)
    alice.addGrade("English", 95.0)
    
    bob.addGrade("Math", 78.5)
    bob.addGrade("Science", 82.0)
    bob.addGrade("History", 90.0)
    
    alice.printTranscript()
    bob.printTranscript()
    
    print f"Total students: {Student.getTotalStudents()}"
'''
    
    print("Enhanced syntax test:")
    print("====================")
    
    parser = PseudoJavaParser()
    java_code = parser.parse_program(sample_code)
    
    print("Generated Java Code:")
    print("=" * 50)
    print(java_code)


if __name__ == "__main__":
    main()


# this is the latest version with print statement in general syntax
# works with level1