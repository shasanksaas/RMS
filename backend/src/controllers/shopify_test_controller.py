"""
Shopify Connectivity Test Controller
Creates repeatable test endpoint to verify Shopify connection with real queries
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import httpx
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shopify-test", tags=["shopify-test"])

# Real Shopify credentials from updated user credentials
SHOPIFY_STORE = "rms34.myshopify.com"
SHOPIFY_ACCESS_TOKEN = "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"
SHOPIFY_API_VERSION = "2025-07"
SHOPIFY_GRAPHQL_URL = f"https://{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"

class ShopifyConnectivityTester:
    """Test Shopify connectivity with real GraphQL queries"""
    
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
        }
    
    async def execute_graphql_query(self, query: str, variables: Dict = None) -> Dict[str, Any]:
        """Execute a GraphQL query against Shopify"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    SHOPIFY_GRAPHQL_URL,
                    json=payload,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {
                        "success": False, 
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    async def test_shop_info(self) -> Dict[str, Any]:
        """Test basic shop information query"""
        query = """
        {
          shop {
            id
            name
            email
            domain
            myshopifyDomain
            currencyCode
            timezone
            plan {
              displayName
            }
          }
        }
        """
        
        result = await self.execute_graphql_query(query)
        if result["success"]:
            shop_data = result["data"].get("data", {}).get("shop", {})
            return {
                "test": "shop_info",
                "success": True,
                "data": {
                    "shop_name": shop_data.get("name"),
                    "domain": shop_data.get("domain"),
                    "myshopify_domain": shop_data.get("myshopifyDomain"),
                    "currency": shop_data.get("currencyCode"),
                    "timezone": shop_data.get("timezone"),
                    "plan": shop_data.get("plan", {}).get("displayName")
                }
            }
        else:
            return {"test": "shop_info", "success": False, "error": result["error"]}
    
    async def test_products_query(self) -> Dict[str, Any]:
        """Test products query - same as your curl command"""
        query = """
        {
          products(first: 3) {
            edges {
              node {
                id
                title
                handle
                status
                createdAt
                updatedAt
                variants(first: 3) {
                  edges {
                    node {
                      id
                      title
                      price
                      sku
                      inventoryQuantity
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        result = await self.execute_graphql_query(query)
        if result["success"]:
            products_data = result["data"].get("data", {}).get("products", {}).get("edges", [])
            products = []
            
            for product_edge in products_data:
                product = product_edge["node"]
                variants = [
                    {
                        "id": variant["node"]["id"],
                        "title": variant["node"]["title"],
                        "price": variant["node"]["price"],
                        "sku": variant["node"]["sku"],
                        "inventory": variant["node"]["inventoryQuantity"]
                    }
                    for variant in product.get("variants", {}).get("edges", [])
                ]
                
                products.append({
                    "id": product["id"],
                    "title": product["title"],
                    "handle": product["handle"],
                    "status": product["status"],
                    "created_at": product["createdAt"],
                    "variants_count": len(variants),
                    "variants": variants
                })
            
            return {
                "test": "products_query",
                "success": True,
                "data": {
                    "products_count": len(products),
                    "products": products
                }
            }
        else:
            return {"test": "products_query", "success": False, "error": result["error"]}
    
    async def test_orders_query(self) -> Dict[str, Any]:
        """Test orders query"""
        query = """
        {
          orders(first: 5, sortKey: CREATED_AT, reverse: true) {
            edges {
              node {
                id
                name
                email
                createdAt
                updatedAt
                displayFinancialStatus
                displayFulfillmentStatus
                totalPriceSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                customer {
                  id
                  firstName
                  lastName
                  email
                }
                lineItems(first: 3) {
                  edges {
                    node {
                      id
                      title
                      quantity
                      variant {
                        id
                        title
                        price
                        sku
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        result = await self.execute_graphql_query(query)
        if result["success"]:
            orders_data = result["data"].get("data", {}).get("orders", {}).get("edges", [])
            orders = []
            
            for order_edge in orders_data:
                order = order_edge["node"]
                customer = order.get("customer") or {}
                total_price = order.get("totalPriceSet", {}).get("shopMoney", {})
                
                line_items = []
                for item_edge in order.get("lineItems", {}).get("edges", []):
                    item = item_edge["node"]
                    variant = item.get("variant") or {}
                    line_items.append({
                        "title": item["title"],
                        "quantity": item["quantity"],
                        "variant_title": variant.get("title"),
                        "price": variant.get("price"),
                        "sku": variant.get("sku")
                    })
                
                orders.append({
                    "id": order["id"],
                    "order_number": order["name"],
                    "customer_email": order.get("email"),
                    "customer_name": f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip(),
                    "financial_status": order["displayFinancialStatus"],
                    "fulfillment_status": order["displayFulfillmentStatus"],
                    "total_amount": total_price.get("amount"),
                    "currency": total_price.get("currencyCode"),
                    "created_at": order["createdAt"],
                    "line_items_count": len(line_items),
                    "line_items": line_items
                })
            
            return {
                "test": "orders_query",
                "success": True,
                "data": {
                    "orders_count": len(orders),
                    "orders": orders
                }
            }
        else:
            return {"test": "orders_query", "success": False, "error": result["error"]}
    
    async def test_returns_query(self) -> Dict[str, Any]:
        """Test returns query - RMS specific"""
        query = """
        {
          orders(first: 5, query: "returnStatus:REQUESTED OR returnStatus:OPEN") {
            edges {
              node {
                id
                name
                returnStatus
                returns(first: 3) {
                  edges {
                    node {
                      id
                      status
                      name
                      totalQuantity
                      returnLineItems(first: 5) {
                        edges {
                          node {
                            ... on ReturnLineItem {
                              id
                              quantity
                              returnReason
                              returnReasonNote
                              fulfillmentLineItem {
                                lineItem {
                                  title
                                  sku
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
        }
        """
        
        result = await self.execute_graphql_query(query)
        if result["success"]:
            orders_data = result["data"].get("data", {}).get("orders", {}).get("edges", [])
            orders_with_returns = []
            
            for order_edge in orders_data:
                order = order_edge["node"]
                returns = []
                
                for return_edge in order.get("returns", {}).get("edges", []):
                    return_data = return_edge["node"]
                    return_line_items = []
                    
                    for item_edge in return_data.get("returnLineItems", {}).get("edges", []):
                        item = item_edge["node"]
                        line_item = item.get("fulfillmentLineItem", {}).get("lineItem", {})
                        return_line_items.append({
                            "quantity": item["quantity"],
                            "return_reason": item["returnReason"],
                            "return_reason_note": item["returnReasonNote"],
                            "product_title": line_item.get("title"),
                            "sku": line_item.get("sku")
                        })
                    
                    returns.append({
                        "id": return_data["id"],
                        "status": return_data["status"],
                        "name": return_data["name"],
                        "total_quantity": return_data["totalQuantity"],
                        "return_line_items": return_line_items
                    })
                
                if returns:  # Only include orders with returns
                    orders_with_returns.append({
                        "order_id": order["id"],
                        "order_number": order["name"],
                        "return_status": order["returnStatus"],
                        "returns_count": len(returns),
                        "returns": returns
                    })
            
            return {
                "test": "returns_query",
                "success": True,
                "data": {
                    "orders_with_returns_count": len(orders_with_returns),
                    "orders_with_returns": orders_with_returns
                }
            }
        else:
            return {"test": "returns_query", "success": False, "error": result["error"]}
    
    async def test_customers_query(self) -> Dict[str, Any]:
        """Test customers query"""
        query = """
        {
          customers(first: 3) {
            edges {
              node {
                id
                firstName
                lastName
                email
                phone
                createdAt
                ordersCount
                totalSpentV2 {
                  amount
                  currencyCode
                }
              }
            }
          }
        }
        """
        
        result = await self.execute_graphql_query(query)
        if result["success"]:
            customers_data = result["data"].get("data", {}).get("customers", {}).get("edges", [])
            customers = []
            
            for customer_edge in customers_data:
                customer = customer_edge["node"]
                total_spent = customer.get("totalSpentV2", {})
                
                customers.append({
                    "id": customer["id"],
                    "name": f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip(),
                    "email": customer["email"],
                    "phone": customer.get("phone"),
                    "orders_count": customer["ordersCount"],
                    "total_spent": total_spent.get("amount"),
                    "currency": total_spent.get("currencyCode"),
                    "created_at": customer["createdAt"]
                })
            
            return {
                "test": "customers_query",
                "success": True,
                "data": {
                    "customers_count": len(customers),
                    "customers": customers
                }
            }
        else:
            return {"test": "customers_query", "success": False, "error": result["error"]}

# Create singleton instance
shopify_tester = ShopifyConnectivityTester()

@router.get("/connectivity")
async def test_shopify_connectivity():
    """
    Comprehensive Shopify connectivity test endpoint
    Tests multiple GraphQL operations to verify connection works
    """
    start_time = datetime.utcnow()
    
    # Run all tests concurrently for speed
    test_tasks = [
        shopify_tester.test_shop_info(),
        shopify_tester.test_products_query(),
        shopify_tester.test_orders_query(),
        shopify_tester.test_returns_query(),
        shopify_tester.test_customers_query()
    ]
    
    try:
        results = await asyncio.gather(*test_tasks, return_exceptions=True)
        
        # Process results
        test_results = []
        success_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_results.append({
                    "test": f"test_{i}",
                    "success": False,
                    "error": str(result)
                })
            else:
                test_results.append(result)
                if result.get("success"):
                    success_count += 1
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "connectivity_test": {
                "store": SHOPIFY_STORE,
                "api_version": SHOPIFY_API_VERSION,
                "test_timestamp": start_time.isoformat(),
                "duration_seconds": duration,
                "tests_run": len(test_results),
                "tests_passed": success_count,
                "success_rate": f"{(success_count / len(test_results) * 100):.1f}%",
                "overall_success": success_count == len(test_results)
            },
            "test_results": test_results
        }
        
    except Exception as e:
        return {
            "connectivity_test": {
                "store": SHOPIFY_STORE,
                "api_version": SHOPIFY_API_VERSION,
                "test_timestamp": start_time.isoformat(),
                "overall_success": False,
                "error": f"Test execution failed: {str(e)}"
            },
            "test_results": []
        }

@router.get("/quick-test")
async def quick_shopify_test():
    """
    Quick Shopify connectivity test - just shop info and products
    """
    try:
        # Test shop info
        shop_result = await shopify_tester.test_shop_info()
        
        # Test products (your original curl query)
        products_result = await shopify_tester.test_products_query()
        
        return {
            "quick_test": {
                "store": SHOPIFY_STORE,
                "timestamp": datetime.utcnow().isoformat(),
                "shop_connected": shop_result.get("success", False),
                "products_accessible": products_result.get("success", False),
                "overall_success": shop_result.get("success", False) and products_result.get("success", False)
            },
            "shop_info": shop_result.get("data", {}),
            "products_sample": products_result.get("data", {})
        }
        
    except Exception as e:
        return {
            "quick_test": {
                "store": SHOPIFY_STORE,
                "timestamp": datetime.utcnow().isoformat(),
                "overall_success": False,
                "error": str(e)
            }
        }

@router.get("/raw-query")
async def test_raw_query():
    """
    Test the exact same query from your curl command
    """
    query = """
    {
      products(first: 3) {
        edges {
          node {
            id
            title
          }
        }
      }
    }
    """
    
    result = await shopify_tester.execute_graphql_query(query)
    
    return {
        "raw_query_test": {
            "store": SHOPIFY_STORE,
            "query_used": query.strip(),
            "timestamp": datetime.utcnow().isoformat(),
            "success": result.get("success", False)
        },
        "result": result
    }