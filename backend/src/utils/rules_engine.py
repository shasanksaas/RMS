"""
Enhanced rules engine with simulation and step-by-step explanation
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from .state_machine import ReturnStatus

@dataclass
class RuleStep:
    """Represents a single step in rule evaluation"""
    rule_name: str
    condition: str
    condition_met: bool
    action_taken: Optional[str] = None
    explanation: str = ""
    
class RulesEngine:
    """Enhanced rules engine with detailed explanation"""
    
    @staticmethod
    def simulate_rules_application(return_request: Dict, order: Dict, rules: List[Dict]) -> Dict[str, Any]:
        """Simulate rule application and return step-by-step explanation"""
        steps = []
        final_status = ReturnStatus.REQUESTED
        final_notes = ""
        rule_applied = None
        
        for rule_data in rules:
            rule = rule_data  # Assume it's already a dict
            rule_steps = RulesEngine._evaluate_rule_with_steps(rule, return_request, order)
            steps.extend(rule_steps)
            
            # Check if this rule resulted in a status change
            if any(step.action_taken for step in rule_steps):
                final_status, final_notes = RulesEngine._apply_rule_actions(rule, return_request, order)
                rule_applied = rule['name']
                break
        
        return {
            "steps": [
                {
                    "rule_name": step.rule_name,
                    "condition": step.condition,
                    "condition_met": step.condition_met,
                    "action_taken": step.action_taken,
                    "explanation": step.explanation
                }
                for step in steps
            ],
            "final_status": final_status.value if isinstance(final_status, ReturnStatus) else final_status,
            "final_notes": final_notes,
            "rule_applied": rule_applied,
            "total_rules_evaluated": len(rules),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _evaluate_rule_with_steps(rule: Dict, return_request: Dict, order: Dict) -> List[RuleStep]:
        """Evaluate a single rule and return detailed steps"""
        steps = []
        conditions = rule.get('conditions', {})
        
        # Check return window
        if 'max_days_since_order' in conditions:
            order_date_str = order['order_date']
            if isinstance(order_date_str, str):
                # Handle ISO format string
                order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00'))
            else:
                # Handle datetime object
                order_date = order_date_str
            
            days_since_order = (datetime.utcnow() - order_date).days
            max_days = conditions['max_days_since_order']
            condition_met = days_since_order <= max_days
            
            step = RuleStep(
                rule_name=rule['name'],
                condition=f"Return within {max_days} days",
                condition_met=condition_met,
                explanation=f"Order placed {days_since_order} days ago. {'Within' if condition_met else 'Exceeds'} {max_days} day window."
            )
            
            if not condition_met:
                step.action_taken = "Deny return - outside return window"
            
            steps.append(step)
            
            if not condition_met:
                return steps  # Stop evaluation if condition fails
        
        # Check auto-approve reasons
        if 'auto_approve_reasons' in conditions:
            auto_reasons = conditions['auto_approve_reasons']
            return_reason = return_request.get('reason', '')
            condition_met = return_reason in auto_reasons
            
            step = RuleStep(
                rule_name=rule['name'],
                condition=f"Return reason in auto-approve list: {auto_reasons}",
                condition_met=condition_met,
                explanation=f"Return reason '{return_reason}' {'is' if condition_met else 'is not'} in auto-approve list."
            )
            
            if condition_met:
                step.action_taken = "Auto-approve return"
            
            steps.append(step)
        
        # Check manual review reasons
        if 'require_manual_review_reasons' in conditions:
            manual_reasons = conditions['require_manual_review_reasons']
            return_reason = return_request.get('reason', '')
            condition_met = return_reason in manual_reasons
            
            step = RuleStep(
                rule_name=rule['name'],
                condition=f"Return reason requires manual review: {manual_reasons}",
                condition_met=condition_met,
                explanation=f"Return reason '{return_reason}' {'requires' if condition_met else 'does not require'} manual review."
            )
            
            if condition_met:
                step.action_taken = "Route to manual review"
            
            steps.append(step)
        
        # Check value thresholds
        if 'min_return_value' in conditions:
            min_value = conditions['min_return_value']
            return_value = return_request.get('refund_amount', 0)
            condition_met = return_value >= min_value
            
            step = RuleStep(
                rule_name=rule['name'],
                condition=f"Return value >= ${min_value}",
                condition_met=condition_met,
                explanation=f"Return value ${return_value} {'meets' if condition_met else 'below'} minimum threshold of ${min_value}."
            )
            
            if not condition_met:
                step.action_taken = "Deny return - below minimum value"
            
            steps.append(step)
        
        return steps
    
    @staticmethod
    def _apply_rule_actions(rule: Dict, return_request: Dict, order: Dict) -> Tuple[ReturnStatus, str]:
        """Apply rule actions and return final status and notes"""
        conditions = rule.get('conditions', {})
        actions = rule.get('actions', {})
        
        # Check return window first (highest priority)
        if 'max_days_since_order' in conditions:
            days_since_order = (datetime.utcnow() - datetime.fromisoformat(order['order_date'].replace('Z', '+00:00'))).days
            if days_since_order > conditions['max_days_since_order']:
                return ReturnStatus.DENIED, f"Return window expired ({days_since_order} days > {conditions['max_days_since_order']} days)"
        
        # Check value threshold
        if 'min_return_value' in conditions:
            return_value = return_request.get('refund_amount', 0)
            if return_value < conditions['min_return_value']:
                return ReturnStatus.DENIED, f"Return value ${return_value} below minimum ${conditions['min_return_value']}"
        
        # Check auto-approve reasons
        if 'auto_approve_reasons' in conditions:
            if return_request.get('reason', '') in conditions['auto_approve_reasons']:
                if actions.get('auto_approve'):
                    return ReturnStatus.APPROVED, "Auto-approved based on return reason"
        
        # Check manual review reasons  
        if 'require_manual_review_reasons' in conditions:
            if return_request.get('reason', '') in conditions['require_manual_review_reasons']:
                return ReturnStatus.REQUESTED, "Requires manual review"
        
        return ReturnStatus.REQUESTED, "No rules applied - default status"