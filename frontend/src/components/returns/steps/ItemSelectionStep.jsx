import React from 'react';
import { Package, Minus, Plus, AlertCircle, CheckCircle } from 'lucide-react';
import { Alert, AlertDescription } from '../../ui/alert';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';

const ItemSelectionStep = ({ 
  formData, 
  updateFormData, 
  errors, 
  isLoading, 
  role 
}) => {
  const handleItemToggle = (item) => {
    const selectedItems = [...formData.selectedItems];
    const existingIndex = selectedItems.findIndex(
      si => si.fulfillment_line_item_id === item.fulfillment_line_item_id
    );
    
    if (existingIndex >= 0) {
      selectedItems.splice(existingIndex, 1);
    } else {
      selectedItems.push({
        ...item,
        quantity: 1,
        id: item.fulfillment_line_item_id
      });
    }
    
    updateFormData({ selectedItems });
  };

  const handleQuantityChange = (itemId, quantity) => {
    const selectedItems = formData.selectedItems.map(item => 
      item.fulfillment_line_item_id === itemId 
        ? { ...item, quantity: Math.max(1, Math.min(quantity, item.quantity_eligible)) }
        : item
    );
    updateFormData({ selectedItems });
  };

  const isItemSelected = (item) => {
    return formData.selectedItems.some(
      si => si.fulfillment_line_item_id === item.fulfillment_line_item_id
    );
  };

  const getSelectedQuantity = (item) => {
    const selected = formData.selectedItems.find(
      si => si.fulfillment_line_item_id === item.fulfillment_line_item_id
    );
    return selected ? selected.quantity : 1;
  };

  const calculateEstimatedRefund = () => {
    return formData.selectedItems.reduce((total, item) => {
      return total + (item.price * item.quantity);
    }, 0);
  };

  if (!formData.eligibleItems || formData.eligibleItems.length === 0) {
    return (
      <div className="text-center py-12">
        <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No Eligible Items
        </h3>
        <p className="text-gray-600">
          Unfortunately, no items from this order are eligible for return.
        </p>
        <Alert className="mt-4 border-amber-200 bg-amber-50">
          <AlertCircle className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            This could be due to return window expiration, items already returned, 
            or specific product policies.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <Package className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Select Items to Return
        </h3>
        <p className="text-gray-600">
          Choose the items you want to return and specify quantities
        </p>
      </div>

      {errors.selectedItems && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {errors.selectedItems}
          </AlertDescription>
        </Alert>
      )}

      <div className="space-y-4">
        {formData.eligibleItems.map((item) => {
          const isSelected = isItemSelected(item);
          const selectedQuantity = getSelectedQuantity(item);
          
          return (
            <div 
              key={item.fulfillment_line_item_id}
              className={`border rounded-lg p-4 transition-all ${
                isSelected 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-start space-x-4">
                {/* Item Image */}
                <div className="flex-shrink-0">
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
                </div>

                {/* Item Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-base font-medium text-gray-900">
                        {item.title}
                      </h4>
                      {item.variant_title && (
                        <p className="text-sm text-gray-600 mt-1">
                          {item.variant_title}
                        </p>
                      )}
                      <p className="text-sm text-gray-500">
                        SKU: {item.sku || 'N/A'}
                      </p>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-900">
                        ${item.price.toFixed(2)}
                      </p>
                      <p className="text-sm text-gray-500">
                        per item
                      </p>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="text-sm text-gray-600">
                        <span className="font-medium">Ordered:</span> {item.quantity_ordered}
                      </div>
                      <div className="text-sm text-gray-600">
                        <span className="font-medium">Eligible:</span> {item.quantity_eligible}
                      </div>
                      {isSelected && (
                        <div className="flex items-center space-x-2 bg-white rounded-lg px-3 py-1 border">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleQuantityChange(item.fulfillment_line_item_id, selectedQuantity - 1)}
                            disabled={selectedQuantity <= 1}
                            className="h-6 w-6 p-0"
                          >
                            <Minus className="h-3 w-3" />
                          </Button>
                          <Input
                            type="number"
                            min="1"
                            max={item.quantity_eligible}
                            value={selectedQuantity}
                            onChange={(e) => handleQuantityChange(
                              item.fulfillment_line_item_id, 
                              parseInt(e.target.value) || 1
                            )}
                            className="w-16 text-center text-sm h-6 px-2 py-0"
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleQuantityChange(item.fulfillment_line_item_id, selectedQuantity + 1)}
                            disabled={selectedQuantity >= item.quantity_eligible}
                            className="h-6 w-6 p-0"
                          >
                            <Plus className="h-3 w-3" />
                          </Button>
                        </div>
                      )}
                    </div>

                    <Button
                      type="button"
                      variant={isSelected ? "secondary" : "outline"}
                      onClick={() => handleItemToggle(item)}
                      className={`${
                        isSelected 
                          ? 'bg-blue-600 text-white hover:bg-blue-700' 
                          : 'border-blue-600 text-blue-600 hover:bg-blue-50'
                      }`}
                    >
                      {isSelected ? (
                        <>
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Selected
                        </>
                      ) : (
                        'Select for Return'
                      )}
                    </Button>
                  </div>

                  {isSelected && (
                    <div className="mt-3 p-3 bg-white rounded-lg border border-blue-200">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Return quantity:</span>
                        <span className="font-medium">{selectedQuantity}</span>
                      </div>
                      <div className="flex justify-between text-sm mt-1">
                        <span className="text-gray-600">Refund amount:</span>
                        <span className="font-medium text-green-600">
                          ${(item.price * selectedQuantity).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      {formData.selectedItems.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <h4 className="font-medium text-gray-900">Selection Summary</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Items selected:</span>
              <span className="font-medium">{formData.selectedItems.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total quantity:</span>
              <span className="font-medium">
                {formData.selectedItems.reduce((sum, item) => sum + item.quantity, 0)}
              </span>
            </div>
            <div className="flex justify-between col-span-2 pt-2 border-t border-gray-200">
              <span className="text-gray-900 font-medium">Estimated refund:</span>
              <span className="font-semibold text-green-600 text-lg">
                ${calculateEstimatedRefund().toFixed(2)}
              </span>
            </div>
          </div>
          <p className="text-xs text-gray-500">
            * Final refund amount may differ based on return policies and applicable fees
          </p>
        </div>
      )}
    </div>
  );
};

export default ItemSelectionStep;