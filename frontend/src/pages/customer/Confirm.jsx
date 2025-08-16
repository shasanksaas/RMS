import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { CheckCircle, Package, ArrowRight, Download, Mail } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';

const Confirm = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { orderNumber, email, selectedItems, resolution, order, mode, tenantId } = location.state || {};
  
  const [returnRequest, setReturnRequest] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!orderNumber || !email || !selectedItems || !resolution || !order) {
      navigate('/returns/start');
      return;
    }
  }, [orderNumber, email, selectedItems, resolution, order, navigate]);

  const handleSubmit = async () => {
    setSubmitting(true);

    try {
      // Get backend URL
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      
      // Use the passed tenant ID or determine it
      let currentTenantId = tenantId;
      if (!currentTenantId) {
        currentTenantId = 'tenant-rms34'; // Default to Shopify-connected tenant
        if (window.location.hostname.includes('fashion') || localStorage.getItem('selectedTenant') === 'tenant-fashion-store') {
          currentTenantId = 'tenant-fashion-store';
        }
      }

      // Prepare return request data using the real order ID
      let returnRequestData;
      
      // Handle exchange requests differently
      if (resolution.id === 'exchange' && resolution.exchange) {
        returnRequestData = {
          order_id: String(order.id),
          customer_email: email,
          return_method: 'prepaid_label',
          items: Object.values(selectedItems).map(item => ({
            line_item_id: String(item.line_item_id || item.id),
            sku: item.sku || 'N/A',
            title: item.title || item.name,
            variant_title: item.variant_title || null,
            quantity: parseInt(item.quantity) || 1,
            unit_price: parseFloat(item.unit_price || item.price) || 0,
            reason: item.reason || 'exchange',
            reason_description: 'Customer requested exchange',
            condition: item.condition || 'used',
            photos: item.photos || [],
            notes: item.notes || ''
          })),
          exchange_items: [{
            product_id: resolution.exchange.product.id,
            variant_id: resolution.exchange.variant.id,
            quantity: 1,
            price: parseFloat(resolution.exchange.variant.price)
          }],
          customer_note: `Exchange request for ${resolution.exchange.product.title} - ${resolution.exchange.variant.title}`,
          resolution_type: 'exchange'
        };
      } else {
        // Regular return request
        returnRequestData = {
          order_id: String(order.id),
          customer_email: email,
          return_method: 'prepaid_label',
          items: Object.values(selectedItems).map(item => ({
            line_item_id: String(item.line_item_id || item.id),
            sku: item.sku || 'N/A',
            title: item.title || item.name,
            variant_title: item.variant_title || null,
            quantity: parseInt(item.quantity) || 1,
            unit_price: parseFloat(item.unit_price || item.price) || 0,
            reason: item.reason || 'wrong_size',
            reason_description: item.reason_description || '',
            condition: item.condition || 'used',
            photos: item.photos || [],
            notes: item.notes || ''
          })),
          customer_note: `Selected resolution: ${resolution.title || resolution.id}`
        };
      }

      console.log('Sending return request data:', JSON.stringify(returnRequestData, null, 2));

      // Choose API endpoint based on request type
      const apiEndpoint = returnRequestData.resolution_type === 'exchange' 
        ? '/api/exchange/create' 
        : '/api/elite/portal/returns/create';

      // Call appropriate API to create return/exchange
      const response = await fetch(`${backendUrl}${apiEndpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': currentTenantId
        },
        body: JSON.stringify(returnRequestData)
      });

      const responseData = await response.json();

      if (response.ok && (responseData.success || responseData.exchange_request)) {
        // Handle different response formats
        let returnId, status, estimatedRefund;
        
        if (returnRequestData.resolution_type === 'exchange') {
          // Exchange response format
          returnId = responseData.exchange_request?.exchange_id;
          status = responseData.exchange_request?.status || 'requested';
          estimatedRefund = 0; // Exchanges don't have estimated refunds
        } else {
          // Regular return response format
          returnId = responseData.return_request?.return_id;
          status = responseData.return_request?.status || 'submitted';
          estimatedRefund = responseData.return_request?.estimated_refund?.amount || resolution.amount;
        }

        // Success - create return request object
        const newReturnRequest = {
          id: returnId,
          orderNumber,
          status: status,
          resolutionType: resolution.id,
          estimatedRefund: estimatedRefund,
          items: selectedItems,
          submittedAt: new Date().toISOString(),
          trackingUrl: `/returns/status/${returnId}`,
          isExchange: returnRequestData.resolution_type === 'exchange'
        };

        setReturnRequest(newReturnRequest);

        // Navigate to status page after brief delay
        setTimeout(() => {
          navigate(newReturnRequest.trackingUrl);
        }, 3000);

      } else {
        // Handle API error
        const errorMessage = responseData.detail || responseData.message || `API Error: ${response.status}`;
        throw new Error(errorMessage);
      }

    } catch (error) {
      console.error('Return submission error:', error);
      alert(`Return creation failed: ${error.message}`);
      setSubmitting(false);
    }
  };

  if (!selectedItems || !resolution) {
    return null;
  }

  // If return request was created successfully
  if (returnRequest) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Return Submitted!</h1>
            <p className="text-xl text-gray-600">
              Your return request has been successfully submitted
            </p>
          </div>
        </div>

        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-6 text-center">
            <h3 className="text-lg font-semibold text-green-900 mb-2">
              {returnRequest.isExchange ? 'Exchange ID:' : 'Return ID:'} {returnRequest.id}
            </h3>
            <p className="text-green-800">
              {returnRequest.isExchange 
                ? "Your exchange request has been submitted! We'll process it once we receive your returned items."
                : "You'll receive an email confirmation shortly with tracking details and next steps."
              }
            </p>
          </CardContent>
        </Card>

        <div className="text-center">
          <p className="text-gray-600 mb-4">Redirecting to tracking page...</p>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        </div>
      </div>
    );
  }

  const totalRefund = Object.values(selectedItems).reduce((total, item) => {
    return total + (item.quantity * (item.price || 0));
  }, 0);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Confirm Your Return</h1>
        <p className="text-gray-500">Please review your return details before submitting</p>
      </div>

      {/* Return Details */}
      <Card>
        <CardHeader>
          <CardTitle>Return Details</CardTitle>
          <CardDescription>Order {orderNumber}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Items */}
          <div>
            <h3 className="font-semibold text-lg mb-3">Items to Return</h3>
            <div className="space-y-3">
              {Object.values(selectedItems).map((selectedItem, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                      <Package className="h-6 w-6 text-gray-400" />
                    </div>
                    <div>
                      <h4 className="font-medium">{selectedItem.name || selectedItem.title}</h4>
                      <p className="text-sm text-gray-500">
                        Quantity: {selectedItem.quantity} • 
                        Reason: {selectedItem.reason?.replace('_', ' ') || 'Not specified'}
                      </p>
                      {selectedItem.notes && (
                        <p className="text-sm text-gray-500 italic">"{selectedItem.notes}"</p>
                      )}
                    </div>
                  </div>
                  <div className="font-semibold">
                    ${(selectedItem.quantity * (selectedItem.price || 0)).toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Resolution Details */}
          <div>
            <h3 className="font-semibold text-lg mb-3">Resolution</h3>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-blue-900">{resolution.title}</h4>
                  <p className="text-sm text-blue-700">{resolution.description}</p>
                  
                  {/* Exchange Item Details */}
                  {resolution.id === 'exchange' && resolution.exchange && (
                    <div className="mt-3 p-3 bg-white rounded border border-blue-200">
                      <h5 className="font-medium text-blue-900 mb-2">Exchange Item:</h5>
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center overflow-hidden">
                          {resolution.exchange.product.image_url ? (
                            <img 
                              src={resolution.exchange.product.image_url} 
                              alt={resolution.exchange.product.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full bg-gray-200 rounded flex items-center justify-center">
                              <span className="text-xs text-gray-500">IMG</span>
                            </div>
                          )}
                        </div>
                        <div>
                          <p className="font-medium text-sm">{resolution.exchange.product.title}</p>
                          <p className="text-sm text-gray-600">{resolution.exchange.variant.title}</p>
                          <p className="text-sm font-semibold text-green-600">
                            ${parseFloat(resolution.exchange.variant.price).toFixed(2)}
                          </p>
                        </div>
                      </div>
                      
                      {/* Price Difference */}
                      {resolution.exchange.price_difference && (
                        <div className="mt-3 pt-3 border-t border-blue-200">
                          <div className="text-sm">
                            {resolution.exchange.price_difference.difference_type === 'charge' && (
                              <p className="text-red-600 font-medium">
                                Additional payment required: ${resolution.exchange.price_difference.absolute_difference.toFixed(2)}
                              </p>
                            )}
                            {resolution.exchange.price_difference.difference_type === 'refund' && (
                              <p className="text-green-600 font-medium">
                                Refund due: ${resolution.exchange.price_difference.absolute_difference.toFixed(2)}
                              </p>
                            )}
                            {resolution.exchange.price_difference.difference_type === 'even' && (
                              <p className="text-gray-600 font-medium">No price difference</p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-600">
                    {resolution.id === 'exchange' ? 'Exchange' : `$${resolution.amount.toFixed(2)}`}
                  </div>
                  <p className="text-sm text-blue-600">{resolution.processing}</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Terms and Conditions */}
      <Card>
        <CardHeader>
          <CardTitle>Terms and Conditions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />
              <p>Items must be returned in original condition with all tags attached</p>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />
              <p>Returns are processed within 3-5 business days of receipt</p>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />
              <p>Refunds may take 5-7 business days to appear on your original payment method</p>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />
              <p>You'll receive email updates throughout the return process</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Next Steps */}
      <Alert>
        <Mail className="h-4 w-4" />
        <AlertDescription>
          <strong>What happens next:</strong> 
          {resolution.id === 'exchange' 
            ? " After submitting your exchange request, you'll receive an email with a prepaid return label. Once we receive and inspect your returned items, we'll send your new exchange item and process any payment difference."
            : " After submitting your return, you'll receive an email with a prepaid return label and packaging instructions. Simply pack your items and drop them off at any authorized location."
          }
        </AlertDescription>
      </Alert>

      {/* Submit Button */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-6">
          <div className="text-center space-y-4">
            <div className="text-lg font-semibold">
              Ready to submit your {resolution.id === 'exchange' ? 'exchange' : 'return'} request?
            </div>
            <Button 
              onClick={handleSubmit} 
              className="w-full max-w-md"
              size="lg"
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Submitting {resolution.id === 'exchange' ? 'Exchange' : 'Return'} Request...
                </>
              ) : (
                <>
                  Submit {resolution.id === 'exchange' ? 'Exchange' : 'Return'} Request
                  <ArrowRight className="ml-2 h-5 w-5" />
                </>
              )}
            </Button>
            <p className="text-sm text-gray-600">
              By submitting, you agree to our {resolution.id === 'exchange' ? 'exchange' : 'return'} policy and terms of service
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Confirm;