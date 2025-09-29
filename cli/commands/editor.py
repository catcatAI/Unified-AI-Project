# cli/commands/editor.py
"""
CLI command for AI Editor functionality
"""

import click
import json
import sys
from pathlib import Path

# Add the backend src directory to the path
backend_src = Path(__file__).parent.parent.parent / "apps" / "backend" / "src"
_ = sys.path.insert(0, str(backend_src))

from apps.backend.src.core.services.ai_editor import AIEditorService
from apps.backend.src.core.services.ai_editor_config import get_config

_ = @click.group()
def editor():
    """AI Editor commands"""
    pass

_ = @editor.command()
@click.option('--text', prompt='Enter text to process', help='Text content to process')
def process_text(text):
    """Process text content"""
    try:
        # Create the AI editor service
        editor_service = AIEditorService()
        
        # Process the text
        result = editor_service.process_text_content(text)
        
        # Output the result
        _ = click.echo("Text processing result:")
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"Error processing text: {e}", err=True)
        _ = sys.exit(1)

_ = @editor.command()
@click.option('--code', prompt='Enter code to process', help='Code content to process')
def process_code(code):
    """Process code content"""
    try:
        # Create the AI editor service
        editor_service = AIEditorService()
        
        # Process the code
        result = editor_service.process_code_content(code)
        
        # Output the result
        _ = click.echo("Code processing result:")
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"Error processing code: {e}", err=True)
        _ = sys.exit(1)

_ = @editor.command()
@click.option('--file', type=click.Path(exists=True), help='File containing data to process')
@click.option('--type', 'data_type', type=click.Choice(['text', 'code', 'json']), 
              default='text', help='Type of data in the file')
def process_file(file, data_type):
    """Process data from a file"""
    try:
        # Read the file
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create the AI editor service
        editor_service = AIEditorService()
        
        # Process based on type
        if data_type == 'text':
            result = editor_service.process_text_content(content)
        elif data_type == 'code':
            result = editor_service.process_code_content(content)
        elif data_type == 'json':
            # Parse JSON content
            json_data = json.loads(content)
            result = editor_service.process_structured_data(json_data)
        
        # Output the result
        _ = click.echo(f"{data_type.capitalize()} processing result:")
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"Error processing file: {e}", err=True)
        _ = sys.exit(1)

_ = @editor.command()
def config():
    """Show current configuration"""
    try:
        # Get the current configuration
        config = get_config()
        
        # Convert to dictionary for JSON serialization
        config_dict = {
            "enabled": config.enabled,
            "log_level": config.log_level,
            "data_processing": {
                "text_summarization_enabled": config.data_processing.text_summarization_enabled,
                "text_keyword_extraction_enabled": config.data_processing.text_keyword_extraction_enabled,
                "code_function_extraction_enabled": config.data_processing.code_function_extraction_enabled,
                "code_class_extraction_enabled": config.data_processing.code_class_extraction_enabled,
                "code_complexity_analysis_enabled": config.data_processing.code_complexity_analysis_enabled
            },
            "sandbox": {
                "timeout_seconds": config.sandbox.timeout_seconds,
                "use_execution_monitoring": config.sandbox.use_execution_monitoring,
                "max_memory_mb": config.sandbox.max_memory_mb
            }
        }
        
        # Output the configuration
        _ = click.echo("Current AI Editor configuration:")
        click.echo(json.dumps(config_dict, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"Error getting configuration: {e}", err=True)
        _ = sys.exit(1)

if __name__ == '__main__':
    _ = editor()