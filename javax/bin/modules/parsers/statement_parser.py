# modules/parsers/statement_parser.py
"""
Statement parser for the Pseudo Java Parser
Handles conversion of pseudo-Java statements to Java
"""

import re
from typing import List, Tuple

from utils.exceptions import PseudoJavaError


class StatementParser:
    """Parser for individual statements and method bodies"""
    
    def __init__(self, synonym_config, type_mapping):
        self.synonym_config = synonym_config
        self.type_mapping = type_mapping
    
    def parse_method_body(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Parse method body with proper brace handling and section detection"""
        body = []
        i = start_idx
        expected_indent = None
        brace_stack = []
        indent_stack = []
        
        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                i += 1
                continue
            
            current_indent = self._get_indentation(line)
            
            # Check if this is a section header
            if self._is_section_header(stripped_line, current_indent):
                break
            
            # Check if we've reached another template or main
            if (current_indent == 0 and 
                (self._is_template_line(stripped_line) or stripped_line == 'main')):
                break
            
            # Determine expected indentation from first non-empty line
            if expected_indent is None:
                expected_indent = current_indent
            
            # If line is not indented enough, we've reached the end of the method
            if current_indent < expected_indent:
                break
            
            # Check if we need to close braces due to decreased indentation
            while indent_stack and current_indent <= indent_stack[-1]:
                body.append('}')
                indent_stack.pop()
                if brace_stack:
                    brace_stack.pop()
            
            # Convert pseudo-Java to Java
            java_line = self.convert_statement_to_java(stripped_line)
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
    
    def convert_statement_to_java(self, statement: str) -> str:
        """Convert a pseudo-Java statement to Java"""
        statement = statement.strip()
        
        # Handle object creation with natural language
        for verb in self.synonym_config.object_creation_verbs:
            # Pattern: create alice as Student with "args"
            pattern = verb + r'\s+(\w+)\s+as\s+(\w+)\s+with\s+(.*)'
            match = re.match(pattern, statement)
            if match:
                var_name = match.group(1)
                class_name = match.group(2)
                args = match.group(3)
                return f"{class_name} {var_name} = new {class_name}({args});"
        
        # Handle object creation without arguments
        for verb in self.synonym_config.object_creation_verbs:
            pattern = verb + r'\s+(\w+)\s+as\s+(\w+)\s+with\s*$'
            match = re.match(pattern, statement)
            if match:
                var_name = match.group(1)
                class_name = match.group(2)
                return f"{class_name} {var_name} = new {class_name}();"
        
        # Handle print statements
        if statement.startswith('print f"'):
            return self._convert_fstring_print(statement)
        elif statement.startswith('print '):
            return self._convert_simple_print(statement)
        
        # Handle variable declarations
        if ' as ' in statement and '=' in statement and not any(op in statement for op in ['==', '!=', '<=', '>=']):
            return self._convert_variable_declaration(statement)
        
        # Handle simple assignments
        if '=' in statement and not any(op in statement for op in ['==', '!=', '<=', '>=']):
            return self._convert_simple_assignment(statement)
        
        # Handle control structures
        if statement.startswith('if '):
            return self._convert_if_statement(statement)
        elif statement.startswith('elif '):
            return self._convert_elif_statement(statement)
        elif statement == 'else:':
            return 'else {'
        elif statement.startswith('for '):
            return self._convert_for_loop(statement)
        elif statement.startswith('while '):
            return self._convert_while_loop(statement)
        elif statement.startswith('switch '):
            return self._convert_switch_statement(statement)
        
        # Handle return statements
        if statement.startswith('return '):
            return statement + ';'
        
        # Handle method calls and other statements
        if not statement.endswith(';') and not statement.endswith('{') and not statement.endswith('}'):
            return statement + ';'
        
        return statement
    
    def _convert_simple_print(self, statement: str) -> str:
        """Convert simple print syntax"""
        content = statement[6:].strip()  # Remove 'print '
        if content.startswith('"') and content.endswith('"'):
            return f"System.out.println({content});"
        else:
            return self._convert_interpolated_print(content)
    
    def _convert_interpolated_print(self, content: str) -> str:
        """Convert print with variable interpolation"""
        variables = re.findall(r'\{([^}]+)\}', content)
        format_str = content
        args = []
        
        for var in variables:
            if ':' in var:
                var_name, format_spec = var.split(':', 1)
                var_name = var_name.strip()
                format_spec = format_spec.strip()
                
                if format_spec.endswith('f'):
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
                if any(op in var for op in ['+', '-', '*', '/', '.', '(']):
                    format_str = format_str.replace(f'{{{var}}}', '%s')
                    args.append(f"({var})")
                else:
                    format_str = format_str.replace(f'{{{var}}}', '%s')
                    args.append(var)
        
        if args:
            args_str = ', ' + ', '.join(args)
            return f'System.out.println(String.format("{format_str}"{args_str}));'
        else:
            return f'System.out.println("{format_str}");'
    
    def _convert_fstring_print(self, statement: str) -> str:
        """Convert f-string print to Java String.format"""
        match = re.match(r'print f"(.*?)"', statement)
        if not match:
            return statement + ';'
        
        content = match.group(1)
        return self._convert_interpolated_print(content)
    
    def _convert_variable_declaration(self, statement: str) -> str:
        """Convert variable declaration with explicit syntax"""
        if ' as ' in statement:
            if ' = ' in statement:
                var_part, value = statement.split(' = ', 1)
            else:
                var_part = statement.strip()
                value = None
            
            if ' as ' in var_part:
                name_part, type_part = var_part.split(' as ', 1)
                name = name_part.strip()
                type_ = type_part.strip()
                
                # Handle collection syntax
                java_type, final_value = self._process_collection_type_in_declaration(type_, value)
                
                if final_value:
                    return f"{java_type} {name} = {final_value};"
                else:
                    return f"{java_type} {name};"
        
        return statement + ';'
    
    def _process_collection_type_in_declaration(self, type_: str, value: str) -> Tuple[str, str]:
        """Process collection types in variable declarations"""
        if '/' in type_:
            container_type, element_type = type_.split('/', 1)
            container_type = container_type.strip().lower()
            element_type = element_type.strip()
            
            mapped_container = self.type_mapping.map_type(container_type)
            mapped_element = self.type_mapping.map_type(element_type)
            
            if self.type_mapping.is_primitive_type(mapped_element):
                mapped_element = self.type_mapping.get_wrapper_type(mapped_element)
            
            if container_type in ['arraylist', 'list']:
                java_type = f"ArrayList<{mapped_element}>"
                if not value or value == 'arraylist':
                    value = f"new ArrayList<{mapped_element}>()"
            elif container_type in ['map', 'hashmap']:
                java_type = f"HashMap<String, {mapped_element}>"
                if not value or value == 'hashmap':
                    value = f"new HashMap<String, {mapped_element}>()"
            elif container_type in ['set', 'hashset']:
                java_type = f"HashSet<{mapped_element}>"
                if not value or value == 'hashset':
                    value = f"new HashSet<{mapped_element}>()"
            else:
                java_type = f"{mapped_container}<{mapped_element}>"
        else:
            java_type = self.type_mapping.map_type(type_)
        
        return java_type, value
    
    def _convert_simple_assignment(self, statement: str) -> str:
        """Convert simple assignment statements"""
        return statement + ';'
    
    def _convert_if_statement(self, statement: str) -> str:
        """Convert if statement"""
        condition = statement[3:].rstrip(':')
        condition = self._convert_logical_operators(condition)
        return f"if ({condition}) {{"
    
    def _convert_elif_statement(self, statement: str) -> str:
        """Convert elif statement"""
        condition = statement[5:].rstrip(':')
        condition = self._convert_logical_operators(condition)
        return f"}} else if ({condition}) {{"
    
    def _convert_for_loop(self, statement: str) -> str:
        """Convert for loop with enhanced syntax"""
        if ' in range(' in statement:
            pattern = r'for\s+(\w+)\s+in\s+range\((.*?)\):'
            match = re.match(pattern, statement)
            if match:
                var = match.group(1)
                range_expr = match.group(2).strip()
                
                if ',' not in range_expr:
                    return f"for (int {var} = 0; {var} < {range_expr}; {var}++) {{"
                else:
                    range_args = range_expr.split(',')
                    start = range_args[0].strip()
                    end = range_args[1].strip()
                    return f"for (int {var} = {start}; {var} < {end}; {var}++) {{"
        elif ' in ' in statement:
            match = re.match(r'for\s+(\w+)\s+in\s+([^:]+):', statement)
            if match:
                var = match.group(1)
                collection = match.group(2).strip()
                return f"for (var {var} : {collection}) {{"
        
        return statement
    
    def _convert_while_loop(self, statement: str) -> str:
        """Convert while loop"""
        condition = statement[6:].rstrip(':')
        condition = self._convert_logical_operators(condition)
        return f"while ({condition}) {{"
    
    def _convert_switch_statement(self, statement: str) -> str:
        """Convert switch statement"""
        variable = statement[7:].rstrip(':')
        return f"switch ({variable}) {{"
    
    def _convert_logical_operators(self, condition: str) -> str:
        """Convert logical operators from pseudo-Java to Java"""
        condition = condition.replace(' and ', ' && ')
        condition = condition.replace(' or ', ' || ')
        condition = condition.replace(' not ', ' !')
        return condition
    
    def _is_section_header(self, stripped_line: str, current_indent: int) -> bool:
        """Check if line is a section header"""
        if not stripped_line.endswith(':') or current_indent != 4:
            return False
        
        section_name = stripped_line[:-1].strip()
        known_sections = [
            'instance vars', 'constructor', 'instance methods', 'getters setters'
        ]
        
        # Add template-specific sections
        for synonym in self.synonym_config.template_synonyms:
            known_sections.extend([f'{synonym} vars', f'{synonym} methods'])
        
        known_sections.extend(self.synonym_config.abstract_methods_synonyms)
        
        return section_name in known_sections
    
    def _is_template_line(self, stripped_line: str) -> bool:
        """Check if line starts a new template"""
        for synonym in self.synonym_config.template_synonyms:
            pattern = f'^{synonym}\\s+(\\w+)'
            if re.match(pattern, stripped_line, re.IGNORECASE):
                return True
        return False
    
    def _get_indentation(self, line: str) -> int:
        """Get the indentation level of a line"""
        return len(line) - len(line.lstrip())