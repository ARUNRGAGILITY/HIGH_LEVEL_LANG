# modules/config/synonyms.py
"""
Pseudo Java Language Synonyms Configuration
Customizable synonyms to match your team's preferred terminology
"""

class SynonymConfig:
    """Configuration class for pseudo-Java language synonyms"""
    
    def __init__(self):
        # Template/Class synonyms
        self.template_synonyms = ['template', 'blueprint', 'design', 'class']
        
        # Abstract/Contract synonyms
        self.abstract_synonyms = ['abstract', 'contract', 'basic', 'base', 'must-do']
        
        # Inheritance synonyms
        self.inheritance_synonyms = ['extends', 'inherits', 'is-a']
        
        # Implementation synonyms
        self.implementation_synonyms = ['implements', 'can', 'can-do', 'capable']
        
        # Abstract methods synonyms
        self.abstract_methods_synonyms = ['abstract methods', 'must-do methods']
        
        # Object creation verbs
        self.object_creation_verbs = ['create', 'make', 'spawn', 'build', 'initialize']
    
    def is_template_keyword(self, word: str) -> bool:
        """Check if a word is any of the template synonyms"""
        return word.lower() in self.template_synonyms
    
    def get_static_vars_patterns(self, template_keyword: str) -> list:
        """Get static variables section patterns"""
        return [
            f'{template_keyword} vars',
            'template vars',
            'static vars',
            'class vars'
        ]
    
    def get_static_methods_patterns(self, template_keyword: str) -> list:
        """Get static methods section patterns"""
        return [
            f'{template_keyword} methods',
            'template methods',
            'static methods',
            'class methods'
        ]
    
    def get_getter_setter_patterns(self) -> list:
        """Get getter/setter section patterns"""
        return [
            'getters setters',
            'getters and setters',
            'getters, setters',
            'setters and getters'
        ]

    def customize_synonyms(self, **kwargs):
        """Allow runtime customization of synonyms"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)