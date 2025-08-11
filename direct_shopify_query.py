#!/usr/bin/env python3
"""
Direct Shopify Order Query Test
Tests direct GraphQL query to Shopify to get order with customer data
"""

import asyncio
import httpx
import json

# Shopify credentials
SHOPIFY_STORE = "rms34.myshopify.com"
SHOPIFY_ACCESS_TOKEN = "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"
SHOPIFY_API_VERSION = "2025-07"
SHOPIFY_GRAPHQL_URL = f"https://{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"

async def query_shopify_order():
    """Query Shopify directly for order data"""
    print("🔍 QUERYING SHOPIFY DIRECTLY FOR ORDER DATA")
    print("=" * 80)
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }
    
    # Query to get order with customer information
    query = """
    query getOrder($id: ID!) {
        order(id: $id) {
            id
            name
            email
            customer {
                id
                email
                firstName
                lastName
                phone
            }
            billingAddress {
                firstName
                lastName
                address1
                city
                province
                country
                zip
                phone
            }
            shippingAddress {
                firstName
                lastName
                address1
                city
                province
                country
                zip
                phone
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
                        }
                    }
                }
            }
            totalPriceSet {
                shopMoney {
                    amount
                    currencyCode
                }
            }
            createdAt
            updatedAt
            displayFulfillmentStatus
            displayFinancialStatus
        }
    }
    """
    
    # Test with order 1004 (Shopify ID: 5813756919993)
    variables = {"id": "gid://shopify/Order/5813756919993"}
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                SHOPIFY_GRAPHQL_URL,
                json=payload,
                headers=headers
            )
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response Data:")
                print(json.dumps(data, indent=2))
                
                # Extract customer information
                if 'data' in data and 'order' in data['data'] and data['data']['order']:
                    order = data['data']['order']
                    print(f"\n📋 ORDER ANALYSIS:")
                    print(f"Order Name: {order.get('name')}")
                    print(f"Order Email: {order.get('email')}")
                    
                    customer = order.get('customer')
                    if customer:
                        print(f"Customer ID: {customer.get('id')}")
                        print(f"Customer Email: {customer.get('email')}")
                        print(f"Customer Name: {customer.get('firstName')} {customer.get('lastName')}")
                        print(f"Customer Phone: {customer.get('phone')}")
                    else:
                        print("❌ No customer object found")
                    
                    billing = order.get('billingAddress')
                    if billing:
                        print(f"Billing Name: {billing.get('firstName')} {billing.get('lastName')}")
                        print(f"Billing Phone: {billing.get('phone')}")
                    
                    shipping = order.get('shippingAddress')
                    if shipping:
                        print(f"Shipping Name: {shipping.get('firstName')} {shipping.get('lastName')}")
                        print(f"Shipping Phone: {shipping.get('phone')}")
                
                else:
                    print("❌ No order data found in response")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(query_shopify_order())