"""
Label Service Adapter
Concrete implementation using existing label service
"""

from ...domain.value_objects import Money, ShippingLabel, Address, TenantId
from ...domain.entities.return_entity import Return
from ...domain.ports.services import LabelService as LabelServicePort
from ...services.label_service import LabelService as ExistingLabelService


class LabelServiceAdapter(LabelServicePort):
    """Adapter for existing label service"""
    
    def __init__(self, label_service: ExistingLabelService):
        self.label_service = label_service
    
    async def generate_return_label(
        self,
        return_obj: Return,
        from_address: Address,
        to_address: Address
    ) -> ShippingLabel:
        """Generate return shipping label"""
        # Convert to format expected by existing service
        from_addr = {
            "line1": from_address.line1,
            "line2": from_address.line2,
            "city": from_address.city,
            "state": from_address.state,
            "postal_code": from_address.postal_code,
            "country": from_address.country
        }
        
        to_addr = {
            "line1": to_address.line1,
            "line2": to_address.line2,
            "city": to_address.city,
            "state": to_address.state,
            "postal_code": to_address.postal_code,
            "country": to_address.country
        }
        
        label_data = await self.label_service.create_return_label(
            return_id=return_obj.id.value,
            from_address=from_addr,
            to_address=to_addr
        )
        
        return ShippingLabel(
            carrier=label_data["carrier"],
            service_type=label_data["service_type"],
            tracking_number=label_data["tracking_number"],
            label_url=label_data["label_url"],
            cost=Money(label_data["cost"], "USD")
        )
    
    async def get_label_cost(
        self,
        from_address: Address,
        to_address: Address,
        service_type: str = "ground"
    ) -> Money:
        """Get estimated label cost"""
        # Mock implementation - in real scenario would call shipping API
        return Money(5.99, "USD")