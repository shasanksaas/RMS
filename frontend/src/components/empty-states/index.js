// Empty States - Smart components that show appropriate empty states based on connection status
export { default as EmptyOrders } from './EmptyOrders';
export { default as EmptyReturns } from './EmptyReturns';
export { default as EmptyAnalytics } from './EmptyAnalytics';
export { default as EmptyCustomers } from './EmptyCustomers';
export { default as EmptyStateCard } from '../tenant/EmptyStateCard';

// Connection status hook for determining which empty state to show
import { useState, useEffect } from 'react';

export const useConnectionStatus = (tenantId) => {
  const [connectionStatus, setConnectionStatus] = useState({
    connected: false,
    loading: true,
    shopifyConnected: false,
    features: ['manual_returns', 'basic_analytics']
  });

  useEffect(() => {
    const checkConnectionStatus = async () => {
      try {
        // This would be replaced with actual API call to check tenant connection
        // For now, assume not connected (empty state)
        setConnectionStatus({
          connected: false,
          loading: false,
          shopifyConnected: false,
          features: ['manual_returns', 'basic_analytics', 'customer_portal']
        });
      } catch (error) {
        console.error('Failed to check connection status:', error);
        setConnectionStatus(prev => ({
          ...prev,
          loading: false
        }));
      }
    };

    if (tenantId) {
      checkConnectionStatus();
    } else {
      setConnectionStatus(prev => ({ ...prev, loading: false }));
    }
  }, [tenantId]);

  return connectionStatus;
};