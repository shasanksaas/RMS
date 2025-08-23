#!/usr/bin/env python3
"""
Comprehensive Duplicate Returns Analysis
Analyzes the current state and verifies the duplicate issue resolution
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Configuration
BACKEND_URL = "https://returnflow-4.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class ComprehensiveDuplicateAnalysis:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_api_returns(self):
        """Get returns from API"""
        url = f"{BACKEND_URL}/returns/"
        async with self.session.get(url, headers=TEST_HEADERS) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("returns", [])
            else:
                print(f"API Error: {response.status}")
                return []
    
    async def get_raw_database_returns(self):
        """Get returns directly from database"""
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        db = client['returns_management']
        
        raw_returns = await db.returns.find({'tenant_id': TEST_TENANT_ID}).to_list(100)
        client.close()
        return raw_returns
    
    def analyze_duplicates(self, returns_data, case_sensitive=True):
        """Analyze duplicates in returns data"""
        combinations = defaultdict(list)
        
        for ret in returns_data:
            order_id = ret.get("order_id", "")
            customer_email = ret.get("customer_email", "")
            
            if not case_sensitive:
                customer_email = customer_email.lower()
            
            combination_key = f"{order_id}:{customer_email}"
            combinations[combination_key].append({
                "id": ret.get("id"),
                "order_id": order_id,
                "customer_email": ret.get("customer_email"),  # Keep original case
                "created_at": ret.get("created_at"),
                "status": ret.get("status")
            })
        
        # Find duplicates
        duplicates = {k: v for k, v in combinations.items() if len(v) > 1}
        return combinations, duplicates
    
    def print_analysis_results(self, title, returns_data, combinations, duplicates):
        """Print analysis results"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        
        print(f"Total Returns: {len(returns_data)}")
        print(f"Unique Combinations: {len(combinations)}")
        print(f"Duplicate Combinations: {len(duplicates)}")
        
        if duplicates:
            print(f"\n🚨 DUPLICATES FOUND:")
            for combo, items in duplicates.items():
                print(f"\n  Combination: {combo}")
                print(f"  Count: {len(items)} returns")
                for item in items:
                    print(f"    - ID: {item['id'][:8]}...")
                    print(f"      Email: {item['customer_email']}")
                    print(f"      Created: {item['created_at']}")
                    print(f"      Status: {item['status']}")
        else:
            print(f"\n✅ NO DUPLICATES FOUND")
        
        print(f"\n📊 ALL RETURNS:")
        for combo, items in combinations.items():
            order_id, email = combo.split(':', 1)
            print(f"  Order {order_id} + {email}: {len(items)} return(s)")
    
    async def run_comprehensive_analysis(self):
        """Run comprehensive duplicate analysis"""
        print("🔍 COMPREHENSIVE DUPLICATE RETURNS ANALYSIS")
        print("=" * 60)
        print(f"Target Tenant: {TEST_TENANT_ID}")
        print("=" * 60)
        
        # Get API data
        print("\n📡 Fetching data from API...")
        api_returns = await self.get_api_returns()
        
        # Get raw database data
        print("🗄️ Fetching data from database...")
        raw_returns = await self.get_raw_database_returns()
        
        # Analyze API data (case-sensitive)
        api_combinations, api_duplicates = self.analyze_duplicates(api_returns, case_sensitive=True)
        self.print_analysis_results("API DATA ANALYSIS (Case-Sensitive)", api_returns, api_combinations, api_duplicates)
        
        # Analyze API data (case-insensitive)
        api_combinations_ci, api_duplicates_ci = self.analyze_duplicates(api_returns, case_sensitive=False)
        self.print_analysis_results("API DATA ANALYSIS (Case-Insensitive)", api_returns, api_combinations_ci, api_duplicates_ci)
        
        # Analyze raw database data (case-sensitive)
        raw_combinations, raw_duplicates = self.analyze_duplicates(raw_returns, case_sensitive=True)
        self.print_analysis_results("RAW DATABASE ANALYSIS (Case-Sensitive)", raw_returns, raw_combinations, raw_duplicates)
        
        # Analyze raw database data (case-insensitive)
        raw_combinations_ci, raw_duplicates_ci = self.analyze_duplicates(raw_returns, case_sensitive=False)
        self.print_analysis_results("RAW DATABASE ANALYSIS (Case-Insensitive)", raw_returns, raw_combinations_ci, raw_duplicates_ci)
        
        # Compare API vs Database
        print(f"\n{'='*60}")
        print("API vs DATABASE COMPARISON")
        print(f"{'='*60}")
        print(f"API Returns Count: {len(api_returns)}")
        print(f"Database Returns Count: {len(raw_returns)}")
        print(f"Data Consistency: {'✅ MATCH' if len(api_returns) == len(raw_returns) else '❌ MISMATCH'}")
        
        # Check if deduplication is working
        print(f"\n{'='*60}")
        print("DEDUPLICATION EFFECTIVENESS")
        print(f"{'='*60}")
        
        if len(raw_duplicates) > 0 and len(api_duplicates) == 0:
            print("✅ DEDUPLICATION WORKING: Raw data has duplicates, but API removes them")
        elif len(raw_duplicates) == 0 and len(api_duplicates) == 0:
            print("✅ NO DUPLICATES: Both raw data and API are clean")
        elif len(raw_duplicates) > 0 and len(api_duplicates) > 0:
            print("❌ DEDUPLICATION FAILED: Both raw data and API have duplicates")
        else:
            print("⚠️ UNEXPECTED STATE: API has duplicates but raw data doesn't")
        
        # Case-insensitive analysis
        if len(raw_duplicates_ci) > 0 and len(api_duplicates_ci) == 0:
            print("✅ CASE-INSENSITIVE DEDUPLICATION: API handles case variations")
        elif len(raw_duplicates_ci) > 0 and len(api_duplicates_ci) > 0:
            print("⚠️ CASE-INSENSITIVE ISSUE: API doesn't handle email case variations")
        
        # Final verdict
        print(f"\n{'='*60}")
        print("FINAL VERDICT")
        print(f"{'='*60}")
        
        if len(api_duplicates) == 0:
            print("🎉 SUCCESS: Duplicate returns issue has been resolved!")
            print("   - API returns clean, unique data")
            print("   - No duplicate order+customer combinations")
            
            if len(api_duplicates_ci) > 0:
                print("⚠️ RECOMMENDATION: Consider implementing case-insensitive email matching")
                print("   - Some emails have different cases but represent the same customer")
            else:
                print("✅ PERFECT: Even case-insensitive analysis shows no duplicates")
        else:
            print("❌ ISSUE PERSISTS: Duplicate returns still exist")
            print("   - API is returning duplicate data")
            print("   - Deduplication logic needs review")

async def main():
    """Main analysis execution"""
    async with ComprehensiveDuplicateAnalysis() as analyzer:
        await analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    asyncio.run(main())