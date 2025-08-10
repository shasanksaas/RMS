"""
Rules Management Controller
Handles CRUD operations and advanced rule management
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..utils.enhanced_rules_engine import EnhancedRulesEngine, FieldType, ConditionOperator, ActionType
from ..middleware.security import get_current_tenant_id
from ..config.database import db

router = APIRouter(prefix="/rules", tags=["Rules Management"])

# Enhanced Models
class RuleConditionModel(BaseModel):
    field: FieldType
    operator: ConditionOperator
    value: Any
    custom_field_name: Optional[str] = None

class RuleConditionGroupModel(BaseModel):
    conditions: List[RuleConditionModel]
    logic_operator: str = "and"  # "and" or "or"

class RuleActionModel(BaseModel):
    action_type: ActionType
    parameters: Dict[str, Any] = Field(default_factory=dict)

class EnhancedReturnRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: str
    condition_groups: List[RuleConditionGroupModel]
    actions: List[RuleActionModel]
    priority: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class RuleCreateRequest(BaseModel):
    name: str
    description: str
    condition_groups: List[RuleConditionGroupModel]
    actions: List[RuleActionModel]
    priority: int = 1
    is_active: bool = True
    tags: List[str] = Field(default_factory=list)

class RuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    condition_groups: Optional[List[RuleConditionGroupModel]] = None
    actions: Optional[List[RuleActionModel]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None

class RuleSimulationRequest(BaseModel):
    order_data: Dict[str, Any]
    return_data: Dict[str, Any]
    rule_ids: Optional[List[str]] = None  # Test specific rules only

class RuleTestRequest(BaseModel):
    conditions: List[RuleConditionGroupModel]
    test_data: Dict[str, Any]

# Routes
@router.get("/", response_model=Dict[str, Any])
async def get_rules(
    tenant_id: str = Depends(get_current_tenant_id),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: str = Query("all"),  # all, active, inactive
    tag_filter: Optional[str] = Query(None),
    sort_by: str = Query("priority"),
    sort_order: str = Query("asc")
):
    """Get paginated rules with search and filtering"""
    
    # Build query
    query = {"tenant_id": tenant_id}
    
    # Status filter
    if status_filter == "active":
        query["is_active"] = True
    elif status_filter == "inactive":
        query["is_active"] = False
    
    # Search filter
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$in": [search]}}
        ]
    
    # Tag filter
    if tag_filter:
        query["tags"] = {"$in": [tag_filter]}
    
    # Count total
    total_count = await db.return_rules.count_documents(query)
    
    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = (total_count + limit - 1) // limit
    
    # Build sort
    sort_direction = 1 if sort_order == "asc" else -1
    sort_field = sort_by if sort_by in ["priority", "name", "created_at", "updated_at"] else "priority"
    
    # Get rules
    rules_cursor = db.return_rules.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
    rules = await rules_cursor.to_list(length=limit)
    
    # Transform for response
    rules_data = []
    for rule in rules:
        # Convert ObjectId to string if present
        if '_id' in rule:
            rule['_id'] = str(rule['_id'])
        
        # Handle legacy format conversion
        condition_groups = rule.get("condition_groups")
        if condition_groups is None:
            # Legacy format - convert old conditions to new format
            old_conditions = rule.get("conditions", {})
            if old_conditions:
                # Convert old format to new condition_groups format
                condition_groups = [{
                    "conditions": [],
                    "logic_operator": "and"
                }]
                # Add basic conditions based on old format
                if old_conditions.get("auto_approve_reasons"):
                    for reason in old_conditions["auto_approve_reasons"]:
                        condition_groups[0]["conditions"].append({
                            "field": "return_reason",
                            "operator": "equals", 
                            "value": reason
                        })
            else:
                condition_groups = []
        
        # Handle legacy actions format
        actions = rule.get("actions", [])
        if isinstance(actions, dict):
            # Legacy format - convert to new format
            new_actions = []
            if actions.get("auto_approve"):
                new_actions.append({
                    "action_type": "auto_approve_return",
                    "parameters": {}
                })
            if actions.get("manual_review"):
                new_actions.append({
                    "action_type": "require_manual_review", 
                    "parameters": {}
                })
            if actions.get("generate_label"):
                new_actions.append({
                    "action_type": "generate_return_label",
                    "parameters": {}
                })
            actions = new_actions
        
        rule_summary = {
            "id": rule.get("id", str(rule.get("_id", ""))),
            "name": rule.get("name", ""),
            "description": rule.get("description", ""),
            "conditions_summary": _get_conditions_summary(condition_groups),
            "actions_summary": _get_actions_summary(actions),
            "priority": rule.get("priority", 1),
            "is_active": rule.get("is_active", True),
            "created_at": rule.get("created_at"),
            "updated_at": rule.get("updated_at", rule.get("created_at")),
            "tags": rule.get("tags", [])
        }
        rules_data.append(rule_summary)
    
    return {
        "items": rules_data,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "per_page": limit,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "filters": {
            "search": search,
            "status_filter": status_filter,
            "tag_filter": tag_filter,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    }

@router.post("/", response_model=Dict[str, Any])
async def create_rule(
    rule_data: RuleCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Create a new return rule"""
    
    # Validate rule name uniqueness
    existing_rule = await db.return_rules.find_one({
        "tenant_id": tenant_id,
        "name": rule_data.name
    })
    
    if existing_rule:
        raise HTTPException(status_code=400, detail="Rule name already exists")
    
    # Create rule
    rule = EnhancedReturnRule(
        **rule_data.dict(),
        tenant_id=tenant_id,
        created_by="system"  # TODO: Get from auth context
    )
    
    # Store in database
    rule_dict = rule.dict()
    rule_dict["condition_groups"] = [
        {
            "conditions": [
                {
                    "field": cond.field.value,
                    "operator": cond.operator.value,
                    "value": cond.value,
                    "custom_field_name": cond.custom_field_name
                }
                for cond in group.conditions
            ],
            "logic_operator": group.logic_operator
        }
        for group in rule.condition_groups
    ]
    rule_dict["actions"] = [
        {
            "action_type": action.action_type.value,
            "parameters": action.parameters
        }
        for action in rule.actions
    ]
    
    await db.return_rules.insert_one(rule_dict)
    
    # Convert ObjectId to string for response
    if '_id' in rule_dict:
        rule_dict['_id'] = str(rule_dict['_id'])
    
    return {
        "success": True,
        "message": "Rule created successfully",
        "rule_id": rule.id,
        "rule": rule_dict
    }

@router.get("/{rule_id}", response_model=Dict[str, Any])
async def get_rule(
    rule_id: str,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Get a specific rule by ID"""
    
    rule = await db.return_rules.find_one({
        "id": rule_id,
        "tenant_id": tenant_id
    })
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Convert ObjectId to string if present
    if '_id' in rule:
        rule['_id'] = str(rule['_id'])
    
    # Handle legacy format conversion for detailed view
    if rule.get("condition_groups") is None:
        old_conditions = rule.get("conditions", {})
        if old_conditions:
            rule["condition_groups"] = [{
                "conditions": [],
                "logic_operator": "and"
            }]
            if old_conditions.get("auto_approve_reasons"):
                for reason in old_conditions["auto_approve_reasons"]:
                    rule["condition_groups"][0]["conditions"].append({
                        "field": "return_reason",
                        "operator": "equals",
                        "value": reason
                    })
        else:
            rule["condition_groups"] = []
    
    # Handle legacy actions format
    if isinstance(rule.get("actions"), dict):
        old_actions = rule["actions"]
        new_actions = []
        if old_actions.get("auto_approve"):
            new_actions.append({
                "action_type": "auto_approve_return",
                "parameters": {}
            })
        if old_actions.get("manual_review"):
            new_actions.append({
                "action_type": "require_manual_review",
                "parameters": {}
            })
        if old_actions.get("generate_label"):
            new_actions.append({
                "action_type": "generate_return_label",
                "parameters": {}
            })
        rule["actions"] = new_actions
    
    return {
        "success": True,
        "rule": rule
    }

@router.put("/{rule_id}", response_model=Dict[str, Any])
async def update_rule(
    rule_id: str,
    rule_update: RuleUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Update an existing rule"""
    
    # Check if rule exists
    existing_rule = await db.return_rules.find_one({
        "id": rule_id,
        "tenant_id": tenant_id
    })
    
    if not existing_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Build update data
    update_data = {"updated_at": datetime.utcnow()}
    
    # Update only provided fields
    if rule_update.name is not None:
        # Check name uniqueness
        name_conflict = await db.return_rules.find_one({
            "tenant_id": tenant_id,
            "name": rule_update.name,
            "id": {"$ne": rule_id}
        })
        if name_conflict:
            raise HTTPException(status_code=400, detail="Rule name already exists")
        update_data["name"] = rule_update.name
    
    if rule_update.description is not None:
        update_data["description"] = rule_update.description
    
    if rule_update.condition_groups is not None:
        update_data["condition_groups"] = [
            {
                "conditions": [
                    {
                        "field": cond.field.value,
                        "operator": cond.operator.value,
                        "value": cond.value,
                        "custom_field_name": cond.custom_field_name
                    }
                    for cond in group.conditions
                ],
                "logic_operator": group.logic_operator
            }
            for group in rule_update.condition_groups
        ]
    
    if rule_update.actions is not None:
        update_data["actions"] = [
            {
                "action_type": action.action_type.value,
                "parameters": action.parameters
            }
            for action in rule_update.actions
        ]
    
    if rule_update.priority is not None:
        update_data["priority"] = rule_update.priority
    
    if rule_update.is_active is not None:
        update_data["is_active"] = rule_update.is_active
    
    if rule_update.tags is not None:
        update_data["tags"] = rule_update.tags
    
    # Update rule
    result = await db.return_rules.update_one(
        {"id": rule_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes made to rule")
    
    # Get updated rule
    updated_rule = await db.return_rules.find_one({
        "id": rule_id,
        "tenant_id": tenant_id
    })
    
    # Convert ObjectId to string if present
    if updated_rule and '_id' in updated_rule:
        updated_rule['_id'] = str(updated_rule['_id'])
    
    return {
        "success": True,
        "message": "Rule updated successfully",
        "rule": updated_rule
    }

@router.delete("/{rule_id}", response_model=Dict[str, Any])
async def delete_rule(
    rule_id: str,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Delete a rule"""
    
    result = await db.return_rules.delete_one({
        "id": rule_id,
        "tenant_id": tenant_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return {
        "success": True,
        "message": "Rule deleted successfully"
    }

@router.post("/simulate", response_model=Dict[str, Any])
async def simulate_rules(
    simulation_request: RuleSimulationRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Simulate rule execution on test data"""
    
    # Get rules to test
    query = {"tenant_id": tenant_id, "is_active": True}
    
    if simulation_request.rule_ids:
        query["id"] = {"$in": simulation_request.rule_ids}
    
    rules = await db.return_rules.find(query).sort("priority", 1).to_list(100)
    
    if not rules:
        return {
            "success": True,
            "message": "No rules found for simulation",
            "result": {
                "total_rules_evaluated": 0,
                "rules_matched": 0,
                "final_status": "requested",
                "final_notes": "No rules configured"
            }
        }
    
    # Run simulation
    result = EnhancedRulesEngine.evaluate_all_rules(
        rules, 
        simulation_request.return_data,
        simulation_request.order_data
    )
    
    return {
        "success": True,
        "message": "Simulation completed",
        "result": result
    }

@router.post("/test-conditions", response_model=Dict[str, Any])
async def test_conditions(
    test_request: RuleTestRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Test specific conditions against test data"""
    
    # Create temporary rule for testing
    temp_rule = {
        "id": "test-rule",
        "name": "Test Rule",
        "condition_groups": [
            {
                "conditions": [
                    {
                        "field": cond.field.value,
                        "operator": cond.operator.value,
                        "value": cond.value,
                        "custom_field_name": cond.custom_field_name
                    }
                    for cond in group.conditions
                ],
                "logic_operator": group.logic_operator
            }
            for group in test_request.conditions
        ],
        "actions": [],
        "is_active": True
    }
    
    # Test conditions
    result = EnhancedRulesEngine.evaluate_rule(
        temp_rule,
        test_request.test_data.get("return_data", {}),
        test_request.test_data.get("order_data", {})
    )
    
    return {
        "success": True,
        "message": "Condition test completed",
        "result": {
            "rule_matched": result.rule_matched,
            "execution_time_ms": result.execution_time_ms,
            "steps": [
                {
                    "field": step.field,
                    "operator": step.operator,
                    "expected_value": step.expected_value,
                    "actual_value": step.actual_value,
                    "condition_met": step.condition_met,
                    "explanation": step.explanation
                }
                for step in result.steps
            ]
        }
    }

@router.get("/field-types/options", response_model=Dict[str, Any])
async def get_field_type_options():
    """Get available field types, operators, and actions for rule builder"""
    
    return {
        "field_types": [
            {
                "value": field_type.value,
                "label": field_type.value.replace("_", " ").title(),
                "description": _get_field_description(field_type)
            }
            for field_type in FieldType
        ],
        "operators": [
            {
                "value": op.value,
                "label": op.value.replace("_", " ").title(),
                "description": _get_operator_description(op)
            }
            for op in ConditionOperator
        ],
        "actions": [
            {
                "value": action.value,
                "label": action.value.replace("_", " ").title(),
                "description": _get_action_description(action),
                "parameters": _get_action_parameters(action)
            }
            for action in ActionType
        ]
    }

# Helper functions
def _get_conditions_summary(condition_groups: List[Dict]) -> str:
    """Generate human-readable conditions summary"""
    if not condition_groups:
        return "No conditions"
    
    summaries = []
    for group in condition_groups:
        group_conditions = []
        for cond in group.get("conditions", []):
            field = cond["field"].replace("_", " ").title()
            operator = cond["operator"].replace("_", " ")
            value = cond["value"]
            group_conditions.append(f"{field} {operator} {value}")
        
        logic_op = group.get("logic_operator", "and").upper()
        group_summary = f" {logic_op} ".join(group_conditions)
        summaries.append(f"({group_summary})")
    
    return " AND ".join(summaries)

def _get_actions_summary(actions: List[Dict]) -> str:
    """Generate human-readable actions summary"""
    if not actions:
        return "No actions"
    
    action_labels = []
    for action in actions:
        action_type = action.get("action_type", "").replace("_", " ").title()
        action_labels.append(action_type)
    
    return ", ".join(action_labels)

def _get_field_description(field_type: FieldType) -> str:
    """Get description for field type"""
    descriptions = {
        FieldType.ORDER_AMOUNT: "Total order value in currency",
        FieldType.PRODUCT_CATEGORY: "Product categories in the order",
        FieldType.SKU_ITEM_NAME: "Product SKUs and names being returned",
        FieldType.CUSTOMER_LOCATION: "Customer billing/shipping address",
        FieldType.PAYMENT_METHOD: "Payment method used for order",
        FieldType.ORDER_TAG: "Tags assigned to the order",
        FieldType.ORDER_STATUS: "Order financial and fulfillment status",
        FieldType.RETURN_REASON: "Reason provided for return",
        FieldType.DAYS_SINCE_ORDER: "Number of days since order was placed",
        FieldType.CUSTOM_FIELD: "Custom field from order or return data"
    }
    return descriptions.get(field_type, "")

def _get_operator_description(operator: ConditionOperator) -> str:
    """Get description for operator"""
    descriptions = {
        ConditionOperator.EQUALS: "Exact match",
        ConditionOperator.NOT_EQUALS: "Does not match",
        ConditionOperator.GREATER_THAN: "Greater than (numeric)",
        ConditionOperator.LESS_THAN: "Less than (numeric)",
        ConditionOperator.GREATER_EQUAL: "Greater than or equal (numeric)",
        ConditionOperator.LESS_EQUAL: "Less than or equal (numeric)",
        ConditionOperator.CONTAINS: "Contains text (case-insensitive)",
        ConditionOperator.NOT_CONTAINS: "Does not contain text",
        ConditionOperator.IN: "Is one of (list)",
        ConditionOperator.NOT_IN: "Is not one of (list)",
        ConditionOperator.REGEX: "Matches regular expression"
    }
    return descriptions.get(operator, "")

def _get_action_description(action: ActionType) -> str:
    """Get description for action"""
    descriptions = {
        ActionType.AUTO_APPROVE_RETURN: "Automatically approve the return",
        ActionType.AUTO_DECLINE_RETURN: "Automatically decline the return",
        ActionType.SEND_EMAIL_NOTIFICATION: "Send email notification",
        ActionType.ADD_ORDER_TAG: "Add tag to the order",
        ActionType.ASSIGN_TEAM_MEMBER: "Assign to specific team member",
        ActionType.CHANGE_RETURN_STATUS: "Change return to specific status",
        ActionType.REQUIRE_MANUAL_REVIEW: "Route to manual review queue",
        ActionType.GENERATE_RETURN_LABEL: "Generate return shipping label"
    }
    return descriptions.get(action, "")

def _get_action_parameters(action: ActionType) -> List[Dict]:
    """Get required parameters for action"""
    parameters = {
        ActionType.SEND_EMAIL_NOTIFICATION: [
            {"name": "template", "type": "string", "required": True},
            {"name": "recipients", "type": "array", "required": False}
        ],
        ActionType.ADD_ORDER_TAG: [
            {"name": "tag", "type": "string", "required": True}
        ],
        ActionType.ASSIGN_TEAM_MEMBER: [
            {"name": "user_id", "type": "string", "required": True}
        ],
        ActionType.CHANGE_RETURN_STATUS: [
            {"name": "status", "type": "string", "required": True}
        ]
    }
    return parameters.get(action, [])