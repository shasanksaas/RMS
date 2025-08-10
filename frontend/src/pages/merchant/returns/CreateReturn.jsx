import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import UnifiedReturnForm from '../../../components/returns/UnifiedReturnForm';

const CreateReturn = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const orderId = searchParams.get('orderId');

  const handleSuccess = (result) => {
    // Navigate to return detail page
    navigate(`/app/returns/${result.return_id}`, {
      state: {
        message: result.message,
        newReturn: true
      }
    });
  };

  const handleCancel = () => {
    // Navigate back to returns list or orders depending on where they came from
    const from = searchParams.get('from');
    if (from === 'orders') {
      navigate('/app/orders');
    } else {
      navigate('/app/returns');
    }
  };

  return (
    <div className="p-6">
      <UnifiedReturnForm
        role="admin"
        prefilledOrderId={orderId}
        onSuccess={handleSuccess}
        onCancel={handleCancel}
      />
    </div>
  );
};

export default CreateReturn;