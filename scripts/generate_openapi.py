#!/usr/bin/env python3
"""
OpenAPI schema generator - static version for CI
"""

import json
import sys
from pathlib import Path

# Static OpenAPI schema based on current API routes
schema = {
    "openapi": "3.0.0",
    "info": {
        "title": "AiFinPay Autonomous Growth OS",
        "description": "AiFinPay Autonomous OS API - Content approvals, MCP integration, and system health monitoring with JWT-based authentication and role-based access control",
        "version": "1.0.0"
    },
    "paths": {
        "/health": {
            "get": {
                "summary": "Health check",
                "description": "Check API and dependency health",
                "responses": {
                    "200": {"description": "Health status"}
                }
            }
        },
        "/metrics": {
            "get": {
                "summary": "Prometheus metrics",
                "description": "Prometheus metrics endpoint",
                "responses": {
                    "200": {"description": "Metrics"}
                }
            }
        },
        "/api/v1/agents": {
            "get": {
                "summary": "List all available agents",
                "description": "Retrieve information about all registered agents including their roles, descriptions, and capabilities",
                "responses": {
                    "200": {"description": "List of agents"}
                }
            }
        },
        "/api/v1/tasks": {
            "get": {
                "summary": "List recent tasks",
                "description": "Retrieve a list of recent task execution records with their current status",
                "responses": {
                    "200": {"description": "List of tasks"}
                }
            }
        },
        "/api/v1/tasks": {
            "post": {
                "summary": "Create a task",
                "description": "Create a new task",
                "responses": {
                    "200": {"description": "Task created"}
                }
            }
        },
        "/api/v1/audit": {
            "get": {
                "summary": "Get audit log",
                "description": "Retrieve recent audit events",
                "responses": {
                    "200": {"description": "Audit events"}
                }
            }
        },
        "/api/v1/campaigns": {
            "get": {
                "summary": "List campaigns",
                "description": "Retrieve recent campaigns",
                "responses": {
                    "200": {"description": "List of campaigns"}
                }
            }
        },
        "/api/v1/campaigns": {
            "post": {
                "summary": "Create campaign",
                "description": "Create a new campaign",
                "responses": {
                    "200": {"description": "Campaign created"}
                }
            }
        },
        "/api/v1/sources": {
            "get": {
                "summary": "List sources",
                "description": "Retrieve sources sorted by relevance",
                "responses": {
                    "200": {"description": "List of sources"}
                }
            }
        },
        "/api/v1/metrics": {
            "get": {
                "summary": "Get system metrics",
                "description": "Retrieve system-wide metrics including agent counts, task statistics, campaign counts, source counts, and recent audit activity",
                "responses": {
                    "200": {"description": "System metrics"}
                }
            }
        },
        "/api/v1/approvals": {
            "get": {
                "summary": "List approvals",
                "description": "Retrieve content approvals (requires viewer role)",
                "responses": {
                    "200": {"description": "List of approvals"}
                }
            }
        },
        "/api/v1/content": {
            "get": {
                "summary": "List content queue",
                "description": "Returns content items ordered by status and creation date for the approval queue (requires viewer role)",
                "responses": {
                    "200": {"description": "Content queue"}
                }
            }
        },
        "/api/v1/content/{content_id}": {
            "patch": {
                "summary": "Edit content item",
                "description": "Edit an existing content item (title, body, variants). Resets status to draft. Requires write permission",
                "responses": {
                    "200": {"description": "Content updated"}
                }
            }
        },
        "/api/v1/content/{content_id}/submit": {
            "post": {
                "summary": "Submit content for approval",
                "description": "Submit content for approval queue. Requires write permission",
                "responses": {
                    "200": {"description": "Content submitted"}
                }
            }
        },
        "/api/v1/approvals/{approval_id}": {
            "get": {
                "summary": "Get approval",
                "description": "Retrieve a specific approval record",
                "responses": {
                    "200": {"description": "Approval details"}
                }
            }
        },
        "/api/v1/approvals/{approval_id}/approve": {
            "post": {
                "summary": "Approve content",
                "description": "Approve content for publishing. Requires approver role",
                "responses": {
                    "200": {"description": "Content approved"}
                }
            }
        },
        "/api/v1/approvals/{approval_id}/reject": {
            "post": {
                "summary": "Reject content",
                "description": "Reject content. Requires approver role",
                "responses": {
                    "200": {"description": "Content rejected"}
                }
            }
        },
        "/api/v1/approvals/{approval_id}/publish": {
            "post": {
                "summary": "Publish approved content",
                "description": "Publish content that has been approved. Requires publisher role",
                "responses": {
                    "200": {"description": "Content published"}
                }
            }
        },
        "/api/v1/settings": {
            "get": {
                "summary": "Get settings",
                "description": "Retrieve system settings (admin only)",
                "responses": {
                    "200": {"description": "System settings"}
                }
            }
        },
        "/api/v1/settings": {
            "put": {
                "summary": "Update settings",
                "description": "Update system settings (admin only)",
                "responses": {
                    "200": {"description": "Settings updated"}
                }
            }
        },
        "/api/v1/marketing/activity": {
            "get": {
                "summary": "List marketing activity",
                "description": "Retrieve marketing activity and evidence",
                "responses": {
                    "200": {"description": "Marketing activity"}
                }
            }
        },
        "/api/v1/marketing/activity": {
            "post": {
                "summary": "Record marketing activity",
                "description": "Record a marketing activity event",
                "responses": {
                    "200": {"description": "Activity recorded"}
                }
            }
        }
    },
    "tags": [
        {
            "name": "System",
            "description": "System health checks and API information"
        },
        {
            "name": "Approvals",
            "description": "Content approval workflow, engagement proposals, and calendar management"
        },
        {
            "name": "Settings",
            "description": "System settings and credential management (admin only)"
        },
        {
            "name": "Marketing",
            "description": "Marketing activity and evidence registry"
        }
    ]
}

output_file = Path(__file__).parent.parent / "docs" / "openapi.json"
output_file.parent.mkdir(exist_ok=True)

with open(output_file, "w") as f:
    json.dump(schema, f, indent=2)

print(f"OpenAPI schema exported to {output_file}")
print(f"Title: {schema['info']['title']}")
print(f"Version: {schema['info']['version']}")
print(f"Endpoints: {len(schema['paths'])}")