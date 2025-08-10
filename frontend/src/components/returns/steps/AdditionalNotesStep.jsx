import React from 'react';
import { MessageSquare, User, AlertCircle } from 'lucide-react';
import { Textarea } from '../../ui/textarea';
import { Input } from '../../ui/input';
import { Alert, AlertDescription } from '../../ui/alert';

const AdditionalNotesStep = ({ 
  formData, 
  updateFormData, 
  errors, 
  isLoading, 
  role 
}) => {
  const handleNotesChange = (value) => {
    updateFormData({ customerNote: value });
  };

  const handleTagsChange = (value) => {
    const tags = value.split(',').map(tag => tag.trim()).filter(tag => tag);
    updateFormData({ internalTags: tags });
  };

  const handleOverrideNoteChange = (value) => {
    updateFormData({ adminOverrideNote: value });
  };

  const characterLimit = 500;
  const remainingChars = characterLimit - (formData.customerNote?.length || 0);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <MessageSquare className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Additional Information
        </h3>
        <p className="text-gray-600">
          {role === 'admin' 
            ? 'Add any internal notes or customer comments for this return'
            : 'Share any additional details that might help us process your return'
          }
        </p>
      </div>

      {/* Customer Notes */}
      <div className="bg-white border rounded-lg p-6">
        <div className="flex items-center mb-4">
          <User className="h-5 w-5 text-blue-600 mr-2" />
          <h4 className="font-medium text-gray-900">
            {role === 'admin' ? 'Customer Comments' : 'Your Comments'}
          </h4>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Additional Details {role === 'customer' && '(Optional)'}
          </label>
          <Textarea
            value={formData.customerNote || ''}
            onChange={(e) => handleNotesChange(e.target.value)}
            placeholder={
              role === 'admin' 
                ? 'Any additional comments from the customer about this return...'
                : 'Tell us more about your return (e.g., specific issues, special circumstances, preferred resolution timeline)...'
            }
            rows={4}
            maxLength={characterLimit}
            className="w-full"
          />
          <div className="flex items-center justify-between mt-2">
            <p className="text-sm text-gray-500">
              {role === 'customer' 
                ? 'This information helps us process your return more effectively'
                : 'This will be visible to the customer in their return confirmation'
              }
            </p>
            <span className={`text-sm ${remainingChars < 50 ? 'text-red-600' : 'text-gray-500'}`}>
              {remainingChars} characters remaining
            </span>
          </div>
        </div>

        {/* Helpful prompts for customers */}
        {role === 'customer' && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h5 className="text-sm font-medium text-blue-900 mb-2">
              Helpful information to include:
            </h5>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Specific defects or damage details</li>
              <li>• How the item differs from your expectations</li>
              <li>• Any urgency or special timing needs</li>
              <li>• Preferred communication method</li>
              <li>• Order or shipping issues encountered</li>
            </ul>
          </div>
        )}
      </div>

      {/* Admin-only sections */}
      {role === 'admin' && (
        <>
          {/* Internal Notes */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <AlertCircle className="h-5 w-5 text-orange-600 mr-2" />
              <h4 className="font-medium text-orange-900">Internal Notes</h4>
              <span className="ml-2 text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded">
                Staff Only
              </span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Internal Comments
              </label>
              <Textarea
                value={formData.adminOverrideNote || ''}
                onChange={(e) => handleOverrideNoteChange(e.target.value)}
                placeholder="Internal notes about this return (not visible to customer)..."
                rows={3}
                className="w-full"
              />
              <p className="text-sm text-gray-500 mt-2">
                These notes are only visible to staff and will not be shared with the customer
              </p>
            </div>
          </div>

          {/* Internal Tags */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <AlertCircle className="h-5 w-5 text-orange-600 mr-2" />
              <h4 className="font-medium text-orange-900">Internal Tags</h4>
              <span className="ml-2 text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded">
                Staff Only
              </span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Classification Tags
              </label>
              <Input
                value={formData.internalTags?.join(', ') || ''}
                onChange={(e) => handleTagsChange(e.target.value)}
                placeholder="e.g., vip-customer, priority, fraud-check, bulk-return"
                className="w-full"
              />
              <p className="text-sm text-gray-500 mt-2">
                Separate tags with commas. Used for filtering and reporting.
              </p>
              
              {/* Common tags suggestions */}
              <div className="mt-3">
                <p className="text-sm text-gray-600 mb-2">Common tags:</p>
                <div className="flex flex-wrap gap-2">
                  {['vip-customer', 'priority', 'bulk-return', 'fraud-check', 'defective-batch', 'warranty', 'exchange-pending'].map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => {
                        const currentTags = formData.internalTags || [];
                        if (!currentTags.includes(tag)) {
                          updateFormData({ internalTags: [...currentTags, tag] });
                        }
                      }}
                      className="text-xs px-2 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                    >
                      + {tag}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Override Options */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
              <h4 className="font-medium text-red-900">Admin Override Options</h4>
              <span className="ml-2 text-xs bg-red-200 text-red-800 px-2 py-1 rounded">
                Use with Caution
              </span>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="admin-override-approve"
                  checked={formData.adminOverrideApprove || false}
                  onChange={(e) => updateFormData({ adminOverrideApprove: e.target.checked })}
                  className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                />
                <label htmlFor="admin-override-approve" className="text-sm font-medium text-gray-900">
                  Override policy and auto-approve this return
                </label>
              </div>
              
              {formData.adminOverrideApprove && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-800">
                    <strong>Warning:</strong> This will bypass all policy checks and automatically approve the return. 
                    Ensure you have proper authorization and document the reason in the internal notes above.
                  </AlertDescription>
                </Alert>
              )}
              
              <div className="text-sm text-gray-600">
                <p className="mb-2">Override should only be used for:</p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Customer service exceptions</li>
                  <li>Manager-authorized special cases</li>
                  <li>System error corrections</li>
                  <li>VIP customer accommodations</li>
                </ul>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Customer Service Note */}
      {role === 'customer' && (
        <Alert className="border-blue-200 bg-blue-50">
          <MessageSquare className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            <strong>Need help?</strong> If you have questions about our return policy or need assistance 
            with your return, our customer service team is available 24/7 via chat, email, or phone. 
            We're here to make the return process as smooth as possible.
          </AlertDescription>
        </Alert>
      )}

      {/* Processing Timeline */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">What Happens Next?</h4>
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-medium">
              1
            </div>
            <div>
              <h5 className="font-medium text-gray-900">Submission Confirmation</h5>
              <p className="text-sm text-gray-600">
                You'll receive an email confirmation with your return reference number
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-medium">
              2
            </div>
            <div>
              <h5 className="font-medium text-gray-900">Return Processing</h5>
              <p className="text-sm text-gray-600">
                {role === 'admin' 
                  ? 'Return will be processed according to admin settings and overrides'
                  : 'Our team will review your return (auto-approved returns skip this step)'
                }
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-medium">
              3
            </div>
            <div>
              <h5 className="font-medium text-gray-900">Return Instructions</h5>
              <p className="text-sm text-gray-600">
                You'll receive return shipping instructions and labels (if applicable)
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-medium">
              4
            </div>
            <div>
              <h5 className="font-medium text-gray-900">Refund Processing</h5>
              <p className="text-sm text-gray-600">
                Refund will be processed within 3-5 business days after we receive your items
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdditionalNotesStep;