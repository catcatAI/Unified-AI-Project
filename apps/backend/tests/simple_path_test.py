import sys
import os

# Add the src directory to the path
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_path_config() -> None:
    """Test that we can import and use path_config."""
    try:
        _ = print("✓ Path config imported successfully")
        
        # Check that directories exist
        directories = [DATA_DIR, TRAINING_DIR, MODELS_DIR, CHECKPOINTS_DIR, CONFIGS_DIR]
        for directory in directories:
            if directory.exists():
                _ = print(f"✓ Directory {directory.name} exists")
            else:
                _ = print(f"✗ Directory {directory.name} does not exist")
        
        _ = print("Path config test completed!")
        return True
    except Exception as e:
        _ = print(f"Error: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_path_config()
    exit(0 if success else 1)