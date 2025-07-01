# modules/tests/test_runner.py
"""
Test runner for the Pseudo Java Parser
"""

import sys
from typing import List, Tuple

from config.synonyms import SynonymConfig
from core.parser_engine import PseudoJavaParser
from generators.java_generator import JavaCodeGenerator
from utils.exceptions import PseudoJavaError


def run_tests():
    """Run all built-in tests"""
    print("Running Pseudo Java Parser Tests...")
    print("=" * 60)
    
    tests = [
        test_hello_world_basic,
        test_design_car_example,
        test_backward_compatibility,
        test_abstract_classes,
        test_interfaces,
        test_inheritance,
        test_utility_methods,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test_name = test.__name__.replace('test_', '').replace('_', ' ').title()
            print(f"\n🧪 Testing: {test_name}")
            print("-" * 40)
            
            test()
            print("✅ PASSED")
            passed += 1
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("Some tests failed. Please check the error messages above.")
        sys.exit(1)
    else:
        print("All tests passed! 🎉")


def test_hello_world_basic():
    """Test basic hello world functionality"""
    
    hello_code = '''program HelloWorld

main
    print "Hello, World!"
    print "This is a test"
'''
    
    synonym_config = SynonymConfig()
    parser = PseudoJavaParser(synonym_config)
    generator = JavaCodeGenerator()
    
    parsed_data = parser.parse_program(hello_code)
    java_code = generator.generate(parsed_data)
    
    # Verify basic structure
    assert 'public class HelloWorld' in java_code
    assert 'public static void main(String[] args)' in java_code
    assert 'System.out.println("Hello, World!");' in java_code
    assert 'System.out.println("This is a test");' in java_code
    
    print("Basic hello world test passed")


def test_design_car_example():
    """Test the exact design Car example from your specification"""
    
    car_code = '''design Car
    design vars:
        - totalCars as int with 0
    design methods:
        * getCarCount() returns int
            return totalCars
    instance vars:
        - name as string with ""
        - model as string with ""
    constructor:
        * name:
            totalCars++
        * name, model:
            totalCars++
    
    getters setters:
        * name
        * model
    
main
    print This is a car class!
    print Total {Car.getCarCount()} cars at the begining
    create toyotaCar as Car with "Toyota"
    create bmwCar as Car with "BMW"
    create hondaCar as Car with "Honda", "Honda"
    print Total {Car.getCarCount()} car(s) got created
    print Honda Car: {hondaCar.getName()} {hondaCar.getModel()}
'''
    
    synonym_config = SynonymConfig()
    parser = PseudoJavaParser(synonym_config)
    generator = JavaCodeGenerator()
    
    parsed_data = parser.parse_program(car_code)
    java_code = generator.generate(parsed_data)
    
    # Verify key elements are present
    assert 'public class Car' in java_code
    assert 'private static int totalCars = 0;' in java_code
    assert 'public static int getCarCount()' in java_code
    assert 'private String name = "";' in java_code
    assert 'private String model = "";' in java_code
    assert 'public Car(String name)' in java_code
    assert 'public Car(String name, String model)' in java_code
    assert 'public String getName()' in java_code
    assert 'public void setName(String name)' in java_code
    assert 'public static void main(String[] args)' in java_code
    
    print("Generated Java code structure verified")


def test_backward_compatibility():
    """Test backward compatibility with template syntax"""
    
    student_code = '''template Student
    template vars:
        * totalStudents as int with 0
        
    instance vars:
        * studentId as string
        * name as string
        
    constructor:
        * Student(studentId, name):
            this.studentId = studentId
            this.name = name
            totalStudents++

main
    create alice as Student with "S001", "Alice Johnson"
    print Total students: {Student.totalStudents}
'''
    
    synonym_config = SynonymConfig()
    parser = PseudoJavaParser(synonym_config)
    generator = JavaCodeGenerator()
    
    parsed_data = parser.parse_program(student_code)
    java_code = generator.generate(parsed_data)
    
    assert 'public class Student' in java_code
    assert 'public static int totalStudents = 0;' in java_code
    assert 'public String studentId;' in java_code
    
    print("Backward compatibility verified")


def test_abstract_classes():
    """Test abstract class support"""
    
    abstract_code = '''abstract template Animal
    instance vars:
        * name as string
    
    constructor:
        * name:
    
    abstract methods:
        * makeSound() returns string
        
    instance methods:
        * getName() returns string
            return name
'''
    
    synonym_config = SynonymConfig()
    parser = PseudoJavaParser(synonym_config)
    generator = JavaCodeGenerator()
    
    parsed_data = parser.parse_program(abstract_code)
    java_code = generator.generate(parsed_data)
    
    assert 'abstract class Animal' in java_code
    assert 'abstract String makeSound();' in java_code
    
    print("Abstract class support verified")


def test_interfaces():
    """Test interface support"""
    
    interface_code = '''interface Flyable
    abstract methods:
        * fly() returns boolean
        * getAltitude() returns double
'''
    
    synonym_config = SynonymConfig()
    parser = PseudoJavaParser(synonym_config)
    generator = JavaCodeGenerator()
    
    parsed_data = parser.parse_program(interface_code)
    java_code = generator.generate(parsed_data)
    
    assert 'interface Flyable' in java_code
    assert 'abstract boolean fly();' in java_code
    assert 'abstract double getAltitude();' in java_code
    
    print("Interface support verified")


def test_inheritance():
    """Test inheritance and implementation"""
    
    inheritance_code = '''class Dog extends Animal implements Flyable
    instance vars:
        * breed as string
    
    constructor:
        * breed:
    
    instance methods:
        * makeSound() returns string
            return "Woof!"
        
        * fly() returns boolean
            return false
'''
    
    synonym_config = SynonymConfig()
    parser = PseudoJavaParser(synonym_config)
    generator = JavaCodeGenerator()
    
    parsed_data = parser.parse_program(inheritance_code)
    java_code = generator.generate(parsed_data)
    
    assert 'class Dog extends Animal implements Flyable' in java_code
    
    print("Inheritance and implementation verified")


def test_utility_methods():
    """Test utility/static methods"""
    
    math_code = '''class MathUtils
    class methods:
        * add(a, b) returns double
            return a + b
        
        * multiply(x, y) returns double
            return x * y

main
    result as double = MathUtils.add(5.0, 3.0)
    print Result: {result}
'''
    
    synonym_config = SynonymConfig()
    parser = PseudoJavaParser(synonym_config)
    generator = JavaCodeGenerator()
    
    parsed_data = parser.parse_program(math_code)
    java_code = generator.generate(parsed_data)
    
    assert 'public static double add(' in java_code
    assert 'public static double multiply(' in java_code
    
    print("Utility methods verified")


def test_error_handling():
    """Test error handling for common mistakes"""
    
    # Test missing type declaration
    try:
        bad_code = '''template Test
    instance vars:
        name  # Missing type
'''
        synonym_config = SynonymConfig()
        parser = PseudoJavaParser(synonym_config)
        parser.parse_program(bad_code)
        assert False, "Should have raised an error for missing type"
    except PseudoJavaError:
        pass  # Expected
    
    print("Error handling verified")


if __name__ == "__main__":
    run_tests()