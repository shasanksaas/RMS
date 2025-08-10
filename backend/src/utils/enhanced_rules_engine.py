"""
Enhanced Rules Engine with Complex Conditional Logic
Support for AND/OR operations, advanced conditions, and real-time execution
"""
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re
import json
from .state_machine import ReturnStatus

class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"

class LogicOperator(str, Enum):
    AND = "and"
    OR = "or"

class FieldType(str, Enum):
    ORDER_AMOUNT = "order_amount"
    PRODUCT_CATEGORY = "product_category"
    SKU_ITEM_NAME = "sku_item_name"
    CUSTOMER_LOCATION = "customer_location"
    PAYMENT_METHOD = "payment_method"
    ORDER_TAG = "order_tag"
    ORDER_STATUS = "order_status"
    RETURN_REASON = "return_reason"
    DAYS_SINCE_ORDER = "days_since_order" 
    CUSTOM_FIELD = "custom_field"

class ActionType(str, Enum):
    AUTO_APPROVE_RETURN = "auto_approve_return"
    AUTO_DECLINE_RETURN = "auto_decline_return"
    SEND_EMAIL_NOTIFICATION = "send_email_notification"
    ADD_ORDER_TAG = "add_order_tag"
    ASSIGN_TEAM_MEMBER = "assign_team_member"
    CHANGE_RETURN_STATUS = "change_return_status"
    REQUIRE_MANUAL_REVIEW = "require_manual_review"
    GENERATE_RETURN_LABEL = "generate_return_label"

@dataclass
class RuleCondition:
    """Single condition in a rule"""
    field: FieldType
    operator: ConditionOperator
    value: Union[str, int, float, List[str]]
    custom_field_name: Optional[str] = None

@dataclass
class RuleConditionGroup:
    """Group of conditions with logic operator"""
    conditions: List[RuleCondition]
    logic_operator: LogicOperator = LogicOperator.AND

@dataclass
class RuleAction:
    """Single action to perform"""
    action_type: ActionType
    parameters: Dict[str, Any]

@dataclass
class RuleEvaluationStep:
    """Step in rule evaluation process"""
    rule_name: str
    condition_group_index: int
    condition_index: int
    field: str
    operator: str
    expected_value: Any
    actual_value: Any
    condition_met: bool
    explanation: str
    timestamp: datetime

@dataclass
class RuleEvaluationResult:
    """Complete rule evaluation result"""
    rule_id: str
    rule_name: str
    rule_matched: bool
    steps: List[RuleEvaluationStep]
    actions_to_execute: List[RuleAction]
    final_status: str
    final_notes: str
    execution_time_ms: float

class EnhancedRulesEngine:
    """Advanced rules engine with complex conditional logic"""
    
    @staticmethod
    def evaluate_rule(rule: Dict[str, Any], return_request: Dict, order: Dict) -> RuleEvaluationResult:
        """Evaluate a single rule and return detailed result"""
        start_time = datetime.utcnow()
        
        rule_id = rule.get("id", "unknown")
        rule_name = rule.get("name", "Unnamed Rule")
        steps = []
        actions_to_execute = []
        rule_matched = False
        final_status = "requested"
        final_notes = ""
        
        try:
            # Parse rule conditions
            condition_groups = EnhancedRulesEngine._parse_conditions(rule.get("conditions", {}))
            
            # Evaluate all condition groups (AND logic between groups)
            all_groups_matched = True
            
            for group_index, condition_group in enumerate(condition_groups):
                group_matched = EnhancedRulesEngine._evaluate_condition_group(
                    condition_group, return_request, order, rule_name, group_index, steps
                )
                
                if not group_matched:
                    all_groups_matched = False
                    break
            
            rule_matched = all_groups_matched
            
            # If rule matched, prepare actions
            if rule_matched:
                actions_data = rule.get("actions", {})
                actions_to_execute = EnhancedRulesEngine._parse_actions(actions_data)
                final_status, final_notes = EnhancedRulesEngine._determine_final_status(actions_to_execute)
        
        except Exception as e:
            # Add error step
            error_step = RuleEvaluationStep(
                rule_name=rule_name,
                condition_group_index=-1,
                condition_index=-1,
                field="error",
                operator="evaluation",
                expected_value="success",
                actual_value=f"error: {str(e)}",
                condition_met=False,
                explanation=f"Rule evaluation failed: {str(e)}",
                timestamp=datetime.utcnow()
            )
            steps.append(error_step)
        
        end_time = datetime.utcnow()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return RuleEvaluationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            rule_matched=rule_matched,
            steps=steps,
            actions_to_execute=actions_to_execute,
            final_status=final_status,
            final_notes=final_notes,
            execution_time_ms=execution_time_ms
        )
    
    @staticmethod
    def evaluate_all_rules(rules: List[Dict], return_request: Dict, order: Dict) -> Dict[str, Any]:
        """Evaluate all rules and return comprehensive result"""
        start_time = datetime.utcnow()
        
        results = []
        matched_rules = []
        final_status = "requested"
        final_notes = ""
        actions_to_execute = []
        
        # Sort rules by priority
        sorted_rules = sorted(rules, key=lambda r: r.get("priority", 999))
        
        for rule in sorted_rules:
            if not rule.get("is_active", True):
                continue
                
            result = EnhancedRulesEngine.evaluate_rule(rule, return_request, order)
            results.append(result)
            
            if result.rule_matched:
                matched_rules.append(result)
                # Use first matched rule's outcome
                if not actions_to_execute:
                    actions_to_execute = result.actions_to_execute
                    final_status = result.final_status
                    final_notes = result.final_notes
        
        end_time = datetime.utcnow()
        total_execution_time = (end_time - start_time).total_seconds() * 1000
        
        return {
            "evaluation_timestamp": start_time.isoformat(),
            "total_rules_evaluated": len(rules),
            "active_rules_evaluated": len([r for r in rules if r.get("is_active", True)]),
            "rules_matched": len(matched_rules),
            "matched_rule_names": [r.rule_name for r in matched_rules],
            "final_status": final_status,
            "final_notes": final_notes,
            "actions_to_execute": [
                {
                    "action_type": action.action_type.value,
                    "parameters": action.parameters
                }
                for action in actions_to_execute
            ],
            "detailed_results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "rule_matched": r.rule_matched,
                    "execution_time_ms": r.execution_time_ms,
                    "steps": [
                        {
                            "field": step.field,
                            "operator": step.operator,
                            "expected_value": step.expected_value,
                            "actual_value": step.actual_value,
                            "condition_met": step.condition_met,
                            "explanation": step.explanation
                        }
                        for step in r.steps
                    ]
                }
                for r in results
            ],
            "total_execution_time_ms": total_execution_time
        }
    
    @staticmethod
    def _parse_conditions(conditions_data: Dict) -> List[RuleConditionGroup]:
        """Parse conditions from rule data"""
        condition_groups = []
        
        # Handle legacy format
        if "auto_approve_reasons" in conditions_data:
            # Convert legacy format to new format
            conditions = []
            
            if "auto_approve_reasons" in conditions_data:
                conditions.append(RuleCondition(
                    field=FieldType.RETURN_REASON,
                    operator=ConditionOperator.IN,
                    value=conditions_data["auto_approve_reasons"]
                ))
            
            if "max_days_since_order" in conditions_data:
                conditions.append(RuleCondition(
                    field=FieldType.DAYS_SINCE_ORDER,
                    operator=ConditionOperator.LESS_EQUAL,
                    value=conditions_data["max_days_since_order"]
                ))
            
            if "min_return_value" in conditions_data:
                conditions.append(RuleCondition(
                    field=FieldType.ORDER_AMOUNT,
                    operator=ConditionOperator.GREATER_EQUAL,
                    value=conditions_data["min_return_value"]
                ))
            
            condition_groups.append(RuleConditionGroup(
                conditions=conditions,
                logic_operator=LogicOperator.AND
            ))
        
        # Handle new format
        elif "condition_groups" in conditions_data:
            for group_data in conditions_data["condition_groups"]:
                conditions = []
                for cond_data in group_data.get("conditions", []):
                    conditions.append(RuleCondition(
                        field=FieldType(cond_data["field"]),
                        operator=ConditionOperator(cond_data["operator"]),
                        value=cond_data["value"],
                        custom_field_name=cond_data.get("custom_field_name")
                    ))
                
                condition_groups.append(RuleConditionGroup(
                    conditions=conditions,
                    logic_operator=LogicOperator(group_data.get("logic_operator", "and"))
                ))
        
        return condition_groups
    
    @staticmethod
    def _evaluate_condition_group(
        condition_group: RuleConditionGroup,
        return_request: Dict,
        order: Dict,
        rule_name: str,
        group_index: int,
        steps: List[RuleEvaluationStep]
    ) -> bool:
        """Evaluate a group of conditions"""
        condition_results = []
        
        for cond_index, condition in enumerate(condition_group.conditions):
            result = EnhancedRulesEngine._evaluate_single_condition(
                condition, return_request, order, rule_name, group_index, cond_index, steps
            )
            condition_results.append(result)
        
        # Apply logic operator
        if condition_group.logic_operator == LogicOperator.AND:
            return all(condition_results)
        else:  # OR
            return any(condition_results)
    
    @staticmethod
    def _evaluate_single_condition(
        condition: RuleCondition,
        return_request: Dict,
        order: Dict,
        rule_name: str,
        group_index: int,
        cond_index: int,
        steps: List[RuleEvaluationStep]
    ) -> bool:
        """Evaluate a single condition"""
        
        # Extract actual value based on field type
        actual_value = EnhancedRulesEngine._extract_field_value(
            condition.field, return_request, order, condition.custom_field_name
        )
        
        # Perform comparison
        condition_met = EnhancedRulesEngine._compare_values(
            actual_value, condition.operator, condition.value
        )
        
        # Create explanation
        explanation = EnhancedRulesEngine._create_explanation(
            condition.field, condition.operator, condition.value, actual_value, condition_met
        )
        
        # Add step
        step = RuleEvaluationStep(
            rule_name=rule_name,
            condition_group_index=group_index,
            condition_index=cond_index,
            field=condition.field.value,
            operator=condition.operator.value,
            expected_value=condition.value,
            actual_value=actual_value,
            condition_met=condition_met,
            explanation=explanation,
            timestamp=datetime.utcnow()
        )
        steps.append(step)
        
        return condition_met
    
    @staticmethod
    def _extract_field_value(
        field: FieldType,
        return_request: Dict,
        order: Dict,
        custom_field_name: Optional[str] = None
    ) -> Any:
        """Extract field value from return request or order"""
        
        if field == FieldType.ORDER_AMOUNT:
            return float(order.get("total_amount", 0))
        
        elif field == FieldType.PRODUCT_CATEGORY:
            # Extract categories from order items
            categories = []
            for item in order.get("items", []):
                if "category" in item:
                    categories.append(item["category"])
            return categories
        
        elif field == FieldType.SKU_ITEM_NAME:
            # Extract SKUs and names from return items
            skus_names = []
            for item in return_request.get("items_to_return", []):
                skus_names.append(item.get("sku", ""))
                skus_names.append(item.get("product_name", ""))
            return skus_names
        
        elif field == FieldType.CUSTOMER_LOCATION:
            billing_address = order.get("billing_address", {})
            return {
                "country": billing_address.get("country", ""),
                "state": billing_address.get("province", ""),
                "city": billing_address.get("city", ""),
                "zip": billing_address.get("zip", "")
            }
        
        elif field == FieldType.PAYMENT_METHOD:
            return order.get("payment_method", "unknown")
        
        elif field == FieldType.ORDER_TAG:
            return order.get("tags", [])
        
        elif field == FieldType.ORDER_STATUS:
            return {
                "financial_status": order.get("financial_status", "unknown"),
                "fulfillment_status": order.get("fulfillment_status", "unknown")
            }
        
        elif field == FieldType.RETURN_REASON:
            return return_request.get("reason", "")
        
        elif field == FieldType.DAYS_SINCE_ORDER:
            order_date_str = order.get("order_date", order.get("created_at"))
            if isinstance(order_date_str, str):
                order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00'))
            else:
                order_date = order_date_str
            return (datetime.utcnow() - order_date).days
        
        elif field == FieldType.CUSTOM_FIELD:
            if custom_field_name:
                return order.get(custom_field_name) or return_request.get(custom_field_name)
            return None
        
        return None
    
    @staticmethod
    def _compare_values(actual_value: Any, operator: ConditionOperator, expected_value: Any) -> bool:
        """Compare actual value with expected value using operator"""
        
        try:
            if operator == ConditionOperator.EQUALS:
                return actual_value == expected_value
            
            elif operator == ConditionOperator.NOT_EQUALS:
                return actual_value != expected_value
            
            elif operator == ConditionOperator.GREATER_THAN:
                return float(actual_value) > float(expected_value)
            
            elif operator == ConditionOperator.LESS_THAN:
                return float(actual_value) < float(expected_value)
            
            elif operator == ConditionOperator.GREATER_EQUAL:
                return float(actual_value) >= float(expected_value)
            
            elif operator == ConditionOperator.LESS_EQUAL:
                return float(actual_value) <= float(expected_value)
            
            elif operator == ConditionOperator.CONTAINS:
                if isinstance(actual_value, list):
                    return any(str(expected_value).lower() in str(item).lower() for item in actual_value)
                return str(expected_value).lower() in str(actual_value).lower()
            
            elif operator == ConditionOperator.NOT_CONTAINS:
                if isinstance(actual_value, list):
                    return not any(str(expected_value).lower() in str(item).lower() for item in actual_value)
                return str(expected_value).lower() not in str(actual_value).lower()
            
            elif operator == ConditionOperator.IN:
                if isinstance(expected_value, list):
                    return actual_value in expected_value
                return str(actual_value) == str(expected_value)
            
            elif operator == ConditionOperator.NOT_IN:
                if isinstance(expected_value, list):
                    return actual_value not in expected_value
                return str(actual_value) != str(expected_value)
            
            elif operator == ConditionOperator.REGEX:
                pattern = re.compile(str(expected_value), re.IGNORECASE)
                return bool(pattern.search(str(actual_value)))
        
        except (ValueError, TypeError):
            return False
        
        return False
    
    @staticmethod
    def _create_explanation(
        field: FieldType,
        operator: ConditionOperator,
        expected_value: Any,
        actual_value: Any,
        condition_met: bool
    ) -> str:
        """Create human-readable explanation of condition evaluation"""
        
        field_name = field.value.replace("_", " ").title()
        op_text = {
            ConditionOperator.EQUALS: "equals",
            ConditionOperator.NOT_EQUALS: "does not equal",
            ConditionOperator.GREATER_THAN: "is greater than",
            ConditionOperator.LESS_THAN: "is less than",
            ConditionOperator.GREATER_EQUAL: "is greater than or equal to",
            ConditionOperator.LESS_EQUAL: "is less than or equal to",
            ConditionOperator.CONTAINS: "contains",
            ConditionOperator.NOT_CONTAINS: "does not contain",
            ConditionOperator.IN: "is in",
            ConditionOperator.NOT_IN: "is not in",
            ConditionOperator.REGEX: "matches pattern"
        }.get(operator, str(operator))
        
        result_text = "✓ PASS" if condition_met else "✗ FAIL"
        
        return f"{field_name} ({actual_value}) {op_text} {expected_value} → {result_text}"
    
    @staticmethod
    def _parse_actions(actions_data: Dict) -> List[RuleAction]:
        """Parse actions from rule data"""
        actions = []
        
        # Handle legacy format
        if "auto_approve" in actions_data and actions_data["auto_approve"]:
            actions.append(RuleAction(
                action_type=ActionType.AUTO_APPROVE_RETURN,
                parameters={}
            ))
        
        if "manual_review" in actions_data and actions_data["manual_review"]:
            actions.append(RuleAction(
                action_type=ActionType.REQUIRE_MANUAL_REVIEW,
                parameters={}
            ))
        
        if "generate_label" in actions_data and actions_data["generate_label"]:
            actions.append(RuleAction(
                action_type=ActionType.GENERATE_RETURN_LABEL,
                parameters={}
            ))
        
        # Handle new format
        if "actions_list" in actions_data:
            for action_data in actions_data["actions_list"]:
                actions.append(RuleAction(
                    action_type=ActionType(action_data["action_type"]),
                    parameters=action_data.get("parameters", {})
                ))
        
        return actions
    
    @staticmethod
    def _determine_final_status(actions: List[RuleAction]) -> Tuple[str, str]:
        """Determine final status based on actions"""
        
        for action in actions:
            if action.action_type == ActionType.AUTO_APPROVE_RETURN:
                return "approved", "Auto-approved by rules engine"
            elif action.action_type == ActionType.AUTO_DECLINE_RETURN:
                return "denied", "Auto-declined by rules engine"
            elif action.action_type == ActionType.REQUIRE_MANUAL_REVIEW:
                return "requested", "Requires manual review"
        
        return "requested", "No status-changing actions matched"