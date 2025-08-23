#!/usr/bin/env python3
"""
Detailed Customer Portal Order Lookup Testing
Tests the order lookup functionality with detailed data verification
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://returnflow-4.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class DetailedOrderLookupTest:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_detailed_order_lookup(self):
        """Test detailed order lookup with data structure verification"""
        print("🔍 DETAILED ORDER LOOKUP TESTING")
        print("=" * 60)
        
        # Test specific order numbers
        test_orders = ["1001", "1002", "1003", "1004"]
        
        for order_number in test_orders:
            print(f"\n📋 Testing Order #{order_number}")
            print("-" * 40)
            
            # Test order lookup
            payload = {"order_number": order_number}
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/elite/portal/returns/lookup-order",
                    headers=TEST_HEADERS,
                    json=payload
                ) as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    print(f"Success: {data.get('success', False)}")
                    print(f"Mode: {data.get('mode', 'unknown')}")
                    
                    if data.get('success') and data.get('order'):
                        order_data = data['order']
                        print(f"Order ID: {order_data.get('id', 'N/A')}")
                        print(f"Customer Email: {order_data.get('customer_email', 'N/A')}")
                        print(f"Customer Name: {order_data.get('customer_name', 'N/A')}")
                        print(f"Total Price: ${order_data.get('total_price', 0)}")
                        print(f"Line Items: {len(order_data.get('line_items', []))}")
                        print(f"Created At: {order_data.get('created_at', 'N/A')}")
                        
                        # Check if order has line items for return eligibility
                        line_items = order_data.get('line_items', [])
                        if line_items:
                            print(f"✅ Order has {len(line_items)} line items - eligible for returns")
                            # Show first line item details
                            first_item = line_items[0]
                            print(f"   First item: {first_item.get('title', 'N/A')} - Qty: {first_item.get('quantity', 0)}")
                        else:
                            print("⚠️  Order has no line items - may affect return creation")
                    else:
                        print(f"❌ Lookup failed: {data.get('message', 'No message')}")
                        
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        # Test with email verification for order 2001 (which has an email)
        print(f"\n📧 Testing Order #2001 with Email Verification")
        print("-" * 40)
        
        payload = {
            "order_number": "2001",
            "customer_email": "demo@example.com"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/elite/portal/returns/lookup-order",
                headers=TEST_HEADERS,
                json=payload
            ) as response:
                data = await response.json()
                
                print(f"Status: {response.status}")
                print(f"Success: {data.get('success', False)}")
                print(f"Mode: {data.get('mode', 'unknown')}")
                
                if data.get('success'):
                    print("✅ Email verification successful")
                else:
                    print(f"❌ Email verification failed: {data.get('message', 'No message')}")
                    
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # Test policy preview functionality
        print(f"\n🔍 Testing Policy Preview")
        print("-" * 40)
        
        policy_payload = {
            "order_id": "test_order",
            "items": [
                {
                    "sku": "TEST-SKU-001",
                    "title": "Test Product",
                    "quantity": 1,
                    "unit_price": 100.0,
                    "reason": "defective"
                }
            ]
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/elite/portal/returns/policy-preview",
                headers=TEST_HEADERS,
                json=policy_payload
            ) as response:
                data = await response.json()
                
                print(f"Status: {response.status}")
                print(f"Success: {data.get('success', False)}")
                
                if data.get('success') and data.get('preview'):
                    preview = data['preview']
                    print(f"✅ Policy preview working")
                    print(f"   Estimated Refund: ${preview.get('estimated_refund', 0)}")
                    print(f"   Processing Fee: ${preview.get('processing_fee', 0)}")
                    print(f"   Return Window: {preview.get('return_window_days', 'N/A')} days")
                else:
                    print(f"❌ Policy preview failed: {data}")
                    
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print(f"\n🎯 DETAILED TESTING COMPLETE!")


async def main():
    """Main test execution"""
    async with DetailedOrderLookupTest() as test:
        await test.test_detailed_order_lookup()


if __name__ == "__main__":
    asyncio.run(main())