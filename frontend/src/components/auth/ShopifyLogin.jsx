import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { useToast } from '../ui/use-toast';

const ShopifyLogin = () => {
  const [shopDomain, setShopDomain] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { toast } = useToast();

  const handleShopifyLogin = async () => {
    if (!shopDomain.trim()) {
      setError('Please enter your shop domain');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Get backend URL from environment
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      
      if (!backendUrl) {
        throw new Error('Backend URL not configured');
      }
      
      // Direct redirect to Shopify OAuth
      const shopifyInstallUrl = `${backendUrl}/api/auth/shopify/install-redirect?shop=${encodeURIComponent(shopDomain.trim())}`;
      
      console.log('🚀 Redirecting to Shopify OAuth:', shopifyInstallUrl);
      console.log('🚀 Backend URL:', backendUrl);
      
      // Immediate redirect without toast or async delays
      window.location.href = shopifyInstallUrl;

    } catch (error) {
      console.error('❌ Shopify login error:', error);
      setError(`Failed to connect: ${error.message}`);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleShopifyLogin();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Returns Manager
          </h1>
          <p className="text-gray-600">
            Connect your Shopify store to get started
          </p>
        </div>

        <Card>
          <CardHeader className="text-center pb-6">
            <CardTitle className="text-xl font-semibold">
              Login with Shopify
            </CardTitle>
            <CardDescription>
              Enter your shop domain to connect your store and start managing returns
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* Shop Domain Input */}
            <div className="space-y-2">
              <Label htmlFor="shopDomain" className="text-sm font-medium text-gray-700">
                Shop Domain
              </Label>
              <Input
                id="shopDomain"
                type="text"
                placeholder="your-store or your-store.myshopify.com"
                value={shopDomain}
                onChange={(e) => setShopDomain(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full px-3 py-2 text-sm"
                disabled={isLoading}
                autoFocus
              />
              <p className="text-xs text-gray-500">
                Enter just the store name (e.g., "rms34") or full domain
              </p>
            </div>

            {/* Error Alert */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Shopify Login Button */}
            <Button
              onClick={handleShopifyLogin}
              disabled={isLoading || !shopDomain.trim()}
              className="w-full bg-[#95bf47] hover:bg-[#7ba337] text-white font-medium py-3 text-base"
              size="lg"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
                  Connecting...
                </div>
              ) : (
                <>
                  <svg 
                    className="w-5 h-5 mr-2" 
                    fill="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path d="M15.337 2.447c-.38-.172-.806-.245-1.245-.245-1.93 0-3.713 1.455-4.888 3.32-.852-.398-1.744-.618-2.659-.618C4.53 4.904 3 6.376 3 8.365c0 .532.134 1.047.368 1.516-.698.87-1.113 1.951-1.113 3.119 0 2.756 2.238 4.991 5 4.991h10.5c2.21 0 4-1.787 4-3.99 0-1.657-.896-3.101-2.23-3.879.147-.468.225-.957.225-1.462 0-2.756-2.238-4.991-5-4.991-.63 0-1.234.117-1.795.33-.317-1.146-1.058-2.175-2.106-2.927-.508-.365-1.09-.625-1.712-.625z"/>
                  </svg>
                  Login with Shopify
                </>
              )}
            </Button>

            {/* Help Text */}
            <div className="text-center">
              <p className="text-xs text-gray-500 mb-4">
                By connecting, you'll be redirected to Shopify to authorize our app.
                Your store data will be securely synced for returns management.
              </p>
              
              <div className="border-t pt-4">
                <p className="text-xs text-gray-400">
                  Need help? Contact support at{' '}
                  <span className="text-blue-600">hello@returnsmanager.com</span>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Features Preview */}
        <div className="mt-8">
          <div className="grid grid-cols-1 gap-4">
            <div className="flex items-start space-x-3 p-4 bg-white rounded-lg border">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-900">Instant Setup</h3>
                <p className="text-sm text-gray-500">Connect your store and start managing returns in seconds</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3 p-4 bg-white rounded-lg border">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-900">Real-time Sync</h3>
                <p className="text-sm text-gray-500">Orders and returns sync automatically with your Shopify store</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShopifyLogin;