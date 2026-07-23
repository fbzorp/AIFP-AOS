import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from apps.models.approval import ApprovalModel

logger = logging.getLogger(__name__)

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
            
        if approval.draft_hash != draft_hash:
            logger.error(f"Hash mismatch: expected {approval.draft_hash}, got {draft_hash}")
            return False
            
        if approval.expires_at and approval.expires_at < datetime.now(timezone.utc):
            logger.error(f"Approval {approval_id} has expired")
            return False
            
        logger.info(f"Approval {approval_id} validated successfully")
        return True
