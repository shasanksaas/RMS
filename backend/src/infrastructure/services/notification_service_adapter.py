"""
Notification Service Adapter
Concrete implementation using existing email service
"""

from typing import Optional
from ...domain.value_objects import TenantId
from ...domain.entities.return_entity import Return
from ...domain.ports.services import NotificationService as NotificationServicePort
from ...services.email_service import EmailService


class NotificationServiceAdapter(NotificationServicePort):
    """Adapter for existing email service"""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    async def send_return_requested_notification(
        self,
        return_obj: Return,
        tenant_id: TenantId
    ) -> bool:
        """Send notification when return is requested"""
        try:
            await self.email_service.send_return_requested_email(
                customer_email=return_obj.customer_email.value,
                return_id=return_obj.id.value,
                order_id=return_obj.order_id.value,
                items=return_obj.line_items,
                tenant_id=tenant_id.value
            )
            return True
        except Exception:
            return False
    
    async def send_return_approved_notification(
        self,
        return_obj: Return,
        tenant_id: TenantId,
        label_url: Optional[str] = None
    ) -> bool:
        """Send notification when return is approved"""
        try:
            await self.email_service.send_return_approved_email(
                customer_email=return_obj.customer_email.value,
                return_id=return_obj.id.value,
                label_url=label_url,
                tenant_id=tenant_id.value
            )
            return True
        except Exception:
            return False
    
    async def send_return_declined_notification(
        self,
        return_obj: Return,
        tenant_id: TenantId,
        reason: str
    ) -> bool:
        """Send notification when return is declined"""
        try:
            # Add a declined email method to email service if needed
            # For now, use existing method with modification
            await self.email_service.send_return_requested_email(
                customer_email=return_obj.customer_email.value,
                return_id=return_obj.id.value,
                order_id=return_obj.order_id.value,
                items=return_obj.line_items,
                tenant_id=tenant_id.value,
                subject="Return Request Declined",
                additional_message=f"Reason: {reason}"
            )
            return True
        except Exception:
            return False