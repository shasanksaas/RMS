import React from 'react';
import { CreditCard, Gift, RefreshCw, Package, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '../../ui/alert';

const PreferredOutcomeStep = ({ 
  formData, 
  updateFormData, 
  errors, 
  isLoading, 
  role 
}) => {
  const outcomes = [
    {
      value: 'refund_original',
      title: 'Refund to Original Payment',
      description: 'Receive money back to your original payment method',
      icon: CreditCard,
      timeframe: '3-5 business days',
      available: true
    },
    {
      value: 'store_credit',
      title: 'Store Credit',
      description: 'Receive store credit for future purchases',
      icon: Gift,
      timeframe: 'Immediate',
      available: true,
      bonus: '10% bonus credit'
    },
    {
      value: 'exchange',
      title: 'Exchange',
      description: 'Exchange for different size, color, or style',
      icon: RefreshCw,
      timeframe: '5-7 business days',
      available: true
    },
    {
      value: 'replacement',
      title: 'Replacement',
      description: 'Receive an exact replacement of the same item',
      icon: Package,
      timeframe: '5-7 business days',
      available: true
    }
  ];

  const handleOutcomeSelect = (value) => {
    updateFormData({ preferredOutcome: value });
  };

  const calculateRefundAmount = () => {
    return formData.selectedItems.reduce((total, item) => {
      return total + (item.price * item.quantity);
    }, 0);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <CreditCard className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Preferred Outcome
        </h3>
        <p className="text-gray-600">
          How would you like us to resolve your return?
        </p>
      </div>

      {errors.preferredOutcome && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {errors.preferredOutcome}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {outcomes.map((outcome) => {
          const Icon = outcome.icon;
          const isSelected = formData.preferredOutcome === outcome.value;
          
          return (
            <div
              key={outcome.value}
              onClick={() => outcome.available && handleOutcomeSelect(outcome.value)}
              className={`relative border-2 rounded-lg p-6 cursor-pointer transition-all ${
                isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : outcome.available
                    ? 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-50'
              }`}
            >
              {/* Selection Indicator */}
              {isSelected && (
                <div className="absolute top-4 right-4 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                </div>
              )}

              {/* Bonus Badge */}
              {outcome.bonus && (
                <div className="absolute top-2 left-2 bg-green-600 text-white text-xs px-2 py-1 rounded-full">
                  {outcome.bonus}
                </div>
              )}

              <div className="flex items-start space-x-4">
                <div className={`flex-shrink-0 p-3 rounded-lg ${
                  isSelected ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
                }`}>
                  <Icon className="h-6 w-6" />
                </div>
                
                <div className="flex-1">
                  <h4 className={`font-semibold ${
                    isSelected ? 'text-blue-900' : 'text-gray-900'
                  }`}>
                    {outcome.title}
                  </h4>
                  <p className={`text-sm mt-1 ${
                    isSelected ? 'text-blue-700' : 'text-gray-600'
                  }`}>
                    {outcome.description}
                  </p>
                  <p className={`text-xs mt-2 ${
                    isSelected ? 'text-blue-600' : 'text-gray-500'
                  }`}>
                    Processing time: {outcome.timeframe}
                  </p>
                </div>
              </div>

              {!outcome.available && (
                <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
                  <span className="text-sm font-medium text-gray-500">
                    Not Available
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Outcome Details */}
      {formData.preferredOutcome && (
        <div className="bg-gray-50 rounded-lg p-6 space-y-4">
          <h4 className="font-medium text-gray-900">
            {outcomes.find(o => o.value === formData.preferredOutcome)?.title} Details
          </h4>
          
          {formData.preferredOutcome === 'refund_original' && (
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Items total:</span>
                <span className="font-medium">${calculateRefundAmount().toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Processing fee:</span>
                <span className="font-medium">$0.00</span>
              </div>
              <div className="flex justify-between text-base font-semibold pt-2 border-t border-gray-200">
                <span>Estimated refund:</span>
                <span className="text-green-600">${calculateRefundAmount().toFixed(2)}</span>
              </div>
              <Alert className="border-blue-200 bg-blue-50">
                <AlertCircle className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  Refunds typically take 3-5 business days to appear on your statement after processing.
                  Original shipping charges are non-refundable.
                </AlertDescription>
              </Alert>
            </div>
          )}

          {formData.preferredOutcome === 'store_credit' && (
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Items total:</span>
                <span className="font-medium">${calculateRefundAmount().toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Bonus credit (10%):</span>
                <span className="font-medium text-green-600">
                  +${(calculateRefundAmount() * 0.1).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-base font-semibold pt-2 border-t border-gray-200">
                <span>Total store credit:</span>
                <span className="text-green-600">
                  ${(calculateRefundAmount() * 1.1).toFixed(2)}
                </span>
              </div>
              <Alert className="border-green-200 bg-green-50">
                <AlertCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  Store credit is issued immediately and never expires. 
                  Plus, you get an extra 10% bonus credit!
                </AlertDescription>
              </Alert>
            </div>
          )}

          {formData.preferredOutcome === 'exchange' && (
            <div className="space-y-3">
              <Alert className="border-blue-200 bg-blue-50">
                <AlertCircle className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  After submitting this return, you'll be guided to select replacement items.
                  If there's a price difference, we'll either refund you or send a payment link.
                </AlertDescription>
              </Alert>
              <div className="text-sm text-gray-600">
                <p>Exchange options:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Different size or color of the same item</li>
                  <li>Completely different product</li>
                  <li>Multiple items of lesser value</li>
                </ul>
              </div>
            </div>
          )}

          {formData.preferredOutcome === 'replacement' && (
            <div className="space-y-3">
              <Alert className="border-blue-200 bg-blue-50">
                <AlertCircle className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  We'll send you an exact replacement of the returned items at no additional cost.
                  Perfect for defective or damaged items.
                </AlertDescription>
              </Alert>
              <div className="text-sm text-gray-600">
                <p>Replacement process:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>We'll ship the replacement once your return is approved</li>
                  <li>No charge for replacement shipping</li>
                  <li>If item is out of stock, we'll contact you with alternatives</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Policy Note */}
      <Alert className="border-gray-200 bg-gray-50">
        <AlertCircle className="h-4 w-4 text-gray-600" />
        <AlertDescription className="text-gray-700">
          <strong>Note:</strong> Final processing may depend on the condition of returned items 
          and our return policy. You'll be notified of any changes to your preferred outcome.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default PreferredOutcomeStep;