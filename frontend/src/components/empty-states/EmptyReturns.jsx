import React from 'react';
import { RotateCcw, Plus, Settings } from 'lucide-react';
import EmptyStateCard from '../tenant/EmptyStateCard';
import { useAuth } from '../../contexts/AuthContext';

const EmptyReturns = ({ connected = false, tenantId }) => {
  const { user } = useAuth();

  const handleCreateReturn = () => {
    window.location.href = '/app/returns/create';
  };

  const handleConnectStore = () => {
    window.location.href = '/app/settings/integrations';
  };

  const handleViewPortal = () => {
    window.location.href = '/returns/start';
  };

  if (connected) {
    return (
      <EmptyStateCard
        title="No Returns Yet"
        description="Your store is connected and ready to receive returns. Customers can create returns through your customer portal, or you can create them manually."
        icon={RotateCcw}
        actionLabel="Create Manual Return"
        onAction={handleCreateReturn}
        secondaryActionLabel="View Customer Portal"
        onSecondaryAction={handleViewPortal}
        features={['Customer portal active', 'Email notifications', 'Shopify sync', 'Advanced analytics']}
        connected={true}
      />
    );
  }

  return (
    <EmptyStateCard
      title="Returns Management Ready"
      description="Start processing returns even without Shopify connected. You can create returns manually or set up the customer portal for self-service returns."
      icon={RotateCcw}
      actionLabel="Create First Return"
      onAction={handleCreateReturn}
      secondaryActionLabel="Set Up Customer Portal"
      onSecondaryAction={handleViewPortal}
      features={['Manual return creation', 'Customer portal', 'Basic analytics']}
      connected={false}
    />
  );
};

export default EmptyReturns;