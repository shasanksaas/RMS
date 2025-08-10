import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import UnifiedReturnForm from '../../components/returns/UnifiedReturnForm';

const CreateReturn = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const prefilledOrderId = searchParams.get('orderId');

  const handleSuccess = (result) => {
    // Navigate to the created return detail page
    navigate(`/admin/returns/${result.return_id}`, {
      state: { 
        message: result.message,
        returnData: result
      }
    });
  };

  const handleCancel = () => {
    // Navigate back to returns list
    navigate('/admin/returns');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <UnifiedReturnForm
          role="admin"
          prefilledOrderId={prefilledOrderId}
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      </div>
    </div>
  );
};

export default CreateReturn;