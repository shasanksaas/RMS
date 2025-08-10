import React, { useState } from 'react';
import { Clock, Mail, CheckCircle, AlertCircle, ArrowLeft, Camera } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Alert, AlertDescription } from '../ui/alert';

const FallbackModeDisplay = ({ 
  fallbackData, 
  onBackToLookup,
  onSubmitAdditionalInfo 
}) => {
  const [showAdditionalForm, setShowAdditionalForm] = useState(false);
  const [additionalData, setAdditionalData] = useState({
    items: [],
    customerNote: '',
    photos: []
  });
  const [newItem, setNewItem] = useState({
    title: '',
    sku: '',
    quantity: 1,
    reason: 'CHANGED_MIND'
  });

  const returnReasons = [
    { value: 'SIZE_WRONG', label: 'Wrong size' },
    { value: 'COLOR_WRONG', label: 'Wrong color/style' },
    { value: 'DEFECTIVE', label: 'Defective/damaged' },
    { value: 'NOT_AS_DESCRIBED', label: 'Not as described' },
    { value: 'CHANGED_MIND', label: 'Changed my mind' },
    { value: 'ARRIVED_LATE', label: 'Arrived too late' },
    { value: 'OTHER', label: 'Other reason' }
  ];

  const addItem = () => {
    if (newItem.title.trim()) {
      setAdditionalData(prev => ({
        ...prev,
        items: [...prev.items, { ...newItem, id: Date.now() }]
      }));
      setNewItem({
        title: '',
        sku: '',
        quantity: 1,
        reason: 'CHANGED_MIND'
      });
    }
  };

  const removeItem = (itemId) => {
    setAdditionalData(prev => ({
      ...prev,
      items: prev.items.filter(item => item.id !== itemId)
    }));
  };

  const handlePhotoUpload = (event) => {
    const files = Array.from(event.target.files);
    // In a real implementation, you would upload to S3 and get URLs
    const photoUrls = files.map(file => URL.createObjectURL(file));
    setAdditionalData(prev => ({
      ...prev,
      photos: [...prev.photos, ...photoUrls]
    }));
  };

  const handleSubmit = () => {
    onSubmitAdditionalInfo({
      ...fallbackData,
      ...additionalData
    });
  };

  if (showAdditionalForm) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-blue-600" />
                <span>Provide Additional Details (Optional)</span>
              </div>
              <Button variant="outline" size="sm" onClick={() => setShowAdditionalForm(false)}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to confirmation
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <Alert className="border-blue-200 bg-blue-50">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-blue-800">
                Help us process your request faster by providing item details. This information is optional but recommended.
              </AlertDescription>
            </Alert>

            {/* Add Items */}
            <div>
              <h3 className="font-semibold mb-3">Items to Return</h3>
              
              {/* Existing items */}
              {additionalData.items.length > 0 && (
                <div className="space-y-3 mb-4">
                  {additionalData.items.map((item) => (
                    <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium">{item.title}</p>
                        {item.sku && <p className="text-sm text-gray-600">SKU: {item.sku}</p>}
                        <p className="text-sm text-gray-600">
                          Qty: {item.quantity} | Reason: {returnReasons.find(r => r.value === item.reason)?.label}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeItem(item.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add new item form */}
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3 p-4 border rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Product Name *
                  </label>
                  <Input
                    value={newItem.title}
                    onChange={(e) => setNewItem(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="e.g., Blue T-Shirt"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    SKU (if known)
                  </label>
                  <Input
                    value={newItem.sku}
                    onChange={(e) => setNewItem(prev => ({ ...prev, sku: e.target.value }))}
                    placeholder="e.g., TS-BLUE-M"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quantity
                  </label>
                  <select
                    className="w-full p-2 border rounded"
                    value={newItem.quantity}
                    onChange={(e) => setNewItem(prev => ({ ...prev, quantity: parseInt(e.target.value) }))}
                  >
                    {[1,2,3,4,5].map(qty => (
                      <option key={qty} value={qty}>{qty}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reason
                  </label>
                  <select
                    className="w-full p-2 border rounded"
                    value={newItem.reason}
                    onChange={(e) => setNewItem(prev => ({ ...prev, reason: e.target.value }))}
                  >
                    {returnReasons.map(reason => (
                      <option key={reason.value} value={reason.value}>
                        {reason.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <Button
                onClick={addItem}
                disabled={!newItem.title.trim()}
                className="mt-2"
                variant="outline"
              >
                Add Item
              </Button>
            </div>

            {/* Photo Upload */}
            <div>
              <h3 className="font-semibold mb-3">Photos (Optional)</h3>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Camera className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600 mb-2">
                  Upload photos of items (especially if damaged)
                </p>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handlePhotoUpload}
                  className="hidden"
                  id="photo-upload"
                />
                <label htmlFor="photo-upload">
                  <Button variant="outline" size="sm" as="span">
                    Choose Photos
                  </Button>
                </label>
              </div>
              {additionalData.photos.length > 0 && (
                <div className="grid grid-cols-3 gap-2 mt-3">
                  {additionalData.photos.map((photo, index) => (
                    <img
                      key={index}
                      src={photo}
                      alt={`Upload ${index + 1}`}
                      className="w-full h-24 object-cover rounded"
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Customer Note */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Notes (Optional)
              </label>
              <textarea
                className="w-full p-3 border rounded-lg resize-none"
                rows="3"
                placeholder="Any additional details about your return request..."
                value={additionalData.customerNote}
                onChange={(e) => setAdditionalData(prev => ({ ...prev, customerNote: e.target.value }))}
              />
            </div>

            <div className="flex justify-center space-x-4">
              <Button
                onClick={() => setShowAdditionalForm(false)}
                variant="outline"
              >
                Skip for Now
              </Button>
              <Button
                onClick={handleSubmit}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Submit Return Request
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardContent className="text-center py-8">
          <div className="bg-blue-100 p-3 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <Clock className="h-8 w-8 text-blue-600" />
          </div>
          
          <h2 className="text-2xl font-bold mb-2">Request Received!</h2>
          <p className="text-gray-600 mb-6">
            {fallbackData.message}
          </p>

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="font-semibold mb-2">Request Details:</h3>
            <div className="text-sm text-gray-600 space-y-1">
              <p><strong>Order Number:</strong> #{fallbackData.captured.orderNumber}</p>
              <p><strong>Email:</strong> {fallbackData.captured.email}</p>
              <p><strong>Submitted:</strong> {new Date(fallbackData.captured.submittedAt).toLocaleString()}</p>
            </div>
          </div>

          <Alert className="border-blue-200 bg-blue-50 mb-6">
            <Mail className="h-4 w-4" />
            <AlertDescription className="text-blue-800">
              We'll email you at <strong>{fallbackData.captured.email}</strong> once we've reviewed your request.
              This typically takes 1-2 business days.
            </AlertDescription>
          </Alert>

          <div className="space-y-3">
            <Button
              onClick={() => setShowAdditionalForm(true)}
              variant="outline"
              className="w-full"
            >
              Provide Additional Details (Optional)
            </Button>
            
            <Button
              onClick={onBackToLookup}
              variant="outline"
              className="w-full"
            >
              Submit Another Return Request
            </Button>
          </div>

          <div className="mt-8 text-center text-sm text-gray-500">
            <h4 className="font-medium mb-2">What happens next?</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span>We verify your order details</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span>You receive email confirmation</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span>Return labels sent (if approved)</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default FallbackModeDisplay;