"""
Fraud Detection Utility
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class FraudDetector:
    """Basic fraud detection utility"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.triggered_rules = []
    
    async def calculate_risk_score(
        self,
        return_data: Dict[str, Any],
        order_data: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]]
    ) -> int:
        """Calculate fraud risk score (0-100)"""
        
        risk_score = 0
        self.triggered_rules = []
        
        # High return frequency
        if customer_data and customer_data.get("return_count", 0) > 10:
            risk_score += 30
            self.triggered_rules.append("high_return_frequency")
        
        # High return value
        return_value = return_data.get("total_value", 0)
        if return_value > 1000:
            risk_score += 20
            self.triggered_rules.append("high_value_return")
        
        # Recent customer
        if customer_data and customer_data.get("account_age_days", 365) < 30:
            risk_score += 15
            self.triggered_rules.append("new_customer")
        
        # Multiple returns same item
        if return_data.get("return_reason") == "wrong_size" and customer_data:
            recent_returns = customer_data.get("recent_size_returns", 0)
            if recent_returns > 3:
                risk_score += 25
                self.triggered_rules.append("sizing_abuse")
        
        # Geographic inconsistency
        order_location = order_data.get("shipping_address", {}).get("country", "")
        customer_location = customer_data.get("billing_address", {}).get("country", "") if customer_data else ""
        
        if order_location and customer_location and order_location != customer_location:
            risk_score += 10
            self.triggered_rules.append("geographic_inconsistency")
        
        return min(risk_score, 100)
    
    def get_triggered_rules(self) -> List[str]:
        """Get list of triggered fraud rules"""
        return self.triggered_rules