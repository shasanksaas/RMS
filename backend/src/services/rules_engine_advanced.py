"""
Advanced Rules Engine
Deterministic policy evaluation pipeline
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class AdvancedRulesEngine:
    """
    Rules evaluation pipeline that always evaluates in order:
    1. window_check
    2. exclusions  
    3. condition_requirements
    4. fee_calc
    5. auto_approve_threshold
    6. offers_applied
    """
    
    async def get_eligible_items(self, order: Dict, policy: Dict) -> List[Dict]:
        """Get items eligible for return based on policy"""
        try:
            eligible_items = []
            
            for item in order.get("items", []):
                eligibility = await self._check_item_eligibility(order, item, policy)
                
                if eligibility["eligible"]:
                    eligible_items.append({
                        "line_item_id": item.get("id", str(item.get("variant_id", ""))),
                        "sku": item.get("sku", ""),
                        "title": item.get("title", item.get("name", "")),
                        "variant": item.get("variant_title", ""),
                        "qty_ordered": item.get("quantity", 1),
                        "qty_available": item.get("quantity", 1),  # TODO: Check already returned qty
                        "unit_price": float(item.get("price", 0)),
                        "image_url": item.get("image_url", ""),
                        "product_id": item.get("product_id"),
                        "variant_id": item.get("variant_id"),
                        "eligibility": eligibility
                    })
            
            return eligible_items
            
        except Exception as e:
            logger.error(f"Get eligible items error: {e}")
            return []
    
    async def evaluate_return_request(self, order: Dict, items: List[Dict], 
                                    preferred_outcome: str, return_method: str, 
                                    policy: Dict) -> Dict[str, Any]:
        """
        Evaluate complete return request against policy
        Returns eligibility, fees, refund amount, and explanation
        """
        try:
            result = {
                "eligible": True,
                "fees": [],
                "estimated_refund": 0.0,
                "explanation": {"steps": [], "reason": ""},
                "auto_approve": False
            }
            
            # 1. Window check
            window_result = await self._check_return_window(order, policy)
            result["explanation"]["steps"].append(window_result)
            if not window_result["passed"]:
                result["eligible"] = False
                result["explanation"]["reason"] = window_result["message"]
                return result
            
            # 2. Exclusions check
            exclusions_result = await self._check_exclusions(order, items, policy)
            result["explanation"]["steps"].append(exclusions_result)
            if not exclusions_result["passed"]:
                result["eligible"] = False
                result["explanation"]["reason"] = exclusions_result["message"]
                return result
            
            # 3. Condition requirements
            conditions_result = await self._check_condition_requirements(items, policy)
            result["explanation"]["steps"].append(conditions_result)
            if not conditions_result["passed"]:
                result["eligible"] = False
                result["explanation"]["reason"] = conditions_result["message"]
                return result
            
            # 4. Calculate fees
            fees_result = await self._calculate_fees(order, items, return_method, policy)
            result["fees"] = fees_result["fees"]
            result["estimated_refund"] = fees_result["estimated_refund"]
            result["explanation"]["steps"].append(fees_result)
            
            # 5. Auto-approve check
            auto_approve_result = await self._check_auto_approve(
                order, items, result["estimated_refund"], policy
            )
            result["auto_approve"] = auto_approve_result["approve"]
            result["explanation"]["steps"].append(auto_approve_result)
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluate return request error: {e}")
            return {
                "eligible": False,
                "explanation": {"reason": "Policy evaluation failed"},
                "fees": [],
                "estimated_refund": 0.0,
                "auto_approve": False
            }
    
    async def _check_item_eligibility(self, order: Dict, item: Dict, policy: Dict) -> Dict[str, Any]:
        """Check if individual item is eligible for return"""
        # Basic window check
        order_date = datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
        days_since_order = (datetime.utcnow() - order_date).days
        
        window_days = policy.get("return_window_days", 30)
        
        # Check for overrides
        for override in policy.get("window_overrides", []):
            if override.get("collection") and item.get("product_type") == override["collection"]:
                window_days = override["days"]
                break
            if override.get("tag") and override["tag"] in item.get("tags", []):
                window_days = override["days"]
                break
        
        if days_since_order > window_days:
            return {
                "eligible": False,
                "reason": f"Return window expired ({window_days} days)",
                "days_remaining": 0
            }
        
        # Check exclusions
        excluded_tags = policy.get("excluded", {}).get("tags", [])
        if any(tag in item.get("tags", []) for tag in excluded_tags):
            return {
                "eligible": False,
                "reason": "Item marked as final sale",
                "days_remaining": window_days - days_since_order
            }
        
        return {
            "eligible": True,
            "reason": "Item eligible for return",
            "days_remaining": window_days - days_since_order
        }
    
    async def _check_return_window(self, order: Dict, policy: Dict) -> Dict[str, Any]:
        """Check if return is within allowed window"""
        try:
            order_date = datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
            days_since_order = (datetime.utcnow() - order_date).days
            window_days = policy.get("return_window_days", 30)
            
            passed = days_since_order <= window_days
            
            return {
                "step": "window_check",
                "passed": passed,
                "message": f"Order placed {days_since_order} days ago, window is {window_days} days",
                "days_remaining": max(0, window_days - days_since_order)
            }
            
        except Exception as e:
            logger.error(f"Window check error: {e}")
            return {"step": "window_check", "passed": False, "message": "Invalid order date"}
    
    async def _check_exclusions(self, order: Dict, items: List[Dict], policy: Dict) -> Dict[str, Any]:
        """Check if any items are excluded from returns"""
        excluded_tags = policy.get("excluded", {}).get("tags", [])
        excluded_categories = policy.get("excluded", {}).get("categories", [])
        
        for item in items:
            # Check tags (would need to be in item metadata)
            item_tags = item.get("tags", [])
            if any(tag in excluded_tags for tag in item_tags):
                return {
                    "step": "exclusions", 
                    "passed": False, 
                    "message": f"Item '{item.get('sku', '')}' is marked as final sale"
                }
            
            # Check categories
            if item.get("category") in excluded_categories:
                return {
                    "step": "exclusions",
                    "passed": False,
                    "message": f"Items in category '{item.get('category')}' cannot be returned"
                }
        
        return {
            "step": "exclusions",
            "passed": True,
            "message": "No excluded items found"
        }
    
    async def _check_condition_requirements(self, items: List[Dict], policy: Dict) -> Dict[str, Any]:
        """Check if condition requirements are met (e.g., photos for damaged items)"""
        photo_required_reasons = policy.get("condition_requirements", {}).get("photo_required_reasons", [])
        
        for item in items:
            reason = item.get("reason_code", "").upper()
            if reason in photo_required_reasons:
                photos = item.get("photos", [])
                if not photos or len(photos) == 0:
                    return {
                        "step": "condition_requirements",
                        "passed": False,
                        "message": f"Photos required for {reason.lower()} items"
                    }
        
        return {
            "step": "condition_requirements", 
            "passed": True,
            "message": "All condition requirements met"
        }
    
    async def _calculate_fees(self, order: Dict, items: List[Dict], 
                            return_method: str, policy: Dict) -> Dict[str, Any]:
        """Calculate applicable fees"""
        fees = []
        total_item_value = sum(float(item.get("unit_price", 0)) * item.get("qty", 1) for item in items)
        
        # Restock fee
        restock_config = policy.get("fees", {}).get("restock", {})
        if restock_config.get("enabled", False):
            restock_amount = max(
                total_item_value * (restock_config.get("percent", 0) / 100),
                restock_config.get("min_amount", 0)
            )
            if restock_amount > 0:
                fees.append({
                    "type": "RESTOCK",
                    "amount": restock_amount,
                    "description": f"Restocking fee ({restock_config.get('percent', 0)}%)"
                })
        
        # Shipping fee
        shipping_config = policy.get("fees", {}).get("shipping", {})
        if shipping_config.get("enabled", False):
            method_fees = shipping_config.get("methods", {})
            shipping_amount = method_fees.get(return_method, {}).get("amount", 0)
            if shipping_amount > 0:
                fees.append({
                    "type": "SHIPPING",
                    "amount": shipping_amount,
                    "description": f"Return shipping via {return_method.lower().replace('_', ' ')}"
                })
        
        # Calculate estimated refund
        total_fees = sum(fee["amount"] for fee in fees)
        estimated_refund = max(0, total_item_value - total_fees)
        
        return {
            "step": "fee_calc",
            "passed": True,
            "message": f"Calculated {len(fees)} applicable fees",
            "fees": fees,
            "estimated_refund": estimated_refund,
            "total_item_value": total_item_value
        }
    
    async def _check_auto_approve(self, order: Dict, items: List[Dict], 
                                estimated_refund: float, policy: Dict) -> Dict[str, Any]:
        """Check if return qualifies for auto-approval"""
        auto_config = policy.get("auto_approve", {})
        
        if not auto_config.get("enabled", False):
            return {
                "step": "auto_approve",
                "approve": False,
                "message": "Auto-approval disabled"
            }
        
        # Check value thresholds
        max_total = auto_config.get("max_total", 999999)
        if estimated_refund > max_total:
            return {
                "step": "auto_approve",
                "approve": False,
                "message": f"Refund amount (${estimated_refund:.2f}) exceeds auto-approval limit (${max_total})"
            }
        
        # Check individual item prices
        max_item_price = auto_config.get("max_item_price", 999999)
        for item in items:
            if float(item.get("unit_price", 0)) > max_item_price:
                return {
                    "step": "auto_approve",
                    "approve": False,
                    "message": f"Item price exceeds auto-approval limit (${max_item_price})"
                }
        
        return {
            "step": "auto_approve",
            "approve": True,
            "message": "Qualifies for automatic approval"
        }

# Singleton instance
advanced_rules_engine = AdvancedRulesEngine()