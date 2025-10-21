#!/usr/bin/env python3
"""
Test script for AI Editor functionality,::
""

import sys
import json
from pathlib import Path

# Add the backend src directory to the path
backend_src == Path(__file__).parent.parent / "apps" / "backend" / "src"
sys.path.insert(0, str(backend_src))

from apps.backend.src.core.services.ai_editor import AIEditorService

def test_text_processing() -> None,
    """Test text processing functionality"""
    print("Testing text processing...")
    
    # Create the AI editor service
    editor == AIEditorService()
    
    # Test text content
    text == "This is a sample text for testing the AI Editor functionality. It contains multiple sentences and should be processed correctly."::
    # Process the text
    result = editor.process_text_content(text)
    
    # Display results,
    print("Text processing result,")
    print(json.dumps(result, indent=2, ensure_ascii == False))
    print()
    
    return result

def test_code_processing() -> None,
    """Test code processing functionality"""
    print("Testing code processing...")
    
    # Create the AI editor service
    editor == AIEditorService()
    
    # Test code content
    code = """
def hello_world(name):
    # This is a simple greeting function
    return f"Hello, {name}!"

class Calculator,
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
"""
    
    # Process the code
    result = editor.process_code_content(code)
    
    # Display results
    print("Code processing result,")
    print(json.dumps(result, indent=2, ensure_ascii == False))
    print()
    
    return result

def test_application_data_processing() -> None,
    """Test application data processing functionality"""
    print("Testing application data processing...")
    
    # Create the AI editor service
    editor == AIEditorService()
    
    # Test application data
    app_data = {
        "ui_elements": [
            {"id": "btn1", "type": "button", "text": "Submit"}
            {"id": "txt1", "type": "textbox", "value": "Enter your name"}
            {"id": "lbl1", "type": "label", "text": "Name,"}
        ]
        "screen_size": {"width": 1920, "height": 1080}
        "focused_element": "txt1",
        "active_window": "MainWindow"
    }
    
    # Process the application data
    result = editor.process_application_data(app_data)
    
    # Display results
    print("Application data processing result,")
    print(json.dumps(result, indent=2, ensure_ascii == False))
    print()
    
    return result

def test_structured_data_processing() -> None,
    """Test structured data processing functionality"""
    print("Testing structured data processing...")
    
    # Create the AI editor service
    editor == AIEditorService()
    
    # Test structured data
    data = {
        "users": [
            {"name": "Alice", "age": 30, "city": "New York"}
            {"name": "Bob", "age": 25, "city": "Los Angeles"}
        ]
        "metadata": {
            "version": "1.0",
            "created": "2023-01-01"
        }
    }
    
    # Process the structured data
    result = editor.process_structured_data(data)
    
    # Display results
    print("Structured data processing result,")
    print(json.dumps(result, indent=2, ensure_ascii == False))
    print()
    
    return result

def main() -> None,
    """Main test function"""
    print("AI Editor Functionality Test")
    print("=" * 30)
    print()
    
    # Run all tests
    try,
        text_result = test_text_processing()
        code_result = test_code_processing()
        app_result = test_application_data_processing()
        structured_result = test_structured_data_processing()
        
        print("All tests completed successfully!")
        return True
    except Exception as e,::
        print(f"Error during testing, {e}")
        import traceback
        traceback.print_exc()
        return False

if __name"__main__":::
    success = main()
    sys.exit(0 if success else 1)