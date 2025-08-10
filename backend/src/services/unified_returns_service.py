"""
Unified Returns Service
Handles business logic for unified return creation from both admin and customer portals
"""
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..config.database import db
from ..services.shopify_service import ShopifyService
from ..utils.enhanced_rules_engine import EnhancedRulesEngine


class UnifiedReturnsService:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.shopify_service = ShopifyService(tenant_id)
        self.rules_engine = EnhancedRulesEngine()

    async def lookup_order_by_number_and_email(self, order_number: str, email: str) -> Dict[str, Any]:
        """
        Lookup order by number and verify email for customer portal
        """
        try:
            # Get order from Shopify
            order = await self.shopify_service.find_order_by_number(order_number)
            
            if not order:
                return {
                    'success': False,
                    'error': 'Order not found. Please check your order number.'
                }
            
            # Verify email matches
            if order.get('email', '').lower() != email.lower():
                return {
                    'success': False,
                    'error': 'Email does not match order records.'
                }
            
            # Get eligible items
            eligible_items = await self._get_eligible_items(order)
            
            # Get policy preview
            policy_preview = await self._get_order_policy_preview(order)
            
            return {
                'success': True,
                'order_id': order['id'],
                'order_number': order['order_number'],
                'customer_name': self._get_customer_name(order),
                'order_date': order['created_at'],
                'total_amount': float(order['total_price']),
                'eligible_items': eligible_items,
                'policy_preview': policy_preview
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to lookup order: {str(e)}'
            }

    async def get_eligible_items_for_order(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Get eligible items for return from a specific order
        """
        try:
            order = await self.shopify_service.get_order(order_id)
            if not order:
                return []
            
            return await self._get_eligible_items(order)
            
        except Exception:
            return []

    async def create_return_request(self, return_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a unified return request
        """
        try:
            return_id = str(uuid.uuid4())
            
            # Get order
            if return_data['channel'] == 'portal':
                order = await self.shopify_service.find_order_by_number(return_data['order_number'])
            else:
                order = await self.shopify_service.get_order(return_data['order_id'])
            
            if not order:
                raise Exception("Order not found")
            
            # Validate return window and items
            await self._validate_return_request(order, return_data)
            
            # Calculate fees and refunds
            fees_and_refunds = await self._calculate_fees_and_refunds(order, return_data['items'])
            
            # Determine approval decision
            decision_result = await self._determine_approval_decision(return_data, fees_and_refunds)
            
            # Create return record
            return_record = {
                'id': return_id,
                'tenant_id': self.tenant_id,
                'order_id': order['id'],
                'order_number': order['order_number'],
                'customer_email': order['email'],
                'customer_name': self._get_customer_name(order),
                'status': decision_result['status'],
                'decision': decision_result['decision'],
                'channel': return_data['channel'],
                'items': return_data['items'],
                'preferred_outcome': return_data['preferred_outcome'],
                'return_method': return_data['return_method'],
                'return_location_id': return_data.get('return_location_id'),
                'customer_note': return_data.get('customer_note'),
                'admin_override_note': return_data.get('admin_override_note'),
                'internal_tags': return_data.get('internal_tags', []),
                'fees': fees_and_refunds['fees'],
                'estimated_refund': fees_and_refunds['final_refund'],
                'policy_version': '1.0',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Save to database
            await db.return_requests.insert_one(return_record)
            
            # Generate label if needed
            label_info = await self._handle_return_label_generation(
                return_record, order, return_data
            )
            
            if label_info:
                return_record.update(label_info)
                await db.return_requests.update_one(
                    {'id': return_id},
                    {'$set': label_info}
                )
            
            # Create response
            return {
                'success': True,
                'return_id': return_id,
                'status': decision_result['status'],
                'decision': decision_result['decision'],
                'policy_version': '1.0',
                'fees': fees_and_refunds['fees'],
                'estimated_refund': fees_and_refunds['final_refund'],
                'label_url': label_info.get('label_url') if label_info else None,
                'tracking_number': label_info.get('tracking_number') if label_info else None,
                'explain_trace': decision_result['explain_trace'],
                'message': decision_result['message']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def _get_eligible_items(self, order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get eligible items for return from an order"""
        eligible_items = []
        
        for line_item in order.get('line_items', []):
            eligible_qty = await self._calculate_eligible_quantity(line_item)
            
            if eligible_qty > 0:
                eligible_items.append({
                    'fulfillment_line_item_id': line_item['id'],
                    'title': line_item['title'],
                    'variant_title': line_item.get('variant_title'),
                    'sku': line_item.get('sku', ''),
                    'image_url': line_item.get('image_url'),
                    'quantity_ordered': line_item['quantity'],
                    'quantity_eligible': eligible_qty,
                    'price': float(line_item['price']),
                    'refundable_amount': float(line_item['price']) * eligible_qty
                })
        
        return eligible_items

    async def _calculate_eligible_quantity(self, line_item: Dict[str, Any]) -> int:
        """Calculate eligible quantity for return based on fulfillment status"""
        try:
            # Check if item is fulfilled
            if line_item.get('fulfillment_status') != 'fulfilled':
                return 0
            
            # Check existing returns for this item
            existing_returns = await db.return_requests.find({
                'tenant_id': self.tenant_id,
                'items.fulfillment_line_item_id': line_item['id'],
                'status': {'$in': ['approved', 'completed', 'requested']}
            }).to_list(100)
            
            returned_quantity = 0
            for return_req in existing_returns:
                for item in return_req.get('items', []):
                    if item.get('fulfillment_line_item_id') == line_item['id']:
                        returned_quantity += item.get('quantity', 0)
            
            eligible_quantity = line_item['quantity'] - returned_quantity
            return max(0, eligible_quantity)
            
        except Exception:
            return 0

    async def _get_order_policy_preview(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Get policy preview for an order"""
        try:
            # Get tenant settings
            tenant = await db.tenants.find_one({'id': self.tenant_id})
            return_window = tenant.get('settings', {}).get('return_window_days', 30)
            
            # Calculate return window
            order_date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            days_since_order = (datetime.utcnow() - order_date).days
            within_window = days_since_order <= return_window
            days_remaining = max(0, return_window - days_since_order)
            
            # Get eligible items
            eligible_items = await self._get_eligible_items(order)
            
            return {
                'within_window': within_window,
                'days_remaining': days_remaining,
                'fees': {'restocking_fee': 0.0, 'shipping_fee': 0.0},
                'estimated_refund': sum(item['refundable_amount'] for item in eligible_items),
                'restrictions': [] if within_window else [f'Order is outside {return_window}-day return window'],
                'auto_approve_eligible': within_window and len(eligible_items) > 0
            }
            
        except Exception:
            return {
                'within_window': False,
                'days_remaining': 0,
                'fees': {'restocking_fee': 0.0, 'shipping_fee': 0.0},
                'estimated_refund': 0.0,
                'restrictions': ['Unable to calculate policy'],
                'auto_approve_eligible': False
            }

    async def _validate_return_request(self, order: Dict[str, Any], return_data: Dict[str, Any]):
        """Validate return request"""
        # Check return window
        order_date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
        tenant = await db.tenants.find_one({'id': self.tenant_id})
        return_window = tenant.get('settings', {}).get('return_window_days', 30)
        days_since_order = (datetime.utcnow() - order_date).days
        
        if days_since_order > return_window and not return_data.get('admin_override_approve'):
            raise Exception(f"Order is outside {return_window}-day return window")
        
        # Validate items
        for item_request in return_data['items']:
            line_item = next(
                (li for li in order['line_items'] if li['id'] == item_request['fulfillment_line_item_id']),
                None
            )
            if not line_item:
                raise Exception(f"Invalid item ID: {item_request['fulfillment_line_item_id']}")
            
            eligible_qty = await self._calculate_eligible_quantity(line_item)
            if item_request['quantity'] > eligible_qty:
                raise Exception(
                    f"Quantity {item_request['quantity']} exceeds eligible quantity {eligible_qty}"
                )

    async def _calculate_fees_and_refunds(self, order: Dict[str, Any], items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate fees and refund amounts"""
        total_refund = 0.0
        fees = {'restocking_fee': 0.0, 'shipping_fee': 0.0}
        
        for item_request in items:
            line_item = next(
                (li for li in order['line_items'] if li['id'] == item_request['fulfillment_line_item_id']),
                None
            )
            if line_item:
                item_refund = float(line_item['price']) * item_request['quantity']
                total_refund += item_refund
                
                # Apply restocking fee for certain reasons
                if item_request.get('reason') in ['changed_mind', 'wrong_size']:
                    fees['restocking_fee'] += item_refund * 0.10
        
        final_refund = total_refund - sum(fees.values())
        
        return {
            'subtotal': total_refund,
            'fees': fees,
            'final_refund': final_refund
        }

    async def _determine_approval_decision(self, return_data: Dict[str, Any], fees_and_refunds: Dict[str, Any]) -> Dict[str, Any]:
        """Determine if return should be auto-approved"""
        # Check for admin override
        if return_data.get('admin_override_approve'):
            return {
                'status': 'approved',
                'decision': 'approved',
                'explain_trace': [
                    'Admin override: Return auto-approved by staff',
                    f'Estimated refund: ${fees_and_refunds["final_refund"]:.2f}',
                    'Return instructions will be sent immediately'
                ],
                'message': 'Return approved via admin override. Return label will be generated.'
            }
        
        # Check auto-approval criteria
        auto_approve_reasons = ['damaged_defective', 'not_as_described']
        auto_approve = all(
            item.get('reason') in auto_approve_reasons 
            for item in return_data['items']
        )
        
        if auto_approve:
            return {
                'status': 'approved',
                'decision': 'approved',
                'explain_trace': [
                    'Auto-approval criteria met (damaged/defective items)',
                    f'Estimated refund: ${fees_and_refunds["final_refund"]:.2f}',
                    'Return instructions will be sent immediately'
                ],
                'message': 'Return approved. Return label has been generated.'
            }
        else:
            return {
                'status': 'requested',
                'decision': 'requested',
                'explain_trace': [
                    'Return submitted for manual review',
                    'Review will be completed within 1-2 business days',
                    f'Estimated refund: ${fees_and_refunds["final_refund"]:.2f}',
                    'You will receive email notification with decision'
                ],
                'message': 'Return request submitted. You will receive updates via email.'
            }

    async def _handle_return_label_generation(self, return_record: Dict[str, Any], order: Dict[str, Any], return_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle return label generation if needed"""
        # Only generate labels for auto-approved returns with prepaid method
        if (return_record['status'] == 'approved' and 
            return_data['return_method'] == 'prepaid_label'):
            
            try:
                # Mock label generation - replace with actual service
                label_url = f"https://returns-api.example.com/labels/{return_record['id']}.pdf"
                tracking_number = f"RET{return_record['id'][:8].upper()}"
                
                return {
                    'label_url': label_url,
                    'tracking_number': tracking_number
                }
            except Exception as e:
                print(f"Label generation failed: {e}")
                return None
        
        return None

    def _get_customer_name(self, order: Dict[str, Any]) -> str:
        """Extract customer name from order"""
        billing_address = order.get('billing_address', {})
        first_name = billing_address.get('first_name', '')
        last_name = billing_address.get('last_name', '')
        return f"{first_name} {last_name}".strip() or "Customer"