"""
Policy Engine Service
Handles policy evaluation and return processing decisions
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass

from ..config.database import db
from ..utils.date_utils import parse_date, calculate_business_days
from ..utils.fraud_detector import FraudDetector
from ..utils.inventory_checker import InventoryChecker

@dataclass
class PolicyEvaluationResult:
    eligible: bool
    outcome: str  # "approved", "denied", "manual_review"
    resolution_types: List[str]  # ["refund", "exchange", "store_credit", "keep_item"]
    conditions: Dict[str, Any]
    fees: Dict[str, float]
    restrictions: List[str]
    automation_confidence: float
    explanation: str
    next_steps: List[str]

class PolicyEngineService:
    """Comprehensive policy evaluation engine"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.fraud_detector = FraudDetector(tenant_id)
        self.inventory_checker = InventoryChecker(tenant_id)
    
    async def evaluate_policy(
        self, 
        policy: Dict[str, Any], 
        return_data: Dict[str, Any],
        order_data: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]] = None
    ) -> PolicyEvaluationResult:
        """Main policy evaluation method"""
        
        # Step 1: Check basic eligibility
        eligibility_check = self._check_basic_eligibility(policy, return_data, order_data)
        if not eligibility_check.eligible:
            return eligibility_check
        
        # Step 2: Evaluate return window
        window_check = self._check_return_window(policy, return_data, order_data)
        if not window_check.eligible:
            return window_check
        
        # Step 3: Check product eligibility
        product_check = self._check_product_eligibility(policy, return_data, order_data)
        if not product_check.eligible:
            return product_check
        
        # Step 4: Evaluate fraud risk
        fraud_check = await self._check_fraud_risk(policy, return_data, order_data, customer_data)
        
        # Step 5: Determine available outcomes
        outcomes = self._determine_available_outcomes(policy, return_data, order_data)
        
        # Step 6: Calculate fees and adjustments
        fees = self._calculate_fees(policy, return_data, order_data)
        
        # Step 7: Apply workflow automation
        automation_result = self._apply_workflow_automation(
            policy, return_data, order_data, customer_data, fraud_check
        )
        
        # Step 8: Generate final decision
        return PolicyEvaluationResult(
            eligible=True,
            outcome=automation_result.outcome,
            resolution_types=outcomes,
            conditions=automation_result.conditions,
            fees=fees,
            restrictions=automation_result.restrictions,
            automation_confidence=automation_result.confidence,
            explanation=automation_result.explanation,
            next_steps=automation_result.next_steps
        )
    
    def _check_basic_eligibility(
        self, 
        policy: Dict[str, Any], 
        return_data: Dict[str, Any],
        order_data: Dict[str, Any]
    ) -> PolicyEvaluationResult:
        """Check basic return eligibility"""
        
        eligibility = policy.get("product_eligibility", {})
        
        # Check if returns are enabled
        if not eligibility.get("default_returnable", True):
            return PolicyEvaluationResult(
                eligible=False,
                outcome="denied",
                resolution_types=[],
                conditions={},
                fees={},
                restrictions=["returns_not_enabled"],
                automation_confidence=1.0,
                explanation="Returns are not enabled for this store",
                next_steps=["contact_support"]
            )
        
        # Check value restrictions
        value_rules = eligibility.get("value_based_rules", {})
        return_value = return_data.get("total_value", 0)
        
        min_value = value_rules.get("min_return_value", 0)
        if return_value < min_value:
            return PolicyEvaluationResult(
                eligible=False,
                outcome="denied",
                resolution_types=[],
                conditions={},
                fees={},
                restrictions=["below_minimum_value"],
                automation_confidence=1.0,
                explanation=f"Return value ${return_value} is below minimum ${min_value}",
                next_steps=["contact_support"]
            )
        
        max_value = value_rules.get("max_return_value", float('inf'))
        if return_value > max_value:
            return PolicyEvaluationResult(
                eligible=False,
                outcome="manual_review",
                resolution_types=[],
                conditions={"requires_manager_approval": True},
                fees={},
                restrictions=["above_maximum_value"],
                automation_confidence=0.8,
                explanation=f"Return value ${return_value} exceeds maximum ${max_value}",
                next_steps=["manager_approval_required"]
            )
        
        return PolicyEvaluationResult(
            eligible=True,
            outcome="pending",
            resolution_types=[],
            conditions={},
            fees={},
            restrictions=[],
            automation_confidence=1.0,
            explanation="Basic eligibility requirements met",
            next_steps=[]
        )
    
    def _check_return_window(
        self, 
        policy: Dict[str, Any], 
        return_data: Dict[str, Any],
        order_data: Dict[str, Any]
    ) -> PolicyEvaluationResult:
        """Check if return is within allowed time window"""
        
        windows = policy.get("return_windows", {})
        standard_window = windows.get("standard_window", {})
        
        # Handle unlimited returns
        if standard_window.get("type") == "unlimited":
            return PolicyEvaluationResult(
                eligible=True,
                outcome="pending",
                resolution_types=[],
                conditions={},
                fees={},
                restrictions=[],
                automation_confidence=1.0,
                explanation="Unlimited return window",
                next_steps=[]
            )
        
        # Calculate days since relevant date
        calculation_from = standard_window.get("calculation_from", "order_date")
        reference_date = self._get_reference_date(order_data, calculation_from)
        
        if not reference_date:
            return PolicyEvaluationResult(
                eligible=False,
                outcome="manual_review",
                resolution_types=[],
                conditions={"missing_reference_date": True},
                fees={},
                restrictions=["missing_date_info"],
                automation_confidence=0.5,
                explanation=f"Cannot determine {calculation_from}",
                next_steps=["verify_order_dates"]
            )
        
        # Calculate days elapsed
        now = datetime.utcnow()
        if standard_window.get("business_days_only", False):
            days_elapsed = calculate_business_days(reference_date, now)
        else:
            days_elapsed = (now - reference_date).days
        
        # Get allowed window (support multiple options, take first)
        allowed_days_list = standard_window.get("days", [30])
        allowed_days = allowed_days_list[0] if allowed_days_list else 30
        
        # Check extensions
        allowed_days = self._calculate_extended_window(
            windows, order_data, return_data, allowed_days
        )
        
        if days_elapsed > allowed_days:
            return PolicyEvaluationResult(
                eligible=False,
                outcome="denied",
                resolution_types=[],
                conditions={},
                fees={},
                restrictions=["outside_return_window"],
                automation_confidence=1.0,
                explanation=f"Return window expired ({days_elapsed} days > {allowed_days} days allowed)",
                next_steps=["contact_support_for_exception"]
            )
        
        return PolicyEvaluationResult(
            eligible=True,
            outcome="pending",
            resolution_types=[],
            conditions={},
            fees={},
            restrictions=[],
            automation_confidence=1.0,
            explanation=f"Within return window ({days_elapsed}/{allowed_days} days)",
            next_steps=[]
        )
    
    def _check_product_eligibility(
        self, 
        policy: Dict[str, Any], 
        return_data: Dict[str, Any],
        order_data: Dict[str, Any]
    ) -> PolicyEvaluationResult:
        """Check product-specific eligibility rules"""
        
        eligibility = policy.get("product_eligibility", {})
        
        # Check category exclusions
        exclusions = eligibility.get("category_exclusions", {})
        excluded_categories = exclusions.get("excluded_categories", [])
        
        # Get product categories from return items
        return_items = return_data.get("items", [])
        for item in return_items:
            product_category = item.get("category", "")
            if product_category in excluded_categories:
                return PolicyEvaluationResult(
                    eligible=False,
                    outcome="denied",
                    resolution_types=[],
                    conditions={},
                    fees={},
                    restrictions=["excluded_category"],
                    automation_confidence=1.0,
                    explanation=f"Product category '{product_category}' is not returnable",
                    next_steps=["contact_support"]
                )
        
        # Check tag-based rules
        tag_rules = eligibility.get("tag_based_rules", {})
        final_sale_tags = tag_rules.get("final_sale_tags", [])
        non_returnable_tags = tag_rules.get("non_returnable_tags", [])
        
        for item in return_items:
            item_tags = item.get("tags", [])
            
            # Check final sale tags
            if any(tag in item_tags for tag in final_sale_tags):
                return PolicyEvaluationResult(
                    eligible=False,
                    outcome="denied",
                    resolution_types=[],
                    conditions={},
                    fees={},
                    restrictions=["final_sale_item"],
                    automation_confidence=1.0,
                    explanation="Item marked as final sale",
                    next_steps=["no_returns_allowed"]
                )
            
            # Check non-returnable tags
            if any(tag in item_tags for tag in non_returnable_tags):
                return PolicyEvaluationResult(
                    eligible=False,
                    outcome="denied",
                    resolution_types=[],
                    conditions={},
                    fees={},
                    restrictions=["non_returnable_item"],
                    automation_confidence=1.0,
                    explanation="Item is not eligible for return",
                    next_steps=["no_returns_allowed"]
                )
        
        # Check condition requirements
        condition_reqs = eligibility.get("condition_requirements", {})
        conditions_check = self._validate_condition_requirements(
            condition_reqs, return_data
        )
        
        if not conditions_check["valid"]:
            return PolicyEvaluationResult(
                eligible=False,
                outcome="denied",
                resolution_types=[],
                conditions={},
                fees={},
                restrictions=conditions_check["failed_requirements"],
                automation_confidence=0.9,
                explanation="Item condition requirements not met",
                next_steps=["verify_item_condition"]
            )
        
        return PolicyEvaluationResult(
            eligible=True,
            outcome="pending",
            resolution_types=[],
            conditions={},
            fees={},
            restrictions=[],
            automation_confidence=1.0,
            explanation="Product eligibility requirements met",
            next_steps=[]
        )
    
    async def _check_fraud_risk(
        self, 
        policy: Dict[str, Any], 
        return_data: Dict[str, Any],
        order_data: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check fraud risk and apply detection rules"""
        
        fraud_config = policy.get("fraud_detection", {})
        
        if not fraud_config.get("ai_models", {}).get("enabled", False):
            return {
                "risk_score": 0,
                "risk_level": "low",
                "triggers": [],
                "action": "auto_approve"
            }
        
        # Calculate fraud risk score
        risk_score = await self.fraud_detector.calculate_risk_score(
            return_data, order_data, customer_data
        )
        
        # Determine risk level
        risk_scoring = fraud_config.get("ai_models", {}).get("risk_scoring", {})
        if risk_score <= int(risk_scoring.get("low_risk", "30").split("-")[1]):
            risk_level = "low"
        elif risk_score <= int(risk_scoring.get("medium_risk", "70").split("-")[1]):
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Get fraud actions
        fraud_actions = fraud_config.get("fraud_actions", {})
        action = fraud_actions.get(f"{risk_level}_risk", "manual_review")
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "triggers": self.fraud_detector.get_triggered_rules(),
            "action": action
        }
    
    def _determine_available_outcomes(
        self, 
        policy: Dict[str, Any], 
        return_data: Dict[str, Any],
        order_data: Dict[str, Any]
    ) -> List[str]:
        """Determine which resolution types are available"""
        
        outcomes = []
        
        # Check refund availability
        refund_settings = policy.get("refund_settings", {})
        if refund_settings.get("enabled", True):
            outcomes.append("refund")
        
        # Check exchange availability
        exchange_settings = policy.get("exchange_settings", {})
        if exchange_settings.get("enabled", True):
            # Verify inventory availability for exchanges
            if self._check_exchange_inventory(return_data, order_data):
                outcomes.append("exchange")
        
        # Check store credit availability
        store_credit = policy.get("store_credit_settings", {})
        if store_credit.get("enabled", True):
            outcomes.append("store_credit")
        
        # Check keep item availability
        keep_item = policy.get("keep_item_settings", {})
        if keep_item.get("enabled", False):
            triggers = keep_item.get("triggers", {})
            if self._check_keep_item_triggers(triggers, return_data, order_data):
                outcomes.append("keep_item")
        
        # Check shop now availability
        shop_now = policy.get("shop_now_settings", {})
        if shop_now.get("enabled", False):
            outcomes.append("shop_now")
        
        return outcomes
    
    def _calculate_fees(
        self, 
        policy: Dict[str, Any], 
        return_data: Dict[str, Any],
        order_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate applicable fees"""
        
        fees = {}
        
        # Restocking fee
        refund_settings = policy.get("refund_settings", {})
        fee_config = refund_settings.get("fees", {}).get("restocking_fee", {})
        
        if fee_config.get("enabled", False):
            if fee_config.get("type") == "percentage":
                return_value = return_data.get("total_value", 0)
                percentage = fee_config.get("percentage_amount", 0)
                fees["restocking"] = return_value * (percentage / 100)
            else:
                fees["restocking"] = fee_config.get("amount", 0)
        
        # Processing fee
        processing_fee = refund_settings.get("fees", {}).get("processing_fee", {})
        if processing_fee.get("enabled", False):
            fees["processing"] = processing_fee.get("amount", 0)
        
        # Return shipping fee
        shipping_fee = refund_settings.get("fees", {}).get("return_shipping_deduction", {})
        if shipping_fee.get("enabled", False):
            if shipping_fee.get("amount") == "actual_cost":
                fees["return_shipping"] = return_data.get("shipping_cost", 0)
            else:
                fees["return_shipping"] = shipping_fee.get("flat_rate_amount", 0)
        
        return fees
    
    def _apply_workflow_automation(
        self, 
        policy: Dict[str, Any], 
        return_data: Dict[str, Any],
        order_data: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]],
        fraud_check: Dict[str, Any]
    ) -> 'AutomationResult':
        """Apply workflow automation rules"""
        
        # Start with fraud check result
        if fraud_check["action"] == "auto_reject":
            return AutomationResult(
                outcome="denied",
                conditions={"fraud_detected": True},
                restrictions=["high_fraud_risk"],
                confidence=0.9,
                explanation="Automatically denied due to fraud risk",
                next_steps=["fraud_review_required"]
            )
        
        if fraud_check["action"] == "manual_review":
            return AutomationResult(
                outcome="manual_review",
                conditions={"fraud_review": True},
                restrictions=["requires_review"],
                confidence=0.7,
                explanation="Requires manual review due to fraud concerns",
                next_steps=["fraud_team_review"]
            )
        
        # Check workflow conditions
        workflow = policy.get("workflow_conditions", {})
        
        # Customer attributes automation
        if self._should_auto_approve_customer(workflow, customer_data, order_data):
            return AutomationResult(
                outcome="approved",
                conditions={"vip_customer": True},
                restrictions=[],
                confidence=0.9,
                explanation="Auto-approved for VIP customer",
                next_steps=["process_immediately"]
            )
        
        # Default to manual review for complex cases
        return AutomationResult(
            outcome="manual_review",
            conditions={},
            restrictions=[],
            confidence=0.6,
            explanation="Requires manual review",
            next_steps=["assign_to_team"]
        )
    
    def _get_reference_date(self, order_data: Dict[str, Any], calculation_from: str) -> Optional[datetime]:
        """Get reference date for return window calculation"""
        
        date_field_map = {
            "order_date": "created_at",
            "fulfillment_date": "fulfilled_at",
            "delivery_date": "delivered_at",
            "first_delivery_attempt": "first_delivery_attempt_at"
        }
        
        field_name = date_field_map.get(calculation_from, "created_at")
        date_value = order_data.get(field_name)
        
        if date_value:
            return parse_date(date_value)
        
        return None
    
    def _calculate_extended_window(
        self,
        windows: Dict[str, Any],
        order_data: Dict[str, Any],
        return_data: Dict[str, Any],
        base_days: int
    ) -> int:
        """Calculate extended return window based on various factors"""
        
        extended_days = base_days
        extended_windows = windows.get("extended_windows", {})
        
        # Holiday extension
        holiday_ext = extended_windows.get("holiday_extension", {})
        if holiday_ext.get("enabled", False):
            order_date = parse_date(order_data.get("created_at"))
            if order_date and self._is_holiday_period(order_date, holiday_ext.get("applicable_months", [])):
                extended_days += holiday_ext.get("extra_days", 0)
        
        # Loyalty member extension
        loyalty_ext = extended_windows.get("loyalty_member_extension", {})
        if loyalty_ext.get("enabled", False):
            customer_tier = return_data.get("customer_tier", "")
            tier_days = loyalty_ext.get(f"{customer_tier}_extra_days", 0)
            extended_days += tier_days
        
        return extended_days
    
    def _validate_condition_requirements(
        self, 
        requirements: Dict[str, Any], 
        return_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate item condition requirements"""
        
        failed_requirements = []
        
        if requirements.get("original_packaging_required") and not return_data.get("has_original_packaging"):
            failed_requirements.append("original_packaging_missing")
        
        if requirements.get("tags_attached_required") and not return_data.get("tags_attached"):
            failed_requirements.append("tags_removed")
        
        if requirements.get("unworn_unused_only") and return_data.get("condition") != "new":
            failed_requirements.append("item_used")
        
        return {
            "valid": len(failed_requirements) == 0,
            "failed_requirements": failed_requirements
        }
    
    def _check_exchange_inventory(self, return_data: Dict[str, Any], order_data: Dict[str, Any]) -> bool:
        """Check if exchange items are available in inventory"""
        return self.inventory_checker.check_availability(return_data.get("items", []))
    
    def _check_keep_item_triggers(
        self, 
        triggers: Dict[str, Any], 
        return_data: Dict[str, Any], 
        order_data: Dict[str, Any]
    ) -> bool:
        """Check if keep item triggers are met"""
        
        if triggers.get("low_value_threshold", 0) > 0:
            if return_data.get("total_value", 0) <= triggers["low_value_threshold"]:
                return True
        
        if triggers.get("damage_reported") and return_data.get("reason") == "damaged":
            return True
        
        if triggers.get("wrong_item_sent") and return_data.get("reason") == "wrong_item":
            return True
        
        return False
    
    def _should_auto_approve_customer(
        self,
        workflow: Dict[str, Any], 
        customer_data: Optional[Dict[str, Any]],
        order_data: Dict[str, Any]
    ) -> bool:
        """Check if customer should be auto-approved"""
        
        if not customer_data:
            return False
        
        # VIP customers
        if "vip" in customer_data.get("tags", []):
            return True
        
        # High lifetime value customers
        if customer_data.get("lifetime_value", 0) > 1000:
            return True
        
        # Low return history customers
        if customer_data.get("return_count", 0) < 2:
            return True
        
        return False
    
    def _is_holiday_period(self, date: datetime, applicable_months: List[str]) -> bool:
        """Check if date falls in holiday period"""
        month_names = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }
        
        month_numbers = [month_names.get(month, 0) for month in applicable_months]
        return date.month in month_numbers

@dataclass
class AutomationResult:
    outcome: str
    conditions: Dict[str, Any]
    restrictions: List[str]
    confidence: float
    explanation: str
    next_steps: List[str]