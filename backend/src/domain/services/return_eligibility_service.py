"""
Domain Service for Return Eligibility
Pure business logic for determining return eligibility
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..value_objects import PolicySnapshot, Money, ReturnReason
from ..entities import return as return_entity


@dataclass
class EligibilityResult:
    """Result of eligibility check"""
    eligible: bool
    reasons: List[str]
    fees: List[Dict[str, Any]]
    estimated_refund: Money
    auto_approve: bool
    warning_messages: List[str]


@dataclass
class OrderItem:
    """Order item for eligibility checking"""
    id: str
    sku: str
    title: str
    variant_title: Optional[str]
    quantity: int
    unit_price: Money
    fulfilled_at: Optional[datetime]
    tags: List[str]
    category: str
    product_type: str
    already_returned_quantity: int = 0


class ReturnEligibilityService:
    """
    Domain service for determining return eligibility
    Encapsulates complex business rules
    """
    
    def check_eligibility(
        self,
        order_items: List[OrderItem],
        requested_items: List[Dict[str, Any]],
        order_date: datetime,
        policy: PolicySnapshot
    ) -> EligibilityResult:
        """
        Main eligibility check method
        Returns comprehensive eligibility assessment
        """
        eligible = True
        reasons = []
        fees = []
        warning_messages = []
        total_item_value = Money(0, "USD")
        
        # Check each requested item
        eligible_items = []
        for requested_item in requested_items:
            item_result = self._check_item_eligibility(
                requested_item, order_items, order_date, policy
            )
            
            if not item_result["eligible"]:
                eligible = False
                reasons.extend(item_result["reasons"])
            else:
                eligible_items.append(requested_item)
                # Add to total value
                order_item = next(
                    (item for item in order_items if item.id == requested_item["line_item_id"]),
                    None
                )
                if order_item:
                    item_value = Money(
                        order_item.unit_price.amount * requested_item["quantity"],
                        order_item.unit_price.currency
                    )
                    total_item_value = total_item_value.add(item_value)
            
            if item_result.get("warnings"):
                warning_messages.extend(item_result["warnings"])
        
        # Calculate fees if any items are eligible
        if eligible_items:
            fees = self._calculate_fees(total_item_value, policy, eligible_items)
        
        # Calculate estimated refund
        estimated_refund = self._calculate_refund(total_item_value, fees)
        
        # Check auto-approval eligibility
        auto_approve = self._check_auto_approval(
            estimated_refund, eligible_items, policy
        )
        
        return EligibilityResult(
            eligible=eligible and len(eligible_items) > 0,
            reasons=reasons,
            fees=fees,
            estimated_refund=estimated_refund,
            auto_approve=auto_approve,
            warning_messages=warning_messages
        )
    
    def _check_item_eligibility(
        self,
        requested_item: Dict[str, Any],
        order_items: List[OrderItem],
        order_date: datetime,
        policy: PolicySnapshot
    ) -> Dict[str, Any]:
        """Check eligibility for a single item"""
        line_item_id = requested_item["line_item_id"]
        requested_quantity = requested_item["quantity"]
        
        # Find the order item
        order_item = next(
            (item for item in order_items if item.id == line_item_id),
            None
        )
        
        if not order_item:
            return {
                "eligible": False,
                "reasons": ["Item not found in order"],
                "warnings": []
            }
        
        reasons = []
        warnings = []
        
        # 1. Quantity check
        available_quantity = order_item.quantity - order_item.already_returned_quantity
        if requested_quantity > available_quantity:
            reasons.append(
                f"Requested quantity ({requested_quantity}) exceeds available quantity ({available_quantity})"
            )
        
        # 2. Return window check
        window_result = self._check_return_window(order_item, order_date, policy)
        if not window_result["eligible"]:
            reasons.extend(window_result["reasons"])
        else:
            if window_result.get("warning"):
                warnings.append(window_result["warning"])
        
        # 3. Exclusions check
        exclusions_result = self._check_exclusions(order_item, policy)
        if not exclusions_result["eligible"]:
            reasons.extend(exclusions_result["reasons"])
        
        # 4. Condition requirements check
        condition_result = self._check_condition_requirements(requested_item, policy)
        if not condition_result["eligible"]:
            reasons.extend(condition_result["reasons"])
        
        return {
            "eligible": len(reasons) == 0,
            "reasons": reasons,
            "warnings": warnings
        }
    
    def _check_return_window(
        self,
        order_item: OrderItem,
        order_date: datetime,
        policy: PolicySnapshot
    ) -> Dict[str, Any]:
        """Check if item is within return window"""
        # Use fulfillment date if available, otherwise order date
        reference_date = order_item.fulfilled_at or order_date
        days_since = (datetime.utcnow() - reference_date).days
        
        # Check for category-specific window overrides
        window_days = policy.return_window_days
        
        # Check if item is within window
        if days_since > window_days:
            return {
                "eligible": False,
                "reasons": [f"Return window expired ({days_since} days ago, limit is {window_days} days)"]
            }
        
        # Warning if close to expiry
        days_remaining = window_days - days_since
        warning = None
        if days_remaining <= 3:
            warning = f"Return window expires in {days_remaining} days"
        
        return {
            "eligible": True,
            "reasons": [],
            "warning": warning
        }
    
    def _check_exclusions(
        self,
        order_item: OrderItem,
        policy: PolicySnapshot
    ) -> Dict[str, Any]:
        """Check if item is excluded from returns"""
        reasons = []
        
        # Check excluded categories
        if order_item.category in policy.excluded_categories:
            reasons.append(f"Category '{order_item.category}' is not eligible for returns")
        
        # Check excluded tags
        for tag in order_item.tags:
            if tag.lower() in [t.lower() for t in policy.excluded_tags]:
                reasons.append(f"Item marked as '{tag}' cannot be returned")
                break
        
        return {
            "eligible": len(reasons) == 0,
            "reasons": reasons
        }
    
    def _check_condition_requirements(
        self,
        requested_item: Dict[str, Any],
        policy: PolicySnapshot
    ) -> Dict[str, Any]:
        """Check if condition requirements are met"""
        reason_code = requested_item.get("reason", "")
        
        # Check if photos are required for this reason
        if reason_code in policy.photo_required_reasons:
            photos = requested_item.get("photos", [])
            if not photos or len(photos) == 0:
                return {
                    "eligible": False,
                    "reasons": [f"Photos are required for reason '{reason_code}'"]
                }
        
        return {
            "eligible": True,
            "reasons": []
        }
    
    def _calculate_fees(
        self,
        total_item_value: Money,
        policy: PolicySnapshot,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate applicable fees"""
        fees = []
        
        # Restocking fee
        if policy.restock_fee_enabled and policy.restock_fee_percent > 0:
            restock_amount = total_item_value.amount * (policy.restock_fee_percent / 100)
            fees.append({
                "type": "restock",
                "description": f"Restocking fee ({policy.restock_fee_percent}%)",
                "amount": float(restock_amount),
                "currency": total_item_value.currency
            })
        
        # Shipping fee
        if policy.shipping_fee_enabled and policy.shipping_fee_amount > 0:
            fees.append({
                "type": "shipping",
                "description": "Return shipping fee",
                "amount": float(policy.shipping_fee_amount),
                "currency": total_item_value.currency
            })
        
        return fees
    
    def _calculate_refund(
        self,
        total_item_value: Money,
        fees: List[Dict[str, Any]]
    ) -> Money:
        """Calculate estimated refund amount"""
        total_fees = sum(fee["amount"] for fee in fees)
        refund_amount = max(0, float(total_item_value.amount) - total_fees)
        
        return Money(refund_amount, total_item_value.currency)
    
    def _check_auto_approval(
        self,
        estimated_refund: Money,
        items: List[Dict[str, Any]],
        policy: PolicySnapshot
    ) -> bool:
        """Check if return qualifies for auto-approval"""
        # Check refund amount threshold
        if estimated_refund.amount > policy.auto_approve_threshold:
            return False
        
        # Check for high-risk reasons (if any)
        high_risk_reasons = ["fraud", "chargeback", "abuse"]
        for item in items:
            reason = item.get("reason", "").lower()
            if any(risk_reason in reason for risk_reason in high_risk_reasons):
                return False
        
        return True