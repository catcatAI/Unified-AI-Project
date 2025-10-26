import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_path_config() -> None,
    """Test that we can import and use path_config."""
    try,
        print("✓ Path config imported successfully")
        
        # Check that directories exist
        directories = [DATA_DIR, TRAINING_DIR, MODELS_DIR, CHECKPOINTS_DIR, CONFIGS_DIR]
        for directory in directories,::
            if directory.exists():::
                print(f"✓ Directory {directory.name} exists")
            else,
                print(f"✗ Directory {directory.name} does not exist")
        
        print("Path config test completed!")
        return True
    except Exception as e,::
        print(f"Error, {e}")
        import traceback
        traceback.print_exc()
        return False

if __name"__main__":::
    success = test_path_config()
    exit(0 if success else 1)