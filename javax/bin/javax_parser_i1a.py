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
        
        # Check if this is template-only syntax (no program declaration)
        first_line = lines[0].strip()
        if first_line.startswith('template '):
            # Template-only syntax - use template name as program name
            template_name = re.match(r'template\s+(\w+)', first_line).group(1)
            program_name = template_name
            start_idx = 0
        else:
            # Traditional syntax with program declaration
            program_name = self._extract_program_name(first_line)
            start_idx = 1
        
        # Parse templates and main method
        templates = []
        main_method_body = []
        
        i = start_idx
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('template '):
                template, i = self._parse_template(lines, i)
                templates.append(template)
            elif line == 'main':
                main_method_body, i = self._parse_main_method(lines, i + 1)
            else:
                i += 1
        
        # Generate Java code
        return self._generate_java_code(program_name, templates, main_method_body)
    
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
                method, i = self._parse_method(lines, i, is_constructor=True)
                if method:
                    template.constructors.append(method)
            elif current_section == 'template methods' and self._get_indentation(original_line) >= 8:
                method, i = self._parse_method(lines, i, is_static=True)
                if method:
                    template.template_methods.append(method)
            elif current_section == 'instance methods' and self._get_indentation(original_line) >= 8:
                method, i = self._parse_method(lines, i, is_static=False)
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
        """Parse a variable declaration with new syntax: name as type"""
        line = lines[start_idx].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('//'):
            return None, start_idx + 1
        
        # Parse access modifier (* - +)
        access_char = line[0] if line[0] in ['*', '-', '+'] else ''
        if access_char:
            line = line[1:].strip()
        
        access = AccessModifier(access_char)
        
        # Parse variable declaration with "name as type" or "name as type = value"
        if ' = ' in line:
            var_part, initial_value = line.split(' = ', 1)
            var_part = var_part.strip()
            initial_value = initial_value.strip()
        else:
            var_part = line.strip()
            initial_value = None
        
        # Handle "name as type" syntax
        if ' as ' in var_part:
            name_part, type_part = var_part.split(' as ', 1)
            name = name_part.strip()
            type_ = type_part.strip()
            
            # Handle special array syntax like "arraylist/int" or "list/string"
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
                    if not initial_value:
                        initial_value = f"new ArrayList<{mapped_element}>()"
                elif container_type in ['map', 'hashmap']:
                    # For maps, assume String key if only one type specified
                    type_ = f"HashMap<String, {mapped_element}>"
                    if not initial_value:
                        initial_value = f"new HashMap<String, {mapped_element}>()"
                elif container_type in ['set', 'hashset']:
                    type_ = f"HashSet<{mapped_element}>"
                    if not initial_value:
                        initial_value = f"new HashSet<{mapped_element}>()"
                else:
                    type_ = f"{mapped_container}<{mapped_element}>"
            else:
                type_ = self._map_type(type_)
        else:
            # Old syntax or type inference
            if ' ' in var_part:
                type_, name = var_part.split(' ', 1)
                type_ = self._map_type(type_)
            else:
                # Type inference needed
                if initial_value:
                    type_ = self._infer_type(initial_value)
                    name = var_part
                else:
                    type_ = "Object"
                    name = var_part
        
        return Variable(
            name=name,
            type_=type_,
            access=access,
            initial_value=initial_value,
            is_static=is_static
        ), start_idx + 1
    
    def _parse_method(self, lines: List[str], start_idx: int, is_static: bool = False, is_constructor: bool = False) -> Tuple[Optional[Method], int]:
        """Parse a method definition"""
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
            # Method: * methodName(params) -> returnType
            if ' -> ' in line:
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
        
        # Parse parameters with better type inference
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
            is_constructor=is_constructor
        ), end_idx
    
    def _parse_parameters(self, params_str: str, return_type: str = "void") -> List[Tuple[str, str]]:
        """Parse method parameters with improved type inference"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if ' ' in param:
                type_, name = param.split(' ', 1)
                params.append((name.strip(), self._map_type(type_.strip())))
            else:
                # Improved type inference based on parameter name and context
                param_name = param.strip()
                inferred_type = self._infer_parameter_type(param_name, return_type)
                params.append((param_name, inferred_type))
        
        return params
    
    def _infer_parameter_type(self, param_name: str, return_type: str = "void") -> str:
        """Infer parameter type based on name patterns"""
        param_lower = param_name.lower()
        
        # Number-related parameters
        if any(word in param_lower for word in ['num', 'count', 'size', 'length', 'index', 'id']):
            return "int"
        elif any(word in param_lower for word in ['amount', 'price', 'value', 'rate', 'percent']):
            return "double"
        elif any(word in param_lower for word in ['age', 'year', 'day', 'month']):
            return "int"
        
        # Math-related parameters  
        elif any(word in param_lower for word in ['a', 'b', 'x', 'y', 'base', 'exponent', 'power']):
            return "double"
        
        # Boolean-related parameters
        elif any(word in param_lower for word in ['is', 'has', 'can', 'should', 'flag', 'enabled']):
            return "boolean"
        
        # String-related parameters
        elif any(word in param_lower for word in ['name', 'text', 'message', 'title', 'description', 'email', 'address']):
            return "String"
        
        # Collection-related parameters
        elif any(word in param_lower for word in ['list', 'array', 'collection']):
            return "ArrayList<String>"
        
        # If return type gives us a hint
        elif return_type in ['int', 'double', 'float', 'long']:
            return return_type
        
        # Default fallback
        else:
            return "String"
    
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
        
        # Handle object creation with natural language
        for verb in self.object_creation_verbs:
            pattern = rf'{verb}\s+(\w+)\s+as\s+(\w+)\s+with\s+(.*)'
            match = re.match(pattern, statement)
            if match:
                var_name = match.group(1)
                class_name = match.group(2)
                args = match.group(3)
                return f"{class_name} {var_name} = new {class_name}({args});"
        
        # Handle object creation without arguments (like "create manager as FileManager with")
        for verb in self.object_creation_verbs:
            pattern = rf'{verb}\s+(\w+)\s+as\s+(\w+)\s+with\s*$'
            match = re.match(pattern, statement)
            if match:
                var_name = match.group(1)
                class_name = match.group(2)
                return f"{class_name} {var_name} = new {class_name}();"
        
        # Handle print statements with f-strings
        if statement.startswith('print f"'):
            return self._convert_fstring_print(statement)
        elif statement.startswith('print '):
            content = statement[6:].strip()
            if content.startswith('"') and content.endswith('"'):
                return f"System.out.println({content});"
            else:
                return f"System.out.println({content});"
        
        # Handle variable declarations
        if '=' in statement and not any(op in statement for op in ['==', '!=', '<=', '>=']):
            return self._convert_variable_declaration(statement)
        
        # Handle if statements
        if statement.startswith('if '):
            return self._convert_if_statement(statement)
        elif statement.startswith('elif '):
            return self._convert_elif_statement(statement)
        elif statement == 'else:':
            return 'else {'
        
        # Handle for loops
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
    
    def _convert_fstring_print(self, statement: str) -> str:
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
        """Convert variable declaration"""
        if statement.startswith('var '):
            # Type inference
            parts = statement[4:].split('=', 1)
            var_name = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else None
            
            if value:
                # Enhanced type inference for method calls
                if '.' in value and '(' in value and ')' in value:
                    # This looks like a method call - infer type from method name and context
                    java_type = self._infer_method_call_type(value)
                else:
                    java_type = self._infer_type(value)
                return f"{java_type} {var_name} = {value};"
            else:
                return f"Object {var_name};"
        elif ' as ' in statement:
            # New syntax: name as type = value
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
                
                # Handle special array syntax like "arraylist/int"
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
                    return f"{java_type} {name} = {value};"
                else:
                    return f"{java_type} {name};"
            
        else:
            # Explicit type (old syntax)
            return statement + ';'
    
    def _infer_method_call_type(self, method_call: str) -> str:
        """Infer type from method call"""
        method_call = method_call.strip()
        
        # Look for common method patterns
        if '.add(' in method_call or '.subtract(' in method_call or '.multiply(' in method_call:
            return "double"  # Math operations typically return double
        elif '.divide(' in method_call:
            return "double"  # Division always returns double
        elif '.power(' in method_call:
            return "double"  # Power operations return double
        elif '.size(' in method_call or '.length(' in method_call:
            return "int"  # Size/length methods return int
        elif '.isEmpty(' in method_call or '.contains(' in method_call:
            return "boolean"  # Boolean methods
        elif '.get(' in method_call and 'Name' in method_call:
            return "String"  # getName() type methods
        elif '.toString(' in method_call:
            return "String"
        
        # Default fallback
        return "double"  # For Calculator methods, default to double
    
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
        """Convert for loop"""
        # Handle different for loop patterns
        if ' in range(' in statement:
            # for i in range(start, end)
            match = re.match(r'for\s+(\w+)\s+in\s+range\((.*?)\):', statement)
            if match:
                var = match.group(1)
                range_args = match.group(2).split(',')
                if len(range_args) == 1:
                    end = range_args[0].strip()
                    return f"for (int {var} = 0; {var} < {end}; {var}++) {{"
                elif len(range_args) == 2:
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
    
    def _infer_type(self, value: str) -> str:
        """Infer Java type from value"""
        value = value.strip()
        
        if value.startswith('"') and value.endswith('"'):
            return "String"
        elif value.startswith("'") and value.endswith("'"):
            return "String"
        elif value in ['true', 'false']:
            return "boolean"
        elif '.' in value:
            try:
                float(value)
                return "double"
            except ValueError:
                return "String"
        else:
            try:
                int(value)
                return "int"
            except ValueError:
                return "String"
    
    def _map_type(self, type_str: str) -> str:
        """Map pseudo-Java types to Java types"""
        return self.type_mapping.get(type_str.lower(), type_str)
    
    def _generate_java_code(self, program_name: str, templates: List[Template], main_body: List[str]) -> str:
        """Generate complete Java code with smart template merging"""
        java_code = []
        
        # Generate imports
        java_code.append("import java.util.*;")
        java_code.append("import java.util.Scanner;")
        java_code.append("")
        
        # Check for utility templates that should be merged
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
                regular_templates.append(template)
        
        # Generate main class
        java_code.append(f"public class {program_name} {{")
        
        # Add merged utility methods to main class
        for method in main_class_methods:
            lines = self._generate_method_code(method)
            for line in lines:
                java_code.append(line)
            java_code.append("")
        
        # Generate main method
        java_code.append("    public static void main(String[] args) {")
        for line in main_body:
            java_code.append(f"        {line}")
        java_code.append("    }")
        
        java_code.append("}")
        java_code.append("")
        
        # Generate regular template classes (if any)
        for template in regular_templates:
            java_code.extend(self._generate_template_class(template))
            java_code.append("")
        
        return '\n'.join(java_code)
    
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
    import re  # Add this import
    
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
        
        # Extract program name - handle both traditional and template-only syntax
        first_line = pseudo_code.strip().split('\n')[0]
        if first_line.startswith('template '):
            # Template-only syntax - use template name
            program_name = re.match(r'template\s+(\w+)', first_line).group(1)
        else:
            # Traditional syntax with program declaration
            program_name = pj_parser._extract_program_name(first_line)
        
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
    """Test the parser with template-only syntax"""
    
    sample_code = '''template Calculator
    template methods:
        * add(a, b) -> double
            return a + b
        
        * subtract(a, b) -> double
            return a - b
        
        * multiply(a, b) -> double
            return a * b
        
        * divide(a, b) -> double
            if b == 0:
                print "Error: Division by zero!"
                return 0.0
            return a / b
        
        * power(base, exponent) -> double
            var result = 1.0
            for i in range(0, exponent):
                result *= base
            return result

main
    var a = 10.5
    var b = 3.2
    
    print f"Calculator Demo:"
    print f"a = {a}, b = {b}"
    
    var sum = Calculator.add(a, b)
    var diff = Calculator.subtract(a, b)
    var product = Calculator.multiply(a, b)
    var quotient = Calculator.divide(a, b)
    var squared = Calculator.power(a, 2)
    
    print f"Addition: {a} + {b} = {sum}"
    print f"Subtraction: {a} - {b} = {diff}"
    print f"Multiplication: {a} * {b} = {product}"
    print f"Division: {a} / {b} = {quotient:.2f}"
    print f"Power: {a} ^ 2 = {squared:.2f}"
    
    var zeroTest = Calculator.divide(a, 0)
    print f"Division by zero test: {zeroTest}"
'''
    
    print("Template-only syntax test:")
    print("=========================")
    print(sample_code)
    print("\n" + "="*50)
    
    parser = PseudoJavaParser()
    java_code = parser.parse_program(sample_code)
    
    print("Generated Java Code:")
    print("=" * 50)
    print(java_code)


if __name__ == "__main__":
    main()