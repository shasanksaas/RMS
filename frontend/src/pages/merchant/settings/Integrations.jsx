import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  ShoppingBag, 
  CreditCard, 
  Truck, 
  Plus, 
  Check, 
  AlertCircle, 
  ExternalLink,
  Trash2,
  RefreshCw,
  Shield,
  Globe
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Badge } from '../../../components/ui/badge';
import { Alert, AlertDescription } from '../../../components/ui/alert';
import { Textarea } from '../../../components/ui/textarea';
import { useAuth } from '../../../contexts/AuthContext';

const Integrations = () => {
  // Get authenticated user and tenant from AuthContext
  const { user, tenant } = useAuth();

  // Connection form state
  const [showConnectionForm, setShowConnectionForm] = useState(false);
  const [connectionForm, setConnectionForm] = useState({
    shop: ''
  });
  
  // App state
  const [connecting, setConnecting] = useState(false);
  const [connectedStores, setConnectedStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [validationResults, setValidationResults] = useState(null);

  // Get backend URL
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  
  // Handle URL parameters for OAuth callback
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    loadConnectedStores();
    
    // Handle OAuth callback parameters
    const connected = searchParams.get('connected');
    const shop = searchParams.get('shop');
    const error = searchParams.get('error');
    const errorMessage = searchParams.get('message');
    
    if (connected === '1' || connected === 'true') {
      setMessage({ 
        type: 'success', 
        text: `Successfully connected to ${shop || 'your store'}! Your store is now integrated and data sync has started.` 
      });
      // Reload connected stores to show the new connection
      setTimeout(() => loadConnectedStores(), 1000);
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (error === '1' || error) {
      setMessage({ 
        type: 'error', 
        text: errorMessage || 'Connection failed. Please try again.' 
      });
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [searchParams]);

  const getApiUrl = () => {
    // Always use the configured backend URL for production
    return backendUrl || 'http://localhost:8001';
  };

  const loadConnectedStores = async () => {
    setLoading(true);
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/integrations/shopify/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': 'tenant-rms34' // Updated to match connected store
        }
      });

      if (response.ok) {
        const status = await response.json();
        
        if (status.connected) {
          // Convert integration status to store format
          const store = {
            id: 'shopify-integration',
            shop: status.shop,
            name: status.shop?.replace('.myshopify.com', '') || 'Shopify Store',
            platform: 'shopify',
            installed_at: status.installedAt,
            last_sync: status.lastSyncAt,
            last_webhook_at: status.lastWebhookAt,
            order_counts: status.orderCounts,
            return_counts: status.returnCounts,
            webhooks: status.webhooks,
            latest_sync_job: status.latestSyncJob
          };
          setConnectedStores([store]);
        } else {
          setConnectedStores([]);
        }
      }
    } catch (error) {
      console.error('Failed to load integration status:', error);
      setConnectedStores([]);
    } finally {
      setLoading(false);
    }
  };

  const validateCredentials = async () => {
    try {
      const apiUrl = getApiUrl();
      
      const response = await fetch(`${apiUrl}/api/auth/test/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(connectionForm)
      });

      if (response.ok) {
        const results = await response.json();
        setValidationResults(results);
        return results.overall_valid;
      }
    } catch (error) {
      console.error('Validation failed:', error);
      setMessage({ type: 'error', text: 'Failed to validate credentials' });
    }
    return false;
  };

  const handleResync = async () => {
    setMessage({ type: '', text: '' });
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/integrations/shopify/resync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': 'tenant-rms34' // Updated to match connected store
        }
      });

      if (response.ok) {
        const result = await response.json();
        setMessage({ 
          type: 'success', 
          text: `Resync started successfully (Job ID: ${result.job_id}). This may take a few minutes.` 
        });
        // Reload status to show updated sync job
        setTimeout(() => loadConnectedStores(), 1000);
      } else {
        const errorData = await response.json();
        setMessage({ 
          type: 'error', 
          text: errorData.detail || 'Failed to start resync' 
        });
      }
    } catch (error) {
      console.error('Resync failed:', error);
      setMessage({ type: 'error', text: 'Failed to start resync. Please try again.' });
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    setMessage({ type: '', text: '' });

    try {
      // Validate shop domain format
      const shop = connectionForm.shop.trim();
      if (!shop) {
        setMessage({ type: 'error', text: 'Please enter your shop domain' });
        setConnecting(false);
        return;
      }
      
      // Normalize shop domain
      let shopDomain = shop;
      if (!shopDomain.endsWith('.myshopify.com')) {
        shopDomain = `${shopDomain}.myshopify.com`;
      }

      // Redirect to OAuth install endpoint
      const apiUrl = getApiUrl();
      const installUrl = `${apiUrl}/api/auth/shopify/install?shop=${encodeURIComponent(shopDomain)}`;
      
      // Redirect to Shopify OAuth
      window.location.href = installUrl;
      
    } catch (error) {
      console.error('Connection failed:', error);
      setMessage({ type: 'error', text: 'Connection failed. Please try again.' });
      setConnecting(false);
    }
  };

  const handleDisconnect = async (tenantId) => {
    try {
      const apiUrl = getApiUrl();
      
      const response = await fetch(`${apiUrl}/api/auth/stores/${tenantId}/disconnect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        await loadConnectedStores();
        setMessage({ type: 'success', text: 'Store disconnected successfully' });
      }
    } catch (error) {
      console.error('Failed to disconnect store:', error);
      setMessage({ type: 'error', text: 'Failed to disconnect store' });
    }
  };

  const otherIntegrations = [
    {
      name: 'Stripe',
      description: 'Process refunds automatically',
      icon: CreditCard,
      status: 'available',
      color: 'bg-gray-100 text-gray-800'
    },
    {
      name: 'Shipping Carriers',
      description: 'Generate return labels',
      icon: Truck,
      status: 'available', 
      color: 'bg-gray-100 text-gray-800'
    }
  ];

  return (
    <div className="space-y-4 md:space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-500 text-sm md:text-base">Connect your Shopify store and other services</p>
      </div>

      {/* Status Messages */}
      {message.text && (
        <Alert className={`border ${message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <div className="flex items-center">
            {message.type === 'success' ? (
              <Check className="h-4 w-4 text-green-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
            )}
            <AlertDescription className={`ml-2 ${message.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
              {message.text}
            </AlertDescription>
          </div>
        </Alert>
      )}

      {/* Shopify Integration Section */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="flex items-start space-x-3">
              <ShoppingBag className="h-8 w-8 text-emerald-600 flex-shrink-0 mt-1" />
              <div className="min-w-0 flex-1">
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <span>Shopify Integration</span>
                  <Shield className="h-4 w-4 text-blue-500 flex-shrink-0" />
                </CardTitle>
                <CardDescription className="text-sm">Connect any Shopify store with your own API credentials</CardDescription>
              </div>
            </div>
            {!showConnectionForm && (
              <Button onClick={() => setShowConnectionForm(true)} className="w-full sm:w-auto touch-manipulation">
                <Plus className="h-4 w-4 mr-2" />
                Connect Store
              </Button>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Connected Stores */}
          {connectedStores.length > 0 && (
            <div>
              <h3 className="font-medium mb-3 text-lg">Connected Stores</h3>
              <div className="space-y-3">
                {connectedStores.map((store) => (
                  <div key={store.id} className="border rounded-lg p-4 bg-white">
                    {/* Store Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4">
                      <div className="flex items-start space-x-3">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <Check className="h-5 w-5 text-green-600" />
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="font-medium text-lg">{store.name}</h4>
                            <Badge className="bg-green-100 text-green-800">Connected</Badge>
                          </div>
                          <p className="text-sm text-gray-600">{store.shop}</p>
                          <p className="text-xs text-gray-500">
                            Connected {store.installed_at ? new Date(store.installed_at).toLocaleDateString() : 'Recently'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2 mt-3 sm:mt-0">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleResync}
                          className="touch-manipulation"
                        >
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Resync
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDisconnect(store.id)}
                          className="touch-manipulation text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                          {store.order_counts?.total || 0}
                        </div>
                        <div className="text-xs text-gray-600">Total Orders</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          {store.order_counts?.last30d || 0}
                        </div>
                        <div className="text-xs text-gray-600">Orders (30d)</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          {store.return_counts?.total || 0}
                        </div>
                        <div className="text-xs text-gray-600">Total Returns</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-orange-600">
                          {store.return_counts?.last30d || 0}
                        </div>
                        <div className="text-xs text-gray-600">Returns (30d)</div>
                      </div>
                    </div>

                    {/* Sync Status */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between text-sm">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-600">Last Sync:</span>
                          <span className="font-medium">
                            {store.last_sync ? new Date(store.last_sync).toLocaleString() : 'Never'}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-600">Last Webhook:</span>
                          <span className="font-medium">
                            {store.last_webhook_at ? new Date(store.last_webhook_at).toLocaleString() : 'None'}
                          </span>
                        </div>
                      </div>

                      {/* Webhook Status */}
                      <div className="mt-2 sm:mt-0">
                        <div className="text-xs text-gray-600 mb-1">Webhook Health:</div>
                        <div className="flex flex-wrap gap-1">
                          {store.webhooks?.slice(0, 3).map((webhook, idx) => (
                            <Badge key={idx} className="bg-green-100 text-green-800 text-xs">
                              ✓ {webhook.topic?.split('/')[0]}
                            </Badge>
                          ))}
                          {store.webhooks?.length > 3 && (
                            <Badge className="bg-gray-100 text-gray-600 text-xs">
                              +{store.webhooks.length - 3} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Latest Sync Job */}
                    {store.latest_sync_job && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-600">Latest Sync Job:</span>
                            <Badge className={
                              store.latest_sync_job.status === 'completed' ? 'bg-green-100 text-green-800' :
                              store.latest_sync_job.status === 'running' ? 'bg-blue-100 text-blue-800' :
                              store.latest_sync_job.status === 'failed' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }>
                              {store.latest_sync_job.status}
                            </Badge>
                          </div>
                          <span className="text-gray-500 text-xs">
                            {store.latest_sync_job.startedAt ? 
                              new Date(store.latest_sync_job.startedAt).toLocaleString() : 
                              'Unknown'
                            }
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Connection Form */}
          {showConnectionForm && (
            <div className="border rounded-lg p-4 md:p-6 bg-gray-50">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 space-y-2 sm:space-y-0">
                <h3 className="font-medium text-lg">Connect New Shopify Store</h3>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => {
                    setShowConnectionForm(false);
                    setValidationResults(null);
                    setMessage({ type: '', text: '' });
                  }}
                  className="touch-manipulation sm:ml-4"
                >
                  Cancel
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="shop" className="text-sm font-medium">Shop Domain</Label>
                  <Input
                    id="shop"
                    placeholder="e.g., rms34 or rms34.myshopify.com"
                    value={connectionForm.shop}
                    onChange={(e) => setConnectionForm({...connectionForm, shop: e.target.value})}
                    className="mt-1 touch-manipulation"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Enter your shop's domain name (with or without .myshopify.com)
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-2 pt-2">
                  <Button 
                    onClick={handleConnect} 
                    disabled={connecting || !connectionForm.shop}
                    className="flex-1 touch-manipulation"
                  >
                    {connecting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                        Connecting...
                      </>
                    ) : (
                      <>
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Connect to Shopify
                      </>
                    )}
                  </Button>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                  <p className="font-medium text-blue-900 mb-1">Secure OAuth Connection:</p>
                  <ol className="text-blue-800 space-y-1 text-xs list-decimal list-inside">
                    <li>Enter your shop domain</li>
                    <li>Click "Connect to Shopify" to start OAuth flow</li>
                    <li>Authorize the app in Shopify</li>
                    <li>Return here to see your connected store and data sync</li>
                  </ol>
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {connectedStores.length === 0 && !showConnectionForm && !loading && (
            <div className="text-center py-8">
              <ShoppingBag className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="font-medium text-gray-900 mb-2">No stores connected</h3>
              <p className="text-gray-500 mb-4 text-sm">Connect your first Shopify store to start managing returns</p>
              <Button onClick={() => setShowConnectionForm(true)} className="touch-manipulation">
                <Plus className="h-4 w-4 mr-2" />
                Connect Your Store
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Other Integrations */}
      <div>
        <h2 className="text-lg md:text-xl font-semibold mb-4">Other Integrations</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {otherIntegrations.map((integration) => {
            const Icon = integration.icon;
            return (
              <Card key={integration.name} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Icon className="h-8 w-8 text-gray-600 flex-shrink-0" />
                    <Badge className={integration.color}>
                      {integration.status}
                    </Badge>
                  </div>
                  <CardTitle className="text-lg">{integration.name}</CardTitle>
                  <CardDescription className="text-sm">{integration.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button 
                    variant="outline"
                    className="w-full touch-manipulation"
                    disabled={true}
                  >
                    Coming Soon
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Integrations;