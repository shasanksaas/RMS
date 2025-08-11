#!/usr/bin/env python3
import asyncio
import aiohttp
import time
import json

async def test_optimized_returns_api():
    print('🔍 Testing Optimized Returns API Performance & Data Completeness')
    print('=' * 70)
    
    base_url = 'http://localhost:8001'
    headers = {
        'Content-Type': 'application/json',
        'X-Tenant-Id': 'tenant-rms34'
    }
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Returns List Performance
        print('\n📊 TEST 1: Returns List Performance')
        start_time = time.time()
        
        async with session.get(f'{base_url}/api/returns/', headers=headers) as response:
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f'✅ Response Status: {response.status}')
            print(f'⚡ Response Time: {response_time:.3f}s (Target: <1s)')
            
            if response.status == 200:
                data = await response.json()
                returns = data.get('returns', [])
                pagination = data.get('pagination', {})
                
                print(f'📋 Total Returns: {pagination.get("total", 0)}')
                print(f'📄 Returns on Page: {len(returns)}')
                
                # Test data completeness
                complete_data_count = 0
                print('\n👤 Data Completeness Check:')
                
                for i, ret in enumerate(returns[:5]):  # Check first 5
                    customer_name = ret.get('customer_name', '')
                    customer_email = ret.get('customer_email', '')
                    order_number = ret.get('order_number', '')
                    estimated_refund = ret.get('estimated_refund', 0)
                    
                    data_complete = bool(customer_name and customer_email and order_number)
                    if data_complete:
                        complete_data_count += 1
                    
                    status = '✅' if data_complete else '❌'
                    print(f'  {status} Return {i+1}: {customer_name} | {customer_email} | Order: {order_number} | ${estimated_refund}')
                
                print(f'\n📈 Data Completeness: {complete_data_count}/5 returns complete')
                
                # Store first return for detail test
                test_return_id = returns[0]['id'] if returns else None
            else:
                test_return_id = None
        
        # Test 2: Individual Return Detail
        if test_return_id:
            print('\n\n🔍 TEST 2: Return Detail Performance')
            start_time = time.time()
            
            async with session.get(f'{base_url}/api/returns/{test_return_id}', headers=headers) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                print(f'✅ Response Status: {response.status}')
                print(f'⚡ Response Time: {response_time:.3f}s')
                
                if response.status == 200:
                    detail_data = await response.json()
                    customer = detail_data.get('customer', {})
                    items = detail_data.get('items', [])
                    
                    print(f'👤 Customer Name: {customer.get("name", "Missing")}')
                    print(f'📧 Customer Email: {customer.get("email", "Missing")}')
                    print(f'📦 Order Number: {detail_data.get("order_number", "Missing")}')
                    print(f'🛍️ Items Count: {len(items)}')
                    print(f'💰 Estimated Refund: ${detail_data.get("estimated_refund", 0)}')
        
        # Test 3: Search & Filter Performance
        print('\n\n🔍 TEST 3: Search & Filter Performance')
        start_time = time.time()
        
        async with session.get(f'{base_url}/api/returns/?search=test&status=REQUESTED', headers=headers) as response:
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f'✅ Search Response Status: {response.status}')
            print(f'⚡ Search Response Time: {response_time:.3f}s')
            
            if response.status == 200:
                search_data = await response.json()
                filtered_returns = search_data.get('returns', [])
                print(f'🔍 Filtered Results: {len(filtered_returns)} returns')

if __name__ == "__main__":
    asyncio.run(test_optimized_returns_api())