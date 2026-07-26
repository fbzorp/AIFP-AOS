
from fastapi import FastAPI
from typing import Dict, Any

app = FastAPI()

@app.get("/mcp/v1/tools")
async def get_tool_manifest() -> Dict[str, Any]:
    """Exposes a basic MCP-style tool manifest."""
    return {
        "tools": [
            {
                "name": "list_content",
                "description": "Lists available content items.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10, "description": "Maximum number of content items to return."}
                    }
                }
            },
            {
                "name": "trigger_campaign",
                "description": "Triggers a marketing campaign.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "campaign_id": {"type": "string", "description": "ID of the campaign to trigger."},
                        "start_date": {"type": "string", "format": "date", "description": "Optional start date for the campaign (YYYY-MM-DD)."}
                    },
                    "required": ["campaign_id"]
                }
            },
            {
                "name": "get_metrics",
                "description": "Retrieves performance metrics.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_name": {"type": "string", "description": "Name of the metric to retrieve."},
                        "timeframe": {"type": "string", "enum": ["day", "week", "month"], "default": "day", "description": "Timeframe for the metrics."}
                    },
                    "required": ["metric_name"]
                }
            }
        ]
    }

# To run this server:
# uvicorn apps.integrations.mcp.server:app --host 0.0.0.0 --port 8000
