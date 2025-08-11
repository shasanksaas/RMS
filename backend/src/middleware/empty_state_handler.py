"""
Empty State Handler - Manages unconnected tenant responses
Returns appropriate empty states for tenants without integrations
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EmptyStateHandler:
    """
    Handles empty state responses for unconnected tenants
    Ensures consistent, helpful empty states across all data endpoints
    """
    
    def __init__(self):
        self.empty_responses = {
            "orders": {
                "orders": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
                "total_pages": 0,
                "message": "Connect your Shopify store to import orders automatically",
                "empty_state": True,
                "connect_url": "/app/settings/integrations"
            },
            "returns": {
                "returns": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
                "total_pages": 0,
                "message": "No returns yet. Returns will appear here once customers start creating them.",
                "empty_state": True,
                "features": {
                    "manual_returns": True,
                    "customer_portal": True,
                    "basic_analytics": True
                }
            },
            "customers": {
                "customers": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
                "total_pages": 0,
                "message": "Connect your Shopify store to sync customer data automatically",
                "empty_state": True,
                "connect_url": "/app/settings/integrations"
            },
            "analytics": {
                "overview": {
                    "total_returns": 0,
                    "returns_this_month": 0,
                    "revenue_saved": 0.0,
                    "avg_processing_time": 0,
                    "customer_satisfaction": None,
                    "return_rate": 0.0
                },
                "charts": {
                    "returns_by_month": [],
                    "returns_by_reason": [],
                    "returns_by_status": []
                },
                "message": "Analytics will populate as you process more returns",
                "empty_state": True,
                "features_available": ["basic_analytics", "manual_tracking"]
            },
            "rules": {
                "rules": [],
                "total": 0,
                "message": "Create automated rules to streamline your return process",
                "empty_state": True,
                "templates": [
                    {
                        "name": "Auto-approve returns under $50",
                        "description": "Automatically approve returns for items under $50"
                    },
                    {
                        "name": "Require photos for electronics",
                        "description": "Require customers to upload photos for electronics returns"
                    }
                ]
            },
            "workflows": {
                "workflows": [],
                "total": 0,
                "message": "Design custom workflows to handle different types of returns",
                "empty_state": True,
                "templates": [
                    {
                        "name": "Standard Return Flow",
                        "description": "Basic return processing workflow"
                    },
                    {
                        "name": "Exchange Workflow",
                        "description": "Handle product exchanges efficiently"
                    }
                ]
            }
        }
    
    def get_empty_orders_response(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Return empty state for orders endpoint"""
        response = self.empty_responses["orders"].copy()
        response.update({
            "page": page,
            "page_size": page_size,
            "timestamp": datetime.utcnow().isoformat()
        })
        return response
    
    def get_empty_returns_response(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Return empty state for returns endpoint"""
        response = self.empty_responses["returns"].copy()
        response.update({
            "page": page,
            "page_size": page_size,
            "timestamp": datetime.utcnow().isoformat()
        })
        return response
    
    def get_empty_customers_response(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Return empty state for customers endpoint"""
        response = self.empty_responses["customers"].copy()
        response.update({
            "page": page,
            "page_size": page_size,
            "timestamp": datetime.utcnow().isoformat()
        })
        return response
    
    def get_empty_analytics_response(self) -> Dict[str, Any]:
        """Return empty state for analytics endpoint"""
        response = self.empty_responses["analytics"].copy()
        response["timestamp"] = datetime.utcnow().isoformat()
        return response
    
    def get_empty_rules_response(self) -> Dict[str, Any]:
        """Return empty state for rules endpoint"""
        response = self.empty_responses["rules"].copy()
        response["timestamp"] = datetime.utcnow().isoformat()
        return response
    
    def get_empty_workflows_response(self) -> Dict[str, Any]:
        """Return empty state for workflows endpoint"""
        response = self.empty_responses["workflows"].copy()
        response["timestamp"] = datetime.utcnow().isoformat()
        return response
    
    def get_connection_status_response(self, tenant_id: str, connected: bool = False) -> Dict[str, Any]:
        """Return connection status for tenant"""
        if connected:
            return {
                "tenant_id": tenant_id,
                "connected": True,
                "shopify_connected": True,
                "features": [
                    "order_sync", "customer_sync", "inventory_sync",
                    "webhook_updates", "advanced_analytics", "automation"
                ],
                "message": "Shopify store connected and syncing"
            }
        else:
            return {
                "tenant_id": tenant_id,
                "connected": False,
                "shopify_connected": False,
                "features": [
                    "manual_returns", "basic_analytics", "customer_portal"
                ],
                "message": "Connect your Shopify store to unlock all features",
                "connect_url": "/app/settings/integrations",
                "benefits": [
                    "Automatic order import",
                    "Customer data sync",
                    "Real-time inventory updates",
                    "Advanced analytics",
                    "Automated workflows"
                ]
            }
    
    def get_order_detail_empty_response(self, order_id: str) -> Dict[str, Any]:
        """Return empty state for specific order detail"""
        return {
            "error": "Order not found",
            "message": "This order may not exist or your store is not connected to Shopify",
            "order_id": order_id,
            "empty_state": True,
            "actions": [
                {
                    "label": "Connect Shopify Store",
                    "url": "/app/settings/integrations",
                    "primary": True
                },
                {
                    "label": "Manual Return Creation",
                    "url": "/app/returns/create",
                    "primary": False
                }
            ]
        }
    
    def get_customer_detail_empty_response(self, customer_id: str) -> Dict[str, Any]:
        """Return empty state for specific customer detail"""
        return {
            "error": "Customer not found",
            "message": "Customer data is only available when your Shopify store is connected",
            "customer_id": customer_id,
            "empty_state": True,
            "connect_url": "/app/settings/integrations"
        }
    
    def should_return_empty_state(self, tenant_connected: bool, endpoint_type: str) -> bool:
        """
        Determine if endpoint should return empty state
        Different endpoints have different requirements for connectivity
        """
        # Returns can work without connection (manual returns)
        if endpoint_type == "returns":
            return False
        
        # Orders, customers, advanced analytics require connection
        if endpoint_type in ["orders", "customers", "advanced_analytics"]:
            return not tenant_connected
        
        # Basic analytics, rules, workflows work without connection
        if endpoint_type in ["basic_analytics", "rules", "workflows"]:
            return False
        
        # Default to requiring connection
        return not tenant_connected

# Global empty state handler instance
empty_state_handler = EmptyStateHandler()