#!/usr/bin/env python3
"""
Export OpenAPI specification from FastAPI application.
This script generates the OpenAPI JSON schema for API documentation.

Usage:
    python scripts/export_openapi.py              # Export to docs/openapi.json
    python scripts/export_openapi.py --check      # Check if docs/openapi.json is up to date
"""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.main import app

def get_openapi_schema():
    """Generate the OpenAPI schema from the FastAPI app."""
    return app.openapi()

def export_openapi():
    """Export the OpenAPI specification to a JSON file."""
    # Get the OpenAPI schema
    openapi_schema = get_openapi_schema()
    
    # Convert to JSON
    openapi_json = json.dumps(openapi_schema, indent=2)
    
    # Write to docs directory
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    output_file = docs_dir / "openapi.json"
    with open(output_file, "w") as f:
        f.write(openapi_json)
    
    print(f"OpenAPI specification exported to: {output_file}")
    print(f"API Title: {openapi_schema['info']['title']}")
    print(f"API Version: {openapi_schema['info']['version']}")
    print(f"Total Endpoints: {len(openapi_schema['paths'])}")
    
    return output_file

def check_openapi():
    """Check if the committed OpenAPI spec is up to date."""
    # Get the current OpenAPI schema
    current_schema = get_openapi_schema()
    current_json = json.dumps(current_schema, indent=2)
    
    # Read the committed OpenAPI spec
    docs_dir = project_root / "docs"
    output_file = docs_dir / "openapi.json"
    
    if not output_file.exists():
        print(f"ERROR: {output_file} does not exist")
        print("Run: python scripts/export_openapi.py")
        sys.exit(1)
    
    with open(output_file, "r") as f:
        committed_json = f.read()
    
    # Compare
    if current_json == committed_json:
        print("[OK] OpenAPI specification is up to date")
        print(f"API Title: {current_schema['info']['title']}")
        print(f"API Version: {current_schema['info']['version']}")
        print(f"Total Endpoints: {len(current_schema['paths'])}")
        sys.exit(0)
    else:
        print("ERROR: docs/openapi.json is stale")
        print("The committed OpenAPI specification does not match the current API routes.")
        print("")
        print("To fix this, run:")
        print("  python scripts/export_openapi.py")
        print("  git add docs/openapi.json")
        print("  git commit -m 'Update OpenAPI specification'")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Export or check OpenAPI specification")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if docs/openapi.json is up to date (exit non-zero if stale)"
    )
    
    args = parser.parse_args()
    
    if args.check:
        check_openapi()
    else:
        export_openapi()

if __name__ == "__main__":
    main()