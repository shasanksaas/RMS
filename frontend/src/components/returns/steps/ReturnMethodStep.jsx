import React from 'react';
import { Truck, MapPin, Package, CreditCard, AlertCircle } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Alert, AlertDescription } from '../../ui/alert';

const ReturnMethodStep = ({ 
  formData, 
  updateFormData, 
  errors, 
  isLoading, 
  role 
}) => {
  const returnMethods = [
    {
      value: 'prepaid_label',
      title: 'Prepaid Return Label',
      description: 'We\'ll email you a prepaid shipping label',
      icon: Truck,
      cost: 'Free',
      timeframe: 'Label available after approval',
      available: true,
      recommended: true
    },
    {
      value: 'qr_dropoff',
      title: 'QR Code Drop-off',
      description: 'Drop off at carrier location with QR code',
      icon: Package,
      cost: 'Free',
      timeframe: 'QR code available after approval',
      available: true
    },
    {
      value: 'in_store',
      title: 'In-Store Return',
      description: 'Return items at any of our store locations',
      icon: MapPin,
      cost: 'Free',
      timeframe: 'Immediate',
      available: true
    },
    {
      value: 'customer_ships',
      title: 'Ship at Your Own Cost',
      description: 'Use your own shipping method and label',
      icon: CreditCard,
      cost: 'Your cost',
      timeframe: 'Ship whenever convenient',
      available: true
    }
  ];

  const storeLocations = [
    { id: '1', name: 'Downtown Store', address: '123 Main St, City, ST 12345', hours: 'Mon-Sat 9am-8pm' },
    { id: '2', name: 'Mall Location', address: '456 Mall Blvd, City, ST 12345', hours: 'Mon-Sun 10am-9pm' },
    { id: '3', name: 'Suburban Outlet', address: '789 Suburb Ave, City, ST 12345', hours: 'Mon-Sat 10am-7pm' }
  ];

  const handleMethodSelect = (value) => {
    updateFormData({ returnMethod: value, returnLocationId: null });
  };

  const handleLocationSelect = (locationId) => {
    updateFormData({ returnLocationId: locationId });
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <Truck className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Return Method
        </h3>
        <p className="text-gray-600">
          Choose how you'd like to return your items
        </p>
      </div>

      {errors.returnMethod && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {errors.returnMethod}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {returnMethods.map((method) => {
          const Icon = method.icon;
          const isSelected = formData.returnMethod === method.value;
          
          return (
            <div
              key={method.value}
              onClick={() => method.available && handleMethodSelect(method.value)}
              className={`relative border-2 rounded-lg p-6 cursor-pointer transition-all ${
                isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : method.available
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

              {/* Recommended Badge */}
              {method.recommended && (
                <div className="absolute top-2 left-2 bg-green-600 text-white text-xs px-2 py-1 rounded-full">
                  Recommended
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
                    {method.title}
                  </h4>
                  <p className={`text-sm mt-1 ${
                    isSelected ? 'text-blue-700' : 'text-gray-600'
                  }`}>
                    {method.description}
                  </p>
                  
                  <div className="flex items-center justify-between mt-3">
                    <span className={`text-xs font-medium px-2 py-1 rounded ${
                      method.cost === 'Free'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {method.cost}
                    </span>
                    <span className={`text-xs ${
                      isSelected ? 'text-blue-600' : 'text-gray-500'
                    }`}>
                      {method.timeframe}
                    </span>
                  </div>
                </div>
              </div>

              {!method.available && (
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

      {/* Store Location Selection */}
      {formData.returnMethod === 'in_store' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Store Location *
            </label>
            <Select
              value={formData.returnLocationId || ''}
              onValueChange={handleLocationSelect}
            >
              <SelectTrigger className={errors.returnLocationId ? 'border-red-500' : ''}>
                <SelectValue placeholder="Choose a store location" />
              </SelectTrigger>
              <SelectContent>
                {storeLocations.map((location) => (
                  <SelectItem key={location.id} value={location.id}>
                    <div>
                      <div className="font-medium">{location.name}</div>
                      <div className="text-sm text-gray-600">{location.address}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.returnLocationId && (
              <p className="text-red-500 text-sm mt-1">{errors.returnLocationId}</p>
            )}
          </div>

          {/* Selected Store Details */}
          {formData.returnLocationId && (
            <div className="bg-gray-50 rounded-lg p-4">
              {(() => {
                const selectedLocation = storeLocations.find(
                  loc => loc.id === formData.returnLocationId
                );
                if (!selectedLocation) return null;
                
                return (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">
                      {selectedLocation.name}
                    </h4>
                    <p className="text-sm text-gray-600 mb-1">
                      <MapPin className="h-4 w-4 inline mr-1" />
                      {selectedLocation.address}
                    </p>
                    <p className="text-sm text-gray-600">
                      Hours: {selectedLocation.hours}
                    </p>
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      )}

      {/* Method Details */}
      {formData.returnMethod && (
        <div className="bg-gray-50 rounded-lg p-6 space-y-4">
          <h4 className="font-medium text-gray-900">
            {returnMethods.find(m => m.value === formData.returnMethod)?.title} Instructions
          </h4>
          
          {formData.returnMethod === 'prepaid_label' && (
            <div className="space-y-3">
              <Alert className="border-blue-200 bg-blue-50">
                <Truck className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  Once your return is approved, we'll email you a prepaid return shipping label.
                </AlertDescription>
              </Alert>
              <div className="text-sm text-gray-600">
                <p className="font-medium mb-2">Steps to return:</p>
                <ol className="list-decimal list-inside space-y-1">
                  <li>Pack items securely in original or similar packaging</li>
                  <li>Print the prepaid return label from your email</li>
                  <li>Attach the label to your package</li>
                  <li>Drop off at any carrier location or schedule pickup</li>
                </ol>
              </div>
            </div>
          )}

          {formData.returnMethod === 'qr_dropoff' && (
            <div className="space-y-3">
              <Alert className="border-blue-200 bg-blue-50">
                <Package className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  We'll send you a QR code to show at participating carrier locations.
                </AlertDescription>
              </Alert>
              <div className="text-sm text-gray-600">
                <p className="font-medium mb-2">Steps to return:</p>
                <ol className="list-decimal list-inside space-y-1">
                  <li>Pack items securely (no need to print labels)</li>
                  <li>Take your package and QR code to a participating location</li>
                  <li>Show the QR code to the staff - they'll handle the rest</li>
                  <li>Keep your receipt for tracking</li>
                </ol>
              </div>
            </div>
          )}

          {formData.returnMethod === 'customer_ships' && (
            <div className="space-y-3">
              <Alert className="border-amber-200 bg-amber-50">
                <CreditCard className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800">
                  You'll be responsible for shipping costs and ensuring safe delivery.
                </AlertDescription>
              </Alert>
              <div className="text-sm text-gray-600">
                <p className="font-medium mb-2">Return address:</p>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <p className="font-mono text-sm">
                    Returns Department<br />
                    Fashion Forward Inc.<br />
                    123 Warehouse Dr<br />
                    Returns City, ST 12345
                  </p>
                </div>
                <p className="mt-2">
                  <strong>Important:</strong> Include your return confirmation number 
                  on the package and use a trackable shipping method.
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Policy Reminder */}
      <Alert className="border-gray-200 bg-gray-50">
        <AlertCircle className="h-4 w-4 text-gray-600" />
        <AlertDescription className="text-gray-700">
          <strong>Return Policy:</strong> Items must be in original condition with tags attached. 
          Some restrictions may apply to final sale items, personalized products, and certain categories.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default ReturnMethodStep;