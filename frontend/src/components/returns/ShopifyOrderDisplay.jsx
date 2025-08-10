import React, { useState, useEffect } from 'react';
import { Package, Calendar, CreditCard, Truck, AlertTriangle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';

const ShopifyOrderDisplay = ({ 
  order, 
  onItemsSelected, 
  onBackToLookup 
}) => {
  const [selectedItems, setSelectedItems] = useState({});
  const [itemReasons, setItemReasons] = useState({});
  const [policyPreview, setPolicyPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  // Available return reasons
  const returnReasons = [
    { value: 'SIZE_WRONG', label: 'Wrong size' },
    { value: 'COLOR_WRONG', label: 'Wrong color/style' },
    { value: 'DEFECTIVE', label: 'Defective/damaged' },
    { value: 'NOT_AS_DESCRIBED', label: 'Not as described' },
    { value: 'CHANGED_MIND', label: 'Changed my mind' },
    { value: 'ARRIVED_LATE', label: 'Arrived too late' },
    { value: 'OTHER', label: 'Other reason' }
  ];

  // Update policy preview when selection changes
  useEffect(() => {
    const selectedItemsList = Object.entries(selectedItems)
      .filter(([_, qty]) => qty > 0)
      .map(([itemId, qty]) => {
        const item = order.lineItems.find(item => item.id === itemId);
        return {
          id: itemId,
          quantity: qty,
          price: item?.price || 0,
          reason: itemReasons[itemId] || 'CHANGED_MIND'
        };
      });

    if (selectedItemsList.length > 0) {
      updatePolicyPreview(selectedItemsList);
    } else {
      setPolicyPreview(null);
    }
  }, [selectedItems, itemReasons, order]);

  const updatePolicyPreview = async (items) => {
    setPreviewLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/returns/policy-preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': 'tenant-rms34'
        },
        body: JSON.stringify({
          items: items,
          orderMeta: {
            id: order.id,
            createdAt: order.createdAt,
            totalPrice: order.totalPrice
          }
        })
      });

      if (response.ok) {
        const preview = await response.json();
        setPolicyPreview(preview);
      }
    } catch (err) {
      console.error('Policy preview error:', err);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleQuantityChange = (itemId, quantity) => {
    setSelectedItems(prev => ({
      ...prev,
      [itemId]: quantity
    }));
  };

  const handleReasonChange = (itemId, reason) => {
    setItemReasons(prev => ({
      ...prev,
      [itemId]: reason
    }));
  };

  const handleContinue = () => {
    const selectedItemsList = Object.entries(selectedItems)
      .filter(([_, qty]) => qty > 0)
      .map(([itemId, qty]) => {
        const item = order.lineItems.find(item => item.id === itemId);
        return {
          ...item,
          returnQuantity: qty,
          reason: itemReasons[itemId] || 'CHANGED_MIND'
        };
      });

    onItemsSelected({
      order,
      selectedItems: selectedItemsList,
      policyPreview
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      'FULFILLED': 'bg-green-100 text-green-800',
      'DELIVERED': 'bg-green-100 text-green-800',
      'SHIPPED': 'bg-blue-100 text-blue-800',
      'PENDING': 'bg-yellow-100 text-yellow-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const eligibleItems = order.lineItems?.filter(item => item.eligibleForReturn) || [];
  const ineligibleItems = order.lineItems?.filter(item => !item.eligibleForReturn) || [];
  const hasSelectedItems = Object.values(selectedItems).some(qty => qty > 0);

  return (
    <div className="space-y-6">
      {/* Order Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Package className="h-5 w-5" />
              <span>Order {order.name}</span>
            </div>
            <Button variant="outline" size="sm" onClick={onBackToLookup}>
              Look up different order
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-sm text-gray-500">Order Date</p>
                <p className="font-medium">
                  {new Date(order.createdAt).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <CreditCard className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-sm text-gray-500">Total</p>
                <p className="font-medium">
                  {order.currency} {order.totalPrice?.toFixed(2)}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Truck className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-sm text-gray-500">Delivery</p>
                <Badge className={getStatusColor(order.deliveryStatus)}>
                  {order.deliveryStatus}
                </Badge>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Return Window</p>
              <p className={`font-medium ${order.returnWindow?.eligible ? 'text-green-600' : 'text-red-600'}`}>
                {order.returnWindow?.daysRemaining || 0} days left
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Return Window Alert */}
      {order.returnWindow && !order.returnWindow.eligible && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-red-800">
            The return window for this order has expired. Returns are typically accepted within 30 days of delivery.
          </AlertDescription>
        </Alert>
      )}

      {/* Eligible Items */}
      {eligibleItems.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span>Items Available for Return</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {eligibleItems.map((item) => (
                <div key={item.id} className="flex items-start space-x-4 p-4 border rounded-lg">
                  {item.imageUrl && (
                    <img
                      src={item.imageUrl}
                      alt={item.title}
                      className="w-16 h-16 rounded object-cover"
                    />
                  )}
                  <div className="flex-1">
                    <h4 className="font-medium">{item.title}</h4>
                    {item.variant && (
                      <p className="text-sm text-gray-600">{item.variant}</p>
                    )}
                    {item.sku && (
                      <p className="text-xs text-gray-500">SKU: {item.sku}</p>
                    )}
                    <p className="text-sm text-gray-600 mt-1">
                      Ordered: {item.quantity} | Available to return: {item.maxReturnQty}
                    </p>
                  </div>
                  
                  <div className="flex flex-col space-y-2 min-w-[200px]">
                    {/* Quantity Selector */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Return Quantity
                      </label>
                      <select
                        className="w-full p-2 border rounded"
                        value={selectedItems[item.id] || 0}
                        onChange={(e) => handleQuantityChange(item.id, parseInt(e.target.value))}
                      >
                        <option value={0}>Select quantity</option>
                        {Array.from({ length: item.maxReturnQty }, (_, i) => i + 1).map(qty => (
                          <option key={qty} value={qty}>{qty}</option>
                        ))}
                      </select>
                    </div>

                    {/* Reason Selector */}
                    {selectedItems[item.id] > 0 && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Return Reason *
                        </label>
                        <select
                          className="w-full p-2 border rounded"
                          value={itemReasons[item.id] || ''}
                          onChange={(e) => handleReasonChange(item.id, e.target.value)}
                          required
                        >
                          <option value="">Select reason</option>
                          {returnReasons.map(reason => (
                            <option key={reason.value} value={reason.value}>
                              {reason.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Ineligible Items */}
      {ineligibleItems.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              <span>Items Not Eligible for Return</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {ineligibleItems.map((item) => (
                <div key={item.id} className="flex items-start space-x-4 p-3 bg-gray-50 rounded-lg opacity-60">
                  {item.imageUrl && (
                    <img
                      src={item.imageUrl}
                      alt={item.title}
                      className="w-12 h-12 rounded object-cover"
                    />
                  )}
                  <div className="flex-1">
                    <h4 className="font-medium">{item.title}</h4>
                    {item.variant && (
                      <p className="text-sm text-gray-600">{item.variant}</p>
                    )}
                    <p className="text-xs text-amber-700 mt-1">
                      Not eligible: {item.maxReturnQty === 0 ? 'Already returned' : 'Outside return window'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Policy Preview */}
      {policyPreview && (
        <Card>
          <CardHeader>
            <CardTitle>Return Preview</CardTitle>
          </CardHeader>
          <CardContent>
            {previewLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Items Value:</span>
                  <span>${policyPreview.totalItemValue?.toFixed(2)}</span>
                </div>
                {policyPreview.fees?.map((fee, index) => (
                  <div key={index} className="flex justify-between text-red-600">
                    <span>- {fee.description}:</span>
                    <span>${fee.amount?.toFixed(2)}</span>
                  </div>
                ))}
                <hr />
                <div className="flex justify-between text-lg font-semibold text-green-600">
                  <span>Estimated Refund:</span>
                  <span>${policyPreview.estimatedRefund?.toFixed(2)}</span>
                </div>
                <p className="text-xs text-gray-500">
                  Return window: {policyPreview.returnWindow?.daysRemaining} days remaining
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Continue Button */}
      {eligibleItems.length > 0 && (
        <div className="flex justify-center">
          <Button
            onClick={handleContinue}
            disabled={!hasSelectedItems || Object.entries(selectedItems).filter(([itemId, qty]) => qty > 0).some(([itemId]) => !itemReasons[itemId])}
            size="lg"
            className="bg-blue-600 hover:bg-blue-700"
          >
            Continue with Return Request
            {hasSelectedItems && (
              <span className="ml-2">
                ({Object.values(selectedItems).reduce((sum, qty) => sum + qty, 0)} items)
              </span>
            )}
          </Button>
        </div>
      )}

      {eligibleItems.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Items Available for Return</h3>
            <p className="text-gray-600 mb-4">
              All items in this order are outside the return window or have already been returned.
            </p>
            <Button variant="outline" onClick={onBackToLookup}>
              Look Up Different Order
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ShopifyOrderDisplay;