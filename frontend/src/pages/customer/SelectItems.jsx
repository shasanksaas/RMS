import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Package, Plus, Minus, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';

const SelectItems = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { orderNumber, email } = location.state || {};
  
  const [order, setOrder] = useState(null);
  const [selectedItems, setSelectedItems] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!orderNumber || !email) {
      navigate('/returns/start');
      return;
    }

    // Mock order data
    const mockOrder = {
      orderNumber: orderNumber,
      customerEmail: email,
      orderDate: '2024-01-10T00:00:00Z',
      items: [
        {
          id: 'item-1',
          productName: 'Blue Cotton T-Shirt',
          productImage: '/placeholder-product.jpg',
          sku: 'SHIRT-001',
          size: 'Medium',
          color: 'Blue',
          quantity: 2,
          price: 24.99,
          eligible: true
        },
        {
          id: 'item-2',
          productName: 'Wireless Headphones',
          productImage: '/placeholder-product.jpg',
          sku: 'AUDIO-001',
          quantity: 1,
          price: 199.99,
          eligible: true
        },
        {
          id: 'item-3',
          productName: 'Gift Card',
          productImage: '/placeholder-product.jpg',
          sku: 'GIFT-001',
          quantity: 1,
          price: 50.00,
          eligible: false,
          ineligibleReason: 'Gift cards cannot be returned'
        }
      ]
    };

    setOrder(mockOrder);
    setLoading(false);
  }, [orderNumber, email, navigate]);

  const returnReasons = [
    { value: 'wrong_size', label: 'Wrong size' },
    { value: 'wrong_color', label: 'Wrong color' },
    { value: 'defective', label: 'Defective/damaged' },
    { value: 'not_as_described', label: 'Not as described' },
    { value: 'changed_mind', label: 'Changed my mind' },
    { value: 'damaged_shipping', label: 'Damaged in shipping' },
    { value: 'other', label: 'Other' }
  ];

  const updateItemQuantity = (itemId, quantity) => {
    setSelectedItems(prev => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        quantity: Math.max(0, quantity)
      }
    }));
  };

  const updateItemReason = (itemId, reason) => {
    setSelectedItems(prev => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        reason
      }
    }));
  };

  const updateItemNotes = (itemId, notes) => {
    setSelectedItems(prev => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        notes
      }
    }));
  };

  const toggleItemSelection = (item) => {
    setSelectedItems(prev => {
      if (prev[item.id]) {
        const { [item.id]: removed, ...rest } = prev;
        return rest;
      } else {
        return {
          ...prev,
          [item.id]: {
            item,
            quantity: 1,
            reason: '',
            notes: ''
          }
        };
      }
    });
  };

  const handleContinue = () => {
    const selectedItemsArray = Object.values(selectedItems).filter(item => item.quantity > 0);
    
    if (selectedItemsArray.length === 0) {
      alert('Please select at least one item to return');
      return;
    }

    // Check that all selected items have reasons
    const missingReasons = selectedItemsArray.some(item => !item.reason);
    if (missingReasons) {
      alert('Please select a reason for all items you want to return');
      return;
    }

    navigate('/returns/resolution', {
      state: {
        orderNumber,
        email,
        selectedItems: selectedItemsArray
      }
    });
  };

  if (loading) {
    return <div className="text-center py-8">Loading your order...</div>;
  }

  if (!order) {
    return <div className="text-center py-8">Order not found</div>;
  }

  const selectedCount = Object.values(selectedItems).filter(item => item.quantity > 0).length;
  const totalRefund = Object.values(selectedItems).reduce((total, item) => {
    return total + (item.quantity * item.item.price);
  }, 0);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate('/returns/start')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Select Items to Return</h1>
          <p className="text-gray-500">Order {order.orderNumber}</p>
        </div>
        <div></div>
      </div>

      {/* Order Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Order Details</CardTitle>
          <CardDescription>
            Order placed on {new Date(order.orderDate).toLocaleDateString()}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Email:</span> {order.customerEmail}
            </div>
            <div>
              <span className="font-medium">Order:</span> {order.orderNumber}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Items List */}
      <div className="space-y-4">
        {order.items.map((item) => {
          const isSelected = selectedItems[item.id];
          const selectedQuantity = isSelected?.quantity || 0;
          
          return (
            <Card key={item.id} className={`${!item.eligible ? 'opacity-50' : ''}`}>
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  {/* Product Image */}
                  <div className="w-20 h-20 bg-gray-200 rounded-lg flex items-center justify-center">
                    <Package className="h-8 w-8 text-gray-400" />
                  </div>

                  {/* Product Details */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-lg text-gray-900">{item.productName}</h3>
                    <div className="mt-1 text-sm text-gray-500 space-y-1">
                      <p>SKU: {item.sku}</p>
                      {item.size && <p>Size: {item.size}</p>}
                      {item.color && <p>Color: {item.color}</p>}
                      <p>Ordered: {item.quantity} × ${item.price.toFixed(2)}</p>
                    </div>

                    {!item.eligible && (
                      <div className="mt-3 flex items-center space-x-2 text-red-600">
                        <AlertTriangle className="h-4 w-4" />
                        <span className="text-sm">{item.ineligibleReason}</span>
                      </div>
                    )}
                  </div>

                  {/* Selection Controls */}
                  <div className="text-right space-y-4">
                    <div className="text-lg font-bold">
                      ${(item.price * item.quantity).toFixed(2)}
                    </div>

                    {item.eligible && (
                      <div className="space-y-4">
                        {/* Select/Unselect Button */}
                        <Button
                          variant={isSelected ? "default" : "outline"}
                          onClick={() => toggleItemSelection(item)}
                          size="sm"
                        >
                          {isSelected ? 'Selected' : 'Select Item'}
                        </Button>

                        {/* Quantity Controls */}
                        {isSelected && (
                          <div className="space-y-4">
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => updateItemQuantity(item.id, selectedQuantity - 1)}
                                disabled={selectedQuantity <= 1}
                              >
                                <Minus className="h-3 w-3" />
                              </Button>
                              <span className="w-8 text-center font-medium">{selectedQuantity}</span>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => updateItemQuantity(item.id, selectedQuantity + 1)}
                                disabled={selectedQuantity >= item.quantity}
                              >
                                <Plus className="h-3 w-3" />
                              </Button>
                            </div>
                            <div className="text-xs text-gray-500">
                              Max: {item.quantity}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Reason Selection */}
                {isSelected && (
                  <div className="mt-6 pt-6 border-t space-y-4">
                    <div>
                      <Label className="text-base font-medium">
                        Why are you returning this item? *
                      </Label>
                      <Select
                        value={isSelected.reason || ''}
                        onValueChange={(value) => updateItemReason(item.id, value)}
                      >
                        <SelectTrigger className="mt-2">
                          <SelectValue placeholder="Select a reason" />
                        </SelectTrigger>
                        <SelectContent>
                          {returnReasons.map((reason) => (
                            <SelectItem key={reason.value} value={reason.value}>
                              {reason.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label className="text-base font-medium">
                        Additional details (optional)
                      </Label>
                      <Textarea
                        placeholder="Tell us more about the issue..."
                        value={isSelected.notes || ''}
                        onChange={(e) => updateItemNotes(item.id, e.target.value)}
                        rows={3}
                        className="mt-2"
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Summary and Continue */}
      {selectedCount > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-lg">Return Summary</h3>
                <p className="text-gray-600">
                  {selectedCount} item{selectedCount !== 1 ? 's' : ''} selected
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  ${totalRefund.toFixed(2)}
                </div>
                <p className="text-sm text-gray-600">Estimated refund</p>
              </div>
            </div>
            
            <Button 
              onClick={handleContinue} 
              className="w-full mt-4"
              size="lg"
            >
              Continue to Resolution
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </CardContent>
        </Card>
      )}

      {selectedCount === 0 && (
        <Card className="border-gray-200">
          <CardContent className="p-6 text-center">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="font-medium text-lg text-gray-900 mb-2">No items selected</h3>
            <p className="text-gray-600">Select the items you'd like to return to continue</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SelectItems;