import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Package, 
  Mail, 
  Search, 
  ChevronRight, 
  Upload, 
  Calculator,
  MapPin,
  CheckCircle,
  AlertCircle,
  Camera,
  Truck,
  Store,
  CreditCard
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';

// Step Component Imports
import OrderVerificationStep from './steps/OrderVerificationStep';
import ItemSelectionStep from './steps/ItemSelectionStep';
import ReturnReasonStep from './steps/ReturnReasonStep';
import PreferredOutcomeStep from './steps/PreferredOutcomeStep';
import ReturnMethodStep from './steps/ReturnMethodStep';
import PolicyPreviewStep from './steps/PolicyPreviewStep';
import AdditionalNotesStep from './steps/AdditionalNotesStep';
import ReviewSubmitStep from './steps/ReviewSubmitStep';

const UnifiedReturnForm = ({ 
  role = 'customer', // 'customer' or 'admin'
  prefilledOrderId = null,
  onSuccess = null,
  onCancel = null 
}) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // Form state
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});
  
  // Form data
  const [formData, setFormData] = useState({
    // Step 1: Order Verification
    orderNumber: '',
    email: '',
    orderId: prefilledOrderId || searchParams.get('orderId'),
    verifiedOrder: null,
    eligibleItems: [],
    
    // Step 2: Item Selection
    selectedItems: [],
    
    // Step 3: Return Reasons
    itemReasons: {}, // itemId -> {reason, note, photos}
    
    // Step 4: Preferred Outcome
    preferredOutcome: '',
    
    // Step 5: Return Method
    returnMethod: '',
    returnLocationId: null,
    
    // Step 6: Policy Preview (read-only)
    policyPreview: null,
    
    // Step 7: Additional Notes
    customerNote: '',
    
    // Admin-only fields
    adminOverrideApprove: false,
    adminOverrideNote: '',
    internalTags: [],
    manualFeeOverride: null
  });
  
  const steps = [
    { number: 1, title: 'Order Verification', component: OrderVerificationStep },
    { number: 2, title: 'Item Selection', component: ItemSelectionStep },
    { number: 3, title: 'Return Reason', component: ReturnReasonStep },
    { number: 4, title: 'Preferred Outcome', component: PreferredOutcomeStep },
    { number: 5, title: 'Return Method', component: ReturnMethodStep },
    { number: 6, title: 'Policy Preview', component: PolicyPreviewStep },
    { number: 7, title: 'Additional Notes', component: AdditionalNotesStep },
    { number: 8, title: 'Review & Submit', component: ReviewSubmitStep }
  ];

  // Auto-save for admin forms
  useEffect(() => {
    if (role === 'admin' && formData.orderId) {
      const saveData = () => {
        localStorage.setItem(`return-draft-${formData.orderId}`, JSON.stringify(formData));
      };
      
      const timer = setTimeout(saveData, 1000);
      return () => clearTimeout(timer);
    }
  }, [formData, role]);

  // Load draft for admin
  useEffect(() => {
    if (role === 'admin' && formData.orderId) {
      const draft = localStorage.getItem(`return-draft-${formData.orderId}`);
      if (draft) {
        try {
          const draftData = JSON.parse(draft);
          setFormData(prev => ({ ...prev, ...draftData }));
        } catch (error) {
          console.error('Failed to load draft:', error);
        }
      }
    }
  }, [role, formData.orderId]);

  const updateFormData = (updates) => {
    setFormData(prev => ({ ...prev, ...updates }));
    setErrors({}); // Clear errors when data changes
  };

  const validateCurrentStep = () => {
    const newErrors = {};
    
    switch (currentStep) {
      case 1: // Order Verification
        if (role === 'customer') {
          if (!formData.orderNumber.trim()) {
            newErrors.orderNumber = 'Order number is required';
          }
          if (!formData.email.trim()) {
            newErrors.email = 'Email is required';
          } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Invalid email format';
          }
        }
        break;
        
      case 2: // Item Selection
        if (formData.selectedItems.length === 0) {
          newErrors.selectedItems = 'Please select at least one item to return';
        }
        break;
        
      case 3: // Return Reasons
        for (const item of formData.selectedItems) {
          const reason = formData.itemReasons[item.id];
          if (!reason?.reason) {
            newErrors[`reason_${item.id}`] = 'Reason is required for this item';
          }
          if (reason?.reason === 'damaged_defective' && (!reason?.photos || reason.photos.length === 0)) {
            newErrors[`photos_${item.id}`] = 'Photos are required for damaged/defective items';
          }
        }
        break;
        
      case 4: // Preferred Outcome
        if (!formData.preferredOutcome) {
          newErrors.preferredOutcome = 'Please select your preferred outcome';
        }
        break;
        
      case 5: // Return Method
        if (!formData.returnMethod) {
          newErrors.returnMethod = 'Please select a return method';
        }
        if (formData.returnMethod === 'in_store' && !formData.returnLocationId) {
          newErrors.returnLocationId = 'Please select a return location';
        }
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = async () => {
    if (!validateCurrentStep()) {
      return;
    }

    // Special handling for order verification step
    if (currentStep === 1 && role === 'customer') {
      await handleOrderLookup();
      return;
    }

    // Special handling for item selection - get policy preview
    if (currentStep === 2) {
      await getPolicyPreview();
    }

    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleOrderLookup = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/unified-returns/order/lookup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
        },
        body: JSON.stringify({
          order_number: formData.orderNumber,
          email: formData.email
        })
      });

      const result = await response.json();
      
      if (result.success) {
        updateFormData({
          verifiedOrder: result,
          eligibleItems: result.eligible_items,
          orderId: result.order_id
        });
        setCurrentStep(2);
      } else {
        setErrors({ general: result.error || 'Failed to verify order' });
      }
    } catch (error) {
      setErrors({ general: 'Failed to lookup order. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const getPolicyPreview = async () => {
    if (formData.selectedItems.length === 0) return;

    setIsLoading(true);
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

      const preview = await response.json();
      updateFormData({ policyPreview: preview });
    } catch (error) {
      console.error('Failed to get policy preview:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!validateCurrentStep()) {
      return;
    }

    setIsLoading(true);
    try {
      // Prepare submission data
      const submissionData = {
        channel: role === 'admin' ? 'admin' : 'portal',
        order_id: role === 'admin' ? formData.orderId : undefined,
        order_number: role === 'customer' ? formData.orderNumber : undefined,
        email: role === 'customer' ? formData.email : undefined,
        items: formData.selectedItems.map(item => ({
          fulfillment_line_item_id: item.fulfillment_line_item_id,
          quantity: item.quantity,
          reason: formData.itemReasons[item.id]?.reason || 'other',
          reason_note: formData.itemReasons[item.id]?.note || '',
          photo_urls: formData.itemReasons[item.id]?.photos || []
        })),
        preferred_outcome: formData.preferredOutcome,
        return_method: formData.returnMethod,
        return_location_id: formData.returnLocationId,
        customer_note: formData.customerNote,
        admin_override_approve: role === 'admin' ? formData.adminOverrideApprove : undefined,
        admin_override_note: role === 'admin' ? formData.adminOverrideNote : undefined,
        internal_tags: role === 'admin' ? formData.internalTags : undefined,
        manual_fee_override: role === 'admin' ? formData.manualFeeOverride : undefined
      };

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/unified-returns/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
        },
        body: JSON.stringify(submissionData)
      });

      const result = await response.json();
      
      if (result.success) {
        // Clear draft if admin
        if (role === 'admin' && formData.orderId) {
          localStorage.removeItem(`return-draft-${formData.orderId}`);
        }
        
        // Call success handler or navigate
        if (onSuccess) {
          onSuccess(result);
        } else {
          navigate(role === 'admin' 
            ? `/app/returns/${result.return_id}` 
            : `/returns/confirmation/${result.return_id}`
          );
        }
      } else {
        setErrors({ general: result.detail || 'Failed to create return request' });
      }
    } catch (error) {
      setErrors({ general: 'Failed to submit return request. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const CurrentStepComponent = steps[currentStep - 1]?.component;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">
          {role === 'admin' ? 'Create Return Request' : 'Start Your Return'}
        </h1>
        <p className="text-gray-600 mt-2">
          {role === 'admin' 
            ? 'Create a return request on behalf of a customer'
            : 'Follow the steps below to initiate your return request'
          }
        </p>
      </div>

      {/* Progress Indicator */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium ${
                  currentStep === step.number 
                    ? 'bg-blue-600 text-white' 
                    : currentStep > step.number 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-200 text-gray-600'
                }`}>
                  {currentStep > step.number ? <CheckCircle className="h-5 w-5" /> : step.number}
                </div>
                <div className={`ml-3 ${index < steps.length - 1 ? 'mr-6' : ''}`}>
                  <div className="text-sm font-medium text-gray-900">{step.title}</div>
                </div>
                {index < steps.length - 1 && (
                  <ChevronRight className={`h-4 w-4 mx-2 ${
                    currentStep > step.number ? 'text-green-600' : 'text-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
          
          <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-in-out"
              style={{ width: `${(currentStep / steps.length) * 100}%` }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {errors.general && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {errors.general}
          </AlertDescription>
        </Alert>
      )}

      {/* Current Step Content */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded">
              Step {currentStep}
            </span>
            <span>{steps[currentStep - 1]?.title}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {CurrentStepComponent && (
            <CurrentStepComponent
              formData={formData}
              updateFormData={updateFormData}
              errors={errors}
              isLoading={isLoading}
              role={role}
            />
          )}
        </CardContent>
      </Card>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {currentStep > 1 && (
            <Button 
              variant="outline" 
              onClick={handlePrevious}
              disabled={isLoading}
            >
              Previous
            </Button>
          )}
          
          {onCancel && (
            <Button 
              variant="ghost" 
              onClick={onCancel}
              disabled={isLoading}
            >
              Cancel
            </Button>
          )}
        </div>

        <div className="flex items-center space-x-3">
          {role === 'admin' && (
            <div className="text-sm text-gray-500">
              Draft auto-saved
            </div>
          )}
          
          {currentStep < steps.length ? (
            <Button 
              onClick={handleNext}
              disabled={isLoading}
              className="min-w-[100px]"
            >
              {isLoading ? 'Loading...' : currentStep === 1 && role === 'customer' ? 'Verify Order' : 'Next'}
              {!isLoading && <ChevronRight className="h-4 w-4 ml-2" />}
            </Button>
          ) : (
            <Button 
              onClick={handleSubmit}
              disabled={isLoading}
              className="min-w-[120px] bg-green-600 hover:bg-green-700"
            >
              {isLoading ? 'Creating...' : 'Submit Return Request'}
            </Button>
          )}
        </div>
      </div>

      {/* Admin Override Panel */}
      {role === 'admin' && currentStep > 2 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="text-orange-800 text-lg">Admin Overrides</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="admin-override"
                checked={formData.adminOverrideApprove}
                onChange={(e) => updateFormData({ adminOverrideApprove: e.target.checked })}
                className="rounded border-gray-300"
              />
              <label htmlFor="admin-override" className="text-sm font-medium text-gray-700">
                Override and auto-approve this return
              </label>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Internal Note
              </label>
              <Textarea
                value={formData.adminOverrideNote}
                onChange={(e) => updateFormData({ adminOverrideNote: e.target.value })}
                placeholder="Internal note for this return (not visible to customer)"
                rows={2}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Internal Tags
              </label>
              <Input
                value={formData.internalTags.join(', ')}
                onChange={(e) => updateFormData({ 
                  internalTags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
                })}
                placeholder="priority, vip, special-case"
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UnifiedReturnForm;