# modules/generators/java_generator.py
"""
Java code generator for the Pseudo Java Parser
"""

from typing import List, Optional, Tuple

from core.data_structures import ParsedProgram, Template, Method, Variable, AccessModifier


class JavaCodeGenerator:
    """Generates Java code from parsed pseudo-Java structures"""
    
    def __init__(self):
        self.access_modifiers = {
            '*': 'public',
            '-': 'private',
            '+': 'protected',
            '': ''  # package-private
        }
    
    def generate(self, parsed_data: ParsedProgram) -> str:
        """Generate complete Java code from parsed data"""
        java_code = []
        
        # Generate imports
        java_code.extend(self._generate_imports())
        java_code.append("")
        
        # Determine generation strategy
        if self._should_merge_into_single_class(parsed_data):
            java_code.extend(self._generate_single_class_with_main(parsed_data))
        elif parsed_data.main_method_body:
            java_code.extend(self._generate_main_class_with_separate_templates(parsed_data))
        elif len(parsed_data.templates) == 1:
            java_code.extend(self._generate_single_template_class(parsed_data.templates[0]))
        else:
            java_code.extend(self._generate_standalone_methods_class(parsed_data))
        
        return '\n'.join(java_code)
    
    def _generate_imports(self) -> List[str]:
        """Generate standard imports"""
        return [
            "import java.util.*;",
            "import java.util.Scanner;"
        ]
    
    def _should_merge_into_single_class(self, parsed_data: ParsedProgram) -> bool:
        """Determine if template should be merged with main method"""
        if len(parsed_data.templates) == 1:
            template = parsed_data.templates[0]
            # Check if template has a main method OR if there's a standalone main method
            has_main_in_template = any(method.name == "main" for method in template.template_methods)
            return (template.name == parsed_data.program_name and 
                   (parsed_data.main_method_body or has_main_in_template))
        return False
    
    def _generate_single_class_with_main(self, parsed_data: ParsedProgram) -> List[str]:
        """Generate a single class containing everything including main method"""
        lines = []
        template = parsed_data.templates[0]
        
        lines.append(f"public class {template.name} {{")
        
        # Generate template variables (static)
        if template.template_vars:
            lines.extend(self._generate_variables(template.template_vars, True))
            lines.append("")
        
        # Generate instance variables
        if template.instance_vars:
            lines.extend(self._generate_variables(template.instance_vars, False))
            lines.append("")
        
        # Generate constructors
        for constructor in template.constructors:
            lines.extend(self._generate_method(constructor, template.name))
            lines.append("")
        
        # Generate template methods (static)
        for method in template.template_methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        # Generate instance methods
        for method in template.instance_methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        # Generate getters and setters
        for var_name, access in template.getters_setters:
            var = self._find_variable(template, var_name)
            if var:
                lines.extend(self._generate_getter_setter(var, access))
                lines.append("")
        
        # Generate standalone methods
        for method in parsed_data.standalone_methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        # Generate main method
        lines.extend(self._generate_main_method(parsed_data.main_method_body))
        
        lines.append("}")
        
        return lines
    
    def _generate_main_class_with_separate_templates(self, parsed_data: ParsedProgram) -> List[str]:
        """Generate main class with separate template classes"""
        lines = []
        
        # Separate utility templates from regular templates
        main_class_methods = []
        regular_templates = []
        
        for template in parsed_data.templates:
            if self._is_utility_template(template) and template.name == parsed_data.program_name:
                main_class_methods.extend(template.template_methods)
            else:
                regular_templates.append(template)
        
        # Add standalone methods to main class
        main_class_methods.extend(parsed_data.standalone_methods)
        
        # Generate main class
        lines.append(f"public class {parsed_data.program_name} {{")
        
        # Add utility methods and standalone methods
        for method in main_class_methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        # Generate main method
        lines.extend(self._generate_main_method(parsed_data.main_method_body))
        
        lines.append("}")
        lines.append("")
        
        # Generate regular template classes
        for template in regular_templates:
            lines.extend(self._generate_single_template_class(template))
            lines.append("")
        
        return lines
    
    def _generate_single_template_class(self, template: Template) -> List[str]:
        """Generate Java class from template with inheritance support"""
        lines = []
        
        # Build class declaration
        class_declaration = self._build_class_declaration(template)
        lines.append(class_declaration)
        
        # For interfaces, skip instance variables and constructors
        if not template.is_interface:
            # Generate template variables (static)
            if template.template_vars:
                lines.extend(self._generate_variables(template.template_vars, True))
                lines.append("")
            
            # Generate instance variables
            if template.instance_vars:
                lines.extend(self._generate_variables(template.instance_vars, False))
                lines.append("")
            
            # Generate constructors
            for constructor in template.constructors:
                lines.extend(self._generate_method(constructor, template.name))
                lines.append("")
        
        # Generate template methods (static)
        for method in template.template_methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        # Generate instance methods
        for method in template.instance_methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        # Generate abstract methods
        for method in template.abstract_methods:
            lines.extend(self._generate_abstract_method(method))
            lines.append("")
        
        # Generate getters and setters (not for interfaces)
        if not template.is_interface:
            for var_name, access in template.getters_setters:
                var = self._find_variable(template, var_name)
                if var:
                    lines.extend(self._generate_getter_setter(var, access))
                    lines.append("")
        
        lines.append("}")
        
        return lines
    
    def _generate_standalone_methods_class(self, parsed_data: ParsedProgram) -> List[str]:
        """Generate class with only standalone methods"""
        lines = []
        
        lines.append(f"public class {parsed_data.program_name} {{")
        
        for method in parsed_data.standalone_methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        lines.append("}")
        
        return lines
    
    def _build_class_declaration(self, template: Template) -> str:
        """Build class declaration with inheritance"""
        declaration_parts = []
        
        # Add modifiers
        if template.is_interface:
            declaration_parts.append("interface")
        elif template.is_abstract:
            declaration_parts.append("abstract class")
        else:
            declaration_parts.append("class")
        
        declaration_parts.append(template.name)
        
        # Add extends clause
        if template.extends:
            declaration_parts.extend(["extends", template.extends])
        
        # Add implements clause
        if template.implements:
            declaration_parts.extend(["implements", ", ".join(template.implements)])
        
        return " ".join(declaration_parts) + " {"
    
    def _generate_variables(self, variables: List[Variable], is_static: bool) -> List[str]:
        """Generate variable declarations"""
        lines = []
        
        for var in variables:
            access_str = self.access_modifiers[var.access.value]
            static_keyword = "static " if is_static else ""
            initial = f" = {var.initial_value}" if var.initial_value else ""
            
            if access_str:
                lines.append(f"    {access_str} {static_keyword}{var.type_} {var.name}{initial};")
            else:
                lines.append(f"    {static_keyword}{var.type_} {var.name}{initial};")
        
        return lines
    
    def _generate_method(self, method: Method, class_name: str = None) -> List[str]:
        """Generate Java method code"""
        lines = []
        
        access_str = self.access_modifiers[method.access.value]
        static_keyword = "static " if method.is_static else ""
        
        # Build parameter list
        params = ", ".join([f"{param_type} {param_name}" for param_name, param_type in method.parameters])
        
        # Build method signature
        if method.is_constructor:
            if access_str:
                signature = f"{access_str} {class_name or method.name}({params})"
            else:
                signature = f"{class_name or method.name}({params})"
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
    
    def _generate_abstract_method(self, method: Method) -> List[str]:
        """Generate abstract method code (no body)"""
        lines = []
        
        access_str = self.access_modifiers[method.access.value]
        params = ", ".join([f"{param_type} {param_name}" for param_name, param_type in method.parameters])
        return_type = method.return_type if method.return_type != "void" else "void"
        
        if access_str:
            signature = f"{access_str} abstract {return_type} {method.name}({params});"
        else:
            signature = f"abstract {return_type} {method.name}({params});"
        
        lines.append(f"    {signature}")
        
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
    
    def _generate_main_method(self, main_body: List[str]) -> List[str]:
        """Generate main method"""
        lines = []
        
        lines.append("    public static void main(String[] args) {")
        for line in main_body:
            lines.append(f"        {line}")
        lines.append("    }")
        
        return lines
    
    def _is_utility_template(self, template: Template) -> bool:
        """Check if template is a utility class (only static methods, no instance data)"""
        return (
            len(template.instance_vars) == 0 and 
            len(template.constructors) == 0 and 
            len(template.getters_setters) == 0 and
            len(template.instance_methods) == 0 and
            len(template.template_methods) > 0
        )
    
    def _find_variable(self, template: Template, var_name: str) -> Optional[Variable]:
        """Find variable in template by name"""
        for var in template.instance_vars + template.template_vars:
            if var.name == var_name:
                return var
        return None