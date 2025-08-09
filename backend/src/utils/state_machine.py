"""
Return request state machine with validation and audit logging
"""
from enum import Enum
from typing import Dict, Set, List, Optional
from datetime import datetime
import uuid

class ReturnStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"  
    DENIED = "denied"
    LABEL_ISSUED = "label_issued"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    RESOLVED = "resolved"

class ReturnStateMachine:
    """State machine for return request status transitions"""
    
    # Define valid state transitions
    VALID_TRANSITIONS: Dict[ReturnStatus, Set[ReturnStatus]] = {
        ReturnStatus.REQUESTED: {
            ReturnStatus.APPROVED,
            ReturnStatus.DENIED
        },
        ReturnStatus.APPROVED: {
            ReturnStatus.LABEL_ISSUED,
            ReturnStatus.DENIED  # Can still deny after approval
        },
        ReturnStatus.LABEL_ISSUED: {
            ReturnStatus.IN_TRANSIT,
            ReturnStatus.RECEIVED  # Customer might deliver directly
        },
        ReturnStatus.IN_TRANSIT: {
            ReturnStatus.RECEIVED
        },
        ReturnStatus.RECEIVED: {
            ReturnStatus.RESOLVED
        },
        ReturnStatus.DENIED: {},  # Terminal state
        ReturnStatus.RESOLVED: {}  # Terminal state
    }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if transition is valid"""
        try:
            from_enum = ReturnStatus(from_status)
            to_enum = ReturnStatus(to_status)
            return to_enum in cls.VALID_TRANSITIONS.get(from_enum, set())
        except ValueError:
            return False
    
    @classmethod
    def get_valid_transitions(cls, from_status: str) -> List[str]:
        """Get list of valid transitions from current status"""
        try:
            from_enum = ReturnStatus(from_status)
            return [status.value for status in cls.VALID_TRANSITIONS.get(from_enum, set())]
        except ValueError:
            return []
    
    @classmethod
    def is_terminal_state(cls, status: str) -> bool:
        """Check if status is a terminal state"""
        try:
            status_enum = ReturnStatus(status)
            return len(cls.VALID_TRANSITIONS.get(status_enum, set())) == 0
        except ValueError:
            return False
    
    @classmethod
    def create_audit_log_entry(cls, return_id: str, from_status: str, to_status: str, 
                             notes: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
        """Create audit log entry for status change"""
        return {
            "id": str(uuid.uuid4()),
            "return_id": return_id,
            "from_status": from_status,
            "to_status": to_status,
            "notes": notes,
            "user_id": user_id or "system",
            "timestamp": datetime.utcnow(),
            "event_type": "status_change"
        }

class ReturnResolutionType(str, Enum):
    REFUND = "refund"
    EXCHANGE = "exchange"
    STORE_CREDIT = "store_credit"

class ReturnResolutionHandler:
    """Handle return resolution actions"""
    
    @staticmethod
    def create_refund_record(return_request_id: str, amount: float, 
                           method: str = "original_payment", notes: str = None) -> Dict:
        """Create refund record"""
        return {
            "id": str(uuid.uuid4()),
            "return_request_id": return_request_id,
            "type": "refund",
            "amount": amount,
            "method": method,
            "status": "pending" if method == "stripe" else "manual",
            "notes": notes,
            "created_at": datetime.utcnow(),
            "processed_at": None if method == "stripe" else datetime.utcnow()
        }
    
    @staticmethod
    def create_exchange_record(return_request_id: str, original_items: List[Dict], 
                             new_items: List[Dict], notes: str = None) -> Dict:
        """Create exchange record with placeholder outbound order"""
        return {
            "id": str(uuid.uuid4()),
            "return_request_id": return_request_id,
            "type": "exchange",
            "original_items": original_items,
            "new_items": new_items,
            "outbound_order_id": f"EXC-{str(uuid.uuid4())[:8]}",
            "status": "pending_fulfillment",
            "notes": notes,
            "created_at": datetime.utcnow()
        }
    
    @staticmethod
    def create_store_credit_record(return_request_id: str, customer_email: str, 
                                 amount: float, notes: str = None) -> Dict:
        """Create store credit record"""
        return {
            "id": str(uuid.uuid4()),
            "return_request_id": return_request_id,
            "type": "store_credit",
            "customer_email": customer_email,
            "amount": amount,
            "balance": amount,
            "status": "active",
            "notes": notes,
            "created_at": datetime.utcnow(),
            "expires_at": None  # Could add expiration logic
        }