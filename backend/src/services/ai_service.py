"""
AI-based return reason suggestions service
"""
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.return_request import ReturnReason
from ..models.product import Product
from ..models.order import Order


class AIService:
    """Service for AI-powered features with local fallback"""
    
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.use_openai = bool(self.openai_api_key)
        
        if not self.use_openai:
            print("Warning: OpenAI API key not found - using local AI suggestions")
    
    async def suggest_return_reasons(self, product_name: str, product_description: str, order_date: datetime) -> List[Dict[str, Any]]:
        """Suggest most likely return reasons for a product"""
        
        if self.use_openai:
            return await self._get_openai_suggestions(product_name, product_description, order_date)
        else:
            return await self._get_local_suggestions(product_name, product_description, order_date)
    
    async def _get_openai_suggestions(self, product_name: str, product_description: str, order_date: datetime) -> List[Dict[str, Any]]:
        """Get return reason suggestions using OpenAI API"""
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            # Calculate days since order
            days_since_order = (datetime.utcnow() - order_date).days
            
            prompt = f"""
            Based on the product information below, suggest the top 3 most likely return reasons with confidence scores (0-100):
            
            Product: {product_name}
            Description: {product_description}
            Days since order: {days_since_order}
            
            Available return reasons:
            - defective: Product has defects or doesn't work properly
            - wrong_size: Incorrect size ordered or received
            - wrong_color: Incorrect color ordered or received  
            - not_as_described: Product doesn't match the description
            - damaged_in_shipping: Product was damaged during delivery
            - changed_mind: Customer simply changed their mind
            - quality_issues: Product quality is below expectations
            
            Return your response as JSON with this structure:
            [
                {{"reason": "reason_code", "confidence": 85, "explanation": "Brief explanation"}},
                {{"reason": "reason_code", "confidence": 70, "explanation": "Brief explanation"}},
                {{"reason": "reason_code", "confidence": 55, "explanation": "Brief explanation"}}
            ]
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in e-commerce return patterns. Analyze products and suggest likely return reasons."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse OpenAI response
            content = response.choices[0].message.content
            import json
            suggestions = json.loads(content)
            
            return suggestions
        
        except Exception as e:
            print(f"OpenAI suggestion error: {e}")
            # Fallback to local suggestions
            return await self._get_local_suggestions(product_name, product_description, order_date)
    
    async def _get_local_suggestions(self, product_name: str, product_description: str, order_date: datetime) -> List[Dict[str, Any]]:
        """Get return reason suggestions using local rule-based AI"""
        
        suggestions = []
        product_text = f"{product_name} {product_description}".lower()
        
        # Handle timezone-aware datetime
        if order_date.tzinfo is not None:
            order_date = order_date.replace(tzinfo=None)
        
        days_since_order = (datetime.utcnow() - order_date).days
        
        # Rule-based suggestion engine
        rules = [
            {
                "reason": ReturnReason.DEFECTIVE,
                "keywords": ["electronic", "device", "gadget", "tech", "battery", "power", "digital", "smart"],
                "base_confidence": 75,
                "time_factor": 0.5,  # Higher confidence if recent order
                "explanation": "Electronics commonly have defects or functionality issues"
            },
            {
                "reason": ReturnReason.WRONG_SIZE,
                "keywords": ["clothing", "shirt", "pants", "shoes", "dress", "jacket", "size", "fit", "wear"],
                "base_confidence": 80,
                "time_factor": 0.2,
                "explanation": "Clothing items frequently have sizing issues"
            },
            {
                "reason": ReturnReason.WRONG_COLOR,
                "keywords": ["color", "colour", "red", "blue", "green", "black", "white", "yellow", "pink"],
                "base_confidence": 60,
                "time_factor": 0.1,
                "explanation": "Color might not match expectations or be as displayed"
            },
            {
                "reason": ReturnReason.NOT_AS_DESCRIBED,
                "keywords": ["premium", "luxury", "high-quality", "professional", "advanced", "superior"],
                "base_confidence": 65,
                "time_factor": 0.3,
                "explanation": "Premium products may not meet high expectations"
            },
            {
                "reason": ReturnReason.DAMAGED_IN_SHIPPING,
                "keywords": ["fragile", "glass", "ceramic", "delicate", "breakable", "mirror"],
                "base_confidence": 70,
                "time_factor": -0.8,  # Lower confidence if order is old
                "explanation": "Fragile items are prone to shipping damage"
            },
            {
                "reason": ReturnReason.QUALITY_ISSUES,
                "keywords": ["cheap", "budget", "affordable", "value", "basic", "standard"],
                "base_confidence": 55,
                "time_factor": 0.4,
                "explanation": "Budget items may have quality concerns"
            },
            {
                "reason": ReturnReason.CHANGED_MIND,
                "keywords": ["gift", "present", "impulse", "sale", "discount", "clearance"],
                "base_confidence": 50,
                "time_factor": -0.2,  # Lower confidence for older orders
                "explanation": "Gift items or impulse purchases are often returned"
            }
        ]
        
        # Calculate confidence for each rule
        for rule in rules:
            confidence = rule["base_confidence"]
            
            # Keyword matching
            keyword_matches = sum(1 for keyword in rule["keywords"] if keyword in product_text)
            if keyword_matches > 0:
                confidence += keyword_matches * 10
            
            # Time factor (recent orders more likely for some reasons)
            time_adjustment = rule["time_factor"] * max(0, 30 - days_since_order)
            confidence += time_adjustment
            
            # Ensure confidence is within bounds
            confidence = max(10, min(95, confidence))
            
            suggestions.append({
                "reason": rule["reason"],
                "confidence": int(confidence),
                "explanation": rule["explanation"]
            })
        
        # Sort by confidence and return top 3
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:3]
    
    async def generate_upsell_message(self, return_reason: str, product_name: str, tenant_name: str) -> str:
        """Generate upsell message for return scenarios"""
        
        if self.use_openai:
            return await self._generate_openai_upsell(return_reason, product_name, tenant_name)
        else:
            return await self._generate_local_upsell(return_reason, product_name, tenant_name)
    
    async def _generate_openai_upsell(self, return_reason: str, product_name: str, tenant_name: str) -> str:
        """Generate upsell message using OpenAI"""
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            prompt = f"""
            Write a friendly, helpful upsell message for a customer returning "{product_name}" due to "{return_reason}".
            The message should:
            1. Acknowledge their concern
            2. Suggest a better alternative or upgrade
            3. Be helpful, not pushy
            4. Keep it under 100 words
            5. Use the store name "{tenant_name}"
            
            Return reason: {return_reason.replace('_', ' ')}
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful customer service representative writing empathetic upsell messages."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"OpenAI upsell generation error: {e}")
            return await self._generate_local_upsell(return_reason, product_name, tenant_name)
    
    async def _generate_local_upsell(self, return_reason: str, product_name: str, tenant_name: str) -> str:
        """Generate upsell message using local templates"""
        
        templates = {
            ReturnReason.DEFECTIVE: [
                f"We're sorry the {product_name} didn't work as expected. Consider our premium version with extended warranty and quality guarantee!",
                f"We understand your frustration. Our upgraded {product_name} model has improved reliability and comes with 24/7 support.",
                f"Sorry for the trouble! We have a professional-grade version that might better meet your needs."
            ],
            ReturnReason.WRONG_SIZE: [
                f"Size issues happen! We'd be happy to help you find the perfect fit. Our size guide has been updated to help you choose better.",
                f"Let's get you the right size! Consider our adjustable version that fits a wider range of sizes.",
                f"We want you to love your purchase! Our customer service team can help you find the perfect size."
            ],
            ReturnReason.QUALITY_ISSUES: [
                f"We're committed to quality at {tenant_name}. Consider upgrading to our premium line with superior materials and craftsmanship.",
                f"Your satisfaction is important to us. Our deluxe version offers the quality you're looking for.",
                f"We hear you on quality. Check out our artisan collection - handcrafted with attention to detail."
            ],
            ReturnReason.NOT_AS_DESCRIBED: [
                f"We want to exceed your expectations! Our detailed product videos and 360° views might help you find exactly what you're looking for.",
                f"Let's find you something perfect! Our customer favorites section has products with thousands of positive reviews.",
                f"We're here to help you find exactly what you need. Consider browsing our curated collections."
            ],
            ReturnReason.CHANGED_MIND: [
                f"No worries at all! Take a look at our bestsellers - you might find something you love even more.",
                f"Happens to everyone! Our recommendation engine can suggest items based on your browsing history.",
                f"That's perfectly fine! Maybe something from our new arrivals will catch your eye."
            ]
        }
        
        # Get templates for the return reason, fallback to general message
        reason_templates = templates.get(return_reason, [
            f"Thank you for your feedback. We're always working to improve our products at {tenant_name}.",
            f"We appreciate your business and want to make this right. Let us know how we can help!",
            f"Your experience matters to us. We're here to ensure you find exactly what you need."
        ])
        
        # Select a template (in a real implementation, this could be randomized or based on customer history)
        import random
        return random.choice(reason_templates)
    
    async def analyze_return_patterns(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze return patterns and provide insights"""
        
        # This would integrate with the analytics service to provide AI insights
        # For now, return a mock analysis structure
        
        return {
            "trends": {
                "most_common_reason": "defective",
                "trending_up": ["quality_issues"],
                "trending_down": ["wrong_size"]
            },
            "recommendations": [
                "Consider improving quality control for electronic items",
                "Update product descriptions to better set customer expectations",
                "Implement size guide improvements for clothing items"
            ],
            "risk_products": [
                {"product_name": "Budget Headphones", "risk_score": 85, "main_issue": "defective"},
                {"product_name": "T-Shirt Collection", "risk_score": 70, "main_issue": "wrong_size"}
            ]
        }
    
    async def suggest_alternative_products(self, returned_product: Product, return_reason: str) -> List[Dict[str, Any]]:
        """Suggest alternative products based on return reason"""
        
        # This would integrate with product catalog to suggest alternatives
        # For now, return mock suggestions
        
        suggestions = [
            {
                "product_id": "alt_001",
                "name": f"Premium {returned_product.name}",
                "price": returned_product.price * 1.3,
                "reason": "Higher quality alternative with better reviews",
                "confidence": 85
            },
            {
                "product_id": "alt_002", 
                "name": f"Upgraded {returned_product.name}",
                "price": returned_product.price * 1.1,
                "reason": "Similar product with improvements addressing common issues",
                "confidence": 75
            }
        ]
        
        return suggestions