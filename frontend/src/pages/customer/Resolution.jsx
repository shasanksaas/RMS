import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, ArrowRight, CreditCard, RefreshCw, Gift, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';

const Resolution = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { orderNumber, email, selectedItems } = location.state || {};
  
  const [selectedResolution, setSelectedResolution] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!orderNumber || !email || !selectedItems) {
      navigate('/returns/start');
    }
  }, [orderNumber, email, selectedItems, navigate]);

  if (!selectedItems) {
    return null;
  }

  const totalRefund = selectedItems.reduce((total, item) => {
    return total + (item.quantity * item.item.price);
  }, 0);

  const storeCreditBonus = totalRefund * 0.1; // 10% bonus
  const storeCreditTotal = totalRefund + storeCreditBonus;

  const resolutionOptions = [
    {
      id: 'refund',
      title: 'Refund to Original Payment',
      description: 'Get your money back to the original payment method',
      icon: CreditCard,
      amount: totalRefund,
      processing: '5-7 business days',
      color: 'bg-blue-50 border-blue-200'
    },
    {
      id: 'exchange',
      title: 'Exchange for Different Item',
      description: 'Swap for a different size, color, or product',
      icon: RefreshCw,
      amount: totalRefund,
      processing: 'New item ships after we receive return',
      color: 'bg-green-50 border-green-200'
    },
    {
      id: 'store_credit',
      title: 'Store Credit',
      description: `Get ${Math.round((storeCreditBonus/totalRefund) * 100)}% bonus credit for future purchases`,
      icon: Gift,
      amount: storeCreditTotal,
      processing: 'Instant credit to your account',
      color: 'bg-purple-50 border-purple-200',
      badge: 'BONUS!'
    }
  ];

  const handleContinue = async () => {
    if (!selectedResolution) {
      alert('Please select a resolution option');
      return;
    }

    setLoading(true);

    try {
      // Navigate immediately without delay
      navigate('/returns/confirm', {
        state: {
          orderNumber,
          email,
          selectedItems,
          resolution: resolutionOptions.find(opt => opt.id === selectedResolution)
        }
      });
    } catch (error) {
      console.error('Navigation error:', error);
      alert('Something went wrong. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate('/returns/select', { state: { orderNumber, email } })}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Choose Your Resolution</h1>
          <p className="text-gray-500">How would you like us to handle your return?</p>
        </div>
        <div></div>
      </div>

      {/* Return Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Return Summary</CardTitle>
          <CardDescription>Items you're returning</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {selectedItems.map((selectedItem, index) => (
              <div key={index} className="flex justify-between items-center py-2 border-b last:border-b-0">
                <div>
                  <span className="font-medium">{selectedItem.item.productName}</span>
                  <span className="text-gray-500 ml-2">×{selectedItem.quantity}</span>
                </div>
                <span className="font-medium">
                  ${(selectedItem.quantity * selectedItem.item.price).toFixed(2)}
                </span>
              </div>
            ))}
            <div className="flex justify-between items-center pt-3 text-lg font-bold">
              <span>Total Return Value</span>
              <span>${totalRefund.toFixed(2)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resolution Options */}
      <Card>
        <CardHeader>
          <CardTitle>Select Your Preferred Resolution</CardTitle>
          <CardDescription>Choose how you'd like to be compensated for your return</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {resolutionOptions.map((option) => {
              const Icon = option.icon;
              return (
                <div key={option.id}>
                  <div 
                    onClick={() => setSelectedResolution(option.id)}
                    className={`block p-6 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${
                      selectedResolution === option.id 
                        ? `${option.color} border-opacity-100` 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start space-x-4">
                      <input 
                        type="radio" 
                        name="resolution" 
                        value={option.id} 
                        checked={selectedResolution === option.id}
                        onChange={() => setSelectedResolution(option.id)}
                        className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      <Icon className="h-6 w-6 mt-1 text-gray-600" />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className="text-lg font-semibold text-gray-900">{option.title}</h3>
                          {option.badge && (
                            <span className="px-2 py-1 text-xs font-bold bg-purple-600 text-white rounded">
                              {option.badge}
                            </span>
                          )}
                        </div>
                        <p className="text-gray-600 mt-1">{option.description}</p>
                        <div className="mt-3 flex items-center justify-between">
                          <div className="text-2xl font-bold text-green-600">
                            ${option.amount.toFixed(2)}
                            {option.id === 'store_credit' && (
                              <span className="text-sm text-gray-500 ml-2">
                                (${totalRefund.toFixed(2)} + ${storeCreditBonus.toFixed(2)} bonus)
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-gray-500">
                            {option.processing}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Exchange Details */}
      {selectedResolution === 'exchange' && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Exchange Process:</strong> After we receive and inspect your return, 
            we'll send you an email with options to select your replacement items. 
            If there's a price difference, we'll either refund the difference or request additional payment.
          </AlertDescription>
        </Alert>
      )}

      {/* Store Credit Details */}
      {selectedResolution === 'store_credit' && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Store Credit Details:</strong> Your store credit will be added to your account 
            after we receive your return. Store credit never expires and can be used for any future purchase.
          </AlertDescription>
        </Alert>
      )}

      {/* Continue Button */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-6">
          <Button 
            onClick={handleContinue} 
            className="w-full"
            size="lg"
            disabled={!selectedResolution || loading}
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Processing...
              </>
            ) : (
              <>
                Continue to Confirmation
                <ArrowRight className="ml-2 h-5 w-5" />
              </>
            )}
          </Button>
          
          {!selectedResolution && (
            <p className="text-center text-sm text-gray-500 mt-2">
              Please select a resolution option to continue
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Resolution;