import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ShoppingCart, Search, Filter, RefreshCw, Package, Eye, ExternalLink, MoreHorizontal } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { useAuth } from '../../contexts/AuthContext';

const Orders = () => {
  // Get authenticated user and tenant from AuthContext
  const { user, tenant } = useAuth();

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [pagination, setPagination] = useState({});
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    search: '',
    status_filter: 'all',
    date_from: '',
    date_to: '',
    sort_by: 'created_at',
    sort_order: 'desc',
    page: 1,
    limit: 20
  });

  // Get backend URL and tenant from environment
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  const tenantId = tenant?.tenant_id || user?.tenant_id; // Use authenticated user's tenant

  useEffect(() => {
    loadOrders();
    
    // Auto-refresh orders every 30 seconds to catch new orders
    const interval = setInterval(() => {
      loadOrders();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [filters]);

  const getApiUrl = () => {
    // Always use the configured backend URL for production
    return backendUrl || 'http://localhost:8001';
  };

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError('');
      
      const apiUrl = getApiUrl();
      
      // Build query parameters
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.status_filter !== 'all') params.append('status_filter', filters.status_filter);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      params.append('sort_by', filters.sort_by);
      params.append('sort_order', filters.sort_order);
      params.append('page', filters.page.toString());
      params.append('limit', filters.limit.toString());

      const response = await fetch(`${apiUrl}/api/orders?${params.toString()}`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        const data = await response.json();
        setOrders(data.items || []);
        setPagination(data.pagination || {});
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to load orders');
      }
    } catch (err) {
      console.error('Error loading orders:', err);
      setError('Failed to load orders. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      const apiUrl = getApiUrl();
      
      // First trigger sync
      const response = await fetch(`${apiUrl}/api/integrations/shopify/resync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        // Wait 2 seconds for sync to process
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Force reload orders immediately
        await loadOrders();
        setError('');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Sync failed');
      }
    } catch (err) {
      console.error('Sync error:', err);
      setError('Sync failed. Please try again.');
    } finally {
      setSyncing(false);
    }
  };

  const getStatusBadge = (status, type = 'financial') => {
    if (type === 'financial') {
      const config = {
        paid: { color: 'bg-green-100 text-green-800', label: 'Paid' },
        pending: { color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
        cancelled: { color: 'bg-red-100 text-red-800', label: 'Cancelled' },
        refunded: { color: 'bg-purple-100 text-purple-800', label: 'Refunded' }
      };
      const { color, label } = config[status] || { color: 'bg-gray-100 text-gray-800', label: status };
      return <Badge className={color}>{label}</Badge>;
    } else {
      const config = {
        fulfilled: { color: 'bg-green-100 text-green-800', label: 'Fulfilled' },
        unfulfilled: { color: 'bg-yellow-100 text-yellow-800', label: 'Unfulfilled' },
        partial: { color: 'bg-blue-100 text-blue-800', label: 'Partial' },
        cancelled: { color: 'bg-red-100 text-red-800', label: 'Cancelled' }
      };
      const { color, label } = config[status] || { color: 'bg-gray-100 text-gray-800', label: status };
      return <Badge className={color}>{label}</Badge>;
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value, page: 1 });
  };

  const handlePageChange = (newPage) => {
    setFilters({ ...filters, page: newPage });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Orders</h1>
          <p className="text-gray-500 text-sm md:text-base">View and manage your store orders</p>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Orders</h1>
          <p className="text-gray-500 text-sm md:text-base">View and manage your store orders</p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
          <Button variant="outline" onClick={handleSync} disabled={syncing} className="touch-manipulation">
            <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync Orders'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-3 sm:space-y-0 sm:space-x-4 w-full md:w-auto">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search orders, customers..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="pl-10 w-full sm:w-64 touch-manipulation"
            />
          </div>

          <Select value={filters.status_filter} onValueChange={(value) => handleFilterChange('status_filter', value)}>
            <SelectTrigger className="w-full sm:w-40 touch-manipulation">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Orders</SelectItem>
              <SelectItem value="paid">Paid</SelectItem>
              <SelectItem value="fulfilled">Fulfilled</SelectItem>
              <SelectItem value="unfulfilled">Unfulfilled</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.sort_by} onValueChange={(value) => handleFilterChange('sort_by', value)}>
            <SelectTrigger className="w-full sm:w-40 touch-manipulation">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="created_at">Date Created</SelectItem>
              <SelectItem value="order_number">Order Number</SelectItem>
              <SelectItem value="total_price">Total Amount</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-lg">
            <ShoppingCart className="h-5 w-5" />
            <span>Orders ({pagination.total_items || orders.length})</span>
          </CardTitle>
          <CardDescription>
            Orders synced from your Shopify store
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0 md:p-6">
          {orders.length === 0 ? (
            <div className="text-center py-12 px-6">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No orders found</h3>
              <p className="text-gray-500 mb-4">Orders from your Shopify store will appear here.</p>
              <Button onClick={handleSync} disabled={syncing} className="touch-manipulation">
                <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                Sync Orders
              </Button>
            </div>
          ) : (
            <>
              {/* Mobile Card View */}
              <div className="md:hidden space-y-4 p-4">
                {orders.map((order) => (
                  <div key={order.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium text-sm">{order.order_number}</div>
                        <div className="text-xs text-gray-500">{order.customer_name}</div>
                        <div className="text-xs text-gray-500">{order.customer_email}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">${order.total_price.toFixed(2)}</div>
                        <div className="text-xs text-gray-500">{order.currency_code}</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-500">Payment:</span>
                        <div>{getStatusBadge(order.financial_status, 'financial')}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Fulfillment:</span>
                        <div>{getStatusBadge(order.fulfillment_status, 'fulfillment')}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Items:</span>
                        <div>{order.line_items?.length || 0} items</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Date:</span>
                        <div>{new Date(order.created_at).toLocaleDateString()}</div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t">
                      <Button variant="ghost" size="sm" asChild className="touch-manipulation">
                        <Link to={`/app/orders/${order.id}`}>
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Link>
                      </Button>
                      {order.shopify_order_url && (
                        <Button variant="ghost" size="sm" asChild className="touch-manipulation">
                          <a href={order.shopify_order_url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4 mr-1" />
                            Shopify
                          </a>
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Desktop Table View */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Order</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Payment</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Fulfillment</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Items</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Total</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {orders.map((order) => (
                      <tr key={order.id} className="hover:bg-gray-50">
                        <td className="py-4 px-4">
                          <div className="font-mono text-sm">{order.order_number}</div>
                        </td>
                        <td className="py-4 px-4">
                          <div>
                            <div className="font-medium">{order.customer_name}</div>
                            <div className="text-sm text-gray-500">{order.customer_email}</div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          {getStatusBadge(order.financial_status, 'financial')}
                        </td>
                        <td className="py-4 px-4">
                          {getStatusBadge(order.fulfillment_status, 'fulfillment')}
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm">{order.line_items?.length || 0}</span>
                        </td>
                        <td className="py-4 px-4">
                          <span className="font-medium">${order.total_price.toFixed(2)} {order.currency_code}</span>
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm text-gray-500">
                            {new Date(order.created_at).toLocaleDateString()}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-2">
                            <Button variant="ghost" size="sm" asChild>
                              <Link to={`/app/orders/${order.id}`}>
                                <Eye className="h-4 w-4" />
                              </Link>
                            </Button>
                            {order.shopify_order_url && (
                              <Button variant="ghost" size="sm" asChild>
                                <a href={order.shopify_order_url} target="_blank" rel="noopener noreferrer">
                                  <ExternalLink className="h-4 w-4" />
                                </a>
                              </Button>
                            )}
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {pagination.total_pages > 1 && (
        <div className="flex flex-col sm:flex-row items-center justify-between space-y-3 sm:space-y-0">
          <p className="text-sm text-gray-700">
            Showing <span className="font-medium">{((pagination.current_page - 1) * pagination.per_page) + 1}</span> to{' '}
            <span className="font-medium">{Math.min(pagination.current_page * pagination.per_page, pagination.total_items)}</span> of{' '}
            <span className="font-medium">{pagination.total_items}</span> results
          </p>
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              disabled={pagination.current_page <= 1}
              onClick={() => handlePageChange(pagination.current_page - 1)}
              className="touch-manipulation"
            >
              Previous
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              disabled={pagination.current_page >= pagination.total_pages}
              onClick={() => handlePageChange(pagination.current_page + 1)}
              className="touch-manipulation"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;