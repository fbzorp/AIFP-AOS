import logging
import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from apps.models.approval import ApprovalModel

logger = logging.getLogger(__name__)

def compute_draft_hash(content_item) -> str:
    """
    Computes a deterministic SHA256 hash of the content item fields that matter for approval.
    """
    data = {
        "title": content_item.title,
        "body": content_item.body or "",
        "channel": content_item.channel,
        "objective": content_item.objective or ""
    }
    # Sort keys for deterministic serialization
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()

class PolicyEngine:
    """
    Policy Engine for AiFinPay Autonomous Growth OS.
    Validates autonomous actions against defined policies and human approvals.
    """
    
    def validate_approval(self, session: Session, approval_id: str, draft_hash: str) -> bool:
        """
        Validates if a specific draft has a valid and signed human approval.
        """
        logger.info(f"Validating approval {approval_id} for draft hash {draft_hash}")
        
        approval = session.query(ApprovalModel).filter(ApprovalModel.id == approval_id).first()
        
        if not approval:
            logger.error(f"Approval {approval_id} not found")
            return False
            
        if approval.status != "approved":
            logger.error(f"Approval {approval_id} is not in 'approved' status")
            return False
            
        if approval.draft_hash != draft_hash:
            logger.error(f"Hash mismatch: expected {approval.draft_hash}, got {draft_hash}")
            return False
            
        if approval.expires_at:
            # Ensure both are offset-aware for comparison
            expires_at = approval.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < datetime.now(timezone.utc):
                logger.error(f"Approval {approval_id} has expired")
                return False
            
        logger.info(f"Approval {approval_id} validated successfully")
        return True
