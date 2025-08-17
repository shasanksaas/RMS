#!/usr/bin/env python3
"""
FOCUSED DUPLICATE INVESTIGATION - API Response Analysis
Tests the /api/returns/ endpoint for tenant-rms34 to identify exact duplicate patterns
"""

import asyncio
import aiohttp
import json
from collections import Counter, defaultdict
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://shopify-sync-fix.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"

class FocusedDuplicateAnalysis:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_all_returns(self) -> List[Dict]:
        """Get all returns from the API"""
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        url = f"{BACKEND_URL}/returns/"
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('returns', [])
            else:
                print(f"❌ Failed to get returns: {response.status}")
                return []
    
    async def analyze_duplicates(self):
        """Analyze the exact duplicate patterns"""
        print("🔍 FOCUSED DUPLICATE ANALYSIS FOR TENANT-RMS34")
        print("=" * 60)
        
        returns = await self.get_all_returns()
        
        if not returns:
            print("❌ No returns data retrieved")
            return
        
        print(f"📊 Total returns retrieved: {len(returns)}")
        
        # Analysis 1: Duplicate Return IDs
        print(f"\n1️⃣ DUPLICATE RETURN IDs ANALYSIS")
        print("-" * 40)
        
        return_ids = [ret.get('id') for ret in returns]
        id_counts = Counter(return_ids)
        duplicate_ids = {id: count for id, count in id_counts.items() if count > 1}
        
        if duplicate_ids:
            print(f"🚨 FOUND {len(duplicate_ids)} DUPLICATE RETURN IDs:")
            for ret_id, count in duplicate_ids.items():
                print(f"   ID: {ret_id} appears {count} times")
        else:
            print("✅ No duplicate return IDs found")
        
        # Analysis 2: Duplicate Order Numbers + Customer Combinations
        print(f"\n2️⃣ DUPLICATE ORDER + CUSTOMER COMBINATIONS")
        print("-" * 40)
        
        order_customer_combos = []
        for ret in returns:
            combo = f"{ret.get('order_number')}|{ret.get('customer_email')}"
            order_customer_combos.append(combo)
        
        combo_counts = Counter(order_customer_combos)
        duplicate_combos = {combo: count for combo, count in combo_counts.items() if count > 1}
        
        if duplicate_combos:
            print(f"🚨 FOUND {len(duplicate_combos)} DUPLICATE ORDER+CUSTOMER COMBINATIONS:")
            for combo, count in duplicate_combos.items():
                order_num, email = combo.split('|')
                print(f"   Order {order_num} + {email}: {count} returns")
                
                # Show the actual return IDs for this combination
                matching_returns = [ret for ret in returns 
                                  if ret.get('order_number') == order_num and ret.get('customer_email') == email]
                return_ids = [ret.get('id') for ret in matching_returns]
                print(f"      Return IDs: {return_ids}")
                
                # Show status and timestamps
                for ret in matching_returns[:3]:  # Show first 3
                    print(f"      - ID: {ret.get('id')}, Status: {ret.get('status')}, Created: {ret.get('created_at')}")
        else:
            print("✅ No duplicate order+customer combinations found")
        
        # Analysis 3: Identical Return Objects
        print(f"\n3️⃣ IDENTICAL RETURN OBJECTS ANALYSIS")
        print("-" * 40)
        
        return_signatures = defaultdict(list)
        for ret in returns:
            # Create signature based on key business fields
            signature = (
                ret.get('order_number'),
                ret.get('customer_email'),
                ret.get('status'),
                ret.get('estimated_refund'),
                ret.get('item_count')
            )
            return_signatures[signature].append(ret.get('id'))
        
        identical_groups = {sig: ids for sig, ids in return_signatures.items() if len(ids) > 1}
        
        if identical_groups:
            print(f"🚨 FOUND {len(identical_groups)} GROUPS OF IDENTICAL RETURNS:")
            for signature, return_ids in identical_groups.items():
                order_num, email, status, refund, items = signature
                print(f"   Group: Order {order_num}, {email}, Status: {status}")
                print(f"          Refund: ${refund}, Items: {items}")
                print(f"          Return IDs: {return_ids}")
        else:
            print("✅ No identical return objects found")
        
        # Analysis 4: Timeline Analysis
        print(f"\n4️⃣ TIMELINE ANALYSIS")
        print("-" * 40)
        
        if duplicate_combos:
            # Analyze the first duplicate combo in detail
            first_combo = list(duplicate_combos.keys())[0]
            order_num, email = first_combo.split('|')
            
            matching_returns = [ret for ret in returns 
                              if ret.get('order_number') == order_num and ret.get('customer_email') == email]
            
            print(f"📅 Timeline for Order {order_num} + {email}:")
            sorted_returns = sorted(matching_returns, key=lambda x: x.get('created_at', ''))
            
            for i, ret in enumerate(sorted_returns):
                print(f"   {i+1}. ID: {ret.get('id')}")
                print(f"      Created: {ret.get('created_at')}")
                print(f"      Updated: {ret.get('updated_at')}")
                print(f"      Status: {ret.get('status')}")
                print(f"      Decision: {ret.get('decision')}")
        
        # Analysis 5: Data Quality Check
        print(f"\n5️⃣ DATA QUALITY CHECK")
        print("-" * 40)
        
        # Check for missing or null key fields
        issues = []
        for ret in returns:
            if not ret.get('id'):
                issues.append("Missing return ID")
            if not ret.get('order_number'):
                issues.append("Missing order number")
            if not ret.get('customer_email'):
                issues.append("Missing customer email")
        
        if issues:
            print(f"🚨 DATA QUALITY ISSUES:")
            issue_counts = Counter(issues)
            for issue, count in issue_counts.items():
                print(f"   {issue}: {count} occurrences")
        else:
            print("✅ No data quality issues found")
        
        # Final Summary
        print(f"\n🎯 DUPLICATE INVESTIGATION SUMMARY")
        print("=" * 60)
        
        total_duplicates = len(duplicate_ids) + len(duplicate_combos) + len(identical_groups)
        
        if total_duplicates > 0:
            print(f"🚨 DUPLICATES CONFIRMED:")
            print(f"   • Duplicate Return IDs: {len(duplicate_ids)}")
            print(f"   • Duplicate Order+Customer: {len(duplicate_combos)}")
            print(f"   • Identical Return Objects: {len(identical_groups)}")
            print(f"   • Total Duplicate Issues: {total_duplicates}")
            
            print(f"\n💡 ROOT CAUSE ANALYSIS:")
            if duplicate_ids:
                print(f"   • Same return ID appearing multiple times = Database integrity issue")
            if duplicate_combos:
                print(f"   • Multiple returns for same order+customer = Business logic issue")
            if identical_groups:
                print(f"   • Identical return objects = Data insertion duplication")
            
            print(f"\n🔧 RECOMMENDED FIXES:")
            print(f"   1. Add unique constraints on return IDs in database")
            print(f"   2. Implement deduplication logic in API response")
            print(f"   3. Add business rule validation to prevent multiple returns for same order")
            print(f"   4. Review return creation process for duplicate insertion")
        else:
            print(f"✅ NO DUPLICATES FOUND - Backend data is clean")
            print(f"   The duplicate issue reported by user is likely in frontend rendering")

async def main():
    """Main analysis execution"""
    async with FocusedDuplicateAnalysis() as analysis:
        await analysis.analyze_duplicates()

if __name__ == "__main__":
    asyncio.run(main())