# modules/utils/cli.py
"""
Command line interface for the Pseudo Java Parser
"""

import argparse
import sys


class CommandLineInterface:
    """Handles command line argument parsing and help"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description='Pseudo Java Language Parser - Convert pseudo-Java to Java',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
Examples:
  javax_parser.py input.pj -o output.java
  javax_parser.py input.pj --output-dir src/main/java
  javax_parser.py input.pj --compile
  javax_parser.py --test

File Extensions:
  .pj              Pseudo-Java source files

Environment Variables:
  JAVAX_VERBOSE=1    Enable verbose output by default
  JAVAX_OUTPUT_DIR   Default output directory
            '''
        )
        
        # Positional arguments
        parser.add_argument(
            'input', 
            nargs='?', 
            help='Input pseudo-Java file (.pj)'
        )
        
        # Output options
        parser.add_argument(
            '-o', '--output', 
            help='Output Java file'
        )
        parser.add_argument(
            '--output-dir', 
            help='Output directory for Java files'
        )
        
        # Compilation options
        parser.add_argument(
            '-c', '--compile', 
            action='store_true', 
            help='Compile generated Java code'
        )
        parser.add_argument(
            '-r', '--run', 
            action='store_true', 
            help='Compile and run the generated Java code'
        )
        
        # Utility options
        parser.add_argument(
            '-v', '--verbose', 
            action='store_true', 
            help='Verbose output'
        )
        parser.add_argument(
            '--test', 
            action='store_true', 
            help='Run built-in test'
        )
        
        # Version
        parser.add_argument(
            '--version', 
            action='version', 
            version='Pseudo Java Parser 2.0 (Modular)'
        )
        
        return parser
    
    def parse_arguments(self, args=None):
        """Parse command line arguments"""
        parsed_args = self.parser.parse_args(args)
        
        # Handle environment variables
        import os
        if os.environ.get('JAVAX_VERBOSE', '0') != '0':
            parsed_args.verbose = True
        
        if not parsed_args.output_dir and os.environ.get('JAVAX_OUTPUT_DIR'):
            parsed_args.output_dir = os.environ.get('JAVAX_OUTPUT_DIR')
        
        return parsed_args
    
    def print_help(self):
        """Print help message"""
        self.parser.print_help()
    
    def print_usage(self):
        """Print usage message"""
        self.parser.print_usage()
    
    def validate_arguments(self, args):
        """Validate parsed arguments"""
        errors = []
        
        if not args.input and not args.test:
            errors.append("Input file is required unless using --test")
        
        if args.input and not args.input.endswith('.pj'):
            print(f"Warning: Input file '{args.input}' does not have .pj extension")
        
        if args.run and not args.compile:
            args.compile = True  # Auto-enable compile when run is requested
        
        if errors:
            for error in errors:
                print(f"Error: {error}", file=sys.stderr)
            return False
        
        return True