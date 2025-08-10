import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Package, Mail, Search, ArrowRight, ShieldCheck, Clock, Truck } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Alert, AlertDescription } from '../../components/ui/alert';
import UnifiedReturnForm from '../../components/returns/UnifiedReturnForm';

const ReturnPortal = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState('lookup'); // 'lookup' or 'form'
  const [orderData, setOrderData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Form data for order lookup
  const [orderNumber, setOrderNumber] = useState(searchParams.get('order') || '');
  const [email, setEmail] = useState(searchParams.get('email') || '');

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  const handleOrderLookup = async () => {
    if (!orderNumber.trim() || !email.trim()) {
      setError('Please enter both order number and email address');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${backendUrl}/api/portal/returns/lookup-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': 'tenant-rms34'
        },
        body: JSON.stringify({
          orderNumber: orderNumber.replace('#', ''),
          email: email.toLowerCase()
        })
      });

      const result = await response.json();

      if (result.success) {
        setOrderData(result);
        setStep('form');
      } else {
        setError(result.error || 'Order not found. Please check your details.');
      }
    } catch (err) {
      setError('Failed to lookup order. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReturnSuccess = (result) => {
    // Navigate to confirmation page
    navigate(`/portal/returns/confirmation/${result.return_id}`, {
      state: { returnData: result }
    });
  };

  if (step === 'form' && orderData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto p-6">
          <UnifiedReturnForm
            role="customer"
            prefilledOrderId={orderData.order?.id}
            onSuccess={handleReturnSuccess}
            onCancel={() => setStep('lookup')}
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
            Simple, hassle-free returns in just a few steps
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card className="text-center">
            <CardContent className="pt-6">
              <ShieldCheck className="h-8 w-8 text-green-600 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Secure & Safe</h3>
              <p className="text-sm text-gray-600">Your data is protected with enterprise-grade security</p>
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
              <h3 className="font-semibold mb-2">Free Shipping</h3>
              <p className="text-sm text-gray-600">Prepaid return labels for eligible items</p>
            </CardContent>
          </Card>
        </div>

        {/* Order Lookup Form */}
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Search className="h-5 w-5" />
              <span>Find Your Order</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <Alert className="border-red-200 bg-red-50">
                <AlertDescription className="text-red-800">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="orderNumber" className="block text-sm font-medium text-gray-700 mb-2">
                  Order Number
                </label>
                <Input
                  id="orderNumber"
                  type="text"
                  placeholder="e.g., 1001 or #1001"
                  value={orderNumber}
                  onChange={(e) => setOrderNumber(e.target.value)}
                  className="w-full"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Email used for your order"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full"
                />
              </div>

              <Button
                onClick={handleOrderLookup}
                disabled={loading || !orderNumber.trim() || !email.trim()}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {loading ? 'Looking up order...' : 'Find My Order'}
                {!loading && <ArrowRight className="h-4 w-4 ml-2" />}
              </Button>
            </div>

            <div className="text-center text-sm text-gray-500 mt-4">
              <p>Need help? Contact our support team</p>
            </div>
          </CardContent>
        </Card>

        {/* How it Works */}
        <div className="max-w-4xl mx-auto mt-12">
          <h2 className="text-2xl font-bold text-center mb-8">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: 1, title: "Find Order", desc: "Enter your order number and email" },
              { step: 2, title: "Select Items", desc: "Choose which items to return" },
              { step: 3, title: "Tell Us Why", desc: "Select reason and upload photos if needed" },
              { step: 4, title: "Get Approved", desc: "Receive instant approval and prepaid label" }
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="bg-blue-100 text-blue-800 rounded-full w-10 h-10 flex items-center justify-center font-bold mx-auto mb-3">
                  {item.step}
                </div>
                <h3 className="font-semibold mb-2">{item.title}</h3>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReturnPortal;