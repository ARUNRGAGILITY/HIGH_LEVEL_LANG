#!/usr/bin/env python3
"""
Pseudo Java Language Parser - Main Entry Point
Modular version with components split into separate modules
"""

import sys
import os
from pathlib import Path

# Add modules directory to Python path
SCRIPT_DIR = Path(__file__).parent.absolute()
MODULES_DIR = SCRIPT_DIR / "modules"
sys.path.insert(0, str(MODULES_DIR))

# Import modules
try:
    from config.synonyms import SynonymConfig
    from core.data_structures import Template, Method, Variable, AccessModifier
    from core.parser_engine import PseudoJavaParser
    from generators.java_generator import JavaCodeGenerator
    from utils.file_handler import FileHandler
    from utils.cli import CommandLineInterface
    from utils.exceptions import PseudoJavaError
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Please ensure all module files are present in {MODULES_DIR}")
    sys.exit(1)


def main():
    """Main entry point for the Pseudo Java Parser"""
    try:
        # Initialize CLI and parse arguments
        cli = CommandLineInterface()
        args = cli.parse_arguments()
        
        # Handle special modes
        if args.test:
            from tests.test_runner import run_tests
            run_tests()
            return
        
        if not args.input:
            cli.print_help()
            sys.exit(1)
        
        # Initialize components
        file_handler = FileHandler(verbose=args.verbose)
        synonym_config = SynonymConfig()
        
        # Read input file
        pseudo_code = file_handler.read_file(args.input)
        
        if args.verbose:
            print(f"Reading pseudo-Java file: {args.input}")
        
        # Parse the code
        parser = PseudoJavaParser(synonym_config)
        parsed_data = parser.parse_program(pseudo_code)
        
        # Generate Java code
        generator = JavaCodeGenerator()
        java_code = generator.generate(parsed_data)
        
        # Determine output file
        output_file = file_handler.determine_output_file(
            args.input, 
            parsed_data.program_name,
            args.output,
            args.output_dir
        )
        
        # Write Java code
        file_handler.write_file(output_file, java_code)
        print(f"Generated Java code: {output_file}")
        
        # Compile and/or run if requested
        if args.compile or args.run:
            from utils.java_tools import JavaTools
            java_tools = JavaTools(verbose=args.verbose)
            
            if java_tools.compile(output_file):
                print("Compilation successful!")
                
                if args.run:
                    java_tools.run(output_file)
            else:
                print("Compilation failed!", file=sys.stderr)
                sys.exit(1)
    
    except PseudoJavaError as e:
        print(f"Pseudo Java Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"File Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()