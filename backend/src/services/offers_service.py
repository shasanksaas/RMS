"""
Offers and Upsells Service
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config.database import db

logger = logging.getLogger(__name__)

class OffersService:
    """Service for managing return offers and upsells"""
    
    async def get_applicable_offers(self, tenant_id: str, order: Dict, items: List[Dict]) -> List[Dict]:
        """Get offers applicable to this return scenario"""
        try:
            # Check if offers are enabled
            feature_offers = os.environ.get('FEATURE_OFFERS', 'on')
            if feature_offers != 'on':
                return []
            
            # Get active offers for tenant
            offers = await db.offers.find({
                "tenant_id": tenant_id,
                "active": True
            }).to_list(None)
            
            applicable_offers = []
            total_value = sum(float(item.get("unit_price", 0)) * item.get("qty", 1) for item in items)
            
            for offer in offers:
                # Check triggers
                triggers = offer.get("triggers", {})
                
                # Min price trigger
                if triggers.get("min_price") and total_value < triggers["min_price"]:
                    continue
                
                # Calculate offer value
                offer_value = self._calculate_offer_value(offer, total_value)
                
                applicable_offers.append({
                    "id": offer["id"],
                    "name": offer["name"],
                    "type": offer["type"],
                    "description": self._get_offer_description(offer, offer_value),
                    "value": offer_value,
                    "ab_flag": offer.get("ab_flag")
                })
            
            return applicable_offers
            
        except Exception as e:
            logger.error(f"Get applicable offers error: {e}")
            return []
    
    async def apply_offer(self, tenant_id: str, offer_data: Dict, base_refund: float) -> Dict[str, Any]:
        """Apply selected offer and calculate benefit"""
        try:
            offer = await db.offers.find_one({
                "id": offer_data["id"],
                "tenant_id": tenant_id,
                "active": True
            })
            
            if not offer:
                return None
            
            offer_value = self._calculate_offer_value(offer, base_refund)
            
            return {
                "code": offer["name"],
                "type": offer["type"],
                "value": offer_value,
                "calculated_amount": offer_value
            }
            
        except Exception as e:
            logger.error(f"Apply offer error: {e}")
            return None
    
    def _calculate_offer_value(self, offer: Dict, base_amount: float) -> float:
        """Calculate monetary value of offer"""
        offer_type = offer["type"]
        value_config = offer.get("value", {})
        
        if offer_type == "BONUS_STORE_CREDIT":
            if "percent" in value_config:
                return base_amount * (value_config["percent"] / 100)
            elif "amount" in value_config:
                return value_config["amount"]
        elif offer_type == "KEEP_ITEM_CREDIT":
            return base_amount * (value_config.get("percent", 30) / 100)
        elif offer_type == "EXCHANGE_DISCOUNT":
            return base_amount * (value_config.get("percent", 10) / 100)
        
        return 0.0
    
    def _get_offer_description(self, offer: Dict, value: float) -> str:
        """Get human-readable offer description"""
        offer_type = offer["type"]
        
        if offer_type == "BONUS_STORE_CREDIT":
            return f"Get ${value:.2f} bonus store credit"
        elif offer_type == "KEEP_ITEM_CREDIT":
            return f"Keep the item and get ${value:.2f} credit"
        elif offer_type == "EXCHANGE_DISCOUNT":
            return f"Get ${value:.2f} discount on your exchange"
        elif offer_type == "UPSELL":
            return f"Upgrade to premium version with ${value:.2f} discount"
        
        return offer.get("name", "Special offer")

# Singleton instance  
offers_service = OffersService()