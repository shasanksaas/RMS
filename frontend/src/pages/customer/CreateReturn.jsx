import React from 'react';
import { useNavigate } from 'react-router-dom';
import UnifiedReturnForm from '../../components/returns/UnifiedReturnForm';

const CreateReturn = () => {
  const navigate = useNavigate();

  const handleSuccess = (result) => {
    // Navigate to confirmation page
    navigate(`/returns/confirmation/${result.return_id}`, {
      state: { 
        message: result.message,
        returnData: result
      }
    });
  };

  const handleCancel = () => {
    // Navigate back to customer portal home
    navigate('/returns');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Customer Portal Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">Return Center</h1>
              <span className="text-sm text-gray-500">Start Your Return</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => navigate('/returns')}
                className="text-gray-600 hover:text-gray-900 text-sm"
              >
                ← Back to Return Center
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Form Container */}
      <div className="container mx-auto py-8">
        <UnifiedReturnForm
          role="customer"
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      </div>

      {/* Customer Support Footer */}
      <div className="bg-white border-t mt-12">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Need Help with Your Return?
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 text-xl">💬</span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Live Chat</h4>
                <p className="text-sm text-gray-600">Available 24/7</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 text-xl">📧</span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Email Support</h4>
                <p className="text-sm text-gray-600">support@company.com</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 text-xl">📞</span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Phone Support</h4>
                <p className="text-sm text-gray-600">1-800-123-4567</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateReturn;