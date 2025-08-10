"""
Enhanced Shopify GraphQL Service for Order Lookup
"""

import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio

from ..config.database import db
from .rules_engine_advanced import advanced_rules_engine

logger = logging.getLogger(__name__)

class ShopifyGraphQLService:
    """Enhanced Shopify GraphQL service for order operations"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.api_version = "2025-07"
        
    async def get_access_token(self) -> Optional[str]:
        """Get decrypted access token for tenant"""
        try:
            integration = await db.integrations_shopify.find_one({
                "tenant_id": self.tenant_id,
                "status": "connected"
            })
            
            if not integration:
                return None
                
            # Decrypt token
            from cryptography.fernet import Fernet
            import os
            
            encryption_key = os.environ.get('ENCRYPTION_KEY')
            if not encryption_key:
                logger.error("ENCRYPTION_KEY not found")
                return None
                
            cipher = Fernet(encryption_key.encode())
            access_token = cipher.decrypt(
                integration["access_token_encrypted"].encode()
            ).decode()
            
            return access_token
            
        except Exception as e:
            logger.error(f"Failed to get access token for {self.tenant_id}: {e}")
            return None
    
    async def lookup_order_by_name_and_email(self, order_name: str, customer_email: str) -> Optional[Dict[str, Any]]:
        """
        Lookup order by order number and verify customer email
        Returns order details with computed eligibility
        """
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return None
            
            # Get shop domain
            integration = await db.integrations_shopify.find_one({
                "tenant_id": self.tenant_id,
                "status": "connected"
            })
            
            if not integration:
                return None
                
            shop_domain = integration["shop"]
            
            # Clean order name
            order_name = order_name.replace("#", "").strip()
            
            # GraphQL query to find order by name and verify email
            query = """
            query GetOrder($orderName: String!) {
              orders(first: 5, query: $orderName) {
                edges {
                  node {
                    id
                    name
                    createdAt
                    updatedAt
                    processedAt
                    currencyCode
                    totalPriceSet {
                      shopMoney {
                        amount
                        currencyCode
                      }
                    }
                    customer {
                      id
                      email
                      firstName
                      lastName
                    }
                    fulfillmentStatus
                    displayFulfillmentStatus
                    displayFinancialStatus
                    lineItems(first: 50) {
                      edges {
                        node {
                          id
                          title
                          name
                          sku
                          variantTitle
                          quantity
                          fulfillmentStatus
                          fulfillableQuantity
                          image {
                            url
                            altText
                          }
                          variant {
                            id
                            price
                            compareAtPrice
                            image {
                              url
                            }
                          }
                          product {
                            id
                            handle
                            productType
                            tags
                          }
                        }
                      }
                    }
                    returns(first: 10) {
                      edges {
                        node {
                          id
                          status
                          returnLineItems(first: 50) {
                            edges {
                              node {
                                id
                                quantity
                                fulfillmentLineItem {
                                  id
                                  lineItem {
                                    id
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            
            variables = {"orderName": f"#{order_name}"}
            
            # Make GraphQL request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://{shop_domain}/admin/api/{self.api_version}/graphql.json",
                    headers={
                        "X-Shopify-Access-Token": access_token,
                        "Content-Type": "application/json"
                    },
                    json={"query": query, "variables": variables}
                ) as response:
                    
                    if response.status != 200:
                        logger.error(f"GraphQL request failed: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    if "errors" in data:
                        logger.error(f"GraphQL errors: {data['errors']}")
                        return None
                    
                    orders = data.get("data", {}).get("orders", {}).get("edges", [])
                    
                    # Find order with matching email
                    for order_edge in orders:
                        order = order_edge["node"]
                        order_customer = order.get("customer")
                        
                        if not order_customer:
                            continue
                            
                        if order_customer.get("email", "").lower() == customer_email.lower():
                            # Found matching order, process and return
                            return await self._process_order_for_returns(order)
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Order lookup error: {e}")
            return None
    
    async def _process_order_for_returns(self, shopify_order: Dict) -> Dict[str, Any]:
        """Process Shopify order and compute return eligibility"""
        try:
            # Calculate return window
            created_at = datetime.fromisoformat(shopify_order["createdAt"].replace("Z", "+00:00"))
            days_since_order = (datetime.utcnow() - created_at.replace(tzinfo=None)).days
            return_window_days = 30  # Default, should come from policy
            days_remaining = max(0, return_window_days - days_since_order)
            
            # Get already returned quantities
            returned_quantities = {}
            for return_edge in shopify_order.get("returns", {}).get("edges", []):
                return_node = return_edge["node"]
                if return_node.get("status") in ["REQUESTED", "IN_PROGRESS", "CLOSED"]:
                    for return_item_edge in return_node.get("returnLineItems", {}).get("edges", []):
                        return_item = return_item_edge["node"]
                        line_item_id = return_item.get("fulfillmentLineItem", {}).get("lineItem", {}).get("id")
                        if line_item_id:
                            returned_quantities[line_item_id] = returned_quantities.get(line_item_id, 0) + return_item.get("quantity", 0)
            
            # Process line items
            eligible_items = []
            for item_edge in shopify_order.get("lineItems", {}).get("edges", []):
                item = item_edge["node"]
                line_item_id = item["id"]
                
                # Calculate eligible quantity
                ordered_qty = item.get("quantity", 0)
                returned_qty = returned_quantities.get(line_item_id, 0)
                max_return_qty = max(0, ordered_qty - returned_qty)
                
                # Determine eligibility
                eligible = max_return_qty > 0 and days_remaining > 0
                
                # Check exclusions (basic implementation)
                product_tags = item.get("product", {}).get("tags", [])
                if isinstance(product_tags, list) and "final-sale" in [tag.lower() for tag in product_tags]:
                    eligible = False
                
                eligible_items.append({
                    "id": line_item_id,
                    "title": item.get("title", ""),
                    "sku": item.get("sku", ""),
                    "variant": item.get("variantTitle", ""),
                    "quantity": ordered_qty,
                    "fulfillmentStatus": item.get("fulfillmentStatus", ""),
                    "eligibleForReturn": eligible,
                    "maxReturnQty": max_return_qty,
                    "price": float(item.get("variant", {}).get("price", "0")),
                    "imageUrl": item.get("image", {}).get("url", "") or item.get("variant", {}).get("image", {}).get("url", "")
                })
            
            # Build response
            return {
                "id": shopify_order["id"],
                "name": shopify_order["name"],
                "createdAt": shopify_order["createdAt"],
                "currency": shopify_order["currencyCode"],
                "totalPrice": float(shopify_order.get("totalPriceSet", {}).get("shopMoney", {}).get("amount", "0")),
                "customer": {
                    "email": shopify_order.get("customer", {}).get("email", ""),
                    "firstName": shopify_order.get("customer", {}).get("firstName", ""),
                    "lastName": shopify_order.get("customer", {}).get("lastName", "")
                },
                "lineItems": eligible_items,
                "deliveryStatus": shopify_order.get("displayFulfillmentStatus", ""),
                "returnWindow": {
                    "daysRemaining": days_remaining,
                    "eligible": days_remaining > 0 and len([item for item in eligible_items if item["eligibleForReturn"]]) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Process order error: {e}")
            return None

# Singleton instance
shopify_graphql_service = ShopifyGraphQLService