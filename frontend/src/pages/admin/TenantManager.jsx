import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Filter, 
  MoreHorizontal, 
  Eye, 
  Edit, 
  Archive, 
  RotateCcw,
  Store,
  Users,
  Calendar,
  ExternalLink
} from 'lucide-react';

import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { useToast } from '../../components/ui/use-toast';

import TenantStatusBadge from '../../components/tenant/TenantStatusBadge';
import ConnectionStatusIndicator from '../../components/tenant/ConnectionStatusIndicator';
import CreateTenantModal from '../../components/tenant/CreateTenantModal';
import { tenantService } from '../../services/tenantService';
import { useAuth } from '../../contexts/AuthContext';

const TenantManager = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  // State management
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0
  });

  // Check admin access
  useEffect(() => {
    if (!user || user.role !== 'admin') {
      navigate('/auth/login?error=access_denied');
      return;
    }
  }, [user, navigate]);

  // Load tenants
  useEffect(() => {
    loadTenants();
  }, [loadTenants]);

  const loadTenants = useCallback(async () => {
    try {
      setLoading(true);
      const response = await tenantService.listTenants(
        pagination.page, 
        pagination.pageSize,
        statusFilter === 'all' ? null : statusFilter
      );

      setTenants(response.tenants || []);
      setPagination(prev => ({
        ...prev,
        total: response.total || 0,
        totalPages: response.total_pages || 0
      }));
    } catch (error) {
      console.error('Failed to load tenants:', error);
      toast({
        title: "Failed to load tenants",
        description: error.message || "Please try again",
        variant: "destructive"
      });
      // Set empty state on error
      setTenants([]);
      setPagination(prev => ({
        ...prev,
        total: 0,
        totalPages: 0
      }));
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.pageSize, statusFilter, toast]);

  const handleCreateTenant = async (tenantData) => {
    try {
      const newTenant = await tenantService.createTenant(tenantData);
      
      toast({
        title: "Tenant Created Successfully!",
        description: (
          <div>
            <p>Tenant ID: <strong>{newTenant.tenant_id}</strong></p>
            <p>Share this Tenant ID with merchants for signup.</p>
          </div>
        ),
        variant: "default"
      });

      setShowCreateModal(false);
      loadTenants(); // Reload list
    } catch (error) {
      toast({
        title: "Failed to create tenant",
        description: error.message || "Please try again",
        variant: "destructive"
      });
    }
  };

  const handleArchiveTenant = async (tenantId) => {
    if (!window.confirm(`Are you sure you want to archive tenant ${tenantId}? This will prevent new signups.`)) {
      return;
    }

    try {
      await tenantService.archiveTenant(tenantId);
      toast({
        title: "Tenant Archived",
        description: `Tenant ${tenantId} has been archived successfully.`,
        variant: "default"
      });
      loadTenants();
    } catch (error) {
      toast({
        title: "Failed to archive tenant",
        description: error.message || "Please try again",
        variant: "destructive"
      });
    }
  };

  const handleReactivateTenant = async (tenantId) => {
    try {
      await tenantService.reactivateTenant(tenantId);
      toast({
        title: "Tenant Reactivated",
        description: `Tenant ${tenantId} is now active again.`,
        variant: "default"
      });
      loadTenants();
    } catch (error) {
      toast({
        title: "Failed to reactivate tenant",
        description: error.message || "Please try again",
        variant: "destructive"
      });
    }
  };

  const filteredTenants = (tenants || []).filter(tenant =>
    tenant.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tenant.tenant_id?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const copyTenantId = (tenantId) => {
    navigator.clipboard.writeText(tenantId);
    toast({
      title: "Copied!",
      description: `Tenant ID ${tenantId} copied to clipboard`,
      variant: "default"
    });
  };

  if (!user || user.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Alert className="max-w-md">
          <AlertDescription>
            Admin access required. Please login with admin credentials.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Tenant Manager</h1>
            <p className="text-gray-600 mt-1">
              Manage tenants and monitor merchant signups
            </p>
          </div>
          <Button onClick={() => setShowCreateModal(true)} size="lg">
            <Plus className="h-4 w-4 mr-2" />
            Create Tenant
          </Button>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <Store className="h-8 w-8 text-blue-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Tenants</p>
                  <p className="text-2xl font-bold text-gray-900">{pagination.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <Users className="h-8 w-8 text-green-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Tenants</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {tenants.filter(t => ['claimed', 'active'].includes(t.status)).length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <Calendar className="h-8 w-8 text-yellow-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-600">New Tenants</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {tenants.filter(t => t.status === 'new').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <Archive className="h-8 w-8 text-gray-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Archived</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {tenants.filter(t => t.status === 'archived').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Filters and Search */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search tenants by name or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="new">New</option>
                <option value="claimed">Claimed</option>
                <option value="active">Active</option>
                <option value="suspended">Suspended</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tenants Table */}
      <Card>
        <CardHeader>
          <CardTitle>Tenants ({filteredTenants.length})</CardTitle>
          <CardDescription>
            Manage all tenants and track their signup status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-gray-600">Loading tenants...</p>
            </div>
          ) : filteredTenants.length === 0 ? (
            <div className="text-center py-12">
              <Store className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No tenants found</h3>
              <p className="text-gray-600 mb-4">
                {searchQuery ? 'Try adjusting your search criteria' : 'Get started by creating your first tenant'}
              </p>
              {!searchQuery && (
                <Button onClick={() => setShowCreateModal(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create First Tenant
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-4 font-semibold text-gray-900">Tenant Info</th>
                    <th className="text-left p-4 font-semibold text-gray-900">Status</th>
                    <th className="text-left p-4 font-semibold text-gray-900">Connection</th>
                    <th className="text-left p-4 font-semibold text-gray-900">Created</th>
                    <th className="text-left p-4 font-semibold text-gray-900">Claimed</th>
                    <th className="text-right p-4 font-semibold text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTenants.map((tenant) => (
                    <tr key={tenant.tenant_id} className="border-b hover:bg-gray-50">
                      <td className="p-4">
                        <div>
                          <h3 className="font-semibold text-gray-900">{tenant.name || 'Unnamed Store'}</h3>
                          <p className="text-sm text-gray-600 font-mono cursor-pointer hover:text-blue-600" 
                             onClick={() => copyTenantId(tenant.tenant_id)}>
                            {tenant.tenant_id}
                          </p>
                          {tenant.notes && (
                            <p className="text-xs text-gray-500 mt-1">{tenant.notes}</p>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <TenantStatusBadge status={tenant.status} />
                      </td>
                      <td className="p-4">
                        <ConnectionStatusIndicator 
                          connected={false} 
                          status="disconnected"
                          showLabel={false}
                        />
                      </td>
                      <td className="p-4 text-sm text-gray-600">
                        {formatDate(tenant.created_at)}
                      </td>
                      <td className="p-4 text-sm text-gray-600">
                        {formatDate(tenant.claimed_at)}
                      </td>
                      <td className="p-4 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/tenants/${tenant.tenant_id}`)}
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => copyTenantId(tenant.tenant_id)}
                            >
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Copy Tenant ID
                            </DropdownMenuItem>
                            {tenant.status === 'archived' ? (
                              <DropdownMenuItem
                                onClick={() => handleReactivateTenant(tenant.tenant_id)}
                              >
                                <RotateCcw className="h-4 w-4 mr-2" />
                                Reactivate
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem
                                onClick={() => handleArchiveTenant(tenant.tenant_id)}
                                className="text-red-600 focus:text-red-600"
                              >
                                <Archive className="h-4 w-4 mr-2" />
                                Archive
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {pagination.totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <p className="text-sm text-gray-600">
                Showing {Math.min((pagination.page - 1) * pagination.pageSize + 1, pagination.total)} to{' '}
                {Math.min(pagination.page * pagination.pageSize, pagination.total)} of {pagination.total} tenants
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.page <= 1}
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.page >= pagination.totalPages}
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Tenant Modal */}
      <CreateTenantModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateTenant}
      />
    </div>
  );
};

export default TenantManager;