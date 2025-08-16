"""
Exchange Controller
Handles exchange requests and product browsing for customer returns
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from src.middleware.security import get_tenant_id
from ..config.database import db
from ..services.shopify_service import ShopifyService
from ..services.policy_engine_service import PolicyEngineService

router = APIRouter(prefix="/exchange", tags=["Exchange"])

# === EXCHANGE MODELS === #

class ExchangeItemRequest(BaseModel):
    original_line_item_id: str
    original_quantity: int
    new_product_id: Optional[str] = None
    new_variant_id: Optional[str] = None
    reason: str = "wrong_size"
    notes: Optional[str] = ""

class ExchangeRequest(BaseModel):
    order_id: str
    customer_email: str
    items: List[ExchangeItemRequest]
    customer_note: Optional[str] = ""

class ProductSearchRequest(BaseModel):
    query: Optional[str] = ""
    product_type: Optional[str] = None
    vendor: Optional[str] = None
    limit: int = Field(default=20, le=100)

class ExchangeAvailabilityRequest(BaseModel):
    original_product_id: str
    original_variant_id: Optional[str] = None

# === API ENDPOINTS === #

@router.post("/browse-products")
async def browse_products(
    request: ProductSearchRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """Browse store catalog for exchange products"""
    
    try:
        shopify_service = ShopifyService(tenant_id)
        
        # Get products from Shopify
        products = await shopify_service.get_products(
            limit=request.limit,
            title=request.query,
            product_type=request.product_type,
            vendor=request.vendor
        )
        
        # Format products for exchange selection
        formatted_products = []
        for product in products:
            # Get variants with inventory
            variants = []
            for variant in product.get('variants', []):
                variants.append({
                    'id': str(variant['id']),
                    'title': variant.get('title', 'Default'),
                    'price': float(variant.get('price', 0)),
                    'compare_at_price': float(variant.get('compare_at_price', 0)) if variant.get('compare_at_price') else None,
                    'sku': variant.get('sku', ''),
                    'inventory_quantity': variant.get('inventory_quantity', 0),
                    'available': variant.get('available', True),
                    'option1': variant.get('option1'),
                    'option2': variant.get('option2'),
                    'option3': variant.get('option3')
                })
            
            formatted_products.append({
                'id': str(product['id']),
                'title': product.get('title', ''),
                'handle': product.get('handle', ''),
                'product_type': product.get('product_type', ''),
                'vendor': product.get('vendor', ''),
                'tags': product.get('tags', ''),
                'images': product.get('images', [])[:3],  # Limit to 3 images
                'variants': variants,
                'options': product.get('options', []),
                'available': any(v['available'] for v in variants)
            })
        
        return {
            'success': True,
            'products': formatted_products,
            'total_count': len(formatted_products)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to browse products: {str(e)}")

@router.post("/check-availability")
async def check_exchange_availability(
    request: ExchangeAvailabilityRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """Check availability of variants for the same product"""
    
    try:
        shopify_service = ShopifyService(tenant_id)
        
        # Get product details
        product = await shopify_service.get_product(request.original_product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get all variants with availability
        available_variants = []
        for variant in product.get('variants', []):
            if variant.get('available', False) and variant.get('inventory_quantity', 0) > 0:
                available_variants.append({
                    'id': str(variant['id']),
                    'title': variant.get('title', 'Default'),
                    'price': float(variant.get('price', 0)),
                    'sku': variant.get('sku', ''),
                    'inventory_quantity': variant.get('inventory_quantity', 0),
                    'option1': variant.get('option1'),
                    'option2': variant.get('option2'),
                    'option3': variant.get('option3'),
                    'is_original': str(variant['id']) == request.original_variant_id
                })
        
        return {
            'success': True,
            'product': {
                'id': str(product['id']),
                'title': product.get('title', ''),
                'images': product.get('images', [])[:1],
                'options': product.get('options', [])
            },
            'available_variants': available_variants,
            'total_available': len(available_variants)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check availability: {str(e)}")

@router.post("/calculate-price-difference")
async def calculate_price_difference(
    original_variant_id: str,
    new_variant_id: str,
    quantity: int,
    tenant_id: str = Depends(get_tenant_id)
):
    """Calculate price difference for exchange"""
    
    try:
        shopify_service = ShopifyService(tenant_id)
        
        # Get variant prices
        original_variant = await shopify_service.get_variant(original_variant_id)
        new_variant = await shopify_service.get_variant(new_variant_id)
        
        if not original_variant or not new_variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        original_price = float(original_variant.get('price', 0))
        new_price = float(new_variant.get('price', 0))
        
        price_difference = (new_price - original_price) * quantity
        
        return {
            'success': True,
            'original_price': original_price,
            'new_price': new_price,
            'quantity': quantity,
            'price_difference': price_difference,
            'customer_pays_more': price_difference > 0,
            'customer_gets_refund': price_difference < 0,
            'message': _get_price_difference_message(price_difference, quantity)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate price difference: {str(e)}")

@router.post("/create")
async def create_exchange_request(
    request: ExchangeRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """Create an exchange request"""
    
    try:
        # Validate exchange eligibility using policy engine
        policy_engine = PolicyEngineService(tenant_id)
        
        # Get active policy
        active_policy = await db.return_policies.find_one({
            'tenant_id': tenant_id,
            'is_active': True
        })
        
        if not active_policy:
            raise HTTPException(status_code=400, detail="No active return policy found")
        
        # Check if exchanges are enabled
        if not active_policy.get('exchange_settings', {}).get('enabled', False):
            raise HTTPException(status_code=400, detail="Exchanges are not enabled for this store")
        
        # Get order details for validation
        shopify_service = ShopifyService(tenant_id)
        order = await shopify_service.get_order(request.order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Validate customer email
        if order.get('customer_email', '').lower() != request.customer_email.lower():
            raise HTTPException(status_code=403, detail="Email does not match order")
        
        # Create exchange request
        exchange_id = str(uuid.uuid4())
        
        # Process each exchange item
        exchange_items = []
        total_price_difference = 0
        
        for item in request.items:
            # Get original item details
            original_line_item = next(
                (li for li in order.get('line_items', []) if str(li['id']) == item.original_line_item_id),
                None
            )
            
            if not original_line_item:
                raise HTTPException(status_code=404, detail=f"Original line item {item.original_line_item_id} not found")
            
            exchange_item = {
                'original_line_item_id': item.original_line_item_id,
                'original_quantity': item.original_quantity,
                'original_product_id': str(original_line_item.get('product_id', '')),
                'original_variant_id': str(original_line_item.get('variant_id', '')),
                'original_price': float(original_line_item.get('price', 0)),
                'new_product_id': item.new_product_id,
                'new_variant_id': item.new_variant_id,
                'reason': item.reason,
                'notes': item.notes,
                'status': 'pending'
            }
            
            # Calculate price difference if new variant specified
            if item.new_variant_id:
                price_calc = await calculate_price_difference(
                    original_line_item.get('variant_id'),
                    item.new_variant_id,
                    item.original_quantity,
                    tenant_id
                )
                
                exchange_item.update({
                    'new_price': price_calc['new_price'],
                    'price_difference': price_calc['price_difference']
                })
                
                total_price_difference += price_calc['price_difference']
            
            exchange_items.append(exchange_item)
        
        # Store exchange request in database
        exchange_request = {
            'id': exchange_id,
            'tenant_id': tenant_id,
            'order_id': request.order_id,
            'order_number': order.get('order_number', order.get('name', '')),
            'customer_email': request.customer_email,
            'customer_note': request.customer_note,
            'items': exchange_items,
            'status': 'requested',
            'total_price_difference': total_price_difference,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        await db.exchange_requests.insert_one(exchange_request)
        
        return {
            'success': True,
            'exchange_request': {
                'id': exchange_id,
                'status': 'requested',
                'total_price_difference': total_price_difference,
                'message': _get_exchange_confirmation_message(total_price_difference),
                'items_count': len(exchange_items)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create exchange request: {str(e)}")

@router.get("/{exchange_id}/status")
async def get_exchange_status(
    exchange_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get exchange request status"""
    
    try:
        exchange_request = await db.exchange_requests.find_one({
            'id': exchange_id,
            'tenant_id': tenant_id
        })
        
        if not exchange_request:
            raise HTTPException(status_code=404, detail="Exchange request not found")
        
        # Convert ObjectId to string if present
        if '_id' in exchange_request:
            exchange_request['_id'] = str(exchange_request['_id'])
        
        return {
            'success': True,
            'exchange_request': exchange_request
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get exchange status: {str(e)}")

# === HELPER FUNCTIONS === #

def _get_price_difference_message(price_difference: float, quantity: int) -> str:
    """Generate human-readable price difference message"""
    
    if abs(price_difference) < 0.01:
        return "No price difference"
    elif price_difference > 0:
        return f"You'll be charged an additional ${abs(price_difference):.2f}"
    else:
        return f"We'll refund the difference of ${abs(price_difference):.2f}"

def _get_exchange_confirmation_message(total_price_difference: float) -> str:
    """Generate exchange confirmation message"""
    
    if abs(total_price_difference) < 0.01:
        return "Your exchange request has been submitted. No additional payment required."
    elif total_price_difference > 0:
        return f"Your exchange request has been submitted. You'll be charged ${total_price_difference:.2f} for the price difference."
    else:
        return f"Your exchange request has been submitted. You'll receive a refund of ${abs(total_price_difference):.2f} for the price difference."