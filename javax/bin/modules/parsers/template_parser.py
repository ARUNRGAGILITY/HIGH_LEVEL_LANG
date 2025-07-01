# modules/parsers/template_parser.py
"""
Template/Class parser for the Pseudo Java Parser
"""

import re
from typing import List, Tuple, Optional

from core.data_structures import Template, Variable, Method, AccessModifier
from utils.exceptions import PseudoJavaError


class TemplateParser:
    """Parser for template/class definitions"""
    
    def __init__(self, synonym_config, type_mapping):
        self.synonym_config = synonym_config
        self.type_mapping = type_mapping
        # Import parsers here to avoid circular imports
        from parsers.variable_parser import VariableParser
        from parsers.method_parser import MethodParser
        
        self.variable_parser = VariableParser(synonym_config, type_mapping)
        self.method_parser = MethodParser(synonym_config, type_mapping)
    
    def parse_template(self, lines: List[str], start_idx: int) -> Tuple[Template, int]:
        """Parse a template definition with inheritance support"""
        template_line = lines[start_idx].strip()
        template_name = self._extract_template_name_from_line(template_line)
        
        if not template_name:
            raise PseudoJavaError(f"Could not extract template name from line: {template_line}")
        
        # Parse inheritance information
        is_abstract, is_interface, extends, implements = self._parse_inheritance_from_line(template_line)
        
        template = Template(
            name=template_name,
            is_abstract=is_abstract,
            is_interface=is_interface,
            extends=extends,
            implements=implements
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
            if (original_line and not original_line.startswith('    ') and 
                not original_line.startswith('\t')):
                if (self._extract_template_name_from_line(line) or 
                    line == 'main' or line.startswith('method ')):
                    break
            
            # Determine current section
            if line.endswith(':') and self._get_indentation(original_line) == 4:
                current_section = line[:-1].strip()
                i += 1
                continue
            
            # Parse based on current section
            i = self._parse_section_content(
                lines, i, current_section, template, original_line
            )
        
        return template, i
    
    def _extract_template_name_from_line(self, line: str) -> Optional[str]:
        """Extract template name from any template synonym line"""
        line = line.strip()
        for synonym in self.synonym_config.template_synonyms:
            pattern = f'^{synonym}\\s+(\\w+)'
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _parse_inheritance_from_line(self, line: str) -> Tuple[bool, bool, Optional[str], List[str]]:
        """Parse inheritance information from template declaration line"""
        line = line.strip()
        is_abstract = False
        is_interface = False
        extends = None
        implements = []
        
        # Check for abstract keywords
        for keyword in self.synonym_config.abstract_synonyms:
            if line.startswith(f'{keyword} '):
                is_abstract = True
                line = line[len(keyword):].strip()
                break
        
        # Check for interface keyword
        if line.startswith('interface '):
            is_interface = True
            line = line[10:].strip()
        
        # Parse extends clause
        for keyword in self.synonym_config.inheritance_synonyms:
            if f' {keyword} ' in line:
                parts = line.split(f' {keyword} ', 1)
                line = parts[0].strip()
                remainder = parts[1].strip()
                
                # Check for implements clause
                for impl_keyword in self.synonym_config.implementation_synonyms:
                    if f' {impl_keyword} ' in remainder:
                        extend_parts = remainder.split(f' {impl_keyword} ', 1)
                        extends = extend_parts[0].strip()
                        implements_part = extend_parts[1].strip()
                        implements = [iface.strip() for iface in implements_part.split(',')]
                        break
                else:
                    extends = remainder
                break
        
        # Parse implements clause (without extends)
        if not extends:
            for keyword in self.synonym_config.implementation_synonyms:
                if f' {keyword} ' in line:
                    parts = line.split(f' {keyword} ', 1)
                    line = parts[0].strip()
                    implements_part = parts[1].strip()
                    implements = [iface.strip() for iface in implements_part.split(',')]
                    break
        
        return is_abstract, is_interface, extends, implements
    
    def _parse_section_content(self, lines: List[str], i: int, current_section: str, 
                             template: Template, original_line: str) -> int:
        """Parse content based on current section"""
        if not current_section or self._get_indentation(original_line) < 8:
            return i + 1
        
        # Get section patterns
        template_keyword = self._extract_template_keyword_from_name(template.name, lines[0])
        static_vars_patterns = self.synonym_config.get_static_vars_patterns(template_keyword)
        static_methods_patterns = self.synonym_config.get_static_methods_patterns(template_keyword)
        getter_setter_patterns = self.synonym_config.get_getter_setter_patterns()
        
        # Parse based on section type
        if current_section in static_vars_patterns:
            var, i = self.variable_parser.parse_variable(lines, i, is_static=True)
            if var:
                template.template_vars.append(var)
        elif current_section == 'instance vars':
            var, i = self.variable_parser.parse_variable(lines, i, is_static=False)
            if var:
                template.instance_vars.append(var)
        elif current_section == 'constructor':
            method, i = self.method_parser.parse_method(
                lines, i, is_constructor=True, template=template
            )
            if method:
                template.constructors.append(method)
        elif current_section in static_methods_patterns:
            method, i = self.method_parser.parse_method(
                lines, i, is_static=True, template=template
            )
            if method:
                template.template_methods.append(method)
        elif current_section == 'instance methods':
            method, i = self.method_parser.parse_method(
                lines, i, is_static=False, template=template
            )
            if method:
                template.instance_methods.append(method)
        elif current_section in self.synonym_config.abstract_methods_synonyms:
            method, i = self.method_parser.parse_abstract_method(lines, i, template=template)
            if method:
                template.abstract_methods.append(method)
        elif current_section in getter_setter_patterns:
            getter_setter, i = self._parse_getter_setter(lines, i)
            if getter_setter:
                template.getters_setters.append(getter_setter)
        else:
            i += 1
        
        return i
    
    def _extract_template_keyword_from_name(self, template_name: str, first_line: str) -> str:
        """Extract the template keyword used in the declaration"""
        for synonym in self.synonym_config.template_synonyms:
            if synonym.lower() in first_line.lower():
                return synonym
        return 'template'  # fallback
    
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
    
    def _get_indentation(self, line: str) -> int:
        """Get the indentation level of a line"""
        return len(line) - len(line.lstrip())