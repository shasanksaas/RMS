import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, Download, MoreHorizontal, Eye, CheckCircle, XCircle, Package, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Badge } from '../../../components/ui/badge';
import { Alert, AlertDescription } from '../../../components/ui/alert';
import { useAuth } from '../../../contexts/AuthContext';

const AllReturns = () => {
  // Get authenticated user and tenant from AuthContext
  const { user, tenant } = useAuth();

  const [allReturns, setAllReturns] = useState([]); // Store all returns
  const [filteredReturns, setFilteredReturns] = useState([]); // Store filtered results
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({});
  const [error, setError] = useState('');
  const [selectedReturns, setSelectedReturns] = useState([]);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    sortBy: 'created_at',
    sortOrder: 'desc',
    page: 1,
    limit: 20
  });
  const [syncing, setSyncing] = useState(false);

  const handleSync = async () => {
    try {
      setSyncing(true);
      
      // Trigger Shopify returns sync
      const response = await fetch(buildApiUrl('/api/integrations/shopify/resync'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        // Wait 2 seconds for sync to process
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Force reload returns
        await loadReturns();
        setError('');
      } else {
        setError('Failed to sync with Shopify. Please try again.');
      }
    } catch (err) {
      console.error('Error syncing returns:', err);
      setError('Unable to sync with Shopify. Please check your connection.');
    } finally {
      setSyncing(false);
    }
  };

  // Get backend URL and use authenticated tenant (NOT hardcoded!)
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  const tenantId = tenant?.tenant_id || user?.tenant_id; // Use authenticated user's tenant

  const buildApiUrl = (endpoint) => {
    const apiUrl = backendUrl || 'http://localhost:8001';
    return `${apiUrl}${endpoint}`;
  };

  // Load returns from backend - Backend handles deduplication now
  const loadReturns = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(buildApiUrl('/api/returns/'), {
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        const data = await response.json();
        const returnsData = data.returns || [];
        
        // Backend now handles deduplication, so just validate essential fields
        const validReturns = returnsData.filter(returnItem => 
          returnItem.id && returnItem.customer_email
        );
        
        setAllReturns(validReturns);
        setPagination(data.pagination || {});
        setError('');
      } else if (response.status === 404) {
        setAllReturns([]);
        setError('No returns found');
      } else {
        setAllReturns([]);
        setError(`Failed to load returns: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error loading returns:', err);
      setAllReturns([]);
      setError('Unable to connect to server. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  // Debounced search function
  const debounce = useCallback((func, delay) => {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func.apply(null, args), delay);
    };
  }, []);

  // Filter and search logic - SIMPLIFIED (backend now handles deduplication)
  const filterReturns = useCallback((returnsData, searchTerm, statusFilter) => {
    let filtered = [...returnsData];

    // Apply search filter (only on real data)
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(returnItem => 
        returnItem.customer_name?.toLowerCase().includes(searchLower) ||
        returnItem.customer_email?.toLowerCase().includes(searchLower) ||
        returnItem.order_number?.toLowerCase().includes(searchLower) ||
        returnItem.id?.toLowerCase().includes(searchLower)
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(returnItem => 
        returnItem.status?.toLowerCase() === statusFilter.toLowerCase()
      );
    }

    return filtered;
  }, []);

  // Memoized filtered results
  const displayReturns = useMemo(() => {
    return filterReturns(allReturns, filters.search, filters.status);
  }, [allReturns, filters.search, filters.status, filterReturns]);

  // Update filtered returns whenever display returns change
  useEffect(() => {
    setFilteredReturns(displayReturns);
  }, [displayReturns]);

  // Initial load with auto-refresh
  useEffect(() => {
    loadReturns();
    
    // Auto-refresh returns every 30 seconds to get live data
    const interval = setInterval(() => {
      loadReturns();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Debounced search handler
  const debouncedSearch = useMemo(
    () => debounce((searchTerm) => {
      setFilters(prev => ({ ...prev, search: searchTerm, page: 1 }));
    }, 300),
    [debounce]
  );

  // Handle search input change
  const handleSearchChange = (e) => {
    const value = e.target.value;
    setFilters(prev => ({ ...prev, search: value }));
    debouncedSearch(value);
  };

  // Handle filter changes
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  };

  const handleStatusUpdate = async (returnId, newStatus) => {
    try {
      const response = await fetch(buildApiUrl(`/api/returns/${returnId}/status`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        // Update local state optimistically
        setAllReturns(prevReturns => 
          prevReturns.map(ret => 
            ret.id === returnId ? { ...ret, status: newStatus } : ret
          )
        );
        setError('');
      } else {
        setError(`Failed to update status: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error updating status:', err);
      setError('Unable to update return status. Please try again.');
    }
  };

  const handleBulkStatusUpdate = async (newStatus) => {
    if (selectedReturns.length === 0) return;
    
    setBulkActionLoading(true);
    try {
      // Process each selected return
      const promises = selectedReturns.map(returnId => 
        fetch(buildApiUrl(`/api/returns/${returnId}/status`), {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-Tenant-Id': tenantId
          },
          body: JSON.stringify({ status: newStatus })
        })
      );

      await Promise.all(promises);
      
      // Update local state
      setAllReturns(prevReturns => 
        prevReturns.map(ret => 
          selectedReturns.includes(ret.id) ? { ...ret, status: newStatus } : ret
        )
      );
      
      // Clear selection
      setSelectedReturns([]);
      setError('');
      
    } catch (err) {
      console.error('Error with bulk action:', err);
      setError('Bulk action failed. Please try again.');
      setSelectedReturns([]);
    } finally {
      setBulkActionLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await fetch(buildApiUrl('/api/returns/export?format=csv'), {
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `returns_export_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('Export failed. Please try again.');
      }
    } catch (err) {
      console.error('Error exporting:', err);
      setError('Unable to export data. Please try again.');
    }
  };

  const generateCSV = (data) => {
    const headers = ['Return ID', 'Order Number', 'Customer', 'Email', 'Status', 'Reason', 'Amount', 'Date'];
    const rows = data.map(ret => [
      ret.id,
      ret.order_number,
      ret.customer_name,
      ret.customer_email,
      ret.status,
      ret.reason,
      ret.refund_amount,
      new Date(ret.created_at).toLocaleDateString()
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  };

  const downloadCSV = (content, filename) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSelectReturn = (returnId) => {
    setSelectedReturns(prev => 
      prev.includes(returnId) 
        ? prev.filter(id => id !== returnId)
        : [...prev, returnId]
    );
  };

  const handleSelectAll = () => {
    if (selectedReturns.length === filteredReturns.length && filteredReturns.length > 0) {
      setSelectedReturns([]);
    } else {
      setSelectedReturns(filteredReturns.map(ret => ret.id));
    }
  };

  const getStatusBadge = (status) => {
    const config = {
      requested: { color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
      REQUESTED: { color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
      approved: { color: 'bg-blue-100 text-blue-800', label: 'Approved' },
      APPROVED: { color: 'bg-blue-100 text-blue-800', label: 'Approved' },
      denied: { color: 'bg-red-100 text-red-800', label: 'Denied' },
      DENIED: { color: 'bg-red-100 text-red-800', label: 'Denied' },
      processing: { color: 'bg-purple-100 text-purple-800', label: 'Processing' },
      PROCESSING: { color: 'bg-purple-100 text-purple-800', label: 'Processing' },
      completed: { color: 'bg-green-100 text-green-800', label: 'Completed' },
      COMPLETED: { color: 'bg-green-100 text-green-800', label: 'Completed' },
      cancelled: { color: 'bg-gray-100 text-gray-800', label: 'Cancelled' },
      CANCELLED: { color: 'bg-gray-100 text-gray-800', label: 'Cancelled' },
      label_issued: { color: 'bg-purple-100 text-purple-800', label: 'Label Issued' },
      in_transit: { color: 'bg-orange-100 text-orange-800', label: 'In Transit' },
      received: { color: 'bg-indigo-100 text-indigo-800', label: 'Received' },
      resolved: { color: 'bg-green-100 text-green-800', label: 'Resolved' }
    };
    
    const { color, label } = config[status] || config.requested;
    return <Badge className={color}>{label}</Badge>;
  };

  const formatReason = (reason) => {
    if (!reason || reason === '') {
      return 'Not specified';
    }
    
    // If it's already a readable string from Shopify, return it as is
    if (reason.length > 10 && reason.includes(' ')) {
      return reason;
    }
    
    const reasons = {
      wrong_size: 'Wrong Size',
      wrong_color: 'Wrong Color', 
      defective: 'Defective',
      not_as_described: 'Not as Described',
      changed_mind: 'Changed Mind',
      damaged_in_shipping: 'Damaged in Shipping',
      // Add common Shopify reason formats
      size_too_small: 'Size Too Small',
      size_too_large: 'Size Too Large',
      color_not_as_expected: 'Color Not as Expected',
      quality_issues: 'Quality Issues',
      damaged: 'Damaged',
      defective_item: 'Defective Item'
    };
    
    return reasons[reason?.toLowerCase()] || reason || 'Not specified';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Returns</h1>
          <p className="text-gray-500 text-sm md:text-base">Manage return requests and track their progress</p>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Returns</h1>
          <p className="text-gray-500 text-sm md:text-base">Manage return requests and track their progress</p>
        </div>
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
        <Card>
          <CardContent className="p-6 text-center">
            <Button onClick={loadReturns} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Returns</h1>
        <p className="text-gray-500 text-sm md:text-base">Manage return requests and track their progress</p>
      </div>

      {/* Header Actions */}
      <div className="flex flex-col space-y-4 md:space-y-0 md:flex-row md:gap-4 items-start md:items-center justify-between">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-3 sm:space-y-0 sm:space-x-4 w-full md:w-auto">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search customers, orders..."
              value={filters.search}
              onChange={handleSearchChange}
              className="pl-10 w-full sm:w-64 touch-manipulation"
            />
          </div>

          <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
            <SelectTrigger className="w-full sm:w-40 touch-manipulation">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="requested">Pending</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="denied">Denied</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.sortBy} onValueChange={(value) => handleFilterChange('sortBy', value)}>
            <SelectTrigger className="w-full sm:w-40 touch-manipulation">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="created_at">Date Created</SelectItem>
              <SelectItem value="order_number">Order Number</SelectItem>
              <SelectItem value="refund_amount">Refund Amount</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-2 w-full md:w-auto">
          <Link to="/app/returns/create">
            <Button className="w-full sm:w-auto touch-manipulation bg-blue-600 hover:bg-blue-700">
              <Package className="h-4 w-4 mr-2" />
              Create Return
            </Button>
          </Link>
          <Button variant="outline" onClick={handleExport} className="w-full sm:w-auto touch-manipulation">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button variant="outline" onClick={handleSync} disabled={syncing} className="w-full sm:w-auto touch-manipulation">
            <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync Returns'}
          </Button>
          {selectedReturns.length > 0 && (
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-2">
              <Button 
                variant="outline" 
                onClick={() => handleBulkStatusUpdate('approved')}
                disabled={bulkActionLoading}
                className="text-green-600 hover:text-green-700 w-full sm:w-auto touch-manipulation"
              >
                {bulkActionLoading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600 mr-2" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Approve ({selectedReturns.length})
              </Button>
              <Button 
                variant="outline" 
                onClick={() => handleBulkStatusUpdate('denied')}
                disabled={bulkActionLoading}
                className="text-red-600 hover:text-red-700 w-full sm:w-auto touch-manipulation"
              >
                <XCircle className="h-4 w-4 mr-2" />
                Deny ({selectedReturns.length})
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Returns Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Return Requests ({filteredReturns.length} of {allReturns.length})
            {filters.search && <span className="text-sm font-normal text-gray-500 ml-2">- Filtered by "{filters.search}"</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 md:p-6">
          {filteredReturns.length === 0 ? (
            <div className="text-center py-12 px-6">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {filters.search || filters.status !== 'all' ? 'No matching returns found' : 'No returns found'}
              </h3>
              <p className="text-gray-500">
                {filters.search || filters.status !== 'all' 
                  ? 'Try adjusting your search or filter criteria.' 
                  : 'When customers submit return requests, they\'ll appear here.'
                }
              </p>
              {(filters.search || filters.status !== 'all') && (
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setFilters(prev => ({ ...prev, search: '', status: 'all' }));
                  }}
                  className="mt-4 touch-manipulation"
                >
                  Clear Filters
                </Button>
              )}
            </div>
          ) : (
            <>
              {/* Mobile Card View */}
              <div className="md:hidden space-y-4 p-4">
                {filteredReturns.map((returnRequest) => (
                  <div key={returnRequest.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedReturns.includes(returnRequest.id)}
                          onChange={() => handleSelectReturn(returnRequest.id)}
                          className="rounded touch-manipulation"
                        />
                        <div>
                          <div className="font-medium text-sm">{returnRequest.customer_name}</div>
                          <div className="text-xs text-gray-500">{returnRequest.customer_email}</div>
                        </div>
                      </div>
                      {getStatusBadge(returnRequest.status)}
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-500">Order:</span>
                        <div className="font-mono text-xs">{returnRequest.order_number}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Amount:</span>
                        <div className="font-medium">
                          {(() => {
                            const refund = returnRequest.estimated_refund;
                            if (typeof refund === 'object' && refund !== null) {
                              const amount = refund.amount || 0;
                              const currency = refund.currency || 'USD';
                              const symbol = currency === 'INR' ? '₹' : '$';
                              return `${symbol}${Number(amount).toFixed(2)}`;
                            } else if (typeof refund === 'number' && refund > 0) {
                              return `$${Number(refund).toFixed(2)}`;
                            } else if (returnRequest.refund_amount) {
                              return `$${Number(returnRequest.refund_amount).toFixed(2)}`;
                            }
                            return '$0.00';
                          })()}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Reason:</span>
                        <div>{formatReason(returnRequest.reason)}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Date:</span>
                        <div>{new Date(returnRequest.created_at).toLocaleDateString()}</div>
                      </div>
                    </div>

                    <div>
                      <span className="text-gray-500 text-sm">Items:</span>
                      <div className="text-sm">
                        {(() => {
                          const items = returnRequest.line_items || returnRequest.items || [];
                          return items.length > 0 ? 
                            items.map((item, idx) => (
                              <div key={idx}>
                                {item.title || item.product_name || 'Product'} (×{item.quantity || 1})
                              </div>
                            )) :
                            <span className="text-gray-400">No items</span>
                        })()}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t">
                      <Button variant="ghost" size="sm" asChild className="touch-manipulation">
                        <Link to={`/app/returns/${returnRequest.id}`}>
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Link>
                      </Button>
                      {returnRequest.status === 'requested' && (
                        <div className="flex space-x-2">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-green-600 hover:text-green-700 touch-manipulation"
                            onClick={() => handleStatusUpdate(returnRequest.id, 'approved')}
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-red-600 hover:text-red-700 touch-manipulation"
                            onClick={() => handleStatusUpdate(returnRequest.id, 'denied')}
                          >
                            <XCircle className="h-4 w-4" />
                          </Button>
                        </div>
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
                      <th className="py-3 px-4 text-left">
                        <input
                          type="checkbox"
                          checked={selectedReturns.length === filteredReturns.length && filteredReturns.length > 0}
                          onChange={handleSelectAll}
                          className="rounded touch-manipulation"
                        />
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Order</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Items</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredReturns.map((returnRequest) => (
                      <tr key={returnRequest.id} className="hover:bg-gray-50">
                        <td className="py-4 px-4">
                          <input
                            type="checkbox"
                            checked={selectedReturns.includes(returnRequest.id)}
                            onChange={() => handleSelectReturn(returnRequest.id)}
                            className="rounded touch-manipulation"
                          />
                        </td>
                        <td className="py-4 px-4">
                          <div>
                            <div className="font-medium">{returnRequest.customer_name || 'N/A'}</div>
                            <div className="text-sm text-gray-500">{returnRequest.customer_email}</div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <span className="font-mono text-sm">{returnRequest.order_number}</span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="text-sm">
                            {(() => {
                              const items = returnRequest.line_items || returnRequest.items || [];
                              if (items.length === 0) {
                                return <span className="text-gray-400">No items</span>;
                              }
                              return (
                                <div>
                                  {items.slice(0, 2).map((item, idx) => (
                                    <div key={idx}>
                                      {item.title || item.product_name || 'Product'} (×{item.quantity || 1})
                                    </div>
                                  ))}
                                  {items.length > 2 && (
                                    <div className="text-gray-400">+{items.length - 2} more</div>
                                  )}
                                </div>
                              );
                            })()}
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm">
                            {(() => {
                              // Handle different reason formats dynamically
                              const reasonData = returnRequest.return_reason_category || returnRequest.reason;
                              if (typeof reasonData === 'object' && reasonData !== null) {
                                return reasonData.description || reasonData.code || 'Not specified';
                              }
                              return reasonData || 'Not specified';
                            })()}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <span className="font-medium">
                            {(() => {
                              const refund = returnRequest.estimated_refund;
                              if (typeof refund === 'object' && refund !== null) {
                                const amount = refund.amount || 0;
                                const currency = refund.currency || 'USD';
                                const symbol = currency === 'INR' ? '₹' : '$';
                                return `${symbol}${Number(amount).toFixed(2)}`;
                              } else if (typeof refund === 'number' && refund > 0) {
                                // Handle simple number format from API
                                return `$${Number(refund).toFixed(2)}`;
                              } else if (returnRequest.refund_amount) {
                                return `$${Number(returnRequest.refund_amount).toFixed(2)}`;
                              }
                              return '$0.00';
                            })()}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          {getStatusBadge(returnRequest.status)}
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm text-gray-500">
                            {returnRequest.created_at ? 
                              new Date(returnRequest.created_at).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric', 
                                year: 'numeric'
                              }) : 'N/A'
                            }
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-2">
                            <Button variant="ghost" size="sm" asChild className="touch-manipulation">
                              <Link to={`/app/returns/${returnRequest.id}`}>
                                <Eye className="h-4 w-4" />
                              </Link>
                            </Button>
                            <select
                              value={returnRequest.status?.toLowerCase() || 'requested'}
                              onChange={(e) => handleStatusUpdate(returnRequest.id, e.target.value)}
                              className="text-xs border rounded px-2 py-1 bg-white"
                            >
                              <option value="requested">Requested</option>
                              <option value="approved">Approved</option>
                              <option value="denied">Denied</option>
                              <option value="processing">Processing</option>
                              <option value="completed">Completed</option>
                              <option value="cancelled">Cancelled</option>
                            </select>
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

    </div>
  );
};

export default AllReturns;