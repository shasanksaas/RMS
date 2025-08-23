#!/usr/bin/env python3
"""
Comprehensive Customer Email Field Analysis
Analyzes all possible customer email fields in Shopify orders
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://returnflow-4.preview.emergentagent.com/api"
TARGET_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TARGET_TENANT_ID
}

async def analyze_customer_fields():
    """Analyze customer fields in orders"""
    print("🔍 ANALYZING CUSTOMER EMAIL FIELDS IN SHOPIFY ORDERS")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        # Get orders
        async with session.get(f"{BACKEND_URL}/orders", headers=TEST_HEADERS) as response:
            if response.status != 200:
                print(f"❌ Failed to get orders: {response.status}")
                return
            
            data = await response.json()
            orders = data.get("items", [])
            
            print(f"📋 Found {len(orders)} orders to analyze")
            
            for i, order in enumerate(orders):
                print(f"\n--- ORDER {i+1} ---")
                print(f"Order Number: {order.get('order_number', 'N/A')}")
                print(f"Order ID: {order.get('id', 'N/A')}")
                
                # Check all possible customer fields
                customer_fields = {}
                for key, value in order.items():
                    if 'customer' in key.lower() or 'email' in key.lower():
                        customer_fields[key] = value
                
                print(f"Customer-related fields:")
                for field, value in customer_fields.items():
                    print(f"  - {field}: '{value}'")
                
                # Check if there's customer data in nested objects
                if 'customer' in order:
                    print(f"Customer object: {order['customer']}")
                
                # Check billing/shipping addresses for email
                for addr_type in ['billing_address', 'shipping_address']:
                    if addr_type in order and order[addr_type]:
                        addr = order[addr_type]
                        if isinstance(addr, dict) and 'email' in addr:
                            print(f"  - {addr_type}.email: '{addr['email']}'")
                
                # Check line items for any customer info
                line_items = order.get('line_items', [])
                print(f"Line items count: {len(line_items)}")
                
                if line_items and len(line_items) > 0:
                    # Check first line item for any customer-related fields
                    first_item = line_items[0]
                    item_customer_fields = {}
                    for key, value in first_item.items():
                        if 'customer' in key.lower() or 'email' in key.lower():
                            item_customer_fields[key] = value
                    
                    if item_customer_fields:
                        print(f"Line item customer fields: {item_customer_fields}")

if __name__ == "__main__":
    asyncio.run(analyze_customer_fields())