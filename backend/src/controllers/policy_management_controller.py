"""
Comprehensive Policy Management Controller
Handles all return policy configurations with full functionality
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
import json

from ..middleware.security import get_current_tenant_id
from ..config.database import db
from ..services.policy_engine_service import PolicyEngineService
from ..utils.policy_validator import PolicyValidator

router = APIRouter(prefix="/policies", tags=["Policy Management"])

# === POLICY MODELS === #

class PolicyZoneModel(BaseModel):
    zone_name: str
    countries_included: List[str] = Field(default_factory=list)
    states_provinces: List[str] = Field(default_factory=list)
    postal_codes: Dict[str, Any] = Field(default_factory=dict)
    destination_warehouse: str = "default"
    backup_destinations: List[str] = Field(default_factory=list)
    generate_labels: bool = True
    bypass_manual_review: bool = False
    generate_packing_slips: bool = True
    customs_handling: Dict[str, Any] = Field(default_factory=dict)
    carrier_restrictions: Dict[str, Any] = Field(default_factory=dict)

class ReturnWindowModel(BaseModel):
    standard_window: Dict[str, Any] = Field(default_factory=dict)
    extended_windows: Dict[str, Any] = Field(default_factory=dict)
    category_specific_windows: Dict[str, Any] = Field(default_factory=dict)
    price_based_windows: Dict[str, Any] = Field(default_factory=dict)

class ProductEligibilityModel(BaseModel):
    default_returnable: bool = True
    tag_based_rules: Dict[str, Any] = Field(default_factory=dict)
    category_exclusions: Dict[str, Any] = Field(default_factory=dict)
    condition_requirements: Dict[str, Any] = Field(default_factory=dict)
    value_based_rules: Dict[str, Any] = Field(default_factory=dict)
    age_restrictions: Dict[str, Any] = Field(default_factory=dict)
    quantity_restrictions: Dict[str, Any] = Field(default_factory=dict)

class RefundSettingsModel(BaseModel):
    enabled: bool = True
    processing_events: List[str] = Field(default_factory=list)
    processing_delay: Dict[str, Any] = Field(default_factory=dict)
    refund_methods: Dict[str, bool] = Field(default_factory=dict)
    partial_refunds: Dict[str, Any] = Field(default_factory=dict)
    fees: Dict[str, Any] = Field(default_factory=dict)
    tax_handling: Dict[str, Any] = Field(default_factory=dict)

class ExchangeSettingsModel(BaseModel):
    enabled: bool = True
    same_product_only: bool = False
    advanced_exchanges: bool = True
    exchange_types: Dict[str, bool] = Field(default_factory=dict)
    instant_exchanges: Dict[str, Any] = Field(default_factory=dict)
    price_difference_handling: Dict[str, Any] = Field(default_factory=dict)
    shipping_methods: Dict[str, Any] = Field(default_factory=dict)
    inventory_allocation: Dict[str, Any] = Field(default_factory=dict)
    exchanges_of_exchanges: Dict[str, Any] = Field(default_factory=dict)

class StoreCreditSettingsModel(BaseModel):
    enabled: bool = True
    provider: str = "shopify"
    bonus_incentives: Dict[str, Any] = Field(default_factory=dict)
    credit_features: Dict[str, Any] = Field(default_factory=dict)
    redemption_rules: Dict[str, Any] = Field(default_factory=dict)

class KeepItemSettingsModel(BaseModel):
    enabled: bool = True
    triggers: Dict[str, Any] = Field(default_factory=dict)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    donation_option: Dict[str, Any] = Field(default_factory=dict)

class ShopNowSettingsModel(BaseModel):
    enabled: bool = True
    immediate_shopping: bool = True
    bonus_incentives: Dict[str, Any] = Field(default_factory=dict)
    shopping_experience: Dict[str, Any] = Field(default_factory=dict)
    shop_later: Dict[str, Any] = Field(default_factory=dict)

class FraudDetectionModel(BaseModel):
    ai_models: Dict[str, Any] = Field(default_factory=dict)
    behavioral_patterns: Dict[str, Any] = Field(default_factory=dict)
    blocklist_management: Dict[str, Any] = Field(default_factory=dict)
    fraud_actions: Dict[str, Any] = Field(default_factory=dict)

class ShippingLogisticsModel(BaseModel):
    label_generation: Dict[str, Any] = Field(default_factory=dict)
    return_methods: Dict[str, Any] = Field(default_factory=dict)
    packaging_requirements: Dict[str, Any] = Field(default_factory=dict)
    tracking: Dict[str, Any] = Field(default_factory=dict)

class EmailCommunicationsModel(BaseModel):
    branding: Dict[str, Any] = Field(default_factory=dict)
    templates: Dict[str, Any] = Field(default_factory=dict)
    sms_notifications: Dict[str, Any] = Field(default_factory=dict)

class ReportingAnalyticsModel(BaseModel):
    dashboard_metrics: Dict[str, Any] = Field(default_factory=dict)
    custom_reports: Dict[str, Any] = Field(default_factory=dict)
    predictive_analytics: Dict[str, Any] = Field(default_factory=dict)

class WorkflowConditionsModel(BaseModel):
    customer_attributes: List[str] = Field(default_factory=list)
    order_attributes: List[str] = Field(default_factory=list)
    product_attributes: List[str] = Field(default_factory=list)
    return_attributes: List[str] = Field(default_factory=list)
    temporal_conditions: List[str] = Field(default_factory=list)

class ComprehensivePolicyModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str = "Default Policy"
    description: str = ""
    
    # Core policy areas
    policy_zones: List[PolicyZoneModel] = Field(default_factory=list)
    return_windows: ReturnWindowModel = Field(default_factory=ReturnWindowModel)
    product_eligibility: ProductEligibilityModel = Field(default_factory=ProductEligibilityModel)
    
    # Return outcomes
    refund_settings: RefundSettingsModel = Field(default_factory=RefundSettingsModel)
    exchange_settings: ExchangeSettingsModel = Field(default_factory=ExchangeSettingsModel)
    store_credit_settings: StoreCreditSettingsModel = Field(default_factory=StoreCreditSettingsModel)
    keep_item_settings: KeepItemSettingsModel = Field(default_factory=KeepItemSettingsModel)
    shop_now_settings: ShopNowSettingsModel = Field(default_factory=ShopNowSettingsModel)
    
    # Advanced features
    workflow_conditions: WorkflowConditionsModel = Field(default_factory=WorkflowConditionsModel)
    fraud_detection: FraudDetectionModel = Field(default_factory=FraudDetectionModel)
    shipping_logistics: ShippingLogisticsModel = Field(default_factory=ShippingLogisticsModel)
    email_communications: EmailCommunicationsModel = Field(default_factory=EmailCommunicationsModel)
    reporting_analytics: ReportingAnalyticsModel = Field(default_factory=ReportingAnalyticsModel)
    
    # Metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    version: int = 1
    tags: List[str] = Field(default_factory=list)

class PolicyUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    policy_zones: Optional[List[PolicyZoneModel]] = None
    return_windows: Optional[ReturnWindowModel] = None
    product_eligibility: Optional[ProductEligibilityModel] = None
    refund_settings: Optional[RefundSettingsModel] = None
    exchange_settings: Optional[ExchangeSettingsModel] = None
    store_credit_settings: Optional[StoreCreditSettingsModel] = None
    keep_item_settings: Optional[KeepItemSettingsModel] = None
    shop_now_settings: Optional[ShopNowSettingsModel] = None
    workflow_conditions: Optional[WorkflowConditionsModel] = None
    fraud_detection: Optional[FraudDetectionModel] = None
    shipping_logistics: Optional[ShippingLogisticsModel] = None
    email_communications: Optional[EmailCommunicationsModel] = None
    reporting_analytics: Optional[ReportingAnalyticsModel] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None

class PolicyEvaluationRequest(BaseModel):
    return_data: Dict[str, Any]
    order_data: Dict[str, Any]
    customer_data: Optional[Dict[str, Any]] = None

# === API ENDPOINTS === #

@router.get("/", response_model=Dict[str, Any])
async def get_policies(
    tenant_id: str = Depends(get_current_tenant_id),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    include_templates: bool = Query(False)
):
    """Get paginated policies with search and filtering"""
    
    # Build query
    query = {"tenant_id": tenant_id}
    
    if active_only:
        query["is_active"] = True
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$in": [search]}}
        ]
    
    # Count total
    total_count = await db.return_policies.count_documents(query)
    
    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = (total_count + limit - 1) // limit
    
    # Get policies
    policies_cursor = db.return_policies.find(query).sort("updated_at", -1).skip(skip).limit(limit)
    policies = await policies_cursor.to_list(length=limit)
    
    # Transform for response
    policies_data = []
    for policy in policies:
        if '_id' in policy:
            policy['_id'] = str(policy['_id'])
        
        policy_summary = {
            "id": policy.get("id"),
            "name": policy.get("name"),
            "description": policy.get("description"),
            "is_active": policy.get("is_active"),
            "version": policy.get("version", 1),
            "created_at": policy.get("created_at"),
            "updated_at": policy.get("updated_at"),
            "tags": policy.get("tags", []),
            "zones_count": len(policy.get("policy_zones", [])),
            "features_enabled": _get_features_summary(policy)
        }
        policies_data.append(policy_summary)
    
    # Include policy templates if requested
    templates = []
    if include_templates:
        templates = await _get_policy_templates()
    
    return {
        "items": policies_data,
        "templates": templates,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "per_page": limit,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.post("/", response_model=Dict[str, Any])
async def create_policy(
    policy_data: ComprehensivePolicyModel,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Create a new comprehensive policy"""
    
    # Validate policy name uniqueness
    existing_policy = await db.return_policies.find_one({
        "tenant_id": tenant_id,
        "name": policy_data.name
    })
    
    if existing_policy:
        raise HTTPException(status_code=400, detail="Policy name already exists")
    
    # Set tenant_id
    policy_data.tenant_id = tenant_id
    policy_data.created_by = "system"  # TODO: Get from auth context
    
    # Validate policy configuration
    validation_result = PolicyValidator.validate_policy(policy_data.dict())
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400, 
            detail=f"Policy validation failed: {validation_result.errors}"
        )
    
    # Store in database
    policy_dict = policy_data.dict()
    await db.return_policies.insert_one(policy_dict)
    
    # Convert ObjectId to string for response
    if '_id' in policy_dict:
        policy_dict['_id'] = str(policy_dict['_id'])
    
    return {
        "success": True,
        "message": "Policy created successfully",
        "policy_id": policy_data.id,
        "policy": policy_dict
    }

@router.get("/{policy_id}", response_model=Dict[str, Any])
async def get_policy(
    policy_id: str,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Get a specific policy by ID"""
    
    policy = await db.return_policies.find_one({
        "id": policy_id,
        "tenant_id": tenant_id
    })
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Convert ObjectId to string if present
    if '_id' in policy:
        policy['_id'] = str(policy['_id'])
    
    return {
        "success": True,
        "policy": policy
    }

@router.put("/{policy_id}", response_model=Dict[str, Any])
async def update_policy(
    policy_id: str,
    policy_update: PolicyUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Update an existing policy"""
    
    # Check if policy exists
    existing_policy = await db.return_policies.find_one({
        "id": policy_id,
        "tenant_id": tenant_id
    })
    
    if not existing_policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Build update data
    update_data = {"updated_at": datetime.utcnow()}
    
    # Update only provided fields
    update_dict = policy_update.dict(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            update_data[field] = value
    
    # Check name uniqueness if name is being updated
    if policy_update.name:
        name_conflict = await db.return_policies.find_one({
            "tenant_id": tenant_id,
            "name": policy_update.name,
            "id": {"$ne": policy_id}
        })
        if name_conflict:
            raise HTTPException(status_code=400, detail="Policy name already exists")
    
    # Increment version
    update_data["version"] = existing_policy.get("version", 1) + 1
    
    # Validate updated policy
    temp_policy = {**existing_policy, **update_data}
    validation_result = PolicyValidator.validate_policy(temp_policy)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400, 
            detail=f"Policy validation failed: {validation_result.errors}"
        )
    
    # Update policy
    result = await db.return_policies.update_one(
        {"id": policy_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes made to policy")
    
    # Get updated policy
    updated_policy = await db.return_policies.find_one({
        "id": policy_id,
        "tenant_id": tenant_id
    })
    
    if updated_policy and '_id' in updated_policy:
        updated_policy['_id'] = str(updated_policy['_id'])
    
    return {
        "success": True,
        "message": "Policy updated successfully",
        "policy": updated_policy
    }

@router.delete("/{policy_id}", response_model=Dict[str, Any])
async def delete_policy(
    policy_id: str,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Delete a policy"""
    
    result = await db.return_policies.delete_one({
        "id": policy_id,
        "tenant_id": tenant_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return {
        "success": True,
        "message": "Policy deleted successfully"
    }

@router.post("/{policy_id}/evaluate", response_model=Dict[str, Any])
async def evaluate_policy(
    policy_id: str,
    evaluation_request: PolicyEvaluationRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Evaluate a policy against return/order data"""
    
    # Get policy
    policy = await db.return_policies.find_one({
        "id": policy_id,
        "tenant_id": tenant_id
    })
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    if not policy.get("is_active"):
        raise HTTPException(status_code=400, detail="Policy is not active")
    
    # Evaluate policy
    engine = PolicyEngineService(tenant_id)
    result = await engine.evaluate_policy(
        policy,
        evaluation_request.return_data,
        evaluation_request.order_data,
        evaluation_request.customer_data
    )
    
    return {
        "success": True,
        "evaluation_result": result
    }

@router.post("/{policy_id}/activate", response_model=Dict[str, Any])
async def activate_policy(
    policy_id: str,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Activate a policy (deactivates others)"""
    
    # Deactivate all other policies
    await db.return_policies.update_many(
        {"tenant_id": tenant_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    # Activate this policy
    result = await db.return_policies.update_one(
        {"id": policy_id, "tenant_id": tenant_id},
        {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return {
        "success": True,
        "message": "Policy activated successfully"
    }

@router.get("/{policy_id}/preview", response_model=Dict[str, Any])
async def preview_policy_settings(
    policy_id: str,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Get a preview of policy settings and their implications"""
    
    policy = await db.return_policies.find_one({
        "id": policy_id,
        "tenant_id": tenant_id
    })
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Generate policy preview
    preview = _generate_policy_preview(policy)
    
    return {
        "success": True,
        "preview": preview
    }

@router.post("/templates/{template_name}/apply", response_model=Dict[str, Any])
async def apply_policy_template(
    template_name: str,
    tenant_id: str = Depends(get_current_tenant_id),
    customizations: Optional[Dict[str, Any]] = None
):
    """Apply a pre-built policy template"""
    
    # Get template
    template = await _get_policy_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Apply customizations
    if customizations:
        template = {**template, **customizations}
    
    # Set metadata
    template["id"] = str(uuid.uuid4())
    template["tenant_id"] = tenant_id
    template["name"] = f"{template_name.title()} Policy"
    template["created_at"] = datetime.utcnow()
    template["updated_at"] = datetime.utcnow()
    template["created_by"] = "template"
    
    # Validate and store
    validation_result = PolicyValidator.validate_policy(template)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400, 
            detail=f"Template validation failed: {validation_result.errors}"
        )
    
    await db.return_policies.insert_one(template)
    
    if '_id' in template:
        template['_id'] = str(template['_id'])
    
    return {
        "success": True,
        "message": f"Applied {template_name} template successfully",
        "policy": template
    }

# === HELPER FUNCTIONS === #

def _get_features_summary(policy: Dict[str, Any]) -> Dict[str, bool]:
    """Generate summary of enabled features"""
    return {
        "refunds": policy.get("refund_settings", {}).get("enabled", False),
        "exchanges": policy.get("exchange_settings", {}).get("enabled", False),
        "store_credit": policy.get("store_credit_settings", {}).get("enabled", False),
        "keep_item": policy.get("keep_item_settings", {}).get("enabled", False),
        "shop_now": policy.get("shop_now_settings", {}).get("enabled", False),
        "fraud_detection": policy.get("fraud_detection", {}).get("ai_models", {}).get("enabled", False),
        "email_notifications": len(policy.get("email_communications", {}).get("templates", {})) > 0,
        "multiple_zones": len(policy.get("policy_zones", [])) > 1
    }

def _generate_policy_preview(policy: Dict[str, Any]) -> Dict[str, Any]:
    """Generate human-readable policy preview"""
    
    # Extract key settings
    return_windows = policy.get("return_windows", {})
    standard_window = return_windows.get("standard_window", {})
    
    refund_settings = policy.get("refund_settings", {})
    exchange_settings = policy.get("exchange_settings", {})
    
    preview = {
        "return_window": {
            "days": standard_window.get("days", [30])[0] if standard_window.get("days") else 30,
            "calculation_from": standard_window.get("calculation_from", "order_date"),
            "business_days_only": standard_window.get("business_days_only", False)
        },
        "available_outcomes": [],
        "fees": {},
        "restrictions": [],
        "automation_level": "manual"
    }
    
    # Determine available outcomes
    if refund_settings.get("enabled"):
        preview["available_outcomes"].append("refund")
    if exchange_settings.get("enabled"):
        preview["available_outcomes"].append("exchange")
    if policy.get("store_credit_settings", {}).get("enabled"):
        preview["available_outcomes"].append("store_credit")
    if policy.get("keep_item_settings", {}).get("enabled"):
        preview["available_outcomes"].append("keep_item")
    
    # Extract fees
    fees = refund_settings.get("fees", {})
    if fees.get("restocking_fee", {}).get("enabled"):
        preview["fees"]["restocking"] = fees["restocking_fee"].get("amount", 0)
    if fees.get("processing_fee", {}).get("enabled"):
        preview["fees"]["processing"] = fees["processing_fee"].get("amount", 0)
    
    # Determine restrictions
    eligibility = policy.get("product_eligibility", {})
    if eligibility.get("category_exclusions", {}).get("excluded_categories"):
        preview["restrictions"].append("category_exclusions")
    if eligibility.get("value_based_rules", {}).get("min_return_value"):
        preview["restrictions"].append("minimum_value")
    
    # Determine automation level
    fraud_detection = policy.get("fraud_detection", {})
    if fraud_detection.get("ai_models", {}).get("enabled"):
        preview["automation_level"] = "high"
    elif len(policy.get("workflow_conditions", {}).get("customer_attributes", [])) > 0:
        preview["automation_level"] = "medium"
    
    return preview

async def _get_policy_templates() -> List[Dict[str, Any]]:
    """Get available policy templates"""
    templates = [
        {
            "name": "standard_retail",
            "display_name": "Standard Retail Policy",
            "description": "Basic return policy for general retail businesses",
            "features": ["30-day returns", "refunds", "exchanges", "restocking fee"]
        },
        {
            "name": "fashion_apparel", 
            "display_name": "Fashion & Apparel Policy",
            "description": "Optimized for clothing and fashion retailers",
            "features": ["60-day returns", "size exchanges", "style exchanges", "seasonal extensions"]
        },
        {
            "name": "electronics_tech",
            "display_name": "Electronics & Technology Policy", 
            "description": "Designed for electronics and tech product sales",
            "features": ["14-day returns", "restocking fees", "condition requirements", "warranty integration"]
        },
        {
            "name": "luxury_premium",
            "display_name": "Luxury & Premium Policy",
            "description": "High-end policy for luxury brands",
            "features": ["90-day returns", "white-glove service", "authentication", "concierge support"]
        },
        {
            "name": "marketplace_seller",
            "display_name": "Marketplace Seller Policy",
            "description": "Multi-seller marketplace policies",
            "features": ["seller-specific rules", "centralized processing", "dispute resolution", "performance tracking"]
        }
    ]
    
    return templates

async def _get_policy_template(template_name: str) -> Optional[Dict[str, Any]]:
    """Get specific policy template configuration"""
    
    templates = {
        "standard_retail": {
            "description": "Standard retail return policy with 30-day window",
            "return_windows": {
                "standard_window": {
                    "type": "limited",
                    "days": [30],
                    "calculation_from": "order_date",
                    "business_days_only": False,
                    "exclude_weekends": False,
                    "exclude_holidays": True,
                    "holiday_calendar": "us"
                }
            },
            "refund_settings": {
                "enabled": True,
                "processing_events": ["delivered"],
                "processing_delay": {"enabled": True, "delay_days": [3], "business_days_only": True},
                "refund_methods": {
                    "original_payment_method": True,
                    "store_credit": True,
                    "bank_transfer": False
                },
                "fees": {
                    "restocking_fee": {"enabled": True, "amount": 15.00, "type": "flat_rate"}
                }
            },
            "exchange_settings": {
                "enabled": True,
                "same_product_only": False,
                "exchange_types": {
                    "size_color_variant": True,
                    "different_product": True
                }
            }
        },
        "fashion_apparel": {
            "description": "Fashion and apparel optimized policy with extended windows",
            "return_windows": {
                "standard_window": {
                    "type": "limited",
                    "days": [60],
                    "calculation_from": "delivery_date",
                    "business_days_only": False
                },
                "extended_windows": {
                    "holiday_extension": {"enabled": True, "extra_days": 15}
                }
            },
            "product_eligibility": {
                "default_returnable": True,
                "tag_based_rules": {
                    "final_sale_tags": ["final_sale", "clearance"],
                    "exchange_only_tags": ["hygiene", "swimwear"]
                },
                "condition_requirements": {
                    "tags_attached_required": True,
                    "unworn_unused_only": True
                }
            }
        },
        "electronics_tech": {
            "description": "Electronics and technology policy with strict conditions",
            "return_windows": {
                "standard_window": {
                    "type": "limited",
                    "days": [14],
                    "calculation_from": "delivery_date"
                }
            },
            "product_eligibility": {
                "condition_requirements": {
                    "original_packaging_required": True,
                    "accessories_included": True,
                    "unworn_unused_only": True
                }
            },
            "refund_settings": {
                "enabled": True,
                "fees": {
                    "restocking_fee": {"enabled": True, "amount": 25.00, "type": "flat_rate"}
                }
            }
        }
    }
    
    return templates.get(template_name)