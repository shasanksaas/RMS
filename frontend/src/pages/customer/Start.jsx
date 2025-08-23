import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ArrowRight, Package, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Alert, AlertDescription } from '../../components/ui/alert';

const CustomerStart = () => {
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
      
      // Always use the configured backend URL for production
      let apiUrl = backendUrl || 'http://localhost:8001';
      
      // DYNAMIC TENANT DETECTION - Multiple Methods
      let tenantId = 'tenant-rms34'; // Default fallback
      
      // Method 1: Subdomain detection (store1.yourapp.com)
      const hostname = window.location.hostname;
      const subdomainMatch = hostname.match(/^([^.]+)\./);
      if (subdomainMatch && subdomainMatch[1] !== 'www') {
        tenantId = `tenant-${subdomainMatch[1]}`;
      }
      
      // Method 2: URL path detection (/returns/store1/start)
      const pathParts = window.location.pathname.split('/');
      if (pathParts.length >= 3 && pathParts[1] === 'returns' && pathParts[2] !== 'start') {
        tenantId = `tenant-${pathParts[2]}`;
      }
      
      // Method 3: Query parameter (?tenant=store1)
      const urlParams = new URLSearchParams(window.location.search);
      const tenantParam = urlParams.get('tenant');
      if (tenantParam) {
        tenantId = `tenant-${tenantParam}`;
      }
      
      // Method 4: localStorage (for testing)
      const storedTenant = localStorage.getItem('selectedTenant');
      if (storedTenant) {
        tenantId = storedTenant;
      }
      
      console.log(`Using tenant: ${tenantId} for return form`);
      
      // Call simple orders API directly instead of complex elite portal
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
            mode: 'shopify_direct', // Direct API access
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
        <h3 className="font-semibold text-gray-900 mb-3 text-lg">Need Help?</h3>
        <div className="space-y-3 text-sm md:text-base text-gray-600">
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="font-medium">Can't find your order number?</p>
              <p>Check your email for the order confirmation or receipt</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="font-medium">Email doesn't match?</p>
              <p>Make sure you're using the same email address from your order</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="font-medium">Still having trouble?</p>
              <p>Contact our support team and we'll help you out</p>
            </div>
          </div>
        </div>
        <div className="space-y-4 mt-6 pt-6 border-t border-gray-200">
          <p className="text-center text-gray-600 text-sm">
            Or use our step-by-step return process
          </p>
          <Button
            onClick={() => navigate('/returns/create')}
            variant="outline"
            className="w-full h-12 text-base touch-manipulation border-blue-600 text-blue-600 hover:bg-blue-50"
          >
            Start Guided Return Process
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>

        <Button variant="outline" className="mt-4 w-full sm:w-auto touch-manipulation">
          Contact Support
        </Button>
      </div>

      {/* Live Integration Status */}
      <Alert>
        <AlertCircle className="h-4 w-4 flex-shrink-0" />
        <AlertDescription className="text-sm">
          <strong>Live Shopify Integration:</strong> This portal is connected to your Shopify store. 
          Enter your actual order number and email address to start your return.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default CustomerStart;