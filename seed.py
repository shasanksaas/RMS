#!/usr/bin/env python3
"""
Comprehensive seed script for Returns Management SaaS
Creates 2 tenants, 50+ products, 30+ orders, 20+ returns with varied states
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
import random
import uuid

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join('backend', '.env'))

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

class SeedData:
    def __init__(self):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        
    async def clean_database(self):
        """Clean existing data"""
        collections = ['tenants', 'products', 'orders', 'return_requests', 'return_rules', 'audit_logs', 'resolutions']
        for collection in collections:
            await self.db[collection].delete_many({})
        print("✅ Cleaned existing data")

    async def create_tenants(self):
        """Create 2 demo tenants with different configurations"""
        tenants = [
            {
                "id": "tenant-fashion-store",
                "name": "Fashion Forward",
                "domain": "fashionforward.com",
                "shopify_store_url": "fashion-forward.myshopify.com",
                "plan": "pro",
                "settings": {
                    "return_window_days": 30,
                    "auto_approve_exchanges": True,
                    "require_photos": True,
                    "brand_color": "#e11d48",
                    "custom_message": "Love it or return it - we've got you covered!",
                    "restocking_fee_percent": 5.0,
                    "store_credit_bonus_percent": 15.0,
                    "logo_url": "https://example.com/fashion-logo.png"
                },
                "created_at": datetime.utcnow(),
                "is_active": True
            },
            {
                "id": "tenant-tech-gadgets",
                "name": "TechHub Electronics",
                "domain": "techhub.com", 
                "shopify_store_url": "techhub-electronics.myshopify.com",
                "plan": "enterprise",
                "settings": {
                    "return_window_days": 45,
                    "auto_approve_exchanges": False,
                    "require_photos": True,
                    "brand_color": "#2563eb",
                    "custom_message": "Quality tech products with hassle-free returns",
                    "restocking_fee_percent": 10.0,
                    "store_credit_bonus_percent": 10.0,
                    "logo_url": "https://example.com/tech-logo.png"
                },
                "created_at": datetime.utcnow(),
                "is_active": True
            }
        ]
        
        for tenant in tenants:
            await self.db.tenants.insert_one(tenant)
        
        print(f"✅ Created {len(tenants)} tenants")
        return [t["id"] for t in tenants]

    async def create_products(self, tenant_ids):
        """Create 50+ products across tenants"""
        fashion_products = [
            {"name": "Premium Cotton T-Shirt", "category": "Clothing", "price": 29.99},
            {"name": "Designer Jeans", "category": "Clothing", "price": 89.99},
            {"name": "Leather Jacket", "category": "Outerwear", "price": 199.99},
            {"name": "Summer Dress", "category": "Clothing", "price": 59.99},
            {"name": "Running Shoes", "category": "Footwear", "price": 129.99},
            {"name": "Casual Sneakers", "category": "Footwear", "price": 79.99},
            {"name": "Wool Sweater", "category": "Clothing", "price": 69.99},
            {"name": "Denim Shorts", "category": "Clothing", "price": 39.99},
            {"name": "Hiking Boots", "category": "Footwear", "price": 159.99},
            {"name": "Silk Scarf", "category": "Accessories", "price": 49.99},
            {"name": "Crossbody Bag", "category": "Accessories", "price": 89.99},
            {"name": "Sunglasses", "category": "Accessories", "price": 119.99},
            {"name": "Winter Coat", "category": "Outerwear", "price": 249.99},
            {"name": "Yoga Pants", "category": "Clothing", "price": 45.99},
            {"name": "Formal Shirt", "category": "Clothing", "price": 79.99},
            {"name": "Ankle Boots", "category": "Footwear", "price": 139.99},
            {"name": "Baseball Cap", "category": "Accessories", "price": 24.99},
            {"name": "Cardigan", "category": "Clothing", "price": 65.99},
            {"name": "Maxi Skirt", "category": "Clothing", "price": 52.99},
            {"name": "Athletic Shorts", "category": "Clothing", "price": 34.99},
            {"name": "Platform Sandals", "category": "Footwear", "price": 95.99},
            {"name": "Tote Bag", "category": "Accessories", "price": 75.99},
            {"name": "Blazer", "category": "Clothing", "price": 129.99},
            {"name": "Tank Top", "category": "Clothing", "price": 19.99},
            {"name": "Chelsea Boots", "category": "Footwear", "price": 179.99}
        ]
        
        tech_products = [
            {"name": "Wireless Bluetooth Headphones", "category": "Audio", "price": 199.99},
            {"name": "Smartphone Case", "category": "Accessories", "price": 29.99},
            {"name": "Laptop Stand", "category": "Computing", "price": 79.99},
            {"name": "USB-C Hub", "category": "Accessories", "price": 59.99},
            {"name": "Mechanical Keyboard", "category": "Computing", "price": 149.99},
            {"name": "Wireless Mouse", "category": "Computing", "price": 69.99},
            {"name": "Monitor", "category": "Computing", "price": 299.99},
            {"name": "Webcam", "category": "Computing", "price": 89.99},
            {"name": "Power Bank", "category": "Accessories", "price": 39.99},
            {"name": "Wireless Charger", "category": "Accessories", "price": 49.99},
            {"name": "Bluetooth Speaker", "category": "Audio", "price": 129.99},
            {"name": "Smart Watch", "category": "Wearables", "price": 249.99},
            {"name": "Tablet", "category": "Computing", "price": 399.99},
            {"name": "Gaming Mouse", "category": "Gaming", "price": 79.99},
            {"name": "Gaming Keyboard", "category": "Gaming", "price": 159.99},
            {"name": "VR Headset", "category": "Gaming", "price": 299.99},
            {"name": "Drone", "category": "Electronics", "price": 499.99},
            {"name": "Action Camera", "category": "Electronics", "price": 199.99},
            {"name": "Fitness Tracker", "category": "Wearables", "price": 99.99},
            {"name": "Smart Home Hub", "category": "Smart Home", "price": 79.99},
            {"name": "Security Camera", "category": "Smart Home", "price": 129.99},
            {"name": "Router", "category": "Networking", "price": 149.99},
            {"name": "External SSD", "category": "Storage", "price": 119.99},
            {"name": "Graphics Card", "category": "Computing", "price": 699.99},
            {"name": "CPU", "category": "Computing", "price": 399.99}
        ]
        
        products = []
        
        # Add fashion products to first tenant
        for i, product_data in enumerate(fashion_products):
            product = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_ids[0],
                "shopify_product_id": f"shopify_fashion_{i+1}",
                "name": product_data["name"],
                "description": f"High-quality {product_data['name'].lower()} from Fashion Forward",
                "price": product_data["price"],
                "category": product_data["category"],
                "image_url": f"https://via.placeholder.com/400x400?text={product_data['name'].replace(' ', '+')}",
                "sku": f"FF-{i+1:03d}",
                "in_stock": random.choice([True, True, True, False]),  # 25% out of stock
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30))
            }
            products.append(product)
        
        # Add tech products to second tenant
        for i, product_data in enumerate(tech_products):
            product = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_ids[1],
                "shopify_product_id": f"shopify_tech_{i+1}",
                "name": product_data["name"],
                "description": f"Premium {product_data['name'].lower()} from TechHub Electronics",
                "price": product_data["price"],
                "category": product_data["category"],
                "image_url": f"https://via.placeholder.com/400x400?text={product_data['name'].replace(' ', '+')}",
                "sku": f"TH-{i+1:03d}",
                "in_stock": random.choice([True, True, True, False]),  # 25% out of stock
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30))
            }
            products.append(product)
        
        await self.db.products.insert_many(products)
        print(f"✅ Created {len(products)} products")
        return products

    async def create_return_rules(self, tenant_ids):
        """Create return rules with different configurations"""
        rules = [
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_ids[0],  # Fashion store
                "name": "Auto-approve defective fashion items",
                "description": "Automatically approve returns for defective clothing",
                "conditions": {
                    "auto_approve_reasons": ["defective", "damaged_in_shipping", "quality_issues"],
                    "max_days_since_order": 30,
                    "min_return_value": 0
                },
                "actions": {
                    "auto_approve": True,
                    "generate_label": True
                },
                "priority": 1,
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_ids[0],  # Fashion store
                "name": "Manual review for wrong size/color",
                "description": "Route sizing and color issues to manual review",
                "conditions": {
                    "require_manual_review_reasons": ["wrong_size", "wrong_color", "not_as_described"],
                    "max_days_since_order": 30
                },
                "actions": {
                    "manual_review": True
                },
                "priority": 2,
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_ids[1],  # Tech store
                "name": "Extended return window for electronics",
                "description": "45-day return window for tech products",
                "conditions": {
                    "auto_approve_reasons": ["defective", "damaged_in_shipping"],
                    "max_days_since_order": 45,
                    "min_return_value": 50
                },
                "actions": {
                    "auto_approve": True,
                    "generate_label": True
                },
                "priority": 1,
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_ids[1],  # Tech store
                "name": "High-value manual review",
                "description": "Manual review for expensive items",
                "conditions": {
                    "require_manual_review_reasons": ["changed_mind"],
                    "max_days_since_order": 45,
                    "min_return_value": 200
                },
                "actions": {
                    "manual_review": True
                },
                "priority": 2,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        ]
        
        await self.db.return_rules.insert_many(rules)
        print(f"✅ Created {len(rules)} return rules")

    async def create_orders(self, tenant_ids, products):
        """Create 30+ orders"""
        customers = [
            {"name": "John Smith", "email": "john.smith@email.com"},
            {"name": "Sarah Johnson", "email": "sarah.j@email.com"},
            {"name": "Michael Brown", "email": "m.brown@email.com"},
            {"name": "Emily Davis", "email": "emily.davis@email.com"},
            {"name": "David Wilson", "email": "d.wilson@email.com"},
            {"name": "Lisa Anderson", "email": "lisa.a@email.com"},
            {"name": "James Miller", "email": "james.miller@email.com"},
            {"name": "Ashley Taylor", "email": "ashley.t@email.com"},
            {"name": "Robert Garcia", "email": "r.garcia@email.com"},
            {"name": "Jessica Martinez", "email": "j.martinez@email.com"},
            {"name": "Christopher Lee", "email": "c.lee@email.com"},
            {"name": "Amanda White", "email": "amanda.white@email.com"},
            {"name": "Joshua Thompson", "email": "j.thompson@email.com"},
            {"name": "Stephanie Clark", "email": "s.clark@email.com"},
            {"name": "Daniel Rodriguez", "email": "d.rodriguez@email.com"},
        ]
        
        orders = []
        order_counter = 1
        
        for tenant_id in tenant_ids:
            tenant_products = [p for p in products if p["tenant_id"] == tenant_id]
            
            # Create 15+ orders per tenant
            for i in range(16):
                customer = random.choice(customers)
                order_date = datetime.utcnow() - timedelta(days=random.randint(1, 90))
                
                # Select 1-4 random products for this order
                selected_products = random.sample(tenant_products, random.randint(1, 4))
                
                order_items = []
                total_amount = 0
                
                for product in selected_products:
                    quantity = random.randint(1, 3)
                    item = {
                        "product_id": product["id"],
                        "product_name": product["name"],
                        "quantity": quantity,
                        "price": product["price"],
                        "sku": product["sku"]
                    }
                    order_items.append(item)
                    total_amount += product["price"] * quantity
                
                order = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "shopify_order_id": f"shopify_order_{order_counter}",
                    "customer_email": customer["email"],
                    "customer_name": customer["name"],
                    "order_number": f"ORD-{order_counter:04d}",
                    "items": order_items,
                    "total_amount": round(total_amount, 2),
                    "order_date": order_date,
                    "created_at": order_date
                }
                
                orders.append(order)
                order_counter += 1
        
        await self.db.orders.insert_many(orders)
        print(f"✅ Created {len(orders)} orders")
        return orders

    async def create_return_requests(self, orders):
        """Create 20+ return requests with various states"""
        return_reasons = ["defective", "wrong_size", "wrong_color", "not_as_described", 
                         "damaged_in_shipping", "changed_mind", "quality_issues"]
        
        return_statuses = ["requested", "approved", "denied", "label_issued", 
                          "in_transit", "received", "resolved"]
        
        returns = []
        resolutions = []
        audit_logs = []
        
        # Create returns for about 60% of orders
        sample_orders = random.sample(orders, min(22, int(len(orders) * 0.6)))
        
        for order in sample_orders:
            # Select 1-2 items to return from the order
            items_to_return = random.sample(order["items"], 
                                          random.randint(1, min(2, len(order["items"]))))
            
            refund_amount = sum(item["price"] * item["quantity"] for item in items_to_return)
            created_at = order["order_date"] + timedelta(days=random.randint(1, 25))
            
            return_id = str(uuid.uuid4())
            reason = random.choice(return_reasons)
            
            # Determine status based on reason and age
            days_old = (datetime.utcnow() - created_at).days
            
            if reason in ["defective", "damaged_in_shipping"]:
                if days_old > 10:
                    status = random.choice(["resolved", "in_transit", "received"])
                elif days_old > 5:
                    status = random.choice(["approved", "label_issued", "in_transit"])
                else:
                    status = "approved"
            elif reason == "changed_mind":
                if days_old > 15:
                    status = random.choice(["denied", "resolved"])
                else:
                    status = random.choice(["requested", "approved"])
            else:
                status = random.choice(return_statuses)
            
            return_request = {
                "id": return_id,
                "tenant_id": order["tenant_id"],
                "order_id": order["id"],
                "customer_email": order["customer_email"],
                "customer_name": order["customer_name"],
                "reason": reason,
                "status": status,
                "items_to_return": items_to_return,
                "refund_amount": round(refund_amount, 2),
                "notes": f"Return request for {reason.replace('_', ' ')}",
                "tracking_number": f"TRK{random.randint(100000, 999999)}" if status in ["in_transit", "received", "resolved"] else None,
                "created_at": created_at,
                "updated_at": datetime.utcnow() if status != "requested" else created_at
            }
            
            returns.append(return_request)
            
            # Create audit log entries
            initial_log = {
                "id": str(uuid.uuid4()),
                "return_id": return_id,
                "from_status": "new",
                "to_status": "requested",
                "notes": "Return request created by customer",
                "user_id": "customer",
                "timestamp": created_at,
                "event_type": "status_change"
            }
            audit_logs.append(initial_log)
            
            # Add more audit entries for advanced statuses
            if status != "requested":
                status_log = {
                    "id": str(uuid.uuid4()),
                    "return_id": return_id,
                    "from_status": "requested",
                    "to_status": status,
                    "notes": f"Status changed to {status}",
                    "user_id": "system",
                    "timestamp": created_at + timedelta(days=random.randint(1, 5)),
                    "event_type": "status_change"
                }
                audit_logs.append(status_log)
            
            # Create resolution records for resolved returns
            if status == "resolved":
                resolution_type = random.choice(["refund", "exchange", "store_credit"])
                
                if resolution_type == "refund":
                    resolution = {
                        "id": str(uuid.uuid4()),
                        "return_request_id": return_id,
                        "type": "refund",
                        "amount": refund_amount,
                        "method": random.choice(["stripe", "manual", "original_payment"]),
                        "status": "completed",
                        "notes": f"Refund processed for {reason.replace('_', ' ')}",
                        "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 5)),
                        "processed_at": datetime.utcnow() - timedelta(days=random.randint(0, 3))
                    }
                elif resolution_type == "exchange":
                    resolution = {
                        "id": str(uuid.uuid4()),
                        "return_request_id": return_id,
                        "type": "exchange",
                        "original_items": items_to_return,
                        "new_items": [{"product_name": f"Replacement {item['product_name']}", 
                                     "quantity": item["quantity"], "price": item["price"]} 
                                    for item in items_to_return],
                        "outbound_order_id": f"EXC-{str(uuid.uuid4())[:8]}",
                        "status": "pending_fulfillment",
                        "notes": "Exchange approved and processed",
                        "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 5))
                    }
                else:  # store_credit
                    resolution = {
                        "id": str(uuid.uuid4()),
                        "return_request_id": return_id,
                        "type": "store_credit",
                        "customer_email": order["customer_email"],
                        "amount": refund_amount * 1.1,  # 10% bonus
                        "balance": refund_amount * 1.1,
                        "status": "active",
                        "notes": "Store credit issued with 10% bonus",
                        "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 5)),
                        "expires_at": None
                    }
                
                resolutions.append(resolution)
                
                # Update return request with resolution info
                return_request["resolution_type"] = resolution_type
                return_request["resolution_id"] = resolution["id"]
        
        # Insert all data
        await self.db.return_requests.insert_many(returns)
        if resolutions:
            await self.db.resolutions.insert_many(resolutions)
        await self.db.audit_logs.insert_many(audit_logs)
        
        print(f"✅ Created {len(returns)} return requests")
        print(f"✅ Created {len(resolutions)} resolutions")
        print(f"✅ Created {len(audit_logs)} audit log entries")

    async def run_seed(self):
        """Run complete seed process"""
        print("🌱 Starting database seed...")
        
        # Clean and seed data
        await self.clean_database()
        tenant_ids = await self.create_tenants()
        products = await self.create_products(tenant_ids)
        await self.create_return_rules(tenant_ids)
        orders = await self.create_orders(tenant_ids, products)
        await self.create_return_requests(orders)
        
        # Print summary
        total_tenants = len(tenant_ids)
        total_products = len(products)
        total_orders = len(orders)
        
        print("\n" + "=" * 50)
        print("🎉 SEED COMPLETE!")
        print("=" * 50)
        print(f"📊 Summary:")
        print(f"  • {total_tenants} tenants with different settings")
        print(f"  • {total_products} products across categories")
        print(f"  • {total_orders} orders from various customers")
        print(f"  • 20+ return requests in different states")
        print(f"  • Return rules covering various scenarios")
        print(f"  • Audit logs for status changes")
        print(f"  • Resolution records for completed returns")
        print("\n🚀 Your Returns Management SaaS is ready to test!")
        
        self.client.close()

async def main():
    seed = SeedData()
    await seed.run_seed()

if __name__ == "__main__":
    asyncio.run(main())