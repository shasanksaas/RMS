import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Package, Mail, Search, ArrowRight, ShieldCheck, Clock, Truck, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import OrderLookupForm from '../../components/returns/OrderLookupForm';
import ShopifyOrderDisplay from '../../components/returns/ShopifyOrderDisplay';
import FallbackModeDisplay from '../../components/returns/FallbackModeDisplay';

const ReturnPortal = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [currentView, setCurrentView] = useState('lookup'); // 'lookup', 'shopify-order', 'fallback-mode', 'return-form'
  const [orderData, setOrderData] = useState(null);
  const [fallbackData, setFallbackData] = useState(null);
  const [selectedReturnData, setSelectedReturnData] = useState(null);

  const handleShopifyOrderFound = (order) => {
    setOrderData(order);
    setCurrentView('shopify-order');
  };

  const handleFallbackModeTriggered = (fallbackResult) => {
    setFallbackData(fallbackResult);
    setCurrentView('fallback-mode');
  };

  const handleItemsSelected = (returnData) => {
    setSelectedReturnData(returnData);
    // You could navigate to a return form here or process directly
    navigate('/portal/returns/create', {
      state: { returnData }
    });
  };

  const handleBackToLookup = () => {
    setCurrentView('lookup');
    setOrderData(null);
    setFallbackData(null);
    setSelectedReturnData(null);
  };

  const handleSubmitAdditionalInfo = (additionalData) => {
    // Process additional fallback data
    console.log('Additional fallback data:', additionalData);
    // Could show success message or navigate elsewhere
  };

  if (currentView === 'shopify-order' && orderData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto p-6">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Return Items from Your Order</h1>
            <p className="text-gray-600 mt-2">
              Select the items you'd like to return and provide a reason for each item.
            </p>
          </div>
          
          <ShopifyOrderDisplay
            order={orderData}
            onItemsSelected={handleItemsSelected}
            onBackToLookup={handleBackToLookup}
          />
        </div>
      </div>
    );
  }

  if (currentView === 'fallback-mode' && fallbackData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto p-6">
          <div className="mb-6 text-center">
            <h1 className="text-3xl font-bold text-gray-900">Return Request Submitted</h1>
            <p className="text-gray-600 mt-2">
              We've received your return request and will review it shortly.
            </p>
          </div>
          
          <FallbackModeDisplay
            fallbackData={fallbackData}
            onBackToLookup={handleBackToLookup}
            onSubmitAdditionalInfo={handleSubmitAdditionalInfo}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Package className="h-12 w-12 text-blue-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Start Your Return</h1>
          <p className="text-xl text-gray-600">
            Quick and hassle-free returns with real-time processing
          </p>
        </div>

        {/* Enhanced Features */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card className="text-center">
            <CardContent className="pt-6">
              <Zap className="h-8 w-8 text-yellow-600 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Instant Processing</h3>
              <p className="text-sm text-gray-600">Connected to your store for real-time order lookup</p>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="pt-6">
              <ShieldCheck className="h-8 w-8 text-green-600 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Secure & Safe</h3>
              <p className="text-sm text-gray-600">Email verification and secure order matching</p>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="pt-6">
              <Clock className="h-8 w-8 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Quick Process</h3>
              <p className="text-sm text-gray-600">Most returns processed within 24 hours</p>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="pt-6">
              <Truck className="h-8 w-8 text-purple-600 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Free Labels</h3>
              <p className="text-sm text-gray-600">Prepaid return labels for eligible items</p>
            </CardContent>
          </Card>
        </div>

        {/* Order Lookup Form */}
        <OrderLookupForm
          onShopifyOrderFound={handleShopifyOrderFound}
          onFallbackModeTriggered={handleFallbackModeTriggered}
          tenantId="tenant-rms34"
          channel="customer"
        />

        {/* How it Works - Enhanced */}
        <div className="max-w-4xl mx-auto mt-16">
          <h2 className="text-2xl font-bold text-center mb-8">How Our Smart Return System Works</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {/* Shopify Connected Flow */}
            <Card className="border-blue-200">
              <CardHeader>
                <CardTitle className="text-blue-800 flex items-center">
                  <Zap className="h-5 w-5 mr-2" />
                  Store Connected (Instant)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">1</div>
                    <span className="text-sm">Enter order number & email</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">2</div>
                    <span className="text-sm">See your order items instantly</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">3</div>
                    <span className="text-sm">Select items & reasons</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">4</div>
                    <span className="text-sm">Get instant approval & label</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Fallback Flow */}
            <Card className="border-amber-200">
              <CardHeader>
                <CardTitle className="text-amber-800 flex items-center">
                  <Clock className="h-5 w-5 mr-2" />
                  Manual Review (24hrs)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="bg-amber-100 text-amber-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">1</div>
                    <span className="text-sm">Submit order details</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="bg-amber-100 text-amber-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">2</div>
                    <span className="text-sm">We verify your order</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="bg-amber-100 text-amber-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">3</div>
                    <span className="text-sm">Email confirmation sent</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="bg-amber-100 text-amber-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">4</div>
                    <span className="text-sm">Receive return instructions</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="text-center mt-8 text-sm text-gray-500">
          <p>Questions? Contact our support team at support@returns-manager.com</p>
        </div>
      </div>
    </div>
  );
};

export default ReturnPortal;

export default ReturnPortal;