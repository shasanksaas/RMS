import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { CheckCircle, Package, ArrowRight, Download, Mail } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';

const Confirm = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { orderNumber, email, selectedItems, resolution } = location.state || {};
  
  const [returnRequest, setReturnRequest] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!orderNumber || !email || !selectedItems || !resolution) {
      navigate('/returns/start');
      return;
    }
  }, [orderNumber, email, selectedItems, resolution, navigate]);

  const handleSubmit = async () => {
    setSubmitting(true);

    try {
      // Simulate API call to create return request
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Mock return request creation
      const newReturnRequest = {
        id: 'RET-' + Math.random().toString(36).substr(2, 9).toUpperCase(),
        orderNumber,
        status: 'submitted',
        resolutionType: resolution.id,
        estimatedRefund: resolution.amount,
        items: selectedItems,
        submittedAt: new Date().toISOString(),
        trackingUrl: `/returns/status/RET-${Math.random().toString(36).substr(2, 9).toUpperCase()}`
      };

      setReturnRequest(newReturnRequest);

      // Navigate to status page after brief delay
      setTimeout(() => {
        navigate(newReturnRequest.trackingUrl);
      }, 3000);

    } catch (error) {
      alert('Something went wrong. Please try again.');
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
              Return ID: {returnRequest.id}
            </h3>
            <p className="text-green-800">
              You'll receive an email confirmation shortly with tracking details and next steps.
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

  const totalRefund = selectedItems.reduce((total, item) => {
    return total + (item.quantity * item.item.price);
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
              {selectedItems.map((selectedItem, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                      <Package className="h-6 w-6 text-gray-400" />
                    </div>
                    <div>
                      <h4 className="font-medium">{selectedItem.item.productName}</h4>
                      <p className="text-sm text-gray-500">
                        Quantity: {selectedItem.quantity} • 
                        Reason: {selectedItem.reason.replace('_', ' ')}
                      </p>
                      {selectedItem.notes && (
                        <p className="text-sm text-gray-500 italic">"{selectedItem.notes}"</p>
                      )}
                    </div>
                  </div>
                  <div className="font-semibold">
                    ${(selectedItem.quantity * selectedItem.item.price).toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Resolution */}
          <div>
            <h3 className="font-semibold text-lg mb-3">Resolution</h3>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-blue-900">{resolution.title}</h4>
                  <p className="text-sm text-blue-700">{resolution.description}</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-600">
                    ${resolution.amount.toFixed(2)}
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
          <strong>What happens next:</strong> After submitting your return, you'll receive an email 
          with a prepaid return label and packaging instructions. Simply pack your items and drop 
          them off at any authorized location.
        </AlertDescription>
      </Alert>

      {/* Submit Button */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-6">
          <div className="text-center space-y-4">
            <div className="text-lg font-semibold">
              Ready to submit your return request?
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
                  Submitting Return Request...
                </>
              ) : (
                <>
                  Submit Return Request
                  <ArrowRight className="ml-2 h-5 w-5" />
                </>
              )}
            </Button>
            <p className="text-sm text-gray-600">
              By submitting, you agree to our return policy and terms of service
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Confirm;