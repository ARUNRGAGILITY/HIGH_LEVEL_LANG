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
        in_multiline_comment = False
        
        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()
            
            # Handle multi-line comments with """
            if '"""' in stripped_line:
                if not in_multiline_comment:
                    in_multiline_comment = True
                    if stripped_line.startswith('"""') and stripped_line.endswith('"""') and len(stripped_line) > 6:
                        comment_content = stripped_line[3:-3].strip()
                        body.append(f"/* {comment_content} */")
                        in_multiline_comment = False
                    elif stripped_line.startswith('"""'):
                        comment_content = stripped_line[3:].strip()
                        if comment_content:
                            body.append(f"/* {comment_content}")
                        else:
                            body.append("/*")
                    else:
                        code_part, comment_part = stripped_line.split('"""', 1)
                        if code_part.strip():
                            java_line = self.convert_statement_to_java(code_part.strip())
                            body.append(java_line)
                        if comment_part.strip():
                            body.append(f"/* {comment_part.strip()}")
                        else:
                            body.append("/*")
                else:
                    if stripped_line.endswith('"""'):
                        comment_content = stripped_line[:-3].strip()
                        if comment_content:
                            body.append(f"   {comment_content} */")
                        else:
                            body.append("*/")
                        in_multiline_comment = False
                    else:
                        comment_part, code_part = stripped_line.split('"""', 1)
                        if comment_part.strip():
                            body.append(f"   {comment_part.strip()} */")
                        else:
                            body.append("*/")
                        in_multiline_comment = False
                        if code_part.strip():
                            java_line = self.convert_statement_to_java(code_part.strip())
                            body.append(java_line)
                i += 1
                continue
            
            if in_multiline_comment:
                if stripped_line:
                    body.append(f"   {stripped_line}")
                else:
                    body.append("")
                i += 1
                continue
            
            if not stripped_line:
                body.append('')
                i += 1
                continue
            
            if stripped_line.startswith('//'):
                body.append(stripped_line)
                i += 1
                continue
            
            if stripped_line.startswith('#'):
                comment_content = stripped_line[1:].strip()
                body.append(f"// {comment_content}")
                i += 1
                continue
            
            current_indent = self._get_indentation(line)
            
            if self._is_section_header(stripped_line, current_indent):
                break
            
            if (current_indent == 0 and 
                (self._is_template_line(stripped_line) or stripped_line == 'main')):
                break
            
            if expected_indent is None:
                expected_indent = current_indent
            
            if current_indent < expected_indent:
                break
                
            while indent_stack and current_indent <= indent_stack[-1]:
                body.append('}')
                indent_stack.pop()
                if brace_stack:
                    brace_stack.pop()
            
            comment_found = False
            java_line = ""
            
            if '//' in stripped_line:
                code_part, comment_part = stripped_line.split('//', 1)
                code_part = code_part.strip()
                comment_part = comment_part.strip()
                comment_found = True
                
                if code_part:
                    java_line = self.convert_statement_to_java(code_part)
                    if comment_part:
                        if java_line.endswith(';'):
                            java_line = java_line[:-1] + f"; // {comment_part}"
                        elif java_line.endswith('{'):
                            java_line = java_line + f" // {comment_part}"
                        else:
                            java_line = java_line + f" // {comment_part}"
                else:
                    java_line = f"// {comment_part}"
            
            elif '#' in stripped_line:
                code_part, comment_part = stripped_line.split('#', 1)
                code_part = code_part.strip()
                comment_part = comment_part.strip()
                comment_found = True
                
                if code_part:
                    java_line = self.convert_statement_to_java(code_part)
                    if comment_part:
                        if java_line.endswith(';'):
                            java_line = java_line[:-1] + f"; // {comment_part}"
                        elif java_line.endswith('{'):
                            java_line = java_line + f" // {comment_part}"
                        else:
                            java_line = java_line + f" // {comment_part}"
                else:
                    java_line = f"// {comment_part}"
            
            if not comment_found:
                java_line = self.convert_statement_to_java(stripped_line)
            
            body.append(java_line)
            
            if java_line.endswith('{'):
                brace_stack.append('open')
                indent_stack.append(current_indent)
            
            i += 1
        
        while brace_stack:
            body.append('}')
            brace_stack.pop()
        
        return body, i
    
    def convert_statement_to_java(self, statement: str) -> str:
        """Convert a pseudo-Java statement to Java"""
        statement = statement.strip()
        
        if statement.startswith('print f"'):
            return self._convert_fstring_print(statement)
        elif statement.startswith('print '):
            return self._convert_simple_print(statement)
        
        if self._is_variable_declaration(statement):
            return self._convert_variable_declaration(statement)
        
        if self._is_collection_operation(statement):
            return self._convert_collection_operation(statement)
        
        if '=' in statement and not any(op in statement for op in ['==', '!=', '<=', '>=']):
            return self._convert_simple_assignment(statement)
        
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
        
        if statement.startswith('return '):
            return statement + ';'
        
        if not statement.endswith(';') and not statement.endswith('{') and not statement.endswith('}'):
            return statement + ';'
        
        return statement
    
    def _is_variable_declaration(self, statement: str) -> bool:
        """Check if statement is a variable declaration"""
        if statement.startswith('var '):
            return True
        
        if ' as ' in statement:
            if ' with ' in statement or ('=' in statement and not any(op in statement for op in ['==', '!=', '<=', '>='])):
                return True
            
            parts = statement.split(' as ')
            if len(parts) == 2:
                name_part = parts[0].strip()
                type_part = parts[1].strip()
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name_part):
                    if not any(keyword in type_part.lower() for keyword in [' to ', ' from ', ' in ', ' at ', ' into ']):
                        return True
        
        return False
    
    def _is_collection_operation(self, statement: str) -> bool:
        """Check if statement is a collection operation"""
        if statement.startswith('print '):
            return False
            
        stmt_lower = statement.lower()
        
        patterns = [
            r'add\s+.+\s+to\s+\w+',
            r'append\s+.+\s+to\s+\w+',
            r'remove\s+.+\s+from\s+\w+',
            r'remove\s+index\s+.+\s+from\s+\w+',
            r'remove\s+value\s+.+\s+from\s+\w+',
            r'clear\s+\w+',
            r'size\s+of\s+\w+',
            r'length\s+of\s+\w+',
            r'count\s+of\s+\w+',
            r'is\s+empty\s+\w+',
            r'contains\s+.+\s+in\s+\w+',
            r'has\s+.+\s+in\s+\w+',
            r'index\s+of\s+.+\s+in\s+\w+',
            r'get\s+.+\s+from\s+\w+',
            r'get\s+item\s+at\s+.+\s+from\s+\w+',
            r'get\s+first\s+from\s+\w+',
            r'get\s+last\s+from\s+\w+',
            r'first\s+in\s+\w+',
            r'last\s+in\s+\w+',
            r'set\s+.+\s+in\s+\w+\s+to\s+.+',
            r'set\s+item\s+at\s+.+\s+in\s+\w+\s+to\s+.+',
            r'insert\s+.+\s+into\s+\w+\s+at\s+.+',
            r'put\s+.+\s+with\s+.+\s+in\s+\w+',
            r'keys\s+of\s+\w+',
            r'values\s+of\s+\w+',
            r'push\s+.+\s+to\s+\w+',
            r'pop\s+from\s+\w+',
            r'peek\s+\w+',
            r'enqueue\s+.+\s+to\s+\w+',
            r'dequeue\s+from\s+\w+',
            r'offer\s+.+\s+to\s+\w+',
            r'poll\s+from\s+\w+',
            r'add\s+first\s+.+\s+to\s+\w+',
            r'add\s+last\s+.+\s+to\s+\w+',
            r'pop\s+first\s+from\s+\w+',
            r'pop\s+last\s+from\s+\w+',
            r'\w+\.add\s*\(\s*first\s+.+\)',
            r'\w+\.add\s*\(\s*last\s+.+\)',
            r'\w+\.set\s*\(.+\)',
            r'sort\s+\w+',
            r'reverse\s+\w+',
            r'shuffle\s+\w+'
        ]
        
        for pattern in patterns:
            if re.match(pattern, stmt_lower):
                return True
        
        return False
    
    def _convert_variable_declaration(self, statement: str) -> str:
        """Convert variable declaration"""
        if statement.startswith('var '):
            var_content = statement[4:].strip()
            if ' = ' in var_content:
                name, value = var_content.split(' = ', 1)
                name = name.strip()
                value = value.strip()
                if self._is_collection_operation(value):
                    value = self._convert_collection_operation_expression(value)
                return f"var {name} = {value};"
            else:
                raise PseudoJavaError(f"Variable declaration '{statement}' with 'var' requires initialization.")
        
        elif ' as ' in statement:
            var_part = statement
            value = None
            
            if ' with ' in statement:
                var_part, value = statement.split(' with ', 1)
                var_part = var_part.strip()
                value = value.strip()
            elif ' = ' in statement:
                var_part, value = statement.split(' = ', 1)
                var_part = var_part.strip()
                value = value.strip()
                if value and self._is_collection_operation(value):
                    value = self._convert_collection_operation_expression(value)
            
            if ' as ' in var_part:
                name_part, type_part = var_part.split(' as ', 1)
                name = name_part.strip()
                type_ = type_part.strip()
                
                java_type, final_value = self._process_collection_type_in_declaration(type_, value)
                
                if final_value:
                    return f"{java_type} {name} = {final_value};"
                else:
                    return f"{java_type} {name};"
            else:
                raise PseudoJavaError(f"Variable declaration '{statement}' must use 'name as type' syntax.")
        
        return statement + ';'
    
    def _convert_collection_operation(self, statement: str) -> str:
        """Convert collection operations to Java statements"""
        converted = self._convert_collection_operation_expression(statement)
        if not converted.endswith(';'):
            converted += ';'
        return converted
    
    def _convert_collection_operation_expression(self, statement: str) -> str:
        """Convert collection operations to Java expressions"""
        stmt_lower = statement.lower()
        
        # Java-style LinkedList operations that need conversion
        if re.match(r'\w+\.add\s*\(\s*first\s+.+\)', stmt_lower):
            match = re.match(r'(\w+)\.add\s*\(\s*first\s+(.+)\)', statement, re.IGNORECASE)
            if match:
                collection, item = match.groups()
                return f"{collection}.addFirst({item.strip()})"
        
        if re.match(r'\w+\.add\s*\(\s*last\s+.+\)', stmt_lower):
            match = re.match(r'(\w+)\.add\s*\(\s*last\s+(.+)\)', statement, re.IGNORECASE)
            if match:
                collection, item = match.groups()
                return f"{collection}.addLast({item.strip()})"
        
        # Handle HashMap set operations -> put operations
        if re.match(r'\w+\.set\s*\(.+\)', stmt_lower):
            match = re.match(r'(\w+)\.set\s*\(\s*(.+?)\s*,\s*(.+?)\s*\)', statement, re.IGNORECASE)
            if match:
                collection, key, value = match.groups()
                return f"{collection}.put({key.strip()}, {value.strip()})"
        
        # Add to collection
        if re.match(r'add\s+.+\s+to\s+\w+', stmt_lower):
            match = re.match(r'add\s+(.+?)\s+to\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.add({item.strip()})"
        
        # Append to collection
        if re.match(r'append\s+.+\s+to\s+\w+', stmt_lower):
            match = re.match(r'append\s+(.+?)\s+to\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.add({item.strip()})"
        
        # Remove operations
        if re.match(r'remove\s+index\s+.+\s+from\s+\w+', stmt_lower):
            match = re.match(r'remove\s+index\s+(.+?)\s+from\s+(\w+)', statement, re.IGNORECASE)
            if match:
                index, collection = match.groups()
                return f"{collection}.remove({index.strip()})"
        elif re.match(r'remove\s+value\s+.+\s+from\s+\w+', stmt_lower):
            match = re.match(r'remove\s+value\s+(.+?)\s+from\s+(\w+)', statement, re.IGNORECASE)
            if match:
                value, collection = match.groups()
                value = value.strip()
                if value.isdigit() and not value.startswith('"'):
                    return f"{collection}.remove(Integer.valueOf({value}))"
                else:
                    return f"{collection}.remove({value})"
        elif re.match(r'remove\s+.+\s+from\s+\w+', stmt_lower):
            match = re.match(r'remove\s+(.+?)\s+from\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                item = item.strip()
                if item.startswith('"') and item.endswith('"'):
                    return f"{collection}.remove({item})"
                elif item.isdigit():
                    return f"{collection}.remove(Integer.valueOf({item}))"
                else:
                    return f"{collection}.remove({item})"
        
        # Clear collection
        if re.match(r'clear\s+\w+', stmt_lower):
            collection = statement[6:].strip()
            return f"{collection}.clear()"
        
        # Size operations
        if re.match(r'size\s+of\s+\w+', stmt_lower):
            collection = statement[8:].strip()
            return f"{collection}.size()"
        
        if re.match(r'length\s+of\s+\w+', stmt_lower):
            collection = statement[10:].strip()
            return f"{collection}.size()"
        
        if re.match(r'count\s+of\s+\w+', stmt_lower):
            collection = statement[9:].strip()
            return f"{collection}.size()"
        
        # Contains operations
        if re.match(r'contains\s+.+\s+in\s+\w+', stmt_lower):
            match = re.match(r'contains\s+(.+?)\s+in\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.contains({item.strip()})"
        
        if re.match(r'has\s+.+\s+in\s+\w+', stmt_lower):
            match = re.match(r'has\s+(.+?)\s+in\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.contains({item.strip()})"
        
        # Get operations
        if re.match(r'get\s+item\s+at\s+.+\s+from\s+\w+', stmt_lower):
            match = re.match(r'get\s+item\s+at\s+(.+?)\s+from\s+(\w+)', statement, re.IGNORECASE)
            if match:
                index, collection = match.groups()
                return f"{collection}.get({index.strip()})"
        elif re.match(r'get\s+first\s+from\s+\w+', stmt_lower):
            collection = statement[15:].strip()
            return f"{collection}.getFirst()"
        elif re.match(r'get\s+last\s+from\s+\w+', stmt_lower):
            collection = statement[14:].strip()
            return f"{collection}.getLast()"
        elif re.match(r'get\s+.+\s+from\s+\w+', stmt_lower):
            match = re.match(r'get\s+(.+?)\s+from\s+(\w+)', statement, re.IGNORECASE)
            if match:
                index, collection = match.groups()
                return f"{collection}.get({index.strip()})"
        
        # Set operations
        if re.match(r'set\s+item\s+at\s+.+\s+in\s+\w+\s+to\s+.+', stmt_lower):
            match = re.match(r'set\s+item\s+at\s+(.+?)\s+in\s+(\w+)\s+to\s+(.+)', statement, re.IGNORECASE)
            if match:
                index, collection, value = match.groups()
                return f"{collection}.set({index.strip()}, {value.strip()})"
        elif re.match(r'set\s+.+\s+in\s+\w+\s+to\s+.+', stmt_lower):
            match = re.match(r'set\s+(.+?)\s+in\s+(\w+)\s+to\s+(.+)', statement, re.IGNORECASE)
            if match:
                index, collection, value = match.groups()
                return f"{collection}.set({index.strip()}, {value.strip()})"
        
        # Insert operation
        if re.match(r'insert\s+.+\s+into\s+\w+\s+at\s+.+', stmt_lower):
            match = re.match(r'insert\s+(.+?)\s+into\s+(\w+)\s+at\s+(.+)', statement, re.IGNORECASE)
            if match:
                item, collection, index = match.groups()
                return f"{collection}.add({index.strip()}, {item.strip()})"
        
        # First/Last operations
        if re.match(r'first\s+in\s+\w+', stmt_lower):
            collection = statement[9:].strip()
            return f"{collection}.get(0)"
        
        if re.match(r'last\s+in\s+\w+', stmt_lower):
            collection = statement[8:].strip()
            return f"{collection}.get({collection}.size() - 1)"
        
        # Index operation
        if re.match(r'index\s+of\s+.+\s+in\s+\w+', stmt_lower):
            match = re.match(r'index\s+of\s+(.+?)\s+in\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.indexOf({item.strip()})"
        
        # Is empty
        if re.match(r'is\s+empty\s+\w+', stmt_lower):
            collection = statement[9:].strip()
            return f"{collection}.isEmpty()"
        
        # Map operations
        if re.match(r'put\s+.+\s+with\s+.+\s+in\s+\w+', stmt_lower):
            match = re.match(r'put\s+(.+?)\s+with\s+(.+?)\s+in\s+(\w+)', statement, re.IGNORECASE)
            if match:
                key, value, collection = match.groups()
                return f"{collection}.put({key.strip()}, {value.strip()})"
        
        if re.match(r'keys\s+of\s+\w+', stmt_lower):
            collection = statement[8:].strip()
            return f"{collection}.keySet()"
        
        if re.match(r'values\s+of\s+\w+', stmt_lower):
            collection = statement[10:].strip()
            return f"{collection}.values()"
        
        # Stack operations
        if re.match(r'push\s+.+\s+to\s+\w+', stmt_lower):
            match = re.match(r'push\s+(.+?)\s+to\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.push({item.strip()})"
        
        if re.match(r'pop\s+from\s+\w+', stmt_lower):
            collection = statement[9:].strip()
            return f"{collection}.pop()"
        
        if re.match(r'peek\s+\w+', stmt_lower):
            collection = statement[5:].strip()
            return f"{collection}.peek()"
        
        # Queue operations
        if re.match(r'enqueue\s+.+\s+to\s+\w+', stmt_lower):
            match = re.match(r'enqueue\s+(.+?)\s+to\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.offer({item.strip()})"
        
        if re.match(r'dequeue\s+from\s+\w+', stmt_lower):
            collection = statement[13:].strip()
            return f"{collection}.poll()"
        
        if re.match(r'offer\s+.+\s+to\s+\w+', stmt_lower):
            match = re.match(r'offer\s+(.+?)\s+to\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.offer({item.strip()})"
        
        if re.match(r'poll\s+from\s+\w+', stmt_lower):
            collection = statement[10:].strip()
            return f"{collection}.poll()"
        
        # LinkedList specific operations
        if re.match(r'add\s+first\s+.+\s+to\s+\w+', stmt_lower):
            match = re.match(r'add\s+first\s+(.+?)\s+to\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.addFirst({item.strip()})"
        
        if re.match(r'add\s+last\s+.+\s+to\s+\w+', stmt_lower):
            match = re.match(r'add\s+last\s+(.+?)\s+to\s+(\w+)', statement, re.IGNORECASE)
            if match:
                item, collection = match.groups()
                return f"{collection}.addLast({item.strip()})"
        
        if re.match(r'pop\s+first\s+from\s+\w+', stmt_lower):
            collection = statement[15:].strip()
            return f"{collection}.removeFirst()"
        
        if re.match(r'pop\s+last\s+from\s+\w+', stmt_lower):
            collection = statement[14:].strip()
            return f"{collection}.removeLast()"
        
        # Collection utilities
        if re.match(r'sort\s+\w+', stmt_lower):
            collection = statement[5:].strip()
            return f"Collections.sort({collection})"
        
        if re.match(r'reverse\s+\w+', stmt_lower):
            collection = statement[8:].strip()
            return f"Collections.reverse({collection})"
        
        if re.match(r'shuffle\s+\w+', stmt_lower):
            collection = statement[8:].strip()
            return f"Collections.shuffle({collection})"
        
        return statement
    
    def _convert_simple_print(self, statement: str) -> str:
        """Convert simple print syntax"""
        content = statement[6:].strip()
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
                if self._is_collection_operation(var):
                    converted_var = self._convert_collection_operation_expression(var)
                    format_str = format_str.replace(f'{{{var}}}', '%s')
                    args.append(f"({converted_var})")
                elif any(op in var for op in ['+', '-', '*', '/', '.', '(']):
                    format_str = format_str.replace(f'{{{var}}}', '%s')
                    args.append(f"({var})")
                else:
                    format_str = format_str.replace(f'{{{var}}}', '%s')
                    args.append(var)
        
        format_str = format_str.replace('"', '\\"')
        
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
            elif container_type in ['linkedlist']:
                java_type = f"LinkedList<{mapped_element}>"
                if not value or value == 'linkedlist':
                    value = f"new LinkedList<{mapped_element}>()"
            elif container_type in ['map', 'hashmap']:
                java_type = f"HashMap<String, {mapped_element}>"
                if not value or value == 'hashmap':
                    value = f"new HashMap<String, {mapped_element}>()"
            elif container_type in ['treemap']:
                java_type = f"TreeMap<String, {mapped_element}>"
                if not value or value == 'treemap':
                    value = f"new TreeMap<String, {mapped_element}>()"
            elif container_type in ['set', 'hashset']:
                java_type = f"HashSet<{mapped_element}>"
                if not value or value == 'hashset':
                    value = f"new HashSet<{mapped_element}>()"
            elif container_type in ['treeset']:
                java_type = f"TreeSet<{mapped_element}>"
                if not value or value == 'treeset':
                    value = f"new TreeSet<{mapped_element}>()"
            elif container_type in ['stack']:
                java_type = f"Stack<{mapped_element}>"
                if not value or value == 'stack':
                    value = f"new Stack<{mapped_element}>()"
            elif container_type in ['queue']:
                java_type = f"ArrayDeque<{mapped_element}>"
                if not value or value == 'queue':
                    value = f"new ArrayDeque<{mapped_element}>()"
            elif container_type in ['deque', 'arraydeque']:
                java_type = f"ArrayDeque<{mapped_element}>"
                if not value or value in ['deque', 'arraydeque']:
                    value = f"new ArrayDeque<{mapped_element}>()"
            elif container_type in ['vector']:
                java_type = f"Vector<{mapped_element}>"
                if not value or value == 'vector':
                    value = f"new Vector<{mapped_element}>()"
            else:
                java_type = f"{mapped_container}<{mapped_element}>"
        else:
            java_type = self.type_mapping.map_type(type_)
        
        return java_type, value
    
    def _convert_simple_assignment(self, statement: str) -> str:
        """Convert simple assignment statements"""
        if '=' in statement:
            left, right = statement.split('=', 1)
            left = left.strip()
            right = right.strip()
            
            if self._is_collection_operation(right):
                right = self._convert_collection_operation_expression(right)
            
            return f"{left} = {right};"
        
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
        """Convert for loop"""
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
                
                if collection.startswith('keys of '):
                    map_name = collection[8:].strip()
                    return f"for (var {var} : {map_name}.keySet()) {{"
                elif collection.startswith('values of '):
                    map_name = collection[10:].strip()
                    return f"for (var {var} : {map_name}.values()) {{"
                elif collection.startswith('each ') or collection.startswith('all '):
                    actual_collection = collection.split()[-1]
                    return f"for (var {var} : {actual_collection}) {{"
                else:
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
        """Convert logical operators"""
        condition = condition.replace(' and ', ' && ')
        condition = condition.replace(' or ', ' || ')
        condition = condition.replace(' not ', ' !')
        return condition
    
    def _is_section_header(self, stripped_line: str, current_indent: int) -> bool:
        """Check if line is a section header"""
        if stripped_line == 'main' and current_indent == 4:
            return True
            
        if not stripped_line.endswith(':') or current_indent != 4:
            return False
        
        section_name = stripped_line[:-1].strip()
        known_sections = [
            'instance vars', 'constructor', 'instance methods', 'getters setters', 'main'
        ]
        
        if hasattr(self.synonym_config, 'template_synonyms'):
            for synonym in self.synonym_config.template_synonyms:
                known_sections.extend([f'{synonym} vars', f'{synonym} methods'])
        
        if hasattr(self.synonym_config, 'abstract_methods_synonyms'):
            known_sections.extend(self.synonym_config.abstract_methods_synonyms)
        
        return section_name in known_sections
    
    def _is_template_line(self, stripped_line: str) -> bool:
        """Check if line starts a new template"""
        if hasattr(self.synonym_config, 'template_synonyms'):
            for synonym in self.synonym_config.template_synonyms:
                pattern = f'^{synonym}\\s+(\\w+)'
                if re.match(pattern, stripped_line, re.IGNORECASE):
                    return True
        return False
    
    def _get_indentation(self, line: str) -> int:
        """Get the indentation level of a line"""
        return len(line) - len(line.lstrip())