import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Badge } from './components/ui/badge';
import { Textarea } from './components/ui/textarea';
import { Alert, AlertDescription } from './components/ui/alert';
import { Separator } from './components/ui/separator';
import { 
  Search, 
  Package, 
  ArrowLeft, 
  Mail, 
  User, 
  Calendar,
  DollarSign,
  CheckCircle,
  Clock,
  XCircle,
  Truck
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// This would normally come from URL params or tenant configuration
const DEMO_TENANT_ID = 'demo-tenant-customer-portal';

const CustomerPortal = () => {
  const [currentStep, setCurrentStep] = useState('lookup'); // lookup, order_select, return_form, confirmation, track
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [customerInfo, setCustomerInfo] = useState({ email: '', orderNumber: '' });
  const [returnRequest, setReturnRequest] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Look up customer orders
  const handleOrderLookup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // In real implementation, this would be a public API endpoint
      // that doesn't require tenant headers for customer access
      const response = await axios.get(`${API}/orders`, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID },
        params: {
          customer_email: customerInfo.email,
          order_number: customerInfo.orderNumber
        }
      });

      const filteredOrders = response.data.filter(order => 
        order.customer_email.toLowerCase() === customerInfo.email.toLowerCase() &&
        (!customerInfo.orderNumber || order.order_number === customerInfo.orderNumber)
      );

      if (filteredOrders.length === 0) {
        setError('No orders found with the provided information. Please check your email and order number.');
        setOrders([]);
      } else {
        setOrders(filteredOrders);
        if (filteredOrders.length === 1) {
          setSelectedOrder(filteredOrders[0]);
          setCurrentStep('return_form');
        } else {
          setCurrentStep('order_select');
        }
      }
    } catch (err) {
      setError('Unable to find orders. Please check your information and try again.');
      console.error('Order lookup error:', err);
    }

    setLoading(false);
  };

  // Submit return request
  const handleReturnSubmit = async (returnData) => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/returns`, returnData, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });

      setReturnRequest(response.data);
      setCurrentStep('confirmation');
    } catch (err) {
      setError('Unable to submit return request. Please try again.');
      console.error('Return submission error:', err);
    }

    setLoading(false);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'requested': return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'approved': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'denied': return <XCircle className="h-4 w-4 text-red-600" />;
      case 'in_transit': return <Truck className="h-4 w-4 text-blue-600" />;
      case 'received': return <Package className="h-4 w-4 text-purple-600" />;
      case 'refunded': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'exchanged': return <CheckCircle className="h-4 w-4 text-indigo-600" />;
      default: return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'requested': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'approved': 'bg-green-100 text-green-800 border-green-200',
      'denied': 'bg-red-100 text-red-800 border-red-200',
      'in_transit': 'bg-blue-100 text-blue-800 border-blue-200',
      'received': 'bg-purple-100 text-purple-800 border-purple-200',
      'refunded': 'bg-green-100 text-green-800 border-green-200',
      'exchanged': 'bg-indigo-100 text-indigo-800 border-indigo-200'
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Package className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Returns Portal</h1>
                <p className="text-sm text-gray-500">Easy returns and exchanges</p>
              </div>
            </div>
            {currentStep !== 'lookup' && (
              <Button 
                variant="ghost" 
                onClick={() => {
                  setCurrentStep('lookup');
                  setOrders([]);
                  setSelectedOrder(null);
                  setReturnRequest(null);
                  setError('');
                }}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Start Over</span>
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Step 1: Order Lookup */}
        {currentStep === 'lookup' && (
          <OrderLookupStep
            customerInfo={customerInfo}
            setCustomerInfo={setCustomerInfo}
            onSubmit={handleOrderLookup}
            loading={loading}
            error={error}
          />
        )}

        {/* Step 2: Order Selection */}
        {currentStep === 'order_select' && (
          <OrderSelectionStep
            orders={orders}
            onSelectOrder={(order) => {
              setSelectedOrder(order);
              setCurrentStep('return_form');
            }}
          />
        )}

        {/* Step 3: Return Form */}
        {currentStep === 'return_form' && selectedOrder && (
          <ReturnFormStep
            order={selectedOrder}
            onSubmit={handleReturnSubmit}
            loading={loading}
            error={error}
          />
        )}

        {/* Step 4: Confirmation */}
        {currentStep === 'confirmation' && returnRequest && (
          <ConfirmationStep
            returnRequest={returnRequest}
            order={selectedOrder}
            formatCurrency={formatCurrency}
            formatDate={formatDate}
            getStatusIcon={getStatusIcon}
            getStatusColor={getStatusColor}
          />
        )}
      </div>
    </div>
  );
};

// Order Lookup Step Component
const OrderLookupStep = ({ customerInfo, setCustomerInfo, onSubmit, loading, error }) => (
  <Card className="max-w-md mx-auto">
    <CardHeader className="text-center">
      <CardTitle className="flex items-center justify-center space-x-2">
        <Search className="h-5 w-5 text-blue-600" />
        <span>Find Your Order</span>
      </CardTitle>
      <CardDescription>
        Enter your email and order number to start a return
      </CardDescription>
    </CardHeader>
    <CardContent>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <Label htmlFor="email">Email Address</Label>
          <div className="relative mt-1">
            <Mail className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={customerInfo.email}
              onChange={(e) => setCustomerInfo({...customerInfo, email: e.target.value})}
              className="pl-10"
              required
            />
          </div>
        </div>

        <div>
          <Label htmlFor="orderNumber">Order Number</Label>
          <div className="relative mt-1">
            <Package className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
            <Input
              id="orderNumber"
              placeholder="Enter order number (optional)"
              value={customerInfo.orderNumber}
              onChange={(e) => setCustomerInfo({...customerInfo, orderNumber: e.target.value})}
              className="pl-10"
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Leave blank to see all orders for your email
          </p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Button 
          type="submit" 
          className="w-full" 
          disabled={loading || !customerInfo.email}
        >
          {loading ? 'Searching...' : 'Find My Orders'}
        </Button>
      </form>
    </CardContent>
  </Card>
);

// Order Selection Step Component
const OrderSelectionStep = ({ orders, onSelectOrder }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Select an Order</CardTitle>
        <CardDescription>
          Choose the order you'd like to return items from
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {orders.map((order) => (
            <Card 
              key={order.id} 
              className="cursor-pointer hover:bg-blue-50 border-2 hover:border-blue-200 transition-all"
              onClick={() => onSelectOrder(order)}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold">Order #{order.order_number}</p>
                    <p className="text-sm text-gray-600">{formatDate(order.order_date)}</p>
                    <p className="text-sm text-gray-600">{order.items.length} item(s)</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{formatCurrency(order.total_amount)}</p>
                    <Button size="sm" className="mt-2">Select</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// Return Form Step Component
const ReturnFormStep = ({ order, onSubmit, loading, error }) => {
  const [selectedItems, setSelectedItems] = useState([]);
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const itemsToReturn = selectedItems.map(itemId => {
      return order.items.find(item => `${item.product_id}-${item.sku}` === itemId);
    }).filter(Boolean);

    onSubmit({
      order_id: order.id,
      reason,
      items_to_return: itemsToReturn,
      notes: notes || undefined
    });
  };

  const totalRefundAmount = selectedItems.reduce((total, itemId) => {
    const item = order.items.find(item => `${item.product_id}-${item.sku}` === itemId);
    return total + (item ? item.price * item.quantity : 0);
  }, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Return Request</CardTitle>
        <CardDescription>
          Order #{order.order_number} - {formatDate(order.order_date)}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Order Items */}
          <div>
            <Label className="text-base font-medium">Items to Return</Label>
            <p className="text-sm text-gray-600 mb-3">Select the items you'd like to return</p>
            
            <div className="space-y-3">
              {order.items.map((item) => {
                const itemId = `${item.product_id}-${item.sku}`;
                const isSelected = selectedItems.includes(itemId);
                
                return (
                  <div 
                    key={itemId} 
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => {
                      if (isSelected) {
                        setSelectedItems(selectedItems.filter(id => id !== itemId));
                      } else {
                        setSelectedItems([...selectedItems, itemId]);
                      }
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}} // Handled by div onClick
                          className="rounded"
                        />
                        <div>
                          <p className="font-medium">{item.product_name}</p>
                          <p className="text-sm text-gray-600">SKU: {item.sku}</p>
                          <p className="text-sm text-gray-600">Quantity: {item.quantity}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{formatCurrency(item.price)}</p>
                        <p className="text-sm text-gray-600">each</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Return Reason */}
          <div>
            <Label htmlFor="reason">Reason for Return</Label>
            <Select value={reason} onValueChange={setReason} required>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select a reason..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="defective">Defective/Damaged</SelectItem>
                <SelectItem value="wrong_size">Wrong Size</SelectItem>
                <SelectItem value="wrong_color">Wrong Color</SelectItem>
                <SelectItem value="not_as_described">Not as Described</SelectItem>
                <SelectItem value="damaged_in_shipping">Damaged in Shipping</SelectItem>
                <SelectItem value="changed_mind">Changed Mind</SelectItem>
                <SelectItem value="quality_issues">Quality Issues</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Additional Notes */}
          <div>
            <Label htmlFor="notes">Additional Details (Optional)</Label>
            <Textarea
              id="notes"
              placeholder="Please provide any additional details about your return..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1"
              rows={3}
            />
          </div>

          {/* Refund Summary */}
          {selectedItems.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex justify-between items-center">
                <span className="font-medium">Estimated Refund:</span>
                <span className="text-lg font-bold text-green-600">
                  {formatCurrency(totalRefundAmount)}
                </span>
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Final refund amount will be processed after item inspection
              </p>
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button 
            type="submit" 
            className="w-full" 
            disabled={loading || selectedItems.length === 0 || !reason}
          >
            {loading ? 'Submitting Return...' : 'Submit Return Request'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

// Confirmation Step Component
const ConfirmationStep = ({ returnRequest, order, formatCurrency, formatDate, getStatusIcon, getStatusColor }) => (
  <div className="space-y-6">
    {/* Success Message */}
    <Card className="border-green-200 bg-green-50">
      <CardContent className="p-6">
        <div className="flex items-center space-x-3">
          <CheckCircle className="h-8 w-8 text-green-600" />
          <div>
            <h3 className="text-lg font-semibold text-green-900">Return Request Submitted</h3>
            <p className="text-green-700">We've received your return request and will process it shortly.</p>
          </div>
        </div>
      </CardContent>
    </Card>

    {/* Return Details */}
    <Card>
      <CardHeader>
        <CardTitle>Return Request Details</CardTitle>
        <CardDescription>
          Keep this information for your records
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-medium text-gray-500">Return Request ID</Label>
            <p className="font-mono text-sm">{returnRequest.id}</p>
          </div>
          <div>
            <Label className="text-sm font-medium text-gray-500">Status</Label>
            <div className="flex items-center space-x-2 mt-1">
              {getStatusIcon(returnRequest.status)}
              <Badge className={getStatusColor(returnRequest.status)}>
                {returnRequest.status.replace('_', ' ').toUpperCase()}
              </Badge>
            </div>
          </div>
          <div>
            <Label className="text-sm font-medium text-gray-500">Order Number</Label>
            <p>{order.order_number}</p>
          </div>
          <div>
            <Label className="text-sm font-medium text-gray-500">Refund Amount</Label>
            <p className="font-semibold text-green-600">{formatCurrency(returnRequest.refund_amount)}</p>
          </div>
        </div>

        <Separator />

        <div>
          <Label className="text-sm font-medium text-gray-500">Items Being Returned</Label>
          <div className="mt-2 space-y-2">
            {returnRequest.items_to_return.map((item, index) => (
              <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>{item.product_name} (SKU: {item.sku})</span>
                <span>Qty: {item.quantity} × {formatCurrency(item.price)}</span>
              </div>
            ))}
          </div>
        </div>

        <Separator />

        <div>
          <Label className="text-sm font-medium text-gray-500">Return Reason</Label>
          <p className="capitalize">{returnRequest.reason.replace('_', ' ')}</p>
        </div>

        {returnRequest.notes && (
          <div>
            <Label className="text-sm font-medium text-gray-500">Additional Notes</Label>
            <p className="text-gray-700">{returnRequest.notes}</p>
          </div>
        )}
      </CardContent>
    </Card>

    {/* Next Steps */}
    <Card>
      <CardHeader>
        <CardTitle>What Happens Next?</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-semibold text-blue-600">1</span>
            </div>
            <div>
              <p className="font-medium">Review and Approval</p>
              <p className="text-sm text-gray-600">We'll review your return request within 1-2 business days.</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-semibold text-blue-600">2</span>
            </div>
            <div>
              <p className="font-medium">Return Label</p>
              <p className="text-sm text-gray-600">Once approved, we'll email you a prepaid return shipping label.</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-semibold text-blue-600">3</span>
            </div>
            <div>
              <p className="font-medium">Ship Items</p>
              <p className="text-sm text-gray-600">Package your items securely and drop off at any shipping location.</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-semibold text-blue-600">4</span>
            </div>
            <div>
              <p className="font-medium">Refund Processing</p>
              <p className="text-sm text-gray-600">Your refund will be processed within 3-5 business days after we receive your items.</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
);

export default CustomerPortal;