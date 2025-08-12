import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { useToast } from '../ui/use-toast';

const ConnectedDashboard = () => {
  const [searchParams] = useSearchParams();
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  // Check if this is a fresh connection from OAuth callback
  const isNewConnection = searchParams.get('connected') === '1';
  const shopFromUrl = searchParams.get('shop');
  const tenantIdFromUrl = searchParams.get('tenant_id');

  useEffect(() => {
    // Show success message for new connections
    if (isNewConnection && shopFromUrl) {
      toast({
        title: "🎉 Store Connected!",
        description: `Successfully connected ${shopFromUrl}. Your data is syncing...`,
        variant: "default"
      });
    }

    // Load connection status
    loadConnectionStatus();
  }, [isNewConnection, shopFromUrl]);

  const loadConnectionStatus = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      
      // Get tenant ID from multiple sources for impersonation support
      let tenantId = tenantIdFromUrl || localStorage.getItem('tenant_id') || localStorage.getItem('currentTenant');
      
      // Check if this is an impersonation session from URL params
      const impersonatedParam = searchParams.get('impersonated');
      const tenantParam = searchParams.get('tenant');
      
      if (impersonatedParam === 'true' && tenantParam) {
        tenantId = tenantParam;
        console.log('🔐 Impersonation session detected, using tenant:', tenantId);
      }
      
      if (!tenantId) {
        setConnectionStatus({ connected: false, error: 'No tenant ID found' });
        return;
      }

      // Get authentication token (supports both localStorage and cookies)
      const token = localStorage.getItem('auth_token');
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(
        `${backendUrl}/api/auth/shopify/status?tenant_id=${tenantId}`, 
        { 
          method: 'GET',
          headers,
          credentials: 'include'  // Include cookies for impersonation sessions
        }
      );
      
      if (response.ok) {
        const status = await response.json();
        setConnectionStatus(status);
        
        console.log('✅ Connection status loaded:', status);
        
        // Store tenant info in localStorage for future use (only if not impersonating)
        if (status.connected && !impersonatedParam) {
          localStorage.setItem('tenant_id', tenantId);
          localStorage.setItem('shop_domain', status.shop_domain || '');
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        setConnectionStatus({ 
          connected: false, 
          error: errorData.detail || `HTTP ${response.status}` 
        });
      }
    } catch (error) {
      console.error('❌ Error loading connection status:', error);
      setConnectionStatus({ 
        connected: false, 
        error: error.message || 'Failed to load connection status' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!connectionStatus?.tenant_id) return;

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/auth/shopify/disconnect?tenant_id=${connectionStatus.tenant_id}`, {
        method: 'POST'
      });

      if (response.ok) {
        toast({
          title: "Store Disconnected",
          description: "Your Shopify store has been disconnected successfully.",
          variant: "default"
        });
        
        // Clear local storage and reload
        localStorage.removeItem('tenant_id');
        localStorage.removeItem('shop_domain');
        window.location.href = '/auth/login';
      } else {
        throw new Error('Failed to disconnect');
      }
    } catch (error) {
      toast({
        title: "Disconnect Failed",
        description: "Failed to disconnect store. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleResync = async () => {
    toast({
      title: "Resync Started",
      description: "Re-syncing your store data. This may take a few minutes...",
      variant: "default"
    });
    // TODO: Implement resync functionality
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (!connectionStatus?.connected) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <CardTitle className="text-red-600">Not Connected</CardTitle>
            <CardDescription>
              Your Shopify store is not connected. Please login to continue.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Button 
              onClick={() => window.location.href = '/auth/login'}
              className="bg-[#95bf47] hover:bg-[#7ba337]"
            >
              Connect Shopify Store
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Returns Manager</h1>
              <p className="text-gray-600">Manage your store returns efficiently</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <Badge variant={connectionStatus.connected ? "success" : "destructive"}>
                  {connectionStatus.connected ? "Connected" : "Disconnected"}
                </Badge>
                {connectionStatus.shop && (
                  <span className="text-sm text-gray-600">
                    {connectionStatus.shop}
                  </span>
                )}
              </div>
              
              {/* User Menu */}
              <div className="flex items-center space-x-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleResync}
                >
                  Resync Data
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleDisconnect}
                >
                  Disconnect
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Connection Success Banner */}
        {isNewConnection && (
          <div className="mb-8 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">
                  🎉 Store Connected Successfully!
                </h3>
                <div className="mt-2 text-sm text-green-700">
                  <p>
                    Your Shopify store <strong>{shopFromUrl}</strong> is now connected. 
                    We're syncing your orders and setting up webhooks for real-time updates.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          
          {/* Store Info Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <svg className="w-5 h-5 mr-2 text-[#95bf47]" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M15.337 2.447c-.38-.172-.806-.245-1.245-.245-1.93 0-3.713 1.455-4.888 3.32-.852-.398-1.744-.618-2.659-.618C4.53 4.904 3 6.376 3 8.365c0 .532.134 1.047.368 1.516-.698.87-1.113 1.951-1.113 3.119 0 2.756 2.238 4.991 5 4.991h10.5c2.21 0 4-1.787 4-3.99 0-1.657-.896-3.101-2.23-3.879.147-.468.225-.957.225-1.462 0-2.756-2.238-4.991-5-4.991-.63 0-1.234.117-1.795.33-.317-1.146-1.058-2.175-2.106-2.927-.508-.365-1.09-.625-1.712-.625z"/>
                </svg>
                Connected Store
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-2xl font-semibold">{connectionStatus.shop}</p>
                <p className="text-sm text-gray-600">
                  Last sync: {connectionStatus.last_sync_at ? 
                    new Date(connectionStatus.last_sync_at).toLocaleString() : 
                    'In progress...'
                  }
                </p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {connectionStatus.scopes?.map(scope => (
                    <Badge key={scope} variant="outline" className="text-xs">
                      {scope}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Orders Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
                Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-2xl font-semibold">—</p>
                <p className="text-sm text-gray-600">Syncing orders...</p>
                <Button size="sm" variant="outline" className="w-full">
                  View Orders
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Returns Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <svg className="w-5 h-5 mr-2 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Returns
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-2xl font-semibold">—</p>
                <p className="text-sm text-gray-600">Loading returns...</p>
                <Button size="sm" variant="outline" className="w-full">
                  Manage Returns
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>
                Common tasks you can perform right now
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full justify-start" variant="outline">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Create Return
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                View Reports
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Settings
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System Status</CardTitle>
              <CardDescription>
                Current status of your integrations and data sync
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Shopify Connection</span>
                <Badge variant="success">Active</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Webhook Status</span>
                <Badge variant="success">Receiving</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Data Sync</span>
                <Badge variant="default">In Progress</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Last Update</span>
                <span className="text-sm text-gray-600">Just now</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default ConnectedDashboard;