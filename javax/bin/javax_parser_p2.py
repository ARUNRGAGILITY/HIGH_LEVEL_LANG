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
            'double': 'double',
            'boolean': 'boolean',
            'List': 'List',
            'Map': 'Map'
        }
        
        self.object_creation_verbs = ['create', 'make', 'spawn', 'build', 'initialize']
    
    def parse_program(self, source_code: str) -> str:
        """Parse the entire pseudo-Java program and convert to Java"""
        lines = source_code.strip().split('\n')
        
        # Find program name
        program_name = self._extract_program_name(lines[0])
        
        # Parse templates and main method
        templates = []
        main_method_body = []
        
        i = 1
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
            
            if not line or line.startswith('//'):
                i += 1
                continue
            
            # Check if we've reached the end of the template
            if not line.startswith(' ') and not line.startswith('\t') and line != '':
                if line.startswith('template ') or line == 'main':
                    break
            
            # Determine current section
            if line.endswith(':'):
                current_section = line[:-1].strip()
                i += 1
                continue
            
            # Parse based on current section
            if current_section == 'template vars':
                var, i = self._parse_variable(lines, i, is_static=True)
                if var:
                    template.template_vars.append(var)
            elif current_section == 'instance vars':
                var, i = self._parse_variable(lines, i, is_static=False)
                if var:
                    template.instance_vars.append(var)
            elif current_section == 'constructor':
                method, i = self._parse_method(lines, i, is_constructor=True)
                if method:
                    template.constructors.append(method)
            elif current_section == 'template methods':
                method, i = self._parse_method(lines, i, is_static=True)
                if method:
                    template.template_methods.append(method)
            elif current_section == 'instance methods':
                method, i = self._parse_method(lines, i, is_static=False)
                if method:
                    template.instance_methods.append(method)
            elif current_section == 'getters setters':
                getter_setter, i = self._parse_getter_setter(lines, i)
                if getter_setter:
                    template.getters_setters.append(getter_setter)
            else:
                i += 1
        
        return template, i
    
    def _parse_variable(self, lines: List[str], start_idx: int, is_static: bool) -> Tuple[Optional[Variable], int]:
        """Parse a variable declaration"""
        line = lines[start_idx].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('//'):
            return None, start_idx + 1
        
        # Parse access modifier
        access_char = line[0] if line[0] in ['*', '-', '+'] else ''
        if access_char:
            line = line[1:].strip()
        
        access = AccessModifier(access_char)
        
        # Parse variable declaration
        if ' = ' in line:
            var_part, initial_value = line.split(' = ', 1)
            var_part = var_part.strip()
            initial_value = initial_value.strip()
        else:
            var_part = line.strip()
            initial_value = None
        
        # Extract type and name
        if ' ' in var_part:
            type_, name = var_part.split(' ', 1)
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
            type_=self._map_type(type_),
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
        
        # Parse access modifier
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
        
        # Parse parameters
        parameters = self._parse_parameters(params_str)
        
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
    
    def _parse_parameters(self, params_str: str) -> List[Tuple[str, str]]:
        """Parse method parameters"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if ' ' in param:
                type_, name = param.split(' ', 1)
                params.append((name.strip(), self._map_type(type_.strip())))
            else:
                # Type inference - assume String for simplicity
                params.append((param.strip(), "String"))
        
        return params
    
    def _parse_method_body(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Parse method body (indented lines)"""
        body = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            
            # If line is not indented, we've reached the end of the method
            if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                break
            
            if line.strip():  # Skip empty lines
                # Convert pseudo-Java to Java
                java_line = self._convert_statement_to_java(line.strip())
                body.append(java_line)
            
            i += 1
        
        return body, i
    
    def _parse_getter_setter(self, lines: List[str], start_idx: int) -> Tuple[Optional[Tuple[str, AccessModifier]], int]:
        """Parse getter/setter specification"""
        line = lines[start_idx].strip()
        
        if not line or line.startswith('//'):
            return None, start_idx + 1
        
        # Parse access modifier
        access_char = line[0] if line[0] in ['*', '-', '+'] else ''
        if access_char:
            line = line[1:].strip()
        
        access = AccessModifier(access_char)
        variable_name = line.strip()
        
        return (variable_name, access), start_idx + 1
    
    def _parse_main_method(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Parse main method body"""
        body = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            
            # If line is not indented, we've reached the end of main
            if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                break
            
            if line.strip():  # Skip empty lines
                # Convert pseudo-Java to Java
                java_line = self._convert_statement_to_java(line.strip())
                body.append(java_line)
            
            i += 1
        
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
        
        # Find variables in {variable} format
        variables = re.findall(r'\{([^}]+)\}', content)
        
        # Replace {variable} with %s, %d, %f based on context
        format_str = content
        args = []
        
        for var in variables:
            # Simple replacement with %s for now (could be enhanced with type detection)
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
                java_type = self._infer_type(value)
                return f"{java_type} {var_name} = {value};"
            else:
                return f"Object {var_name};"
        else:
            # Explicit type
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
        """Generate complete Java code"""
        java_code = []
        
        # Generate imports
        java_code.append("import java.util.*;")
        java_code.append("import java.util.Scanner;")
        java_code.append("")
        
        # Generate main class
        java_code.append(f"public class {program_name} {{")
        
        # Generate main method
        java_code.append("    public static void main(String[] args) {")
        for line in main_body:
            java_code.append(f"        {line}")
        java_code.append("    }")
        
        java_code.append("}")
        java_code.append("")
        
        # Generate template classes
        for template in templates:
            java_code.extend(self._generate_template_class(template))
            java_code.append("")
        
        return '\n'.join(java_code)
    
    def _generate_template_class(self, template: Template) -> List[str]:
        """Generate Java class from template"""
        lines = []
        
        lines.append(f"class {template.name} {{")
        
        # Generate template variables (static)
        for var in template.template_vars:
            access = self.access_modifiers[var.access.value]
            static_keyword = "static" if var.is_static else ""
            initial = f" = {var.initial_value}" if var.initial_value else ""
            
            if access:
                lines.append(f"    {access} static {var.type_} {var.name}{initial};")
            else:
                lines.append(f"    static {var.type_} {var.name}{initial};")
        
        if template.template_vars:
            lines.append("")
        
        # Generate instance variables
        for var in template.instance_vars:
            access = self.access_modifiers[var.access.value]
            initial = f" = {var.initial_value}" if var.initial_value else ""
            
            if access:
                lines.append(f"    {access} {var.type_} {var.name}{initial};")
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
        
        access = self.access_modifiers[method.access.value]
        static_keyword = "static " if method.is_static else ""
        
        # Build parameter list
        params = ", ".join([f"{param_type} {param_name}" for param_name, param_type in method.parameters])
        
        # Build method signature
        if method.is_constructor:
            signature = f"{access} {class_name}({params})"
        else:
            return_type = method.return_type if method.return_type != "void" else "void"
            signature = f"{access} {static_keyword}{return_type} {method.name}({params})"
        
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
        lines.append(f"    {access_str} {var.type_} {getter_name}() {{")
        lines.append(f"        return {var.name};")
        lines.append("    }")
        
        # Setter
        setter_name = f"set{var.name.capitalize()}"
        lines.append(f"    {access_str} void {setter_name}({var.type_} {var.name}) {{")
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
        
        # Determine output file
        if args.output:
            output_file = args.output
        elif args.output_dir:
            # Extract program name from the first line
            first_line = pseudo_code.strip().split('\n')[0]
            program_name = pj_parser._extract_program_name(first_line)
            output_file = os.path.join(args.output_dir, f"{program_name}.java")
        else:
            # Default output file
            base_name = os.path.splitext(args.input)[0]
            output_file = f"{base_name}.java"
        
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
    """Test the parser with a sample program"""
    
    sample_code = '''program TestProgram
    template Person
        template vars:
            * int totalPersons = 0
        
        instance vars:
            * String name
            - int age
        
        constructor:
            * Person(name, age)
                this.name = name
                this.age = age
                totalPersons += 1
        
        template methods:
            * getTotalPersons() -> int
                return totalPersons
        
        instance methods:
            * greet()
                print f"Hello, I'm {name} and I'm {age} years old"
            
            * isAdult() -> boolean
                return age >= 18
        
        getters setters:
            * name
            - age
    
    main
        create alice as Person with "Alice", 25
        make bob as Person with "Bob", 17
        
        alice.greet()
        bob.greet()
        
        if alice.isAdult():
            print f"{alice.name} is an adult"
        
        if not bob.isAdult():
            print f"{bob.name} is a minor"
        
        print f"Total persons: {Person.getTotalPersons()}"
'''
    
    parser = PseudoJavaParser()
    java_code = parser.parse_program(sample_code)
    
    print("Generated Java Code:")
    print("=" * 50)
    print(java_code)


if __name__ == "__main__":
    main()