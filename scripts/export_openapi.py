#!/usr/bin/env python3
"""
Export OpenAPI specification from FastAPI application.
This script generates the OpenAPI JSON schema for API documentation.
"""

import json
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.main import app

def export_openapi():
    """Export the OpenAPI specification to a JSON file."""
    # Get the OpenAPI schema
    openapi_schema = app.openapi()
    
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

if __name__ == "__main__":
    export_openapi()