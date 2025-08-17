import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ArrowRight, Package, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Alert, AlertDescription } from '../../components/ui/alert';

const SimpleStart = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    orderNumber: '',
    email: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Get backend URL from environment
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      let apiUrl = backendUrl || 'http://localhost:8001';
      
      // Use the tenant that has Shopify orders
      const tenantId = 'tenant-rms34';
      
      // Call simple orders API directly
      const response = await fetch(`${apiUrl}/api/orders`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const orders = data.items || [];
      console.log('Available orders:', orders);

      // Find matching order by order number (flexible matching)
      const normalizedInput = formData.orderNumber.toLowerCase().trim();
      const matchingOrder = orders.find(order => {
        const orderNum = (order.order_number || '').toLowerCase();
        const orderId = (order.id || '').toLowerCase();
        
        return orderNum === normalizedInput || 
               orderNum === `#${normalizedInput}` ||
               normalizedInput === orderNum.replace('#', '') ||
               orderId === normalizedInput;
      });

      if (matchingOrder) {
        // Success - navigate to item selection with order data
        navigate('/returns/select', { 
          state: { 
            order: matchingOrder,
            orderNumber: formData.orderNumber, 
            email: formData.email,
            mode: 'shopify_direct',
            tenantId: tenantId
          } 
        });
      } else {
        // Show available orders for testing
        const availableOrders = orders.slice(0, 5).map(o => o.order_number).join(', ');
        setError(`Order not found. Available test orders: ${availableOrders}`);
      }
    } catch (err) {
      console.error('Order lookup error:', err);
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (error) setError(''); // Clear error when user types
  };

  const handleTestOrder = () => {
    setFormData({
      orderNumber: '#1001',
      email: 'test@example.com'
    });
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 md:space-y-8 px-4 sm:px-0">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <div className="w-12 h-12 md:w-16 md:h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
          <Package className="h-6 w-6 md:h-8 md:w-8 text-blue-600" />
        </div>
        <div>
          <h1 className="text-2xl md:text-4xl font-bold text-gray-900 mb-2">Start Your Return</h1>
          <p className="text-lg md:text-xl text-gray-600">
            We'll help you return or exchange your items quickly and easily
          </p>
        </div>
      </div>

      {/* Quick Test Button */}
      <div className="text-center">
        <Button
          onClick={handleTestOrder}
          variant="outline"
          className="mb-4"
        >
          Use Test Order (#1001)
        </Button>
      </div>

      {/* Order Lookup Form */}
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-lg md:text-xl">
            <Search className="h-5 w-5 flex-shrink-0" />
            <span>Find Your Order</span>
          </CardTitle>
          <CardDescription className="text-sm md:text-base">
            Enter your order number and email address to get started
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-4">
              <div>
                <Label htmlFor="orderNumber" className="text-sm md:text-base font-medium">
                  Order Number
                </Label>
                <Input
                  id="orderNumber"
                  type="text"
                  placeholder="e.g. #1001, #1002, #1003, etc."
                  value={formData.orderNumber}
                  onChange={(e) => handleInputChange('orderNumber', e.target.value)}
                  required
                  className="mt-2 h-12 text-base md:text-lg touch-manipulation"
                  disabled={loading}
                />
                <p className="text-xs md:text-sm text-gray-500 mt-1">
                  Try: #1001, #1002, #1003, #1004, #1005, or #1006
                </p>
              </div>

              <div>
                <Label htmlFor="email" className="text-sm md:text-base font-medium">
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter any email for testing"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  required
                  className="mt-2 h-12 text-base md:text-lg touch-manipulation"
                  disabled={loading}
                />
                <p className="text-xs md:text-sm text-gray-500 mt-1">
                  Any email works for testing
                </p>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-12 text-base md:text-lg touch-manipulation"
              disabled={loading || !formData.orderNumber || !formData.email}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Looking up your order...
                </>
              ) : (
                <>
                  Look up order
                  <ArrowRight className="ml-2 h-5 w-5" />
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Help Section */}
      <div className="bg-gray-50 rounded-lg p-4 md:p-6">
        <h3 className="font-semibold text-gray-900 mb-3 text-lg">Testing Instructions</h3>
        <div className="space-y-3 text-sm md:text-base text-gray-600">
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="font-medium">Available Test Orders:</p>
              <p>#1001, #1002, #1003, #1004, #1005, #1006</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="font-medium">Exchange Feature:</p>
              <p>After selecting items, choose "Exchange" to test the new exchange feature with ProductSelector</p>
            </div>
          </div>
        </div>
      </div>

      {/* Live Integration Status */}
      <Alert>
        <AlertCircle className="h-4 w-4 flex-shrink-0" />
        <AlertDescription className="text-sm">
          <strong>Live Shopify Data:</strong> This form uses real orders synced from your Shopify store. 
          6 orders are available for testing the return and exchange flow.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default SimpleStart;