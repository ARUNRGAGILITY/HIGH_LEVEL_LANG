# modules/parsers/variable_parser.py
"""
Variable parser for the Pseudo Java Parser
"""

from typing import Optional, Tuple, List

from core.data_structures import Variable, AccessModifier
from utils.exceptions import PseudoJavaError


class VariableParser:
    """Parser for variable declarations"""
    
    def __init__(self, synonym_config, type_mapping):
        self.synonym_config = synonym_config
        self.type_mapping = type_mapping
    
    def parse_variable(self, lines: List[str], start_idx: int, is_static: bool) -> Tuple[Optional[Variable], int]:
        """Parse a variable declaration requiring explicit type syntax"""
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
            raise PseudoJavaError(
                f"Variable declaration '{line}' must use 'name as type' syntax. "
                f"Example: 'studentId as int' or 'name as string'"
            )
        
        name_part, type_part = var_part.split(' as ', 1)
        name = name_part.strip()
        type_ = type_part.strip()
        
        # Handle special collection syntax
        type_, initial_value = self._process_collection_type(type_, initial_value)
        
        return Variable(
            name=name,
            type_=type_,
            access=access,
            initial_value=initial_value,
            is_static=is_static
        ), start_idx + 1
    
    def _process_collection_type(self, type_: str, initial_value: Optional[str]) -> Tuple[str, Optional[str]]:
        """Process collection types like 'arraylist/double' or 'list/string'"""
        if '/' not in type_:
            return self.type_mapping.map_type(type_), initial_value
        
        container_type, element_type = type_.split('/', 1)
        container_type = container_type.strip().lower()
        element_type = element_type.strip()
        
        # Map container and element types
        mapped_container = self.type_mapping.map_type(container_type)
        mapped_element = self.type_mapping.map_type(element_type)
        
        # Convert primitive types to wrapper types for generics
        if self.type_mapping.is_primitive_type(mapped_element):
            mapped_element = self.type_mapping.get_wrapper_type(mapped_element)
        
        # Build collection type and default initialization
        if container_type in ['arraylist', 'list']:
            final_type = f"ArrayList<{mapped_element}>"
            if not initial_value or initial_value == 'arraylist':
                initial_value = f"new ArrayList<{mapped_element}>()"
        elif container_type in ['map', 'hashmap']:
            final_type = f"HashMap<String, {mapped_element}>"
            if not initial_value or initial_value == 'hashmap':
                initial_value = f"new HashMap<String, {mapped_element}>()"
        elif container_type in ['set', 'hashset']:
            final_type = f"HashSet<{mapped_element}>"
            if not initial_value or initial_value == 'hashset':
                initial_value = f"new HashSet<{mapped_element}>()"
        else:
            final_type = f"{mapped_container}<{mapped_element}>"
        
        return final_type, initial_value