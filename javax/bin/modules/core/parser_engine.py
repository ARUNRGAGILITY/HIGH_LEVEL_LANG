# modules/core/parser_engine.py
"""
Main parsing engine for the Pseudo Java Parser
"""

import re
from typing import List, Dict, Tuple, Optional

from core.data_structures import (
    Template, Method, Variable, AccessModifier, 
    ParsedProgram, TypeMapping
)
from parsers.statement_parser import StatementParser
from utils.exceptions import PseudoJavaError


class PseudoJavaParser:
    """Main parser class for pseudo-Java language"""
    
    def __init__(self, synonym_config):
        self.synonym_config = synonym_config
        self.type_mapping = TypeMapping()
        
        # Initialize sub-parsers
        self.statement_parser = StatementParser(synonym_config, self.type_mapping)
        
        # Import here to avoid circular imports
        from parsers.template_parser import TemplateParser
        from parsers.method_parser import MethodParser
        
        self.template_parser = TemplateParser(synonym_config, self.type_mapping)
        self.method_parser = MethodParser(synonym_config, self.type_mapping)
        
        # Set statement parser reference to avoid circular imports
        self.method_parser.set_statement_parser(self.statement_parser)
        self.template_parser.method_parser.set_statement_parser(self.statement_parser)
    
    def parse_program(self, source_code: str) -> ParsedProgram:
        """Parse the entire pseudo-Java program and return structured data"""
        lines = source_code.strip().split('\n')
        
        # Determine program structure and name
        program_name, start_idx = self._analyze_program_structure(lines)
        
        # Parse components
        templates = []
        main_method_body = []
        standalone_methods = []
        
        i = start_idx
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if line starts with any template synonym
            if self._extract_template_name_from_line(line):
                template, i = self.template_parser.parse_template(lines, i)
                templates.append(template)
                
                # Check if template contains a main method - if so, don't parse standalone main
                has_main_in_template = any(method.name == "main" for method in template.template_methods)
                if has_main_in_template:
                    # Skip any standalone main method since it's already in the template
                    continue
                    
            elif line == 'main':
                main_method_body, i = self._parse_main_method(lines, i + 1)
            elif line.startswith('method '):
                method, i = self.method_parser.parse_standalone_method(lines, i)
                if method:
                    standalone_methods.append(method)
            else:
                i += 1
        
        return ParsedProgram(
            program_name=program_name,
            templates=templates,
            main_method_body=main_method_body,
            standalone_methods=standalone_methods
        )
    
    def _analyze_program_structure(self, lines: List[str]) -> Tuple[str, int]:
        """Analyze program structure and determine program name and starting index"""
        if not lines:
            return "DefaultProgram", 0
        
        first_line = lines[0].strip()
        
        # Check if first line starts with any template synonym
        template_name = self._extract_template_name_from_line(first_line)
        if template_name:
            return template_name, 0
        elif first_line.startswith('program '):
            program_name = self._extract_program_name(first_line)
            return program_name, 1
        elif first_line == 'main':
            return "MainProgram", 0
        else:
            # Search for main or template in the file
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped == 'main':
                    return "MainProgram", 0
                else:
                    template_name = self._extract_template_name_from_line(stripped)
                    if template_name:
                        return template_name, 0
            
            return "DefaultProgram", 0
    
    def _extract_template_name_from_line(self, line: str) -> Optional[str]:
        """Extract template name from any template synonym line"""
        line = line.strip()
        for synonym in self.synonym_config.template_synonyms:
            pattern = f'^{synonym}\\s+(\\w+)'
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_program_name(self, line: str) -> str:
        """Extract program name from 'program ProgramName'"""
        match = re.match(r'program\s+(\w+)', line)
        return match.group(1) if match else "DefaultProgram"
    
    def _parse_main_method(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Parse main method body using the statement parser"""
        return self.statement_parser.parse_method_body(lines, start_idx)
    
    def _get_indentation(self, line: str) -> int:
        """Get the indentation level of a line"""
        return len(line) - len(line.lstrip())