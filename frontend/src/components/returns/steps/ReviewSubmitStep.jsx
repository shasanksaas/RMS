import React from 'react';
import { 
  CheckCircle, 
  Package, 
  User, 
  MessageSquare, 
  DollarSign, 
  Truck, 
  MapPin,
  AlertTriangle,
  Clock,
  Edit3
} from 'lucide-react';
import { Alert, AlertDescription } from '../../ui/alert';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';

const ReviewSubmitStep = ({ 
  formData, 
  updateFormData, 
  errors, 
  isLoading, 
  role 
}) => {
  const calculateItemsTotal = () => {
    return formData.selectedItems.reduce((total, item) => {
      return total + (item.price * item.quantity);
    }, 0);
  };

  const calculateTotalItems = () => {
    return formData.selectedItems.reduce((total, item) => {
      return total + item.quantity;
    }, 0);
  };

  const getReturnMethodLabel = () => {
    const methods = {
      'prepaid_label': 'Prepaid Return Label',
      'qr_dropoff': 'QR Code Drop-off',
      'in_store': 'In-Store Return',
      'customer_ships': 'Ship at Own Cost'
    };
    return methods[formData.returnMethod] || formData.returnMethod;
  };

  const getOutcomeLabel = () => {
    const outcomes = {
      'refund_original': 'Refund to Original Payment',
      'store_credit': 'Store Credit',
      'exchange': 'Exchange',
      'replacement': 'Replacement'
    };
    return outcomes[formData.preferredOutcome] || formData.preferredOutcome;
  };

  const getReasonLabel = (reason) => {
    const reasons = {
      'wrong_size': 'Wrong Size',
      'wrong_color': 'Wrong Color',
      'damaged_defective': 'Damaged/Defective',
      'not_as_described': 'Not as Described',
      'changed_mind': 'Changed Mind',
      'late_delivery': 'Late Delivery',
      'received_extra': 'Received Extra Item',
      'other': 'Other'
    };
    return reasons[reason] || reason;
  };

  const goToStep = (stepNumber) => {
    // This would be handled by the parent component
    console.log(`Navigate to step ${stepNumber}`);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Review Your Return Request
        </h3>
        <p className="text-gray-600">
          Please review all details before submitting your return request
        </p>
      </div>

      {errors.general && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {errors.general}
          </AlertDescription>
        </Alert>
      )}

      {/* Order Information */}
      <div className="bg-white border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-gray-900 flex items-center">
            <Package className="h-5 w-5 mr-2 text-blue-600" />
            Order Information
          </h4>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => goToStep(1)}
            className="text-blue-600 hover:text-blue-700"
          >
            <Edit3 className="h-3 w-3 mr-1" />
            Edit
          </Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">Order Number:</span>
            <p className="text-gray-900">
              {formData.verifiedOrder?.order_number || formData.orderNumber}
            </p>
          </div>
          <div>
            <span className="font-medium text-gray-700">Customer:</span>
            <p className="text-gray-900">
              {formData.verifiedOrder?.customer_name || 'N/A'}
            </p>
          </div>
          <div>
            <span className="font-medium text-gray-700">Order Date:</span>
            <p className="text-gray-900">
              {formData.verifiedOrder?.order_date 
                ? new Date(formData.verifiedOrder.order_date).toLocaleDateString()
                : 'N/A'
              }
            </p>
          </div>
          <div>
            <span className="font-medium text-gray-700">Email:</span>
            <p className="text-gray-900">{formData.email}</p>
          </div>
        </div>
      </div>

      {/* Return Items */}
      <div className="bg-white border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-gray-900 flex items-center">
            <Package className="h-5 w-5 mr-2 text-blue-600" />
            Return Items ({formData.selectedItems.length} items, {calculateTotalItems()} pieces)
          </h4>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => goToStep(2)}
            className="text-blue-600 hover:text-blue-700"
          >
            <Edit3 className="h-3 w-3 mr-1" />
            Edit
          </Button>
        </div>
        
        <div className="space-y-4">
          {formData.selectedItems.map((item) => {
            const itemId = item.id || item.fulfillment_line_item_id;
            const reason = formData.itemReasons?.[itemId]?.reason;
            const reasonNote = formData.itemReasons?.[itemId]?.note;
            const photos = formData.itemReasons?.[itemId]?.photos || [];
            
            return (
              <div key={itemId} className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg">
                {item.image_url ? (
                  <img
                    src={item.image_url}
                    alt={item.title}
                    className="w-16 h-16 object-cover rounded-lg"
                  />
                ) : (
                  <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                    <Package className="h-6 w-6 text-gray-400" />
                  </div>
                )}
                
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h5 className="font-medium text-gray-900">{item.title}</h5>
                      {item.variant_title && (
                        <p className="text-sm text-gray-600">{item.variant_title}</p>
                      )}
                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                        <span>Qty: {item.quantity}</span>
                        <span>Price: ${item.price.toFixed(2)}</span>
                        <span>Subtotal: ${(item.price * item.quantity).toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-3 space-y-2">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Reason: </span>
                      <Badge variant="outline" className="text-xs">
                        {reason ? getReasonLabel(reason) : 'Not specified'}
                      </Badge>
                    </div>
                    
                    {reasonNote && (
                      <div>
                        <span className="text-sm font-medium text-gray-700">Note: </span>
                        <p className="text-sm text-gray-600 mt-1">{reasonNote}</p>
                      </div>
                    )}
                    
                    {photos.length > 0 && (
                      <div>
                        <span className="text-sm font-medium text-gray-700">
                          Photos ({photos.length}): 
                        </span>
                        <div className="flex space-x-2 mt-1">
                          {photos.slice(0, 3).map((photo, index) => (
                            <img
                              key={index}
                              src={photo}
                              alt={`Return photo ${index + 1}`}
                              className="w-10 h-10 object-cover rounded border"
                            />
                          ))}
                          {photos.length > 3 && (
                            <div className="w-10 h-10 bg-gray-200 rounded border flex items-center justify-center">
                              <span className="text-xs text-gray-600">+{photos.length - 3}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Return Details */}
      <div className="bg-white border rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">Return Details</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 flex items-center">
                <User className="h-4 w-4 mr-2" />
                Preferred Outcome:
              </span>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => goToStep(4)}
                className="text-blue-600 hover:text-blue-700 h-6 px-2"
              >
                <Edit3 className="h-3 w-3" />
              </Button>
            </div>
            <Badge variant="default" className="mb-4">
              {getOutcomeLabel()}
            </Badge>
            
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 flex items-center">
                <Truck className="h-4 w-4 mr-2" />
                Return Method:
              </span>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => goToStep(5)}
                className="text-blue-600 hover:text-blue-700 h-6 px-2"
              >
                <Edit3 className="h-3 w-3" />
              </Button>
            </div>
            <Badge variant="outline" className="mb-4">
              {getReturnMethodLabel()}
            </Badge>
          </div>
          
          <div>
            <span className="text-sm font-medium text-gray-700 flex items-center mb-2">
              <DollarSign className="h-4 w-4 mr-2" />
              Estimated Refund:
            </span>
            <div className="text-2xl font-bold text-green-600 mb-4">
              ${formData.policyPreview?.estimated_refund?.toFixed(2) || calculateItemsTotal().toFixed(2)}
            </div>
            
            {formData.policyPreview && (
              <div className="text-sm text-gray-600 space-y-1">
                <div className="flex justify-between">
                  <span>Items total:</span>
                  <span>${calculateItemsTotal().toFixed(2)}</span>
                </div>
                {formData.policyPreview.fees && Object.entries(formData.policyPreview.fees).map(([feeType, amount]) => (
                  <div key={feeType} className="flex justify-between">
                    <span className="capitalize">{feeType.replace('_', ' ')}:</span>
                    <span className="text-red-600">-${amount.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {formData.returnLocationId && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <span className="text-sm font-medium text-blue-800 flex items-center">
              <MapPin className="h-4 w-4 mr-2" />
              Selected Store Location: Store #{formData.returnLocationId}
            </span>
          </div>
        )}
      </div>

      {/* Additional Notes */}
      {(formData.customerNote || (role === 'admin' && (formData.adminOverrideNote || formData.internalTags?.length > 0))) && (
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900 flex items-center">
              <MessageSquare className="h-5 w-5 mr-2 text-blue-600" />
              Additional Information
            </h4>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => goToStep(7)}
              className="text-blue-600 hover:text-blue-700"
            >
              <Edit3 className="h-3 w-3 mr-1" />
              Edit
            </Button>
          </div>
          
          {formData.customerNote && (
            <div className="mb-4">
              <span className="text-sm font-medium text-gray-700">
                {role === 'admin' ? 'Customer Comments:' : 'Your Comments:'}
              </span>
              <p className="text-sm text-gray-600 mt-1 p-3 bg-gray-50 rounded">
                {formData.customerNote}
              </p>
            </div>
          )}
          
          {role === 'admin' && formData.adminOverrideNote && (
            <div className="mb-4">
              <span className="text-sm font-medium text-orange-700">Internal Notes:</span>
              <p className="text-sm text-gray-600 mt-1 p-3 bg-orange-50 rounded border border-orange-200">
                {formData.adminOverrideNote}
              </p>
            </div>
          )}
          
          {role === 'admin' && formData.internalTags?.length > 0 && (
            <div>
              <span className="text-sm font-medium text-orange-700">Internal Tags:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {formData.internalTags.map((tag, index) => (
                  <Badge key={index} variant="outline" className="text-xs bg-orange-50 border-orange-200">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Admin Override Warning */}
      {role === 'admin' && formData.adminOverrideApprove && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>Admin Override Active:</strong> This return will be automatically approved, 
            bypassing all policy checks. Ensure you have proper authorization for this action.
          </AlertDescription>
        </Alert>
      )}

      {/* Auto-Approval Status */}
      {formData.policyPreview && (
        <Alert className={
          formData.policyPreview.auto_approve_eligible 
            ? 'border-green-200 bg-green-50' 
            : 'border-amber-200 bg-amber-50'
        }>
          {formData.policyPreview.auto_approve_eligible ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <Clock className="h-4 w-4 text-amber-600" />
          )}
          <AlertDescription className={
            formData.policyPreview.auto_approve_eligible 
              ? 'text-green-800' 
              : 'text-amber-800'
          }>
            {formData.policyPreview.auto_approve_eligible ? (
              <>
                <strong>Auto-Approval:</strong> Your return meets the criteria for automatic approval. 
                You'll receive confirmation and return instructions immediately.
              </>
            ) : (
              <>
                <strong>Manual Review:</strong> Your return will be reviewed by our team within 1-2 business days. 
                You'll receive an email notification with the decision.
              </>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Final Terms */}
      <Alert className="border-gray-200 bg-gray-50">
        <AlertTriangle className="h-4 w-4 text-gray-600" />
        <AlertDescription className="text-gray-700">
          <strong>By submitting this return request, you agree to our return policy terms.</strong> 
          Final refund amounts are subject to item inspection. Items must be returned in original 
          condition with tags attached. Processing typically takes 3-5 business days after receipt.
        </AlertDescription>
      </Alert>

      {/* Summary Box */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
        <div className="text-center">
          <CheckCircle className="h-8 w-8 text-blue-600 mx-auto mb-3" />
          <h4 className="text-lg font-semibold text-gray-900 mb-2">Ready to Submit</h4>
          <p className="text-gray-600 mb-4">
            You're returning {formData.selectedItems.length} item{formData.selectedItems.length !== 1 ? 's' : ''} 
            {' '}for an estimated refund of ${formData.policyPreview?.estimated_refund?.toFixed(2) || calculateItemsTotal().toFixed(2)}
          </p>
          
          <div className="flex items-center justify-center space-x-6 text-sm text-gray-600">
            <div className="flex items-center">
              <Package className="h-4 w-4 mr-1" />
              {calculateTotalItems()} pieces
            </div>
            <div className="flex items-center">
              <DollarSign className="h-4 w-4 mr-1" />
              ${calculateItemsTotal().toFixed(2)} value
            </div>
            <div className="flex items-center">
              <Truck className="h-4 w-4 mr-1" />
              {getReturnMethodLabel()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewSubmitStep;