import React from 'react';
import { Users, Settings, ExternalLink } from 'lucide-react';
import EmptyStateCard from '../tenant/EmptyStateCard';
import { useAuth } from '../../contexts/AuthContext';

const EmptyCustomers = ({ connected = false, tenantId }) => {
  const { user } = useAuth();

  const handleConnectStore = () => {
    window.location.href = '/app/settings/integrations';
  };

  const handleViewReturns = () => {
    window.location.href = '/app/returns';
  };

  const handleViewHelp = () => {
    window.open('https://help.shopify.com/en/manual/customers', '_blank');
  };

  if (connected) {
    return (
      <EmptyStateCard
        title="No Customer Data Yet"
        description="Your Shopify store is connected but no customer data has been synced yet. Customer information will appear here as orders and returns are processed."
        icon={Users}
        actionLabel="Sync Customer Data"
        onAction={() => window.location.reload()}
        secondaryActionLabel="View Returns"
        onSecondaryAction={handleViewReturns}
        features={['Customer sync active', 'Order history', 'Return tracking']}
        connected={true}
      />
    );
  }

  return (
    <EmptyStateCard
      title="Connect Store to Sync Customers"
      description="Automatically sync customer data from your Shopify store to track return history, preferences, and provide better customer service."
      icon={Users}
      actionLabel="Connect Shopify Store"
      onAction={handleConnectStore}
      secondaryActionLabel="Learn More"
      onSecondaryAction={handleViewHelp}
      features={['Manual customer tracking']}
      connected={false}
    />
  );
};

export default EmptyCustomers;