"""
Advanced Email Service for Returns
Handles all return-related email notifications
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from ..config.database import db

logger = logging.getLogger(__name__)

class EmailService:
    """Email service with mock and Resend implementations"""
    
    def __init__(self):
        self.feature_mode = os.environ.get('FEATURE_EMAIL', 'mock')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@returns-manager.com')
        self.from_name = os.environ.get('FROM_NAME', 'Returns Manager')
    
    async def send_return_requested(self, tenant_id: str, return_request: Dict, order: Dict):
        """Send return requested notification"""
        try:
            # Email to customer
            await self._send_email(
                tenant_id=tenant_id,
                to_email=order.get("customer_email"),
                to_name=order.get("customer_name"),
                template="return_requested_customer",
                data={
                    "return_id": return_request["id"],
                    "order_number": order.get("order_number"),
                    "items_count": len(return_request["items"]),
                    "estimated_refund": return_request["estimated_refund_amount"]
                }
            )
            
            # Email to merchant
            await self._send_email(
                tenant_id=tenant_id,
                to_email="merchant@example.com",  # TODO: Get from tenant settings
                to_name="Merchant",
                template="return_requested_merchant",
                data={
                    "return_id": return_request["id"],
                    "customer_name": order.get("customer_name"),
                    "order_number": order.get("order_number"),
                    "status": return_request["status"]
                }
            )
            
        except Exception as e:
            logger.error(f"Send return requested email error: {e}")
    
    async def send_return_approved(self, tenant_id: str, return_request: Dict, order: Dict):
        """Send return approved notification"""
        try:
            await self._send_email(
                tenant_id=tenant_id,
                to_email=order.get("customer_email"),
                to_name=order.get("customer_name"),
                template="return_approved",
                data={
                    "return_id": return_request["id"],
                    "order_number": order.get("order_number"),
                    "next_steps": "Please ship your items back to us using the prepaid label."
                }
            )
            
        except Exception as e:
            logger.error(f"Send return approved email error: {e}")
    
    async def send_return_declined(self, tenant_id: str, return_request: Dict, order: Dict, reason: str):
        """Send return declined notification"""
        try:
            await self._send_email(
                tenant_id=tenant_id,
                to_email=order.get("customer_email"),
                to_name=order.get("customer_name"),
                template="return_declined",
                data={
                    "return_id": return_request["id"],
                    "order_number": order.get("order_number"),
                    "reason": reason
                }
            )
            
        except Exception as e:
            logger.error(f"Send return declined email error: {e}")
    
    async def send_label_issued(self, tenant_id: str, return_request: Dict, order: Dict, label_data: Dict):
        """Send shipping label to customer"""
        try:
            await self._send_email(
                tenant_id=tenant_id,
                to_email=order.get("customer_email"),
                to_name=order.get("customer_name"),
                template="label_issued",
                data={
                    "return_id": return_request["id"],
                    "order_number": order.get("order_number"),
                    "label_url": label_data.get("label_url"),
                    "tracking": label_data.get("tracking"),
                    "instructions": "Please attach this label to your return package."
                }
            )
            
        except Exception as e:
            logger.error(f"Send label issued email error: {e}")
    
    async def send_refund_processed(self, tenant_id: str, return_request: Dict, order: Dict, amount: float, method: str):
        """Send refund processed notification"""
        try:
            await self._send_email(
                tenant_id=tenant_id,
                to_email=order.get("customer_email"),
                to_name=order.get("customer_name"),
                template="refund_processed",
                data={
                    "return_id": return_request["id"],
                    "order_number": order.get("order_number"),
                    "refund_amount": amount,
                    "refund_method": method,
                    "processing_time": "3-5 business days"
                }
            )
            
        except Exception as e:
            logger.error(f"Send refund processed email error: {e}")
    
    async def send_draft_approved(self, tenant_id: str, draft: Dict, return_id: str):
        """Send draft approval notification"""
        try:
            await self._send_email(
                tenant_id=tenant_id,
                to_email=draft.get("email"),
                to_name="Customer",
                template="draft_approved",
                data={
                    "order_number": draft.get("order_number"),
                    "return_id": return_id,
                    "message": "Your return request has been approved and is now being processed."
                }
            )
        except Exception as e:
            logger.error(f"Send draft approved email error: {e}")
    
    async def send_draft_rejected(self, tenant_id: str, draft: Dict, reason: str):
        """Send draft rejection notification"""
        try:
            await self._send_email(
                tenant_id=tenant_id,
                to_email=draft.get("email"),
                to_name="Customer",
                template="draft_rejected",
                data={
                    "order_number": draft.get("order_number"),
                    "reason": reason
                }
            )
        except Exception as e:
            logger.error(f"Send draft rejected email error: {e}")

    async def _send_email(self, tenant_id: str, to_email: str, to_name: str, 
                         template: str, data: Dict[str, Any]):
        """Send email using configured service"""
        try:
            if self.feature_mode == 'mock':
                await self._send_mock_email(tenant_id, to_email, to_name, template, data)
            elif self.feature_mode == 'resend':
                await self._send_resend_email(tenant_id, to_email, to_name, template, data)
            
        except Exception as e:
            logger.error(f"Send email error: {e}")
    
    async def _send_mock_email(self, tenant_id: str, to_email: str, to_name: str, 
                              template: str, data: Dict[str, Any]):
        """Store email in message center for testing"""
        try:
            email_doc = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "to_email": to_email,
                "to_name": to_name,
                "template": template,
                "subject": self._get_email_subject(template, data),
                "body": self._get_email_body(template, data),
                "status": "sent",
                "sent_at": datetime.utcnow()
            }
            
            await db.email_logs.insert_one(email_doc)
            logger.info(f"Mock email sent: {template} to {to_email}")
            
        except Exception as e:
            logger.error(f"Mock email error: {e}")
    
    async def _send_resend_email(self, tenant_id: str, to_email: str, to_name: str, 
                                template: str, data: Dict[str, Any]):
        """Send email using Resend API"""
        # TODO: Implement Resend integration
        logger.warning("Resend integration not implemented, falling back to mock")
        await self._send_mock_email(tenant_id, to_email, to_name, template, data)
    
    def _get_email_subject(self, template: str, data: Dict) -> str:
        """Get email subject for template"""
        subjects = {
            "return_requested_customer": f"Return Request Received - #{data.get('return_id', '')}",
            "return_requested_merchant": f"New Return Request - #{data.get('return_id', '')}",
            "return_approved": f"Return Approved - #{data.get('return_id', '')}",
            "return_declined": f"Return Request Declined - #{data.get('return_id', '')}",
            "label_issued": f"Return Label Ready - #{data.get('return_id', '')}",
            "refund_processed": f"Refund Processed - #{data.get('return_id', '')}"
        }
        return subjects.get(template, "Return Update")
    
    def _get_email_body(self, template: str, data: Dict) -> str:
        """Get email body for template"""
        if template == "return_requested_customer":
            return f"""
Your return request #{data.get('return_id')} has been received.

Order: #{data.get('order_number')}
Items: {data.get('items_count')} item(s)
Estimated Refund: ${data.get('estimated_refund', 0):.2f}

We'll review your request and get back to you within 1-2 business days.

Thank you for your business!
            """
        elif template == "return_approved":
            return f"""
Great news! Your return request #{data.get('return_id')} has been approved.

Order: #{data.get('order_number')}

Next Steps: {data.get('next_steps', 'We will send you a prepaid return label shortly.')}

Thank you for your business!
            """
        # Add more templates as needed
        return f"Return update for #{data.get('return_id', '')}"

# Singleton instance
email_service = EmailService()