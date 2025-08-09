import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import CustomerPortal from './CustomerPortal';
import ShopifyIntegration from './components/ShopifyIntegration';
import EnhancedFeatures from './components/EnhancedFeatures';
import ErrorBoundary from './components/ErrorBoundary';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Textarea } from './components/ui/textarea';
import { Separator } from './components/ui/separator';
import { Progress } from './components/ui/progress';
import { Alert, AlertDescription } from './components/ui/alert';
import { 
  ArrowUpCircle, 
  ArrowDownCircle, 
  Package, 
  TrendingUp, 
  Users, 
  DollarSign,
  RefreshCw,
  Filter,
  Search,
  Plus,
  Calendar,
  BarChart3,
  Settings,
  Wifi,
  WifiOff
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Demo tenant ID - will be created automatically
let DEMO_TENANT_ID = null;

const App = () => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [returns, setReturns] = useState([]);
  const [orders, setOrders] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [lastDataUpdate, setLastDataUpdate] = useState(null);
  
  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      // Create demo tenant if it doesn't exist
      await createDemoTenantAndData();
      
      // Load data
      await Promise.all([
        loadReturns(),
        loadOrders(),
        loadAnalytics()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
    }
    setLoading(false);
  };

  const createDemoTenantAndData = async () => {
    try {
      // Create tenant first
      const tenantResponse = await axios.post(`${API}/tenants`, {
        name: "Demo Store",
        domain: "demo-store.com",
        shopify_store_url: "demo-store.myshopify.com"
      });
      
      // Set the tenant ID for subsequent requests
      DEMO_TENANT_ID = tenantResponse.data.id;
      console.log('Created demo tenant:', DEMO_TENANT_ID);

      const headers = { 'X-Tenant-Id': DEMO_TENANT_ID };
      
      // Create demo products
      const demoProducts = [
        { name: "Premium T-Shirt", price: 29.99, category: "Clothing", sku: "TSH-001" },
        { name: "Wireless Headphones", price: 199.99, category: "Electronics", sku: "HEAD-002" },
        { name: "Running Shoes", price: 89.99, category: "Footwear", sku: "SHOE-003" }
      ];

      for (const product of demoProducts) {
        await axios.post(`${API}/products`, product, { headers });
      }

      // Create demo orders
      const demoOrders = [
        {
          customer_email: "john@example.com",
          customer_name: "John Smith",
          order_number: "ORD-001",
          items: [{ product_id: "1", product_name: "Premium T-Shirt", quantity: 2, price: 29.99, sku: "TSH-001" }],
          total_amount: 59.98,
          order_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
          customer_email: "jane@example.com",
          customer_name: "Jane Doe",
          order_number: "ORD-002",
          items: [{ product_id: "2", product_name: "Wireless Headphones", quantity: 1, price: 199.99, sku: "HEAD-002" }],
          total_amount: 199.99,
          order_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
        }
      ];

      for (const order of demoOrders) {
        await axios.post(`${API}/orders`, order, { headers });
      }

      // Create demo return rules
      await axios.post(`${API}/return-rules`, {
        name: "Auto-approve defective items",
        description: "Automatically approve returns for defective products",
        conditions: {
          auto_approve_reasons: ["defective", "damaged_in_shipping"],
          max_days_since_order: 30
        },
        actions: {
          auto_approve: true,
          generate_label: true
        },
        priority: 1
      }, { headers });

      // Create a demo return request
      const orders = await axios.get(`${API}/orders`, { headers });
      if (orders.data.length > 0) {
        const firstOrder = orders.data[0];
        await axios.post(`${API}/returns`, {
          order_id: firstOrder.id,
          reason: "defective",
          items_to_return: firstOrder.items.slice(0, 1), // Return first item
          notes: "Product arrived with a defect"
        }, { headers });
      }

    } catch (error) {
      console.error('Demo data setup error:', error);
      // If tenant creation fails, try to find an existing tenant
      try {
        const existingTenants = await axios.get(`${API}/tenants`);
        if (existingTenants.data.length > 0) {
          DEMO_TENANT_ID = existingTenants.data[0].id;
          console.log('Using existing tenant:', DEMO_TENANT_ID);
        }
      } catch (e) {
        console.error('Could not find existing tenants');
      }
    }
  };

  const loadReturns = async () => {
    try {
      const response = await axios.get(`${API}/returns`, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      // Handle paginated response structure
      if (response.data && response.data.items) {
        setReturns(response.data.items);
      } else {
        // Fallback for old structure
        setReturns(response.data || []);
      }
    } catch (error) {
      console.error('Error loading returns:', error);
      // Don't set empty array immediately, let the user see there might be an issue
      if (error.response?.status !== 404) {
        setReturns([]);
      }
    }
  };

  const loadOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      setOrders(response.data);
    } catch (error) {
      console.error('Error loading orders:', error);
      if (error.response?.status !== 404) {
        setOrders([]);
      }
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics?days=30`, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
      setAnalytics({
        total_returns: 0,
        total_refunds: 0,
        exchange_rate: 0,
        top_return_reasons: []
      });
    }
  };

  const handleCreateReturn = async (returnData) => {
    try {
      await axios.post(`${API}/returns`, returnData, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      await loadReturns();
      await loadAnalytics();
    } catch (error) {
      console.error('Error creating return:', error);
    }
  };

  const handleUpdateReturnStatus = async (returnId, status, notes = '') => {
    try {
      await axios.put(`${API}/returns/${returnId}/status`, {
        status,
        notes
      }, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      await loadReturns();
      await loadAnalytics();
    } catch (error) {
      console.error('Error updating return status:', error);
    }
  };

  const filteredReturns = useMemo(() => {
    return returns.filter(ret => {
      const matchesSearch = ret.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          ret.customer_email.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || ret.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [returns, searchTerm, statusFilter]);

  const getStatusColor = (status) => {
    const colors = {
      'requested': 'bg-yellow-100 text-yellow-800',
      'approved': 'bg-green-100 text-green-800',
      'denied': 'bg-red-100 text-red-800',
      'in_transit': 'bg-blue-100 text-blue-800',
      'received': 'bg-purple-100 text-purple-800',
      'processed': 'bg-gray-100 text-gray-800',
      'refunded': 'bg-green-100 text-green-800',
      'exchanged': 'bg-indigo-100 text-indigo-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900">Loading your returns dashboard...</p>
          <p className="text-sm text-gray-500 mt-2">Setting up demo data for first time use</p>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/customer" element={<CustomerPortal />} />
          <Route path="*" element={<MerchantDashboard isOnline={isOnline} />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

const MerchantDashboard = ({ isOnline }) => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [returns, setReturns] = useState([]);
  const [orders, setOrders] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [lastDataUpdate, setLastDataUpdate] = useState(null);
  
  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      // Create demo tenant if it doesn't exist
      await createDemoTenantAndData();
      
      // Load data
      await Promise.all([
        loadReturns(),
        loadOrders(),
        loadAnalytics()
      ]);
      
      // Update timestamp when data loads successfully
      if (isOnline) {
        setLastDataUpdate(new Date());
        // Cache data in localStorage
        const cacheData = {
          returns,
          orders,
          analytics,
          timestamp: new Date().toISOString()
        };
        localStorage.setItem('returns_app_cache', JSON.stringify(cacheData));
      }
    } catch (error) {
      console.error('Error loading data:', error);
      
      // Try to load from cache if offline
      if (!isOnline) {
        loadFromCache();
      }
    }
    setLoading(false);
  };

  const loadFromCache = () => {
    try {
      const cached = localStorage.getItem('returns_app_cache');
      if (cached) {
        const cacheData = JSON.parse(cached);
        setReturns(cacheData.returns || []);
        setOrders(cacheData.orders || []);
        setAnalytics(cacheData.analytics || null);
        setLastDataUpdate(new Date(cacheData.timestamp));
      }
    } catch (error) {
      console.error('Error loading cache:', error);
    }
  };

  const createDemoTenantAndData = async () => {
    try {
      // Create tenant first
      const tenantResponse = await axios.post(`${API}/tenants`, {
        name: "Demo Store",
        domain: "demo-store.com",
        shopify_store_url: "demo-store.myshopify.com"
      });
      
      // Set the tenant ID for subsequent requests
      DEMO_TENANT_ID = tenantResponse.data.id;
      console.log('Created demo tenant:', DEMO_TENANT_ID);

      const headers = { 'X-Tenant-Id': DEMO_TENANT_ID };
      
      // Create demo products
      const demoProducts = [
        { name: "Premium T-Shirt", price: 29.99, category: "Clothing", sku: "TSH-001" },
        { name: "Wireless Headphones", price: 199.99, category: "Electronics", sku: "HEAD-002" },
        { name: "Running Shoes", price: 89.99, category: "Footwear", sku: "SHOE-003" }
      ];

      for (const product of demoProducts) {
        await axios.post(`${API}/products`, product, { headers });
      }

      // Create demo orders
      const demoOrders = [
        {
          customer_email: "john@example.com",
          customer_name: "John Smith",
          order_number: "ORD-001",
          items: [{ product_id: "1", product_name: "Premium T-Shirt", quantity: 2, price: 29.99, sku: "TSH-001" }],
          total_amount: 59.98,
          order_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
          customer_email: "jane@example.com",
          customer_name: "Jane Doe",
          order_number: "ORD-002",
          items: [{ product_id: "2", product_name: "Wireless Headphones", quantity: 1, price: 199.99, sku: "HEAD-002" }],
          total_amount: 199.99,
          order_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
        }
      ];

      for (const order of demoOrders) {
        await axios.post(`${API}/orders`, order, { headers });
      }

      // Create demo return rules
      await axios.post(`${API}/return-rules`, {
        name: "Auto-approve defective items",
        description: "Automatically approve returns for defective products",
        conditions: {
          auto_approve_reasons: ["defective", "damaged_in_shipping"],
          max_days_since_order: 30
        },
        actions: {
          auto_approve: true,
          generate_label: true
        },
        priority: 1
      }, { headers });

      // Create a demo return request
      const orders = await axios.get(`${API}/orders`, { headers });
      if (orders.data.length > 0) {
        const firstOrder = orders.data[0];
        await axios.post(`${API}/returns`, {
          order_id: firstOrder.id,
          reason: "defective",
          items_to_return: firstOrder.items.slice(0, 1), // Return first item
          notes: "Product arrived with a defect"
        }, { headers });
      }

    } catch (error) {
      console.error('Demo data setup error:', error);
      // If tenant creation fails, try to find an existing tenant
      try {
        const existingTenants = await axios.get(`${API}/tenants`);
        if (existingTenants.data.length > 0) {
          DEMO_TENANT_ID = existingTenants.data[0].id;
          console.log('Using existing tenant:', DEMO_TENANT_ID);
        }
      } catch (e) {
        console.error('Could not find existing tenants');
      }
    }
  };

  const loadReturns = async () => {
    try {
      const response = await axios.get(`${API}/returns`, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      // Handle paginated response structure
      if (response.data && response.data.items) {
        setReturns(response.data.items);
      } else {
        // Fallback for old structure
        setReturns(response.data || []);
      }
    } catch (error) {
      console.error('Error loading returns:', error);
      // Don't set empty array immediately, let the user see there might be an issue
      if (error.response?.status !== 404) {
        setReturns([]);
      }
    }
  };

  const loadOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      setOrders(response.data);
    } catch (error) {
      console.error('Error loading orders:', error);
      if (error.response?.status !== 404) {
        setOrders([]);
      }
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics?days=30`, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
      setAnalytics({
        total_returns: 0,
        total_refunds: 0,
        exchange_rate: 0,
        top_return_reasons: []
      });
    }
  };

  const handleCreateReturn = async (returnData) => {
    try {
      await axios.post(`${API}/returns`, returnData, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      await loadReturns();
      await loadAnalytics();
    } catch (error) {
      console.error('Error creating return:', error);
    }
  };

  const handleUpdateReturnStatus = async (returnId, status, notes = '') => {
    try {
      await axios.put(`${API}/returns/${returnId}/status`, {
        status,
        notes
      }, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      await loadReturns();
      await loadAnalytics();
    } catch (error) {
      console.error('Error updating return status:', error);
    }
  };

  const filteredReturns = useMemo(() => {
    return returns.filter(ret => {
      const matchesSearch = ret.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          ret.customer_email.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || ret.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [returns, searchTerm, statusFilter]);

  const getStatusColor = (status) => {
    const colors = {
      'requested': 'bg-yellow-100 text-yellow-800',
      'approved': 'bg-green-100 text-green-800',
      'denied': 'bg-red-100 text-red-800',
      'in_transit': 'bg-blue-100 text-blue-800',
      'received': 'bg-purple-100 text-purple-800',
      'processed': 'bg-gray-100 text-gray-800',
      'refunded': 'bg-green-100 text-green-800',
      'exchanged': 'bg-indigo-100 text-indigo-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900">Loading your returns dashboard...</p>
          <p className="text-sm text-gray-500 mt-2">Setting up demo data for first time use</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <Package className="h-8 w-8 text-blue-600" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Returns Dashboard</h1>
                  <p className="text-sm text-gray-500">Manage your return requests</p>
                </div>
              </div>
              
              {/* Online/Offline Indicator */}
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                isOnline ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {isOnline ? (
                  <>
                    <Wifi className="h-4 w-4" />
                    <span>Online</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-4 w-4" />
                    <span>Offline</span>
                  </>
                )}
              </div>
            </div>
            
            {!isOnline && lastDataUpdate && (
              <div className="text-sm text-gray-500">
                Last updated: {lastDataUpdate.toLocaleTimeString()}
              </div>
            )}
            
            <div className="flex items-center space-x-4">
              <Button
                variant={currentView === 'dashboard' ? 'default' : 'outline'}
                onClick={() => setCurrentView('dashboard')}
                className="flex items-center space-x-2"
              >
                <BarChart3 className="h-4 w-4" />
                <span>Dashboard</span>
              </Button>
              <Button
                variant={currentView === 'returns' ? 'default' : 'outline'}
                onClick={() => setCurrentView('returns')}
                className="flex items-center space-x-2"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Returns</span>
              </Button>
              <Button
                variant={currentView === 'settings' ? 'default' : 'outline'}
                onClick={() => setCurrentView('settings')}
                className="flex items-center space-x-2"
              >
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </Button>
            </div>
          </div>
          
          {!isOnline && (
            <Alert className="mt-4 border-yellow-200 bg-yellow-50">
              <WifiOff className="h-4 w-4" />
              <AlertDescription className="text-yellow-800">
                You're currently offline. Data may be outdated. Changes won't be saved until you're back online.
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'dashboard' && (
          <DashboardView 
            analytics={analytics} 
            returns={returns} 
            formatCurrency={formatCurrency}
            getStatusColor={getStatusColor}
          />
        )}

        {currentView === 'returns' && (
          <ReturnsView
            returns={filteredReturns}
            orders={orders}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            handleCreateReturn={handleCreateReturn}
            handleUpdateReturnStatus={handleUpdateReturnStatus}
            formatCurrency={formatCurrency}
            formatDate={formatDate}
            getStatusColor={getStatusColor}
          />
        )}

        {currentView === 'settings' && (
          <div className="space-y-6">
            <SettingsView />
            <ShopifyIntegration tenantId={DEMO_TENANT_ID} />
            <EnhancedFeatures tenantId={DEMO_TENANT_ID} />
          </div>
        )}
      </div>
    </div>
  );
};

const DashboardView = ({ analytics, returns, formatCurrency, getStatusColor }) => {
  if (!analytics) {
    return <div>Loading analytics...</div>;
  }

  const recentReturns = returns.slice(0, 5);

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Returns</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_returns}</div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Refunds</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(analytics.total_refunds)}</div>
            <p className="text-xs text-muted-foreground">Processed refunds</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Exchange Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.exchange_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Returns converted to exchanges</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Processing Time</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.avg_processing_time} days</div>
            <p className="text-xs text-muted-foreground">From request to resolution</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Return Reasons */}
        <Card>
          <CardHeader>
            <CardTitle>Top Return Reasons</CardTitle>
            <CardDescription>Most common reasons for returns in the last 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.top_return_reasons.map((reason, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                    <span className="text-sm font-medium capitalize">
                      {reason.reason.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">{reason.count}</span>
                    <Progress value={reason.percentage} className="w-20" />
                    <span className="text-sm text-gray-500">{reason.percentage.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Returns */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Returns</CardTitle>
            <CardDescription>Latest return requests</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentReturns.map((ret) => (
                <div key={ret.id} className="flex items-center justify-between border-b pb-2 last:border-b-0">
                  <div>
                    <p className="text-sm font-medium">{ret.customer_name}</p>
                    <p className="text-xs text-gray-500">{formatCurrency(ret.refund_amount)}</p>
                  </div>
                  <Badge className={getStatusColor(ret.status)}>
                    {ret.status.replace('_', ' ')}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const ReturnsView = ({ 
  returns, 
  orders, 
  searchTerm, 
  setSearchTerm, 
  statusFilter, 
  setStatusFilter,
  handleCreateReturn,
  handleUpdateReturnStatus,
  formatCurrency,
  formatDate,
  getStatusColor 
}) => {
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Return Requests</h2>
          <p className="text-sm text-gray-500">Manage and process customer returns</p>
        </div>
        
        <CreateReturnDialog 
          orders={orders}
          onCreateReturn={handleCreateReturn}
          open={showCreateDialog}
          setOpen={setShowCreateDialog}
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
            <div className="flex-1">
              <Label htmlFor="search" className="sr-only">Search</Label>
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  id="search"
                  placeholder="Search by customer name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="status" className="sr-only">Filter by status</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="All Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="requested">Requested</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="denied">Denied</SelectItem>
                  <SelectItem value="in_transit">In Transit</SelectItem>
                  <SelectItem value="received">Received</SelectItem>
                  <SelectItem value="processed">Processed</SelectItem>
                  <SelectItem value="refunded">Refunded</SelectItem>
                  <SelectItem value="exchanged">Exchanged</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Returns List */}
      <div className="space-y-4">
        {returns.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No returns found</h3>
              <p className="text-gray-500 mb-4">
                {searchTerm || statusFilter !== 'all' 
                  ? 'No returns match your current filters.' 
                  : 'Start by creating your first return request.'}
              </p>
              <Button 
                onClick={() => setShowCreateDialog(true)}
                className="flex items-center space-x-2"
              >
                <Plus className="h-4 w-4" />
                <span>Create Return</span>
              </Button>
            </CardContent>
          </Card>
        ) : (
          returns.map((ret) => (
            <ReturnCard 
              key={ret.id} 
              returnRequest={ret}
              onUpdateStatus={handleUpdateReturnStatus}
              formatCurrency={formatCurrency}
              formatDate={formatDate}
              getStatusColor={getStatusColor}
            />
          ))
        )}
      </div>
    </div>
  );
};

const ReturnCard = ({ returnRequest, onUpdateStatus, formatCurrency, formatDate, getStatusColor }) => {
  const [showDetails, setShowDetails] = useState(false);

  const canApprove = returnRequest.status === 'requested';
  const canProcess = returnRequest.status === 'approved' || returnRequest.status === 'received';

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg">{returnRequest.customer_name}</CardTitle>
            <CardDescription>{returnRequest.customer_email}</CardDescription>
          </div>
          <Badge className={getStatusColor(returnRequest.status)}>
            {returnRequest.status.replace('_', ' ').toUpperCase()}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <p className="text-sm font-medium text-gray-500">Return Amount</p>
            <p className="text-lg font-semibold">{formatCurrency(returnRequest.refund_amount)}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Reason</p>
            <p className="text-sm capitalize">{returnRequest.reason.replace('_', ' ')}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Created</p>
            <p className="text-sm">{formatDate(returnRequest.created_at)}</p>
          </div>
        </div>

        {returnRequest.notes && (
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-500">Notes</p>
            <p className="text-sm text-gray-700">{returnRequest.notes}</p>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </Button>

          {canApprove && (
            <>
              <Button 
                size="sm" 
                onClick={() => onUpdateStatus(returnRequest.id, 'approved', 'Return approved by admin')}
                className="bg-green-600 hover:bg-green-700"
              >
                Approve
              </Button>
              <Button 
                size="sm" 
                variant="destructive"
                onClick={() => onUpdateStatus(returnRequest.id, 'denied', 'Return denied by admin')}
              >
                Deny
              </Button>
            </>
          )}

          {canProcess && (
            <>
              <Button 
                size="sm" 
                onClick={() => onUpdateStatus(returnRequest.id, 'refunded', 'Refund processed')}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Process Refund
              </Button>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => onUpdateStatus(returnRequest.id, 'exchanged', 'Exchange processed')}
              >
                Process Exchange
              </Button>
            </>
          )}
        </div>

        {showDetails && (
          <div className="mt-4 pt-4 border-t">
            <h4 className="font-medium mb-2">Items to Return:</h4>
            <div className="space-y-2">
              {returnRequest.items_to_return.map((item, index) => (
                <div key={index} className="flex justify-between items-center text-sm">
                  <span>{item.product_name} (SKU: {item.sku})</span>
                  <span>Qty: {item.quantity} × {formatCurrency(item.price)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const CreateReturnDialog = ({ orders, onCreateReturn, open, setOpen }) => {
  const [selectedOrder, setSelectedOrder] = useState('');
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedItems, setSelectedItems] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedOrder || !reason || selectedItems.length === 0) return;

    const order = orders.find(o => o.id === selectedOrder);
    if (!order) return;

    const itemsToReturn = selectedItems.map(itemId => {
      return order.items.find(item => `${item.product_id}-${item.sku}` === itemId);
    }).filter(Boolean);

    await onCreateReturn({
      order_id: selectedOrder,
      reason,
      items_to_return: itemsToReturn,
      notes: notes || undefined
    });

    // Reset form
    setSelectedOrder('');
    setReason('');
    setNotes('');
    setSelectedItems([]);
    setOpen(false);
  };

  const selectedOrderObj = orders.find(o => o.id === selectedOrder);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="flex items-center space-x-2">
          <Plus className="h-4 w-4" />
          <span>Create Return</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create Return Request</DialogTitle>
          <DialogDescription>
            Create a new return request for a customer order.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="order">Select Order</Label>
            <Select value={selectedOrder} onValueChange={setSelectedOrder}>
              <SelectTrigger>
                <SelectValue placeholder="Choose an order..." />
              </SelectTrigger>
              <SelectContent>
                {orders.map((order) => (
                  <SelectItem key={order.id} value={order.id}>
                    {order.order_number} - {order.customer_name} ({order.customer_email})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedOrderObj && (
            <div>
              <Label>Items to Return</Label>
              <div className="space-y-2 mt-2">
                {selectedOrderObj.items.map((item) => {
                  const itemId = `${item.product_id}-${item.sku}`;
                  return (
                    <div key={itemId} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={itemId}
                        checked={selectedItems.includes(itemId)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedItems([...selectedItems, itemId]);
                          } else {
                            setSelectedItems(selectedItems.filter(id => id !== itemId));
                          }
                        }}
                        className="rounded"
                      />
                      <Label htmlFor={itemId} className="flex-1 cursor-pointer">
                        {item.product_name} - Qty: {item.quantity} - ${item.price}
                      </Label>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div>
            <Label htmlFor="reason">Return Reason</Label>
            <Select value={reason} onValueChange={setReason}>
              <SelectTrigger>
                <SelectValue placeholder="Select reason..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="defective">Defective</SelectItem>
                <SelectItem value="wrong_size">Wrong Size</SelectItem>
                <SelectItem value="wrong_color">Wrong Color</SelectItem>
                <SelectItem value="not_as_described">Not as Described</SelectItem>
                <SelectItem value="damaged_in_shipping">Damaged in Shipping</SelectItem>
                <SelectItem value="changed_mind">Changed Mind</SelectItem>
                <SelectItem value="quality_issues">Quality Issues</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="notes">Additional Notes (Optional)</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Any additional details about the return..."
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={!selectedOrder || !reason || selectedItems.length === 0}
            >
              Create Return
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

const SettingsView = () => {
  const [settings, setSettings] = useState({
    return_window_days: 30,
    auto_approve_exchanges: true,
    require_photos: false,
    brand_color: "#3b82f6",
    custom_message: "We're here to help with your return!",
    restocking_fee_percent: 0,
    store_credit_bonus_percent: 10,
    logo_url: ""
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Load current settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    if (!DEMO_TENANT_ID) return;
    
    try {
      const response = await axios.get(`${API}/tenants/${DEMO_TENANT_ID}/settings`, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      setSettings({ ...settings, ...response.data.settings });
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const saveSettings = async () => {
    if (!DEMO_TENANT_ID) return;
    
    setLoading(true);
    setMessage('');

    try {
      const response = await axios.put(`${API}/tenants/${DEMO_TENANT_ID}/settings`, settings, {
        headers: { 'X-Tenant-Id': DEMO_TENANT_ID }
      });
      
      setMessage('Settings saved successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Error saving settings. Please try again.');
      console.error('Error saving settings:', error);
    }
    
    setLoading(false);
  };

  const handleInputChange = (key, value) => {
    setSettings({ ...settings, [key]: value });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
        <p className="text-sm text-gray-500">Configure your return policies and preferences</p>
      </div>

      {message && (
        <Alert className={message.includes('Error') ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}>
          <AlertDescription className={message.includes('Error') ? 'text-red-800' : 'text-green-800'}>
            {message}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Return Policy</CardTitle>
            <CardDescription>Configure default return rules and timeframes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="return-window">Return Window (Days)</Label>
              <Input 
                id="return-window" 
                type="number" 
                value={settings.return_window_days}
                onChange={(e) => handleInputChange('return_window_days', parseInt(e.target.value) || 30)}
                min="1"
                max="365"
              />
            </div>
            <div>
              <Label htmlFor="restocking-fee">Restocking Fee (%)</Label>
              <Input 
                id="restocking-fee" 
                type="number" 
                value={settings.restocking_fee_percent}
                onChange={(e) => handleInputChange('restocking_fee_percent', parseFloat(e.target.value) || 0)}
                min="0"
                max="50"
                step="0.1"
              />
            </div>
            <div>
              <Label htmlFor="credit-bonus">Store Credit Bonus (%)</Label>
              <Input 
                id="credit-bonus" 
                type="number" 
                value={settings.store_credit_bonus_percent}
                onChange={(e) => handleInputChange('store_credit_bonus_percent', parseFloat(e.target.value) || 0)}
                min="0"
                max="50"
                step="0.1"
              />
              <p className="text-xs text-gray-500 mt-1">Extra credit given when customer chooses store credit over refund</p>
            </div>
            <div className="flex items-center space-x-2">
              <input 
                type="checkbox" 
                id="auto-approve" 
                checked={settings.auto_approve_exchanges}
                onChange={(e) => handleInputChange('auto_approve_exchanges', e.target.checked)}
                className="rounded" 
              />
              <Label htmlFor="auto-approve">Auto-approve exchange requests</Label>
            </div>
            <div className="flex items-center space-x-2">
              <input 
                type="checkbox" 
                id="require-photos" 
                checked={settings.require_photos}
                onChange={(e) => handleInputChange('require_photos', e.target.checked)}
                className="rounded" 
              />
              <Label htmlFor="require-photos">Require photos for return requests</Label>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Branding</CardTitle>
            <CardDescription>Customize the look and feel of your return portal</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="brand-color">Brand Color</Label>
              <div className="flex items-center space-x-2">
                <Input 
                  id="brand-color" 
                  type="color" 
                  value={settings.brand_color}
                  onChange={(e) => handleInputChange('brand_color', e.target.value)}
                  className="w-20 h-10"
                />
                <Input 
                  type="text" 
                  value={settings.brand_color}
                  onChange={(e) => handleInputChange('brand_color', e.target.value)}
                  placeholder="#3b82f6"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="logo-url">Logo URL</Label>
              <Input 
                id="logo-url" 
                type="url" 
                value={settings.logo_url}
                onChange={(e) => handleInputChange('logo_url', e.target.value)}
                placeholder="https://example.com/logo.png"
              />
            </div>
            <div>
              <Label htmlFor="custom-message">Welcome Message</Label>
              <Textarea
                id="custom-message"
                value={settings.custom_message}
                onChange={(e) => handleInputChange('custom_message', e.target.value)}
                placeholder="Enter a custom welcome message..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end">
        <Button 
          onClick={saveSettings}
          disabled={loading}
          className="flex items-center space-x-2"
        >
          {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Settings className="h-4 w-4" />}
          <span>{loading ? 'Saving...' : 'Save Settings'}</span>
        </Button>
      </div>
    </div>
  );
};

export default App;