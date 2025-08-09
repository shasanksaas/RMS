"""
Analytics service - handles analytics calculations and data
"""
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

from ..models import Analytics
from ..config.database import db, COLLECTIONS


class AnalyticsService:
    """Service class for analytics operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase = db):
        self.db = database
    
    async def get_tenant_analytics(self, tenant_id: str, days: int = 30) -> Analytics:
        """Get analytics for a tenant over specified time period"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get return requests in period
        returns = await self.db[COLLECTIONS['return_requests']].find({
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(1000)
        
        # Calculate metrics
        total_returns = len(returns)
        total_refunds = sum(ret.get("refund_amount", 0) for ret in returns)
        
        # Calculate exchange rate
        exchanges = [ret for ret in returns if ret.get("status") == "exchanged"]
        exchange_rate = (len(exchanges) / total_returns * 100) if total_returns > 0 else 0
        
        # Calculate average processing time (mock for now)
        avg_processing_time = 2.5
        
        # Top return reasons
        reason_counts = {}
        for ret in returns:
            reason = ret.get("reason", "unknown")
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        top_return_reasons = [
            {
                "reason": reason, 
                "count": count, 
                "percentage": count / total_returns * 100 if total_returns > 0 else 0
            }
            for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return Analytics(
            tenant_id=tenant_id,
            total_returns=total_returns,
            total_refunds=total_refunds,
            exchange_rate=exchange_rate,
            avg_processing_time=avg_processing_time,
            top_return_reasons=top_return_reasons,
            period_start=start_date,
            period_end=end_date
        )
    
    async def get_return_trends(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get return trends over time"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Aggregate returns by day
        pipeline = [
            {
                "$match": {
                    "tenant_id": tenant_id,
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1},
                    "total_refund": {"$sum": "$refund_amount"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        trends = await self.db[COLLECTIONS['return_requests']].aggregate(pipeline).to_list(100)
        
        return {
            "daily_trends": trends,
            "period_start": start_date,
            "period_end": end_date
        }