"""
Return rule model definitions and schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
import uuid


class ReturnRule(BaseModel):
    """Return rule model for rules engine"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: str
    conditions: Dict[str, Any]  # JSON conditions for rule evaluation
    actions: Dict[str, Any]     # Actions to take when rule matches
    priority: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReturnRuleCreate(BaseModel):
    """Schema for creating a return rule"""
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int = 1


class ReturnRuleUpdate(BaseModel):
    """Schema for updating a return rule"""
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None