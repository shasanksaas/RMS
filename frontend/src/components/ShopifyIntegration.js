import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Separator } from './ui/separator';
import { 
  ShoppingBag, 
  Link as LinkIcon, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw,
  Globe,
  Wifi,
  WifiOff
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ShopifyIntegration = ({ tenantId }) => {
  const [shopDomain, setShopDomain] = useState('');
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    if (!shopDomain) return;
    
    try {
      const response = await axios.get(`${API}/shopify/connection-status`, {
        params: { shop: shopDomain }
      });
      setConnectionStatus(response.data);
    } catch (error) {
      console.error('Error checking connection status:', error);
    }
  };

  const handleConnect = async () => {
    if (!shopDomain) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/shopify/install`, {
        params: { shop: shopDomain }
      });
      
      if (response.data.auth_url) {
        // Redirect to Shopify OAuth
        window.location.href = response.data.auth_url;
      }
    } catch (error) {
      console.error('Error initiating Shopify connection:', error);
      alert('Failed to connect to Shopify. Please check your shop domain.');
    }
    setLoading(false);
  };

  const handleSync = async () => {
    if (!shopDomain || !tenantId) return;
    
    setSyncing(true);
    try {
      const response = await axios.post(`${API}/shopify/sync`, {
        shop: shopDomain,
        tenant_id: tenantId
      });
      
      if (response.data.success) {
        alert('Data synced successfully!');
        await checkConnectionStatus();
      }
    } catch (error) {
      console.error('Error syncing data:', error);
      alert('Failed to sync data. Please try again.');
    }
    setSyncing(false);
  };

  const normalizeShopDomain = (domain) => {
    return domain.replace('https://', '').replace('http://', '').replace('.myshopify.com', '');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <ShoppingBag className="h-5 w-5 text-green-600" />
          <span>Shopify Integration</span>
        </CardTitle>
        <CardDescription>
          Connect your Shopify store to sync orders and automate returns
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Connection Status */}
        {connectionStatus && (
          <Alert className={connectionStatus.connected ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'}>
            <div className="flex items-center space-x-2">
              {connectionStatus.online ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
              {connectionStatus.connected ? <CheckCircle className="h-4 w-4 text-green-600" /> : <AlertCircle className="h-4 w-4 text-yellow-600" />}
            </div>
            <AlertDescription>
              <div className="flex items-center justify-between">
                <span>
                  {connectionStatus.connected ? 'Connected to Shopify' : 'Not connected'} 
                  ({connectionStatus.mode} mode)
                </span>
                <div className="flex items-center space-x-2">
                  <Badge variant={connectionStatus.online ? 'default' : 'secondary'}>
                    {connectionStatus.online ? 'Online' : 'Offline'}
                  </Badge>
                  {connectionStatus.connected && (
                    <Badge variant="outline" className="text-green-600 border-green-600">
                      Connected
                    </Badge>
                  )}
                </div>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Shop Domain Input */}
        <div className="space-y-2">
          <Label htmlFor="shopDomain">Shop Domain</Label>
          <div className="flex space-x-2">
            <Input
              id="shopDomain"
              placeholder="your-store (without .myshopify.com)"
              value={shopDomain}
              onChange={(e) => setShopDomain(normalizeShopDomain(e.target.value))}
              disabled={loading}
            />
            <Button 
              onClick={checkConnectionStatus}
              variant="outline"
              disabled={!shopDomain || loading}
            >
              Check
            </Button>
          </div>
          <p className="text-xs text-gray-500">
            Enter your Shopify store name (e.g., "demo-store" for demo-store.myshopify.com)
          </p>
        </div>

        <Separator />

        {/* Action Buttons */}
        <div className="flex space-x-2">
          <Button 
            onClick={handleConnect}
            disabled={!shopDomain || loading || (connectionStatus?.connected)}
            className="flex items-center space-x-2"
          >
            <LinkIcon className="h-4 w-4" />
            <span>{loading ? 'Connecting...' : 'Connect to Shopify'}</span>
          </Button>

          {connectionStatus?.connected && (
            <Button 
              onClick={handleSync}
              variant="outline"
              disabled={syncing}
              className="flex items-center space-x-2"
            >
              <Sync className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
              <span>{syncing ? 'Syncing...' : 'Sync Data'}</span>
            </Button>
          )}
        </div>

        {/* Integration Benefits */}
        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">Benefits of Shopify Integration:</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Automatic order synchronization</li>
            <li>• Real-time inventory updates</li>
            <li>• Seamless return processing</li>
            <li>• Customer data integration</li>
            <li>• Webhook-based live updates</li>
          </ul>
        </div>

        {/* Offline Mode Info */}
        {connectionStatus?.mode === 'offline' && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2 flex items-center space-x-2">
              <WifiOff className="h-4 w-4" />
              <span>Offline Mode Active</span>
            </h4>
            <p className="text-sm text-gray-700">
              The system is currently using cached data and mock Shopify responses. 
              All features remain fully functional for testing and development.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ShopifyIntegration;