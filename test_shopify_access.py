"""
Test script to check what Shopify GraphQL data we can access without protected customer data approval
"""
import asyncio
import httpx
import json

async def test_shopify_graphql_access():
    """Test various GraphQL queries to see what we can access"""
    
    # Test credentials from our integration
    shop_domain = "rms34.myshopify.com"
    access_token = "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0L"  # This would normally be encrypted
    
    base_url = f"https://{shop_domain}/admin/api/2025-07/graphql.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    # Test queries for different data types
    test_queries = {
        "Shop Info": """
        query getShopInfo {
            shop {
                id
                name
                email
                domain
                myshopifyDomain
                plan {
                    displayName
                }
                billingAddress {
                    country
                    province
                    city
                }
            }
        }
        """,
        
        "Products": """
        query getProducts($first: Int!) {
            products(first: $first) {
                edges {
                    node {
                        id
                        title
                        handle
                        status
                        productType
                        vendor
                        tags
                        variants(first: 10) {
                            edges {
                                node {
                                    id
                                    title
                                    sku
                                    price
                                    inventoryQuantity
                                    availableForSale
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """,
        
        "Orders (Protected)": """
        query getOrders($first: Int!) {
            orders(first: $first) {
                edges {
                    node {
                        id
                        name
                        email
                        totalPrice
                    }
                }
            }
        }
        """,
        
        "App Installation": """
        query getCurrentAppInstallation {
            currentAppInstallation {
                id
                accessScopes {
                    handle
                }
            }
        }
        """,
        
        "Webhooks": """
        query getWebhooks($first: Int!) {
            webhookSubscriptions(first: $first) {
                edges {
                    node {
                        id
                        callbackUrl
                        topic
                        format
                        createdAt
                        updatedAt
                    }
                }
            }
        }
        """
    }
    
    async with httpx.AsyncClient() as client:
        results = {}
        
        for query_name, query in test_queries.items():
            try:
                print(f"\n🔍 Testing: {query_name}")
                
                variables = {"first": 5} if "$first" in query else {}
                
                response = await client.post(
                    base_url,
                    headers=headers,
                    json={"query": query, "variables": variables}
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "errors" in data:
                        print(f"❌ GraphQL Errors: {data['errors']}")
                        results[query_name] = {"success": False, "errors": data["errors"]}
                    else:
                        print(f"✅ Success: Got data")
                        results[query_name] = {"success": True, "data_keys": list(data.get("data", {}).keys())}
                        # Print first few keys to see what we got
                        if data.get("data"):
                            for key, value in data["data"].items():
                                if isinstance(value, dict) and "edges" in value:
                                    edge_count = len(value["edges"])
                                    print(f"   - {key}: {edge_count} items")
                                elif isinstance(value, dict):
                                    print(f"   - {key}: object with keys {list(value.keys())}")
                                else:
                                    print(f"   - {key}: {type(value)}")
                else:
                    print(f"❌ HTTP Error: {response.text}")
                    results[query_name] = {"success": False, "http_error": response.text}
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                results[query_name] = {"success": False, "exception": str(e)}
        
        print(f"\n\n📊 SUMMARY:")
        print("=" * 50)
        for query_name, result in results.items():
            status = "✅ ACCESSIBLE" if result["success"] else "❌ BLOCKED"
            print(f"{status}: {query_name}")
            if not result["success"] and "errors" in result:
                for error in result["errors"]:
                    if "ACCESS_DENIED" in error.get("extensions", {}).get("code", ""):
                        print(f"   Reason: Protected data approval required")
                    else:
                        print(f"   Reason: {error.get('message', 'Unknown error')}")
        
        return results

if __name__ == "__main__":
    asyncio.run(test_shopify_graphql_access())