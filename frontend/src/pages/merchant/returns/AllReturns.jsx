import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, Download, MoreHorizontal, Eye, CheckCircle, XCircle, Package, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Badge } from '../../../components/ui/badge';
import { Alert, AlertDescription } from '../../../components/ui/alert';

const AllReturns = () => {
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

  // Get backend URL and tenant from environment
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  const tenantId = 'tenant-fashion-store'; // TODO: Get from auth context

  const getApiUrl = () => {
    // Always use the configured backend URL for production
    return backendUrl || 'http://localhost:8001';
  };

  // Debounced search function
  const debounce = useCallback((func, delay) => {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func.apply(null, args), delay);
    };
  }, []);

  // Filter and search logic
  const filterReturns = useCallback((returnsData, searchTerm, statusFilter) => {
    let filtered = [...returnsData];

    // Apply search filter
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
      filtered = filtered.filter(returnItem => returnItem.status === statusFilter);
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

  // Load returns from backend
  const loadReturns = async () => {
    try {
      setLoading(true);
      setError('');
      
      const apiUrl = getApiUrl();
      
      const response = await fetch(`${apiUrl}/api/returns`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        const data = await response.json();
        const returnsData = data.items || [];
        setAllReturns(returnsData);
        setPagination(data.pagination || {});
      } else {
        // Fallback to mock data if API fails
        console.warn('API failed, using mock data');
        const mockData = getMockReturns();
        setAllReturns(mockData);
        setPagination({ total_items: mockData.length, current_page: 1, total_pages: 1, per_page: 20 });
      }
    } catch (err) {
      console.error('Error loading returns:', err);
      // Fallback to mock data
      const mockData = getMockReturns();
      setAllReturns(mockData);
      setPagination({ total_items: mockData.length, current_page: 1, total_pages: 1, per_page: 20 });
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadReturns();
  }, []);

  const getMockReturns = () => [
    {
      id: 'RET-001',
      order_number: 'ORD-12345',
      customer_name: 'Sarah Johnson',
      customer_email: 'sarah@example.com',
      status: 'requested',
      reason: 'wrong_size',
      refund_amount: 49.99,
      created_at: '2024-01-15T10:30:00Z',
      items: [{ product_name: 'Blue Cotton T-Shirt', quantity: 1 }]
    },
    {
      id: 'RET-002',
      order_number: 'ORD-12346',
      customer_name: 'Mike Chen',
      customer_email: 'mike@example.com',
      status: 'approved',
      reason: 'defective',
      refund_amount: 199.99,
      created_at: '2024-01-14T15:45:00Z',
      items: [{ product_name: 'Wireless Headphones', quantity: 1 }]
    },
    {
      id: 'RET-003',
      order_number: 'ORD-12347',
      customer_name: 'Emma Davis',
      customer_email: 'emma@example.com',
      status: 'resolved',
      reason: 'not_as_described',
      refund_amount: 79.99,
      created_at: '2024-01-13T09:15:00Z',
      items: [{ product_name: 'Summer Dress', quantity: 1 }]
    }
  ];

  const handleStatusUpdate = async (returnId, newStatus) => {
    try {
      const apiUrl = getApiUrl();
      
      const response = await fetch(`${apiUrl}/api/returns/${returnId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        // Refresh the returns list
        await loadReturns();
        setError('');
      } else {
        // Fallback to local state update if API fails
        setReturns(returns.map(ret => 
          ret.id === returnId ? { ...ret, status: newStatus } : ret
        ));
      }
    } catch (err) {
      console.error('Error updating status:', err);
      // Fallback to local state update
      setReturns(returns.map(ret => 
        ret.id === returnId ? { ...ret, status: newStatus } : ret
      ));
    }
  };

  const handleBulkStatusUpdate = async (newStatus) => {
    if (selectedReturns.length === 0) return;
    
    setBulkActionLoading(true);
    try {
      const apiUrl = getApiUrl();
      
      // Process each selected return
      const promises = selectedReturns.map(returnId => 
        fetch(`${apiUrl}/api/returns/${returnId}/status`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-Tenant-Id': tenantId
          },
          body: JSON.stringify({ status: newStatus })
        })
      );

      await Promise.all(promises);
      
      // Clear selection and refresh
      setSelectedReturns([]);
      await loadReturns();
      setError('');
      
    } catch (err) {
      console.error('Error with bulk action:', err);
      // Fallback to local state update
      setReturns(returns.map(ret => 
        selectedReturns.includes(ret.id) ? { ...ret, status: newStatus } : ret
      ));
      setSelectedReturns([]);
    } finally {
      setBulkActionLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const apiUrl = getApiUrl();
      
      const response = await fetch(`${apiUrl}/api/returns/export?format=csv`, {
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
        // Fallback CSV generation
        const csvContent = generateCSV(returns);
        downloadCSV(csvContent, `returns_export_${new Date().toISOString().split('T')[0]}.csv`);
      }
    } catch (err) {
      console.error('Export error:', err);
      // Fallback CSV generation
      const csvContent = generateCSV(returns);
      downloadCSV(csvContent, `returns_export_${new Date().toISOString().split('T')[0]}.csv`);
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
    if (selectedReturns.length === returns.length) {
      setSelectedReturns([]);
    } else {
      setSelectedReturns(returns.map(ret => ret.id));
    }
  };

  const getStatusBadge = (status) => {
    const config = {
      requested: { color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
      approved: { color: 'bg-blue-100 text-blue-800', label: 'Approved' },
      denied: { color: 'bg-red-100 text-red-800', label: 'Denied' },
      label_issued: { color: 'bg-purple-100 text-purple-800', label: 'Label Issued' },
      in_transit: { color: 'bg-orange-100 text-orange-800', label: 'In Transit' },
      received: { color: 'bg-indigo-100 text-indigo-800', label: 'Received' },
      resolved: { color: 'bg-green-100 text-green-800', label: 'Resolved' }
    };
    
    const { color, label } = config[status] || config.requested;
    return <Badge className={color}>{label}</Badge>;
  };

  const formatReason = (reason) => {
    const reasons = {
      wrong_size: 'Wrong Size',
      wrong_color: 'Wrong Color',
      defective: 'Defective',
      not_as_described: 'Not as Described',
      changed_mind: 'Changed Mind',
      damaged_in_shipping: 'Damaged in Shipping'
    };
    return reasons[reason] || reason;
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value, page: 1 }); // Reset to page 1 when filtering
  };

  const handlePageChange = (newPage) => {
    setFilters({ ...filters, page: newPage });
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
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="pl-10 w-full sm:w-64"
            />
          </div>

          <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
            <SelectTrigger className="w-full sm:w-40">
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
            <SelectTrigger className="w-full sm:w-40">
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
          <Button variant="outline" onClick={handleExport} className="w-full sm:w-auto">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          {selectedReturns.length > 0 && (
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-2">
              <Button 
                variant="outline" 
                onClick={() => handleBulkStatusUpdate('approved')}
                disabled={bulkActionLoading}
                className="text-green-600 hover:text-green-700 w-full sm:w-auto"
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
                className="text-red-600 hover:text-red-700 w-full sm:w-auto"
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
          <CardTitle className="text-lg">Return Requests ({pagination.total_items || returns.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0 md:p-6">
          {returns.length === 0 ? (
            <div className="text-center py-12 px-6">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No returns found</h3>
              <p className="text-gray-500">When customers submit return requests, they'll appear here.</p>
            </div>
          ) : (
            <>
              {/* Mobile Card View */}
              <div className="md:hidden space-y-4 p-4">
                {returns.map((returnRequest) => (
                  <div key={returnRequest.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedReturns.includes(returnRequest.id)}
                          onChange={() => handleSelectReturn(returnRequest.id)}
                          className="rounded"
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
                        <div className="font-medium">${returnRequest.refund_amount}</div>
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
                        {returnRequest.items && returnRequest.items.length > 0 ? 
                          returnRequest.items.map((item, idx) => (
                            <div key={idx}>
                              {item.product_name} (×{item.quantity})
                            </div>
                          )) :
                          <span className="text-gray-400">No items</span>
                        }
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t">
                      <Button variant="ghost" size="sm" asChild>
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
                            className="text-green-600 hover:text-green-700"
                            onClick={() => handleStatusUpdate(returnRequest.id, 'approved')}
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-red-600 hover:text-red-700"
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
                          checked={selectedReturns.length === returns.length && returns.length > 0}
                          onChange={handleSelectAll}
                          className="rounded"
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
                    {returns.map((returnRequest) => (
                      <tr key={returnRequest.id} className="hover:bg-gray-50">
                        <td className="py-4 px-4">
                          <input
                            type="checkbox"
                            checked={selectedReturns.includes(returnRequest.id)}
                            onChange={() => handleSelectReturn(returnRequest.id)}
                            className="rounded"
                          />
                        </td>
                        <td className="py-4 px-4">
                          <div>
                            <div className="font-medium">{returnRequest.customer_name}</div>
                            <div className="text-sm text-gray-500">{returnRequest.customer_email}</div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <span className="font-mono text-sm">{returnRequest.order_number}</span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="text-sm">
                            {returnRequest.items && returnRequest.items.length > 0 ? 
                              returnRequest.items.map((item, idx) => (
                                <div key={idx}>
                                  {item.product_name} (×{item.quantity})
                                </div>
                              )) :
                              <span className="text-gray-400">No items</span>
                            }
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm">{formatReason(returnRequest.reason)}</span>
                        </td>
                        <td className="py-4 px-4">
                          <span className="font-medium">${returnRequest.refund_amount}</span>
                        </td>
                        <td className="py-4 px-4">
                          {getStatusBadge(returnRequest.status)}
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm text-gray-500">
                            {new Date(returnRequest.created_at).toLocaleDateString()}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-2">
                            <Button variant="ghost" size="sm" asChild>
                              <Link to={`/app/returns/${returnRequest.id}`}>
                                <Eye className="h-4 w-4" />
                              </Link>
                            </Button>
                            {returnRequest.status === 'requested' && (
                              <>
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  className="text-green-600 hover:text-green-700"
                                  onClick={() => handleStatusUpdate(returnRequest.id, 'approved')}
                                  title="Approve Return"
                                >
                                  <CheckCircle className="h-4 w-4" />
                                </Button>
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  className="text-red-600 hover:text-red-700"
                                  onClick={() => handleStatusUpdate(returnRequest.id, 'denied')}
                                  title="Deny Return"
                                >
                                  <XCircle className="h-4 w-4" />
                                </Button>
                              </>
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
            >
              Previous
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              disabled={pagination.current_page >= pagination.total_pages}
              onClick={() => handlePageChange(pagination.current_page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AllReturns;