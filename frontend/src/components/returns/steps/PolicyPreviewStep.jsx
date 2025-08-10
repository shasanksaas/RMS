import React, { useEffect, useState } from 'react';
import { Calculator, Clock, DollarSign, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { Alert, AlertDescription } from '../../ui/alert';
import { Badge } from '../../ui/badge';

const PolicyPreviewStep = ({ 
  formData, 
  updateFormData, 
  errors, 
  isLoading, 
  role 
}) => {
  const [policyPreview, setPolicyPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (formData.selectedItems.length > 0) {
      loadPolicyPreview();
    }
  }, [formData.selectedItems, formData.itemReasons]);

  const loadPolicyPreview = async () => {
    setLoading(true);
    try {
      const items = formData.selectedItems.map(item => ({
        fulfillment_line_item_id: item.fulfillment_line_item_id,
        quantity: item.quantity,
        reason: formData.itemReasons[item.id]?.reason || 'other'
      }));

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/unified-returns/policy-preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
        },
        body: JSON.stringify({
          items: items,
          order_id: formData.orderId
        })
      });

      const result = await response.json();
      setPolicyPreview(result);
      updateFormData({ policyPreview: result });
    } catch (error) {
      console.error('Failed to load policy preview:', error);
    } finally {
      setLoading(false);
    }
  };

  const preview = policyPreview || formData.policyPreview;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Calculator className="h-12 w-12 text-gray-400 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-600">Calculating return details...</p>
        </div>
      </div>
    );
  }

  if (!preview) {
    return (
      <div className="text-center py-12">
        <Calculator className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Policy Preview Not Available
        </h3>
        <p className="text-gray-600">
          Unable to load return policy details at this time.
        </p>
      </div>
    );
  }

  const calculateItemsTotal = () => {
    return formData.selectedItems.reduce((total, item) => {
      return total + (item.price * item.quantity);
    }, 0);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <Calculator className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Return Policy Preview
        </h3>
        <p className="text-gray-600">
          Review the policy details and estimated refund for your return
        </p>
      </div>

      {/* Return Window Status */}
      <div className="bg-white border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-gray-900 flex items-center">
            <Clock className="h-5 w-5 mr-2 text-blue-600" />
            Return Window Status
          </h4>
          <Badge 
            variant={formData.verifiedOrder?.policy_preview?.within_window ? 'default' : 'destructive'}
            className="text-sm"
          >
            {formData.verifiedOrder?.policy_preview?.within_window ? 'Within Policy' : 'Expired'}
          </Badge>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {formData.verifiedOrder?.policy_preview?.days_remaining || 0}
            </div>
            <div className="text-sm text-gray-600">Days Remaining</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">30</div>
            <div className="text-sm text-gray-600">Day Policy</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {new Date(formData.verifiedOrder?.order_date).toLocaleDateString()}
            </div>
            <div className="text-sm text-gray-600">Order Date</div>
          </div>
        </div>
      </div>

      {/* Fee Breakdown */}
      <div className="bg-white border rounded-lg p-6">
        <h4 className="font-medium text-gray-900 flex items-center mb-4">
          <DollarSign className="h-5 w-5 mr-2 text-green-600" />
          Fee Breakdown & Refund Calculation
        </h4>
        
        <div className="space-y-3">
          <div className="flex justify-between text-base">
            <span className="text-gray-600">Items subtotal:</span>
            <span className="font-medium">${calculateItemsTotal().toFixed(2)}</span>
          </div>
          
          {preview.fees && Object.entries(preview.fees).map(([feeType, amount]) => (
            <div key={feeType} className="flex justify-between text-sm">
              <span className="text-gray-600 capitalize">
                {feeType.replace('_', ' ')}:
              </span>
              <span className="text-red-600">-${amount.toFixed(2)}</span>
            </div>
          ))}
          
          <div className="border-t border-gray-200 pt-3">
            <div className="flex justify-between text-lg font-semibold">
              <span className="text-gray-900">Estimated refund:</span>
              <span className="text-green-600">
                ${preview.estimated_refund?.toFixed(2) || calculateItemsTotal().toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Fee Explanations */}
        {preview.fees && Object.keys(preview.fees).length > 0 && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex">
              <Info className="h-5 w-5 text-amber-600 mt-0.5 mr-2 flex-shrink-0" />
              <div className="text-sm text-amber-800">
                <p className="font-medium mb-2">Fee Information:</p>
                <ul className="space-y-1">
                  {preview.fees.restocking_fee > 0 && (
                    <li>• Restocking fee applies to change-of-mind returns</li>
                  )}
                  {preview.fees.shipping_fee > 0 && (
                    <li>• Return shipping fee (when not using free return options)</li>
                  )}
                  <li>• Original shipping charges are non-refundable per policy</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Auto-Approval Status */}
      <div className="bg-white border rounded-lg p-6">
        <h4 className="font-medium text-gray-900 flex items-center mb-4">
          {preview.auto_approve_eligible ? (
            <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
          ) : (
            <AlertTriangle className="h-5 w-5 mr-2 text-amber-600" />
          )}
          Approval Process
        </h4>
        
        {preview.auto_approve_eligible ? (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              <strong>Auto-Approval Eligible:</strong> Your return meets the criteria for automatic approval. 
              You'll receive confirmation and return instructions immediately after submission.
            </AlertDescription>
          </Alert>
        ) : (
          <Alert className="border-amber-200 bg-amber-50">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              <strong>Manual Review Required:</strong> Your return will be reviewed by our team within 1-2 business days. 
              You'll receive an email notification with the decision.
            </AlertDescription>
          </Alert>
        )}

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <h5 className="font-medium text-gray-900 mb-2">Auto-Approval Criteria:</h5>
            <ul className="space-y-1 text-gray-600">
              <li className="flex items-center">
                <CheckCircle className="h-3 w-3 mr-2 text-green-600" />
                Defective or damaged items
              </li>
              <li className="flex items-center">
                <CheckCircle className="h-3 w-3 mr-2 text-green-600" />
                Items not as described
              </li>
              <li className="flex items-center">
                <CheckCircle className="h-3 w-3 mr-2 text-green-600" />
                Within return window
              </li>
              <li className="flex items-center">
                <CheckCircle className="h-3 w-3 mr-2 text-green-600" />
                Photos provided when required
              </li>
            </ul>
          </div>
          
          <div>
            <h5 className="font-medium text-gray-900 mb-2">Manual Review Reasons:</h5>
            <ul className="space-y-1 text-gray-600">
              <li className="flex items-center">
                <AlertTriangle className="h-3 w-3 mr-2 text-amber-600" />
                Change of mind returns
              </li>
              <li className="flex items-center">
                <AlertTriangle className="h-3 w-3 mr-2 text-amber-600" />
                High-value items
              </li>
              <li className="flex items-center">
                <AlertTriangle className="h-3 w-3 mr-2 text-amber-600" />
                Multiple recent returns
              </li>
              <li className="flex items-center">
                <AlertTriangle className="h-3 w-3 mr-2 text-amber-600" />
                Special circumstances
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Return Items Summary */}
      <div className="bg-white border rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">Return Items Summary</h4>
        <div className="space-y-3">
          {formData.selectedItems.map((item) => {
            const reason = formData.itemReasons[item.id]?.reason || 'not_specified';
            const reasonLabel = {
              'wrong_size': 'Wrong Size',
              'wrong_color': 'Wrong Color',
              'damaged_defective': 'Damaged/Defective',
              'not_as_described': 'Not as Described',
              'changed_mind': 'Changed Mind',
              'late_delivery': 'Late Delivery',
              'received_extra': 'Received Extra Item',
              'other': 'Other'
            }[reason] || 'Not Specified';
            
            return (
              <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt={item.title}
                      className="w-10 h-10 object-cover rounded"
                    />
                  ) : (
                    <div className="w-10 h-10 bg-gray-200 rounded flex items-center justify-center">
                      <Calculator className="h-4 w-4 text-gray-400" />
                    </div>
                  )}
                  <div>
                    <div className="font-medium text-sm text-gray-900">{item.title}</div>
                    <div className="text-xs text-gray-600">
                      Qty: {item.quantity} • Reason: {reasonLabel}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-sm text-gray-900">
                    ${(item.price * item.quantity).toFixed(2)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Policy Terms */}
      <Alert className="border-gray-200 bg-gray-50">
        <Info className="h-4 w-4 text-gray-600" />
        <AlertDescription className="text-gray-700">
          <strong>Return Policy Terms:</strong> Final refund amounts are determined after inspection 
          of returned items. Items must be in original condition with tags attached. 
          Personalized items and final sale products may not be eligible for return. 
          Processing typically takes 3-5 business days after we receive your items.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default PolicyPreviewStep;