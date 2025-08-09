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
      const backendUrl = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
      
      // Call backend API to validate order
      const response = await fetch(`${backendUrl}/api/orders/lookup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          order_number: formData.orderNumber,
          email: formData.email
        })
      });

      if (response.ok) {
        const orderData = await response.json();
        // Success - navigate to item selection with order data
        navigate('/returns/select', { 
          state: { 
            order: orderData,
            orderNumber: formData.orderNumber, 
            email: formData.email 
          } 
        });
      } else if (response.status === 404) {
        setError('We couldn\'t find that order. Please check the order number and email address.');
      } else if (response.status === 403) {
        setError('The email address doesn\'t match our records for this order.');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Unable to lookup order. Please try again.');
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
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
          <Package className="h-8 w-8 text-blue-600" />
        </div>
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Start Your Return</h1>
          <p className="text-xl text-gray-600">
            We'll help you return or exchange your items quickly and easily
          </p>
        </div>
      </div>

      {/* Order Lookup Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Search className="h-5 w-5" />
            <span>Find Your Order</span>
          </CardTitle>
          <CardDescription>
            Enter your order number and email address to get started
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-4">
              <div>
                <Label htmlFor="orderNumber" className="text-base font-medium">
                  Order Number
                </Label>
                <Input
                  id="orderNumber"
                  type="text"
                  placeholder="e.g. ORD-12345, #1001, or 1234567890"
                  value={formData.orderNumber}
                  onChange={(e) => handleInputChange('orderNumber', e.target.value)}
                  required
                  className="mt-2 h-12 text-lg"
                  disabled={loading}
                />
                <p className="text-sm text-gray-500 mt-1">
                  Check your email confirmation or receipt for your order number
                </p>
              </div>

              <div>
                <Label htmlFor="email" className="text-base font-medium">
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter the email used for your order"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  required
                  className="mt-2 h-12 text-lg"
                  disabled={loading}
                />
                <p className="text-sm text-gray-500 mt-1">
                  Use the same email address you used when placing the order
                </p>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-12 text-lg"
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
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="font-semibold text-gray-900 mb-3">Need Help?</h3>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />
            <div>
              <p className="font-medium">Can't find your order number?</p>
              <p>Check your email for the order confirmation or receipt</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />
            <div>
              <p className="font-medium">Email doesn't match?</p>
              <p>Make sure you're using the same email address from your order</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />
            <div>
              <p className="font-medium">Still having trouble?</p>
              <p>Contact our support team and we'll help you out</p>
            </div>
          </div>
        </div>
        <Button variant="outline" className="mt-4">
          Contact Support
        </Button>
      </div>

      {/* Demo Instructions */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Demo Mode:</strong> Try using order number "ORD-12345" with any valid email address, 
          or use "ORD-404" to see error handling in action.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default CustomerStart;