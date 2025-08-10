import React from 'react';
import { Package, Mail, Search, AlertCircle } from 'lucide-react';
import { Input } from '../../ui/input';
import { Alert, AlertDescription } from '../../ui/alert';

const OrderVerificationStep = ({ 
  formData, 
  updateFormData, 
  errors, 
  isLoading, 
  role 
}) => {
  if (role === 'admin') {
    // Admin version - order already known or searchable
    return (
      <div className="space-y-6">
        <div className="text-center">
          <Package className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Order Information
          </h3>
          <p className="text-gray-600">
            {formData.orderId 
              ? `Creating return for Order #${formData.verifiedOrder?.order_number || formData.orderId}`
              : 'Please select an order to create a return request'
            }
          </p>
        </div>

        {formData.verifiedOrder && (
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">Order Number:</span>
              <span>{formData.verifiedOrder.order_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Customer:</span>
              <span>{formData.verifiedOrder.customer_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Order Date:</span>
              <span>{new Date(formData.verifiedOrder.order_date).toLocaleDateString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Total Amount:</span>
              <span>${formData.verifiedOrder.total_amount.toFixed(2)}</span>
            </div>
          </div>
        )}

        {!formData.orderId && (
          <div className="text-center">
            <p className="text-gray-500 mb-4">
              To create a return, navigate from an order detail page or use the order search.
            </p>
          </div>
        )}
      </div>
    );
  }

  // Customer version - order lookup
  return (
    <div className="space-y-6">
      <div className="text-center">
        <Search className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Find Your Order
        </h3>
        <p className="text-gray-600">
          Enter your order number and email address to get started
        </p>
      </div>

      {errors.general && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {errors.general}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Order Number *
          </label>
          <div className="relative">
            <Package className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <Input
              type="text"
              placeholder="e.g., #1001"
              value={formData.orderNumber}
              onChange={(e) => updateFormData({ orderNumber: e.target.value })}
              className={`pl-10 ${errors.orderNumber ? 'border-red-500' : ''}`}
              disabled={isLoading}
            />
          </div>
          {errors.orderNumber && (
            <p className="text-red-500 text-sm mt-1">{errors.orderNumber}</p>
          )}
          <p className="text-gray-500 text-sm mt-1">
            Found in your order confirmation email
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Address *
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <Input
              type="email"
              placeholder="your-email@example.com"
              value={formData.email}
              onChange={(e) => updateFormData({ email: e.target.value })}
              className={`pl-10 ${errors.email ? 'border-red-500' : ''}`}
              disabled={isLoading}
            />
          </div>
          {errors.email && (
            <p className="text-red-500 text-sm mt-1">{errors.email}</p>
          )}
          <p className="text-gray-500 text-sm mt-1">
            The email used when placing the order
          </p>
        </div>
      </div>

      <div className="bg-blue-50 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <AlertCircle className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              Can't find your order information?
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Check your email confirmation for the exact order number format</li>
                <li>Ensure you're using the same email address used during checkout</li>
                <li>Order numbers usually start with # followed by numbers</li>
                <li>Contact our support team if you need assistance</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderVerificationStep;