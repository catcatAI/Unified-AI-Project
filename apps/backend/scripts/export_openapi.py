"""
Angela AI - OpenAPI Spec Exporter
Exports the OpenAPI specification to a static file.
"""

import json
import sys
from pathlib import Path

# Add the backend source to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend" / "src"))


def export_openapi_spec():
    """Export the OpenAPI specification to a static file."""
    try:
        from main import app

        # Get the OpenAPI schema
        openapi_schema = app.openapi()

        # Write to file
        output_path = Path("docs/api/openapi.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

        print(f"OpenAPI spec exported to: {output_path}")
        print(f"Version: {openapi_schema.get('info', {}).get('version', 'unknown')}")
        print(f"Endpoints: {len(openapi_schema.get('paths', {}))}")

        return True

    except ImportError as e:
        print(f"Error importing app: {e}")
        print("Make sure you're running this from the project root.")
        return False

    except Exception as e:
        print(f"Error exporting OpenAPI spec: {e}")
        return False


if __name__ == "__main__":
    success = export_openapi_spec()
    sys.exit(0 if success else 1)
