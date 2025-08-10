import React, { useState } from 'react';
import { Search, Package, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Alert, AlertDescription } from '../ui/alert';

const OrderLookupForm = ({ 
  onShopifyOrderFound, 
  onFallbackModeTriggered, 
  tenantId, 
  channel = 'customer' 
}) => {
  const [orderNumber, setOrderNumber] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  const handleLookup = async () => {
    if (!orderNumber.trim() || !email.trim()) {
      setError('Please enter both order number and email address');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${backendUrl}/api/returns/order-lookup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(tenantId && { 'X-Tenant-Id': tenantId })
        },
        body: JSON.stringify({
          orderNumber: orderNumber.replace('#', '').trim(),
          email: email.toLowerCase().trim(),
          channel,
          tenantId
        })
      });

      const result = await response.json();

      if (response.ok) {
        if (result.mode === 'shopify') {
          // Shopify mode - order found
          onShopifyOrderFound(result.order);
        } else if (result.mode === 'fallback') {
          // Fallback mode - request captured for manual review
          onFallbackModeTriggered(result);
        }
        setRetryCount(0);
      } else {
        // Handle specific errors
        if (result.detail === 'ORDER_NOT_FOUND_OR_EMAIL_MISMATCH') {
          setError("We couldn't find that order. Please check your order number and email address.");
        } else if (result.detail === 'RATE_LIMIT') {
          setError(`Too many requests. Please wait ${result.retryAfterSeconds || 5} seconds and try again.`);
          // Auto retry after the specified time
          setTimeout(() => {
            if (retryCount < 3) {
              setRetryCount(prev => prev + 1);
              handleLookup();
            }
          }, (result.retryAfterSeconds || 5) * 1000);
        } else {
          setError(result.detail || 'Failed to lookup order. Please try again.');
        }
      }
    } catch (err) {
      console.error('Order lookup error:', err);
      setError('Failed to lookup order. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLookup();
    }
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Search className="h-5 w-5" />
          <span>Find Your Order</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert className={error.includes("couldn't find") ? "border-amber-200 bg-amber-50" : "border-red-200 bg-red-50"}>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className={error.includes("couldn't find") ? "text-amber-800" : "text-red-800"}>
              {error}
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="orderNumber" className="block text-sm font-medium text-gray-700 mb-2">
              Order Number *
            </label>
            <Input
              id="orderNumber"
              type="text"
              placeholder="e.g., 1001 or #1001"
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address *
            </label>
            <Input
              id="email"
              type="email"
              placeholder="Email used when placing your order"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full"
              disabled={loading}
            />
          </div>

          <Button
            onClick={handleLookup}
            disabled={loading || !orderNumber.trim() || !email.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700"
            size="lg"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {retryCount > 0 ? `Retrying... (${retryCount}/3)` : 'Looking up order...'}
              </>
            ) : (
              <>
                <Package className="h-4 w-4 mr-2" />
                Find My Order
              </>
            )}
          </Button>
        </div>

        <div className="text-center text-sm text-gray-500 mt-6">
          <div className="flex items-center justify-center space-x-4 text-xs">
            <div className="flex items-center">
              <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
              <span>Secure lookup</span>
            </div>
            <div className="flex items-center">
              <Clock className="h-3 w-3 text-blue-600 mr-1" />
              <span>Instant results</span>
            </div>
          </div>
          <p className="mt-2">
            Need help finding your order? <a href="#" className="text-blue-600 hover:underline">Contact support</a>
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default OrderLookupForm;