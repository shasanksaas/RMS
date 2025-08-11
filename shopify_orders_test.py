#!/usr/bin/env python3
"""
Shopify Real Orders Discovery Test
Help find actual order numbers in the user's Shopify store (rms34.myshopify.com)
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://2df859a5-1f9c-46d3-81c6-dff0c2023545.preview.emergentagent.com/api"
SHOPIFY_STORE = "rms34.myshopify.com"
TENANT_ID = "tenant-rms34"

class ShopifyOrdersDiscovery:
    def __init__(self):
        self.session = None
        self.real_orders = []
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        if data and success:
            print(f"   Data: {json.dumps(data, indent=2)[:200]}...")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "data": data
        })
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    response_data = await response.json()
                    return response.status < 400, response_data, response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    response_data = await response.json()
                    return response.status < 400, response_data, response.status
                    
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    async def test_shopify_connectivity(self):
        """Test Shopify connectivity to rms34.myshopify.com"""
        print("\n🔗 Testing Shopify Connectivity...")
        
        # Test 1: Quick connectivity test
        success, response, status = await self.make_request("GET", "/shopify-test/quick-test")
        
        if success and response.get("shop_connected"):
            self.log_test("Shopify Connectivity: Quick Test", True, 
                         f"Connected to {response.get('shop_domain', 'unknown')}")
            
            # Check if products are accessible
            if response.get("products_accessible"):
                product_count = len(response.get("products", []))
                self.log_test("Shopify Connectivity: Products Access", True, 
                             f"Retrieved {product_count} products from store")
            else:
                self.log_test("Shopify Connectivity: Products Access", False, 
                             "Cannot access products from store")
        else:
            self.log_test("Shopify Connectivity: Quick Test", False, 
                         f"Failed to connect to Shopify store. Status: {status}")
            return False
        
        return True
    
    async def test_shopify_orders_query(self):
        """Test GraphQL orders query to get real orders"""
        print("\n📦 Testing Shopify Orders Query...")
        
        # Test 1: Raw GraphQL query for orders
        orders_query = """
        query getOrders($first: Int!) {
          orders(first: $first, sortKey: CREATED_AT, reverse: true) {
            edges {
              node {
                id
                name
                email
                createdAt
                updatedAt
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
                lineItems(first: 10) {
                  edges {
                    node {
                      id
                      title
                      quantity
                      variant {
                        id
                        title
                        sku
                        price
                      }
                    }
                  }
                }
                fulfillments(first: 5) {
                  id
                  status
                  trackingNumber
                  createdAt
                }
              }
            }
          }
        }
        """
        
        query_data = {
            "query": orders_query,
            "variables": {"first": 10}
        }
        
        success, response, status = await self.make_request("POST", "/shopify-test/raw-query", query_data)
        
        if success and response.get("data", {}).get("orders"):
            orders_data = response["data"]["orders"]["edges"]
            self.log_test("Shopify Orders Query: Raw GraphQL", True, 
                         f"Retrieved {len(orders_data)} orders from Shopify")
            
            # Extract real order information
            for edge in orders_data:
                order = edge["node"]
                order_info = {
                    "order_number": order.get("name", "Unknown"),
                    "customer_email": order.get("email", "No email"),
                    "customer_name": f"{order.get('customer', {}).get('firstName', '')} {order.get('customer', {}).get('lastName', '')}".strip() or "Unknown Customer",
                    "total_amount": order.get("totalPriceSet", {}).get("shopMoney", {}).get("amount", "0"),
                    "currency": order.get("totalPriceSet", {}).get("shopMoney", {}).get("currencyCode", "USD"),
                    "created_at": order.get("createdAt", "Unknown"),
                    "line_items": []
                }
                
                # Extract line items
                for item_edge in order.get("lineItems", {}).get("edges", []):
                    item = item_edge["node"]
                    order_info["line_items"].append({
                        "title": item.get("title", "Unknown Product"),
                        "quantity": item.get("quantity", 0),
                        "sku": item.get("variant", {}).get("sku", "No SKU"),
                        "price": item.get("variant", {}).get("price", "0")
                    })
                
                self.real_orders.append(order_info)
            
            return True
        else:
            self.log_test("Shopify Orders Query: Raw GraphQL", False, 
                         f"Failed to retrieve orders. Status: {status}, Response: {response}")
            return False
    
    async def test_full_connectivity_suite(self):
        """Test full connectivity suite to get comprehensive data"""
        print("\n🔍 Testing Full Connectivity Suite...")
        
        success, response, status = await self.make_request("GET", "/shopify-test/full-connectivity")
        
        if success and response.get("overall_success"):
            self.log_test("Full Connectivity Suite: Overall", True, 
                         f"Success rate: {response.get('success_rate', 0)}%")
            
            # Check individual operations
            operations = response.get("operations", {})
            
            # Shop info
            if operations.get("shop_info", {}).get("success"):
                shop_data = operations["shop_info"]["data"]
                self.log_test("Full Connectivity: Shop Info", True, 
                             f"Shop: {shop_data.get('name', 'Unknown')} - {shop_data.get('domain', 'Unknown')}")
            
            # Products query
            if operations.get("products_query", {}).get("success"):
                products_data = operations["products_query"]["data"]
                product_count = len(products_data.get("products", {}).get("edges", []))
                self.log_test("Full Connectivity: Products Query", True, 
                             f"Retrieved {product_count} products")
            
            # Orders query - This is what we're most interested in
            if operations.get("orders_query", {}).get("success"):
                orders_data = operations["orders_query"]["data"]
                orders_edges = orders_data.get("orders", {}).get("edges", [])
                self.log_test("Full Connectivity: Orders Query", True, 
                             f"Retrieved {len(orders_edges)} orders")
                
                # Extract order details for user testing
                for edge in orders_edges:
                    order = edge["node"]
                    order_info = {
                        "order_number": order.get("name", "Unknown"),
                        "customer_email": order.get("email", "No email"),
                        "customer_name": f"{order.get('customer', {}).get('firstName', '')} {order.get('customer', {}).get('lastName', '')}".strip() or "Unknown Customer",
                        "total_amount": order.get("totalPriceSet", {}).get("shopMoney", {}).get("amount", "0"),
                        "currency": order.get("totalPriceSet", {}).get("shopMoney", {}).get("currencyCode", "USD"),
                        "created_at": order.get("createdAt", "Unknown"),
                        "line_items": []
                    }
                    
                    # Extract line items with more details
                    for item_edge in order.get("lineItems", {}).get("edges", []):
                        item = item_edge["node"]
                        order_info["line_items"].append({
                            "title": item.get("title", "Unknown Product"),
                            "quantity": item.get("quantity", 0),
                            "sku": item.get("variant", {}).get("sku", "No SKU"),
                            "price": item.get("variant", {}).get("price", "0"),
                            "variant_title": item.get("variant", {}).get("title", "")
                        })
                    
                    self.real_orders.append(order_info)
            else:
                self.log_test("Full Connectivity: Orders Query", False, 
                             "Failed to retrieve orders from full connectivity test")
            
            # Returns query
            if operations.get("returns_query", {}).get("success"):
                returns_data = operations["returns_query"]["data"]
                returns_count = len(returns_data.get("returns", {}).get("edges", []))
                self.log_test("Full Connectivity: Returns Query", True, 
                             f"Retrieved {returns_count} existing returns")
            
            # Customers query
            if operations.get("customers_query", {}).get("success"):
                customers_data = operations["customers_query"]["data"]
                customers_count = len(customers_data.get("customers", {}).get("edges", []))
                self.log_test("Full Connectivity: Customers Query", True, 
                             f"Retrieved {customers_count} customers")
            
            return True
        else:
            self.log_test("Full Connectivity Suite: Overall", False, 
                         f"Failed connectivity suite. Status: {status}")
            return False
    
    async def test_synced_orders_in_database(self):
        """Check if there are synced orders in the database for tenant-rms34"""
        print("\n💾 Testing Synced Orders in Database...")
        
        # Test with tenant-rms34 header
        headers = {"X-Tenant-Id": TENANT_ID}
        success, response, status = await self.make_request("GET", "/orders?limit=20", headers=headers)
        
        if success and response.get("items"):
            orders = response["items"]
            self.log_test("Database Orders: Synced Data", True, 
                         f"Found {len(orders)} synced orders for {TENANT_ID}")
            
            # Extract synced order information
            for order in orders:
                order_info = {
                    "order_number": order.get("order_number", order.get("name", "Unknown")),
                    "customer_email": order.get("customer_email", order.get("email", "No email")),
                    "customer_name": order.get("customer_name", "Unknown Customer"),
                    "total_amount": str(order.get("total_price", "0")),
                    "currency": order.get("currency_code", "USD"),
                    "created_at": order.get("created_at", "Unknown"),
                    "shopify_order_id": order.get("order_id", "No Shopify ID"),
                    "line_items": order.get("line_items", [])
                }
                
                # Add to real orders if not already present
                if not any(existing["order_number"] == order_info["order_number"] for existing in self.real_orders):
                    self.real_orders.append(order_info)
            
            return True
        else:
            self.log_test("Database Orders: Synced Data", False, 
                         f"No synced orders found for {TENANT_ID}. Status: {status}")
            return False
    
    async def test_customer_portal_lookup(self):
        """Test customer portal order lookup with real data"""
        print("\n🔍 Testing Customer Portal Order Lookup...")
        
        if not self.real_orders:
            self.log_test("Customer Portal: No real orders available for testing", False)
            return
        
        # Test with the first real order
        test_order = self.real_orders[0]
        
        if test_order["customer_email"] and test_order["customer_email"] != "No email":
            lookup_data = {
                "order_number": test_order["order_number"],
                "email": test_order["customer_email"]
            }
            
            success, response, status = await self.make_request("POST", "/orders/lookup", lookup_data)
            
            if success:
                self.log_test("Customer Portal: Order Lookup", True, 
                             f"Successfully looked up order {test_order['order_number']} for {test_order['customer_email']}")
            else:
                self.log_test("Customer Portal: Order Lookup", False, 
                             f"Failed to lookup order. Status: {status}")
        else:
            self.log_test("Customer Portal: Order Lookup", False, 
                         "No valid customer email found in real orders")
    
    def display_real_orders_summary(self):
        """Display summary of real orders found"""
        print("\n" + "=" * 80)
        print("🎯 REAL SHOPIFY ORDERS FOUND FOR TESTING")
        print("=" * 80)
        
        if not self.real_orders:
            print("❌ No real orders found in the Shopify store")
            print("   This could mean:")
            print("   • The store has no orders yet")
            print("   • Orders are not accessible with current permissions")
            print("   • There's a connectivity issue")
            return
        
        print(f"✅ Found {len(self.real_orders)} real orders in rms34.myshopify.com")
        print("\n📋 ORDER DETAILS FOR TESTING:")
        
        for i, order in enumerate(self.real_orders[:10], 1):  # Show first 10 orders
            print(f"\n{i}. Order #{order['order_number']}")
            print(f"   📧 Customer Email: {order['customer_email']}")
            print(f"   👤 Customer Name: {order['customer_name']}")
            print(f"   💰 Total: {order['currency']} {order['total_amount']}")
            print(f"   📅 Created: {order['created_at']}")
            
            if order['line_items']:
                print(f"   📦 Products ({len(order['line_items'])} items):")
                for item in order['line_items'][:3]:  # Show first 3 items
                    print(f"      • {item.get('title', 'Unknown')} (Qty: {item.get('quantity', 0)}) - SKU: {item.get('sku', 'No SKU')}")
                if len(order['line_items']) > 3:
                    print(f"      ... and {len(order['line_items']) - 3} more items")
            else:
                print("   📦 No line items data available")
        
        if len(self.real_orders) > 10:
            print(f"\n... and {len(self.real_orders) - 10} more orders")
        
        print("\n🧪 TESTING RECOMMENDATIONS:")
        print("Use these real order numbers and customer emails to test:")
        print("1. Customer portal order lookup")
        print("2. Return creation process")
        print("3. Policy preview functionality")
        
        # Show best orders for testing
        valid_orders = [order for order in self.real_orders if order['customer_email'] != "No email" and order['line_items']]
        
        if valid_orders:
            print(f"\n⭐ BEST ORDERS FOR TESTING (with email and products):")
            for i, order in enumerate(valid_orders[:5], 1):
                print(f"{i}. Order #{order['order_number']} - {order['customer_email']}")
        else:
            print("\n⚠️  WARNING: No orders found with both customer email and product data")
            print("   You may need to create test orders in your Shopify store")
    
    async def run_discovery(self):
        """Run the complete Shopify orders discovery process"""
        print("🚀 Starting Shopify Real Orders Discovery")
        print(f"🏪 Target Store: {SHOPIFY_STORE}")
        print(f"🏷️  Tenant ID: {TENANT_ID}")
        print("=" * 80)
        
        # Test connectivity first
        if not await self.test_shopify_connectivity():
            print("❌ Cannot connect to Shopify store. Aborting discovery.")
            return
        
        # Try multiple methods to get real orders
        await self.test_shopify_orders_query()
        await self.test_full_connectivity_suite()
        await self.test_synced_orders_in_database()
        
        # Test customer portal functionality with real data
        await self.test_customer_portal_lookup()
        
        # Display results
        self.display_real_orders_summary()
        
        # Print test summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test execution summary"""
        print("\n" + "=" * 80)
        print("📊 DISCOVERY TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")

async def main():
    """Main discovery execution"""
    async with ShopifyOrdersDiscovery() as discovery:
        await discovery.run_discovery()

if __name__ == "__main__":
    asyncio.run(main())