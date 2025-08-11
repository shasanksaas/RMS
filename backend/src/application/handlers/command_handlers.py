"""
Command Handlers for CQRS Implementation
Handle commands that change system state
"""

from typing import Dict, Any
import uuid
from datetime import datetime

from ..commands import (
    CreateReturnRequest, CreateReturnDraft, ApproveReturn, RejectReturn,
    ProcessRefund, GenerateReturnLabel, ApproveDraftAndConvert
)
from ...domain.entities.return_entity import Return, ReturnDraft, ReturnChannel, ReturnMethod, ReturnLineItem
from ...domain.value_objects import (
    ReturnId, TenantId, OrderId, Email, Money, ReturnReason, Address
)
from ...domain.services.return_eligibility_service import ReturnEligibilityService
from ...domain.ports.repositories import ReturnRepository, ReturnDraftRepository, OrderRepository
from ...domain.ports.services import (
    ShopifyService, LabelService, NotificationService, PolicyService, EventPublisher
)


class CreateReturnRequestHandler:
    """Handle return request creation"""
    
    def __init__(
        self,
        return_repository: ReturnRepository,
        order_repository: OrderRepository,
        policy_service: PolicyService,
        eligibility_service: ReturnEligibilityService,
        notification_service: NotificationService,
        event_publisher: EventPublisher,
        shopify_service: ShopifyService
    ):
        self.return_repository = return_repository
        self.order_repository = order_repository
        self.policy_service = policy_service
        self.eligibility_service = eligibility_service
        self.notification_service = notification_service
        self.event_publisher = event_publisher
        self.shopify_service = shopify_service
    
    async def handle(self, command: CreateReturnRequest) -> Dict[str, Any]:
        """Create a new return request"""
        # Get order data
        order = await self.order_repository.get_by_id(command.order_id, command.tenant_id)
        if not order:
            raise ValueError("Order not found")
        
        # Get current policy
        policy = await self.policy_service.get_current_policy(command.tenant_id)
        
        # Create return entity
        return_obj = Return.create_new(
            tenant_id=command.tenant_id,
            order_id=command.order_id,
            customer_email=command.customer_email,
            channel=command.channel,
            return_method=command.return_method,
            policy_snapshot=policy
        )
        
        # Add line items
        for item_data in command.line_items:
            line_item = ReturnLineItem(
                line_item_id=item_data["line_item_id"],
                sku=item_data["sku"],
                title=item_data["title"],
                variant_title=item_data.get("variant_title"),
                quantity=item_data["quantity"],
                unit_price=Money(str(item_data["unit_price"]), "USD"),  # Convert to string for Decimal
                reason=ReturnReason(item_data["reason"], item_data.get("reason_description", "")),
                condition=item_data["condition"],
                photos=item_data.get("photos", []),
                notes=item_data.get("notes", "")
            )
            return_obj.add_line_item(line_item)
        
        # Calculate estimated refund
        return_obj.estimated_refund = return_obj.calculate_refund()
        
        # Submit the return
        return_obj.change_status(
            return_obj.status.REQUESTED, 
            command.submitted_by or "customer",
            "Return request submitted"
        )
        
        # Save return
        await self.return_repository.save(return_obj)
        
        # Publish domain events
        for event in return_obj.get_domain_events():
            await self.event_publisher.publish(event)
        return_obj.clear_domain_events()
        
        # Send notification
        await self.notification_service.send_return_requested_notification(
            return_obj, command.tenant_id
        )
        
        return {
            "return_id": return_obj.id.value,
            "status": return_obj.status.value,
            "estimated_refund": {
                "amount": float(return_obj.estimated_refund.amount),
                "currency": return_obj.estimated_refund.currency
            }
        }


class CreateReturnDraftHandler:
    """Handle return draft creation (fallback mode)"""
    
    def __init__(
        self,
        draft_repository: ReturnDraftRepository,
        event_publisher: EventPublisher
    ):
        self.draft_repository = draft_repository
        self.event_publisher = event_publisher
    
    async def handle(self, command: CreateReturnDraft) -> Dict[str, Any]:
        """Create a return draft for manual review"""
        draft = ReturnDraft(
            id=str(uuid.uuid4()),
            tenant_id=command.tenant_id,
            order_number=command.order_number,
            customer_email=command.customer_email,
            channel=command.channel,
            items=command.items,
            photos=command.photos,
            customer_note=command.customer_note
        )
        
        await self.draft_repository.save(draft)
        
        return {
            "draft_id": draft.id,
            "status": draft.status,
            "message": "Return request submitted for review"
        }


class ApproveReturnHandler:
    """Handle return approval"""
    
    def __init__(
        self,
        return_repository: ReturnRepository,
        notification_service: NotificationService,
        label_service: LabelService,
        event_publisher: EventPublisher
    ):
        self.return_repository = return_repository
        self.notification_service = notification_service
        self.label_service = label_service
        self.event_publisher = event_publisher
    
    async def handle(self, command: ApproveReturn) -> Dict[str, Any]:
        """Approve a return"""
        return_id = ReturnId(command.return_id)
        return_obj = await self.return_repository.get_by_id(return_id, command.tenant_id)
        
        if not return_obj:
            raise ValueError("Return not found")
        
        # Approve the return
        return_obj.approve(command.approver, command.override_policy, command.notes)
        
        # Save changes
        await self.return_repository.save(return_obj)
        
        # Publish domain events
        for event in return_obj.get_domain_events():
            await self.event_publisher.publish(event)
        return_obj.clear_domain_events()
        
        # Send notification (will include label if generated)
        await self.notification_service.send_return_approved_notification(
            return_obj, command.tenant_id
        )
        
        return {
            "return_id": return_obj.id.value,
            "status": return_obj.status.value,
            "message": "Return approved successfully"
        }


class RejectReturnHandler:
    """Handle return rejection"""
    
    def __init__(
        self,
        return_repository: ReturnRepository,
        notification_service: NotificationService,
        event_publisher: EventPublisher
    ):
        self.return_repository = return_repository
        self.notification_service = notification_service
        self.event_publisher = event_publisher
    
    async def handle(self, command: RejectReturn) -> Dict[str, Any]:
        """Reject a return"""
        return_id = ReturnId(command.return_id)
        return_obj = await self.return_repository.get_by_id(return_id, command.tenant_id)
        
        if not return_obj:
            raise ValueError("Return not found")
        
        # Reject the return
        return_obj.reject(command.rejector, command.reason)
        
        # Save changes
        await self.return_repository.save(return_obj)
        
        # Publish domain events
        for event in return_obj.get_domain_events():
            await self.event_publisher.publish(event)
        return_obj.clear_domain_events()
        
        # Send notification
        await self.notification_service.send_return_declined_notification(
            return_obj, command.tenant_id, command.reason
        )
        
        return {
            "return_id": return_obj.id.value,
            "status": return_obj.status.value,
            "message": "Return declined"
        }


class ApproveDraftAndConvertHandler:
    """Handle draft approval and conversion to return"""
    
    def __init__(
        self,
        draft_repository: ReturnDraftRepository,
        return_repository: ReturnRepository,
        order_repository: OrderRepository,
        policy_service: PolicyService,
        event_publisher: EventPublisher
    ):
        self.draft_repository = draft_repository
        self.return_repository = return_repository
        self.order_repository = order_repository
        self.policy_service = policy_service
        self.event_publisher = event_publisher
    
    async def handle(self, command: ApproveDraftAndConvert) -> Dict[str, Any]:
        """Approve draft and convert to return"""
        draft = await self.draft_repository.get_by_id(command.draft_id, command.tenant_id)
        if not draft:
            raise ValueError("Draft not found")
        
        # Get linked order
        order_id = OrderId(command.linked_order_id)
        
        # Get current policy
        policy = await self.policy_service.get_current_policy(command.tenant_id)
        
        # Convert draft to return
        return_obj = draft.approve_and_convert_to_return(command.approver, order_id, policy)
        
        # Save return
        await self.return_repository.save(return_obj)
        
        # Delete draft
        await self.draft_repository.delete(command.draft_id, command.tenant_id)
        
        # Publish domain events
        for event in return_obj.get_domain_events():
            await self.event_publisher.publish(event)
        return_obj.clear_domain_events()
        
        return {
            "return_id": return_obj.id.value,
            "status": return_obj.status.value,
            "message": "Draft approved and converted to return"
        }