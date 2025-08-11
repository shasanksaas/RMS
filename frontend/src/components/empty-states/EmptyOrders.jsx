import React from 'react';
import { Package, Settings, ExternalLink } from 'lucide-react';
import EmptyStateCard from '../tenant/EmptyStateCard';
import { useAuth } from '../../contexts/AuthContext';

const EmptyOrders = ({ connected = false, tenantId }) => {
  const { user } = useAuth();

  const handleConnectStore = () => {
    // Navigate to integrations settings
    window.location.href = '/app/settings/integrations';
  };

  const handleViewHelp = () => {
    window.open('https://help.shopify.com/en/api', '_blank');
  };

  if (connected) {
    return (
      <EmptyStateCard
        title="No Orders Found"
        description="Your Shopify store is connected but no orders have been imported yet. This could be because you haven't had any orders, or the sync is still in progress."
        icon={Package}
        actionLabel="Refresh Orders"
        onAction={() => window.location.reload()}
        secondaryActionLabel="Check Sync Settings"
        onSecondaryAction={handleConnectStore}
        features={['Order sync active', 'Real-time updates', 'Customer data sync']}
        connected={true}
      />
    );
  }

  return (
    <EmptyStateCard
      title="Connect Your Shopify Store"
      description="Import your orders automatically by connecting your Shopify store. This enables order lookup, customer data, and advanced return management features."
      icon={Package}
      actionLabel="Connect Shopify Store"
      onAction={handleConnectStore}
      secondaryActionLabel="Learn More"
      onSecondaryAction={handleViewHelp}
      features={['Manual order entry', 'Basic return processing']}
      connected={false}
    />
  );
};

export default EmptyOrders;