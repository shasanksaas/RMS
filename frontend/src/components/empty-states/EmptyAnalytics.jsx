import React from 'react';
import { BarChart3, TrendingUp, Settings } from 'lucide-react';
import EmptyStateCard from '../tenant/EmptyStateCard';
import { useAuth } from '../../contexts/AuthContext';

const EmptyAnalytics = ({ connected = false, tenantId, hasReturns = false }) => {
  const { user } = useAuth();

  const handleConnectStore = () => {
    window.location.href = '/app/settings/integrations';
  };

  const handleViewReturns = () => {
    window.location.href = '/app/returns';
  };

  if (hasReturns) {
    return (
      <EmptyStateCard
        title="Analytics Loading"
        description="You have returns data! Analytics are being processed and will appear here shortly. Check back in a few minutes."
        icon={TrendingUp}
        actionLabel="View Returns"
        onAction={handleViewReturns}
        secondaryActionLabel="Refresh Analytics"
        onSecondaryAction={() => window.location.reload()}
        features={['Return tracking', 'Performance metrics', 'Trend analysis']}
        connected={connected}
      />
    );
  }

  if (connected) {
    return (
      <EmptyStateCard
        title="No Analytics Data Yet"
        description="Your store is connected, but you need some returns data to generate analytics. Once customers start creating returns, you'll see detailed insights here."
        icon={BarChart3}
        actionLabel="View Returns"
        onAction={handleViewReturns}
        secondaryActionLabel="Create Test Return"
        onSecondaryAction={() => window.location.href = '/app/returns/create'}
        features={['Advanced analytics', 'Revenue tracking', 'Customer insights', 'Trend analysis']}
        connected={true}
      />
    );
  }

  return (
    <EmptyStateCard
      title="Connect Store for Advanced Analytics"
      description="Get detailed insights into your returns with advanced analytics. Connect your Shopify store to unlock revenue tracking, customer insights, and performance metrics."
      icon={BarChart3}
      actionLabel="Connect Shopify Store"
      onAction={handleConnectStore}
      secondaryActionLabel="View Basic Analytics"
      onSecondaryAction={() => window.location.href = '/app/analytics?mode=basic'}
      features={['Basic return tracking', 'Simple metrics']}
      connected={false}
    />
  );
};

export default EmptyAnalytics;