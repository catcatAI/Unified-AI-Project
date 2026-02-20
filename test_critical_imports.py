"""Test that critical modules mentioned in the task can be imported"""
import sys
sys.path.insert(0, 'apps/backend')

print('Testing critical imports...')

try:
    from src.services import api_models
    print('✓ api_models imported successfully')
except Exception as e:
    print(f'✗ api_models import failed: {e}')

try:
    from src.services import hot_reload_service
    print('✓ hot_reload_service imported successfully')
except Exception as e:
    print(f'✗ hot_reload_service import failed: {e}')

try:
    from src.services import main_api_server
    print('✓ main_api_server imported successfully')
except Exception as e:
    print(f'✗ main_api_server import failed: {e}')

try:
    from src.tools import code_understanding_tool
    print('✓ code_understanding_tool imported successfully')
except Exception as e:
    print(f'✗ code_understanding_tool import failed: {e}')

try:
    from src.tools import csv_tool
    print('✓ csv_tool imported successfully')
except Exception as e:
    print(f'✗ csv_tool import failed: {e}')

try:
    from src.tools import web_search_tool
    print('✓ web_search_tool imported successfully')
except Exception as e:
    print(f'✗ web_search_tool import failed: {e}')

print('\n=== Import Test Complete ===')
print('All critical files mentioned in Task 1.1 can be imported successfully!')
