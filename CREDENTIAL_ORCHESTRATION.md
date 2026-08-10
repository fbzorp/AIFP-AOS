# Credential Orchestration - Single Source of Truth

## Overview
The credential system has been restructured to use `.env` as the single source of truth for all agent credentials. Each agent fetches its credentials directly from environment variables in the `.env` file.

## Architecture

### 1. Single Source of Truth: `.env` File
The `.env` file now contains dedicated sections for each agent:

```bash
# ------------------- FOUNDER CONTENT AGENT -------------------
FOUNDER_CONTENT_X_API_KEY=...
FOUNDER_CONTENT_X_API_SECRET=...
FOUNDER_CONTENT_X_ACCESS_TOKEN=...
FOUNDER_CONTENT_X_ACCESS_TOKEN_SECRET=...
FOUNDER_CONTENT_X_AUTOPUBLISH=true
FOUNDER_CONTENT_TELEGRAM_BOT_TOKEN=...
FOUNDER_CONTENT_TELEGRAM_CHAT_ID=...
FOUNDER_CONTENT_TELEGRAM_AUTOPUBLISH=true
FOUNDER_CONTENT_TELEGRAM_DEFAULT_CHANNEL=...
FOUNDER_CONTENT_MOLTBOOK_AGENT_API_KEY=...
FOUNDER_CONTENT_MOLTBOOK_APP_KEY=...
FOUNDER_CONTENT_MOLTBOOK_AUTOPUBLISH=true

# ------------------- TECHNICAL CONTENT AGENT -------------------
TECHNICAL_CONTENT_X_API_KEY=...
# ... (similar structure)

# ------------------- SEO CONTENT AGENT -------------------
SEO_CONTENT_X_API_KEY=...
# ... (similar structure)
```

### 2. Credential Service (`apps/core/credential/service.py`)
The credential service now:
- Reads directly from environment variables
- No longer uses database for credential storage
- Converts agent names to environment variable prefixes
- Falls back to global credentials if agent-specific ones aren't set

**Example Logic:**
```python
def get_x_credentials_sync(agent_name: str) -> Dict[str, Any]:
    agent_prefix = agent_name.upper().replace(" ", "_")  # "Founder Content" -> "FOUNDER_CONTENT"
    
    # Try agent-specific credentials first
    agent_api_key = getattr(settings, f"{agent_prefix}_X_API_KEY", None)
    
    if agent_api_key:
        return agent_specific_credentials
    
    # Fallback to global credentials
    return global_credentials
```

### 3. Configuration (`apps/api/config.py`)
Added agent-specific environment variable definitions to the Settings class:

```python
# Agent-Specific Credentials (Single Source of Truth)
FOUNDER_CONTENT_X_API_KEY: Optional[str] = None
FOUNDER_CONTENT_X_API_SECRET: Optional[str] = None
# ... (for all agents and platforms)
```

### 4. Publisher Dispatcher (`apps/integrations/publishing/dispatcher.py`)
All publishers now:
- Accept `agent_name` parameter in constructor
- Lazy-initialize with agent-specific credentials
- Use CredentialService to fetch credentials from `.env`

## Benefits

1. **Single Source of Truth**: All credentials in one place (`.env`)
2. **No Database Dependency**: Eliminates credential table and migration complexity
3. **Agent Isolation**: Each agent can have distinct credentials
4. **Simple Debugging**: Easy to verify which credentials each agent uses
5. **Security**: `.env` is gitignored, credentials stay local
6. **Flexibility**: Easy to add new agents or platforms

## Credential Fetching Flow

```
Agent Execution
    ↓
Publisher instantiated with agent_name
    ↓
CredentialService.get_x_credentials_sync("Founder Content")
    ↓
Converts to "FOUNDER_CONTENT_X_API_KEY"
    ↓
Reads from settings (loaded from .env)
    ↓
Returns agent-specific credentials or falls back to global
```

## Testing

Run the credential test script to verify:
```bash
docker compose -f docker-compose.dev.yml exec -T api uv run python scripts/test_env_credentials.py
```

## Migration Notes

- Database credential table is no longer used
- Legacy scripts (`setup_agent_credentials.sh`, `manage_credentials.py`) have been removed
- CredentialModel and database credential storage have been eliminated
- All credential management now happens in `.env`
- Global credentials are kept as fallbacks for backward compatibility
