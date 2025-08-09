import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, Download, MoreHorizontal, Eye, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Badge } from '../../../components/ui/badge';

const AllReturns = () => {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({});
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    sortBy: 'created_at',
    sortOrder: 'desc',
    page: 1,
    limit: 20
  });

  // Get backend URL and tenant from environment
  const backendUrl = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
  const tenantId = 'tenant-fashion-store'; // TODO: Get from auth context

  // Load returns from backend
  useEffect(() => {
    loadReturns();
  }, [filters]);

  const loadReturns = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Build query parameters
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.status !== 'all') params.append('status_filter', filters.status);
      params.append('sort_by', filters.sortBy);
      params.append('sort_order', filters.sortOrder);
      params.append('page', filters.page.toString());
      params.append('limit', filters.limit.toString());

      const response = await fetch(`${backendUrl}/api/returns?${params.toString()}`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        const data = await response.json();
        setReturns(data.items || []);
        setPagination(data.pagination || {});
      } else {
        setError('Failed to load returns');
        console.error('Failed to load returns:', response.status);
      }
    } catch (err) {
      console.error('Error loading returns:', err);
      setError('Error loading returns');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (returnId, newStatus) => {
    try {
      const response = await fetch(`${backendUrl}/api/returns/${returnId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        // Refresh the returns list
        loadReturns();
      } else {
        console.error('Failed to update status:', response.status);
      }
    } catch (err) {
      console.error('Error updating status:', err);
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

  const exportReturns = () => {
    console.log('Exporting returns...');
    // TODO: Implement CSV export
  };

  const bulkApprove = () => {
    console.log('Bulk approve...');
    // TODO: Implement bulk actions
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value, page: 1 }); // Reset to page 1 when filtering
  };

  const handlePageChange = (newPage) => {
    setFilters({ ...filters, page: newPage });
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 rounded animate-pulse" />
        <div className="h-96 bg-gray-200 rounded animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Returns</h1>
          <p className="text-gray-500">Manage return requests and track their progress</p>
        </div>
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-red-600">{error}</p>
            <Button onClick={loadReturns} className="mt-4">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Returns</h1>
          <p className="text-gray-500">Manage return requests and track their progress</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={exportReturns}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button onClick={bulkApprove}>
            <CheckCircle className="h-4 w-4 mr-2" />
            Bulk Actions
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search customers, orders..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
              <SelectTrigger>
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
              <SelectTrigger>
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="created_at">Date Created</SelectItem>
                <SelectItem value="refund_amount">Amount</SelectItem>
                <SelectItem value="customer_name">Customer</SelectItem>
                <SelectItem value="status">Status</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              More Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Returns Table */}
      <Card>
        <CardHeader>
          <CardTitle>Return Requests ({pagination.total_items || returns.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Return ID</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Customer</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Order</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Items</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Reason</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Amount</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Status</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {returns.map((returnRequest) => (
                  <tr key={returnRequest.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-4 px-4">
                      <Link 
                        to={`/app/returns/${returnRequest.id}`}
                        className="font-mono text-sm text-blue-600 hover:text-blue-800"
                      >
                        {returnRequest.id}
                      </Link>
                    </td>
                    <td className="py-4 px-4">
                      <div>
                        <div className="font-medium">{returnRequest.customer_name || returnRequest.customer?.name}</div>
                        <div className="text-sm text-gray-500">{returnRequest.customer_email || returnRequest.customer?.email}</div>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-mono text-sm">{returnRequest.order_number || returnRequest.orderNumber}</span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="text-sm">
                        {returnRequest.items && returnRequest.items.length > 0 ? 
                          returnRequest.items.map((item, idx) => (
                            <div key={idx}>
                              {item.product_name || item.productName} (×{item.quantity})
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
                      <span className="font-medium">${returnRequest.refund_amount || returnRequest.refundAmount}</span>
                    </td>
                    <td className="py-4 px-4">
                      {getStatusBadge(returnRequest.status)}
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-sm text-gray-500">
                        {new Date(returnRequest.created_at || returnRequest.createdAt).toLocaleDateString()}
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

          {returns.length === 0 && (
            <div className="text-center py-12">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No returns found</h3>
              <p className="text-gray-500">Returns will appear here when customers submit them.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
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