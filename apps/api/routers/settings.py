from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from apps.models.base import get_db
from apps.api.auth import require_admin
from apps.api.config import settings
from apps.core.audit.service import record_event
import os

router = APIRouter()

# Credential definitions with their environment variable names
CREDENTIAL_DEFINITIONS = {
    "DEEPSEEK_API_KEY": {"description": "DeepSeek API Key for LLM services"},
    "DEEPSEEK_API_BASE": {"description": "DeepSeek API Base URL"},
    "MOLTBOOK_API_KEY": {"description": "Moltbook API Key"},
    "MOLTBOOK_AGENT_API_KEY": {"description": "Moltbook Agent API Key"},
    "MOLTBOOK_APP_KEY": {"description": "Moltbook App Key"},
    "AIFINPAY_AGENT_SECRET": {"description": "AiFinPay Agent Secret (Ed25519)"},
    "AIFINPAY_AGENT_PUBKEY": {"description": "AiFinPay Agent Public Key"},
    "SOLANA_PRIVATE_KEY": {"description": "Solana Private Key"},
    "EVM_PRIVATE_KEY": {"description": "EVM Private Key"},
    "X_API_KEY": {"description": "X (Twitter) API Key"},
    "X_API_SECRET": {"description": "X (Twitter) API Secret"},
    "X_ACCESS_TOKEN": {"description": "X (Twitter) Access Token"},
    "X_ACCESS_TOKEN_SECRET": {"description": "X (Twitter) Access Token Secret"},
    "TELEGRAM_BOT_TOKEN": {"description": "Telegram Bot Token"},
    "ANTHROPIC_API_KEY": {"description": "Anthropic API Key"},
    "OPENAI_API_KEY": {"description": "OpenAI API Key"},
}


class CredentialStatus(BaseModel):
    name: str
    configured: bool
    masked: str
    description: str


class CredentialUpdateRequest(BaseModel):
    name: str
    value: str


class CredentialUpdateResponse(BaseModel):
    success: bool
    message: str
    credential_name: str


def mask_value(value: str) -> str:
    """Mask a credential value, showing only first 4 and last 4 characters."""
    if not value or len(value) < 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


@router.get("/settings/credentials", response_model=List[CredentialStatus])
async def get_credentials(db: AsyncSession = Depends(get_db), user: dict = Depends(require_admin)):
    """
    Get masked status of all configured credentials.
    Returns only masked values, never the raw secrets.
    """
    credentials = []
    
    for name, definition in CREDENTIAL_DEFINITIONS.items():
        # Get value from environment or settings object
        value = getattr(settings, name, None) or os.environ.get(name)
        configured = bool(value and value != "" and value != "None")
        masked = mask_value(value) if configured else "Not configured"
        
        credentials.append(CredentialStatus(
            name=name,
            configured=configured,
            masked=masked,
            description=definition["description"]
        ))
    
    return credentials


@router.patch("/settings/credentials", response_model=CredentialUpdateResponse)
async def update_credential(
    request: CredentialUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Update a credential value in the process-local settings.
    
    Note: This updates the runtime settings object only. For durable changes,
    you must update the environment variable and redeploy the service.
    This design ensures secrets are never written to the database or committed files.
    """
    if request.name not in CREDENTIAL_DEFINITIONS:
        raise HTTPException(status_code=400, detail=f"Unknown credential: {request.name}")
    
    # Update the settings object (process-local only)
    setattr(settings, request.name, request.value)
    os.environ[request.name] = request.value
    
    # Record audit event with credential name only (never the value)
    record_event(
        db,
        agent_name=user.get("sub", "admin"),
        event_type="credential_updated",
        message=f"Credential {request.name} updated via settings API",
        metadata={"credential_name": request.name}
    )
    await db.commit()
    
    return CredentialUpdateResponse(
        success=True,
        message=f"Credential {request.name} updated in runtime settings. For durable changes, update the environment variable and redeploy.",
        credential_name=request.name
    )
