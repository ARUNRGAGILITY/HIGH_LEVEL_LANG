# modules/core/data_structures.py
"""
Core data structures for the Pseudo Java Parser
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional


class AccessModifier(Enum):
    """Access modifier enumeration"""
    PUBLIC = "*"
    PRIVATE = "-"
    PROTECTED = "+"
    PACKAGE_PRIVATE = ""


@dataclass
class Variable:
    """Represents a variable declaration"""
    name: str
    type_: str
    access: AccessModifier
    initial_value: Optional[str] = None
    is_static: bool = False


@dataclass
class Method:
    """Represents a method declaration"""
    name: str
    parameters: List[Tuple[str, str]]  # (name, type)
    return_type: str
    access: AccessModifier
    body: List[str]
    is_static: bool = False
    is_constructor: bool = False


@dataclass
class Template:
    """Represents a template/class declaration"""
    name: str
    template_vars: List[Variable] = field(default_factory=list)
    instance_vars: List[Variable] = field(default_factory=list)
    constructors: List[Method] = field(default_factory=list)
    template_methods: List[Method] = field(default_factory=list)
    instance_methods: List[Method] = field(default_factory=list)
    getters_setters: List[Tuple[str, AccessModifier]] = field(default_factory=list)
    
    # APIE features
    is_abstract: bool = False
    is_interface: bool = False
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    abstract_methods: List[Method] = field(default_factory=list)


@dataclass
class ParsedProgram:
    """Represents the complete parsed program"""
    program_name: str
    templates: List[Template] = field(default_factory=list)
    main_method_body: List[str] = field(default_factory=list)
    standalone_methods: List[Method] = field(default_factory=list)


class TypeMapping:
    """Handles type mapping from pseudo-Java to Java"""
    
    def __init__(self):
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
    
    def map_type(self, type_str: str) -> str:
        """Map pseudo-Java types to Java types"""
        return self.type_mapping.get(type_str.lower(), type_str)
    
    def is_primitive_type(self, type_str: str) -> bool:
        """Check if a type is a primitive type"""
        primitives = {'int', 'byte', 'short', 'long', 'float', 'double', 'boolean', 'char'}
        return type_str.lower() in primitives
    
    def get_wrapper_type(self, primitive_type: str) -> str:
        """Get wrapper type for primitive types (for generics)"""
        wrapper_mapping = {
            'int': 'Integer',
            'double': 'Double',
            'float': 'Float',
            'boolean': 'Boolean',
            'byte': 'Byte',
            'short': 'Short',
            'long': 'Long',
            'char': 'Character'
        }
        return wrapper_mapping.get(primitive_type.lower(), primitive_type)