"""
Analytics model definitions and schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime


class Analytics(BaseModel):
    """Analytics data model"""
    tenant_id: str
    total_returns: int = 0
    total_refunds: float = 0.0
    exchange_rate: float = 0.0
    avg_processing_time: float = 0.0
    top_return_reasons: List[Dict[str, Any]] = Field(default_factory=list)
    period_start: datetime
    period_end: datetime


class AnalyticsRequest(BaseModel):
    """Request schema for analytics"""
    days: int = 30
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None