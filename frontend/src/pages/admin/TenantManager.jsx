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
  ExternalLink,
  LogIn,
  Trash2,
  AlertTriangle
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

import { tenantService } from '../../services/tenantService';
import { useAuth } from '../../contexts/AuthContext';
import CreateTenantModal from '../../components/tenant/CreateTenantModal';

const TenantManager = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  // State management - NO MOCK DATA
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

  // Load tenants function - REAL API CALLS ONLY
  const loadTenants = useCallback(async () => {
    if (!user || user.role !== 'admin') {
      return;
    }

    try {
      setLoading(true);
      
      // Call REAL API - no mocks
      const response = await tenantService.listTenants(
        pagination.page, 
        pagination.pageSize,
        statusFilter === 'all' ? null : statusFilter
      );

      // Set real data from API
      setTenants(response.tenants || []);
      setPagination(prev => ({
        ...prev,
        total: response.total || 0,
        totalPages: Math.ceil((response.total || 0) / prev.pageSize)
      }));

      console.log(`✅ Loaded ${response.tenants?.length || 0} real tenants from database`);

    } catch (error) {
      console.error('❌ Failed to load real tenants:', error);
      toast({
        title: "Failed to load tenants",
        description: error.message || "Please try again",
        variant: "destructive"
      });
      
      // Set empty state on error - NO FALLBACK TO MOCKS
      setTenants([]);
      setPagination(prev => ({
        ...prev,
        total: 0,
        totalPages: 0
      }));
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.pageSize, statusFilter, toast, user]);

  // Load tenants on component mount and when dependencies change
  useEffect(() => {
    if (user && user.role === 'admin') {
      loadTenants();
    }
  }, [loadTenants, user]);

  // Check admin access
  useEffect(() => {
    if (!user || user.role !== 'admin') {
      navigate('/auth/login?error=access_denied');
      return;
    }
  }, [user, navigate]);

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
      loadTenants(); // Reload real data
    } catch (error) {
      toast({
        title: "Failed to create tenant",
        description: error.message || "Please try again",
        variant: "destructive"
      });
    }
  };

  const handleDeleteTenant = async (tenantId, tenantName) => {
    if (!window.confirm(`Are you sure you want to delete tenant "${tenantName}" (${tenantId})? This action cannot be undone.`)) {
      return;
    }

    try {
      await tenantService.deleteTenant(tenantId);
      toast({
        title: "Tenant Deleted",
        description: `Tenant "${tenantName}" has been deleted successfully.`,
        variant: "default"
      });
      loadTenants(); // Reload real data
    } catch (error) {
      toast({
        title: "Failed to delete tenant",
        description: error.message || "Please try again",
        variant: "destructive"
      });
    }
  };

  const handleImpersonate = async (tenantId, tenantName) => {
    try {
      console.log(`🔐 Admin impersonating tenant: ${tenantId}`);
      
      // This will redirect the browser to the tenant dashboard
      await tenantService.impersonateTenant(tenantId);
      
      // If we reach here, something went wrong with the redirect
      toast({
        title: "Impersonation Started",
        description: `Opening dashboard for ${tenantName}...`,
        variant: "default"
      });
      
    } catch (error) {
      console.error('❌ Impersonation failed:', error);
      toast({
        title: "Failed to open tenant dashboard",
        description: error.message || "Please try again",
        variant: "destructive"
      });
    }
  };

  // Filter tenants based on search query
  const filteredTenants = tenants.filter(tenant => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      tenant.tenant_id.toLowerCase().includes(query) ||
      tenant.name.toLowerCase().includes(query) ||
      (tenant.shop_domain && tenant.shop_domain.toLowerCase().includes(query))
    );
  });

  // Calculate stats from real data
  const stats = {
    total: tenants.length,
    active: tenants.filter(t => t.connected_provider === 'shopify').length,
    new: tenants.filter(t => !t.connected_provider).length,
    archived: 0 // Would need to include archived tenants in API
  };

  // Utility functions
  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'active':
        return {
          badge: 'bg-green-100 text-green-800 border-green-200',
          bg: 'bg-green-100',
          text: 'text-green-600'
        };
      case 'pending':
        return {
          badge: 'bg-orange-100 text-orange-800 border-orange-200',
          bg: 'bg-orange-100',
          text: 'text-orange-600'
        };
      case 'suspended':
        return {
          badge: 'bg-red-100 text-red-800 border-red-200',
          bg: 'bg-red-100',
          text: 'text-red-600'
        };
      default:
        return {
          badge: 'bg-gray-100 text-gray-800 border-gray-200',
          bg: 'bg-gray-100',
          text: 'text-gray-600'
        };
    }
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
      <div className="p-6 max-w-7xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4 w-1/3"></div>
          <div className="h-4 bg-gray-200 rounded mb-8 w-1/2"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!user || user.role !== 'admin') {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Access denied. Admin privileges required to manage tenants.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Beautiful Header Section */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 md:p-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
                  <Users className="h-8 w-8 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                    Tenant Management
                  </h1>
                  <p className="text-gray-600 font-medium">
                    Manage and monitor all tenant accounts across the platform
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={() => navigate('/auth/login')}
                variant="outline"
                className="border-2 border-blue-200 text-blue-700 hover:bg-blue-50 hover:border-blue-300 transition-all duration-200 font-semibold"
              >
                <LogIn className="h-4 w-4 mr-2" />
                Merchant Login
              </Button>
              <Button
                onClick={() => setShowCreateModal(true)}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create New Tenant
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200 shadow-lg hover:shadow-xl transition-all duration-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-xl">
                  <Store className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-green-600 uppercase tracking-wide">Active Tenants</p>
                  <p className="text-2xl font-bold text-green-900">{stats.active}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-orange-50 to-amber-50 border-orange-200 shadow-lg hover:shadow-xl transition-all duration-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-orange-100 rounded-xl">
                  <Calendar className="h-6 w-6 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-orange-600 uppercase tracking-wide">Not Connected</p>
                  <p className="text-2xl font-bold text-orange-900">{stats.new}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 shadow-lg hover:shadow-xl transition-all duration-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-xl">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-blue-600 uppercase tracking-wide">Total Tenants</p>
                  <p className="text-2xl font-bold text-blue-900">{stats.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Modern Search & Filter Section */}
        <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <Input
                  placeholder="Search tenants by name, domain, or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 h-12 bg-white border-2 border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all duration-200"
                />
              </div>
              
              <div className="flex gap-3">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button 
                      variant="outline" 
                      className="h-12 px-6 border-2 border-gray-200 hover:border-gray-300 bg-white font-medium"
                    >
                      <Filter className="h-4 w-4 mr-2" />
                      {statusFilter === 'all' ? 'All Status' : statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1)}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem onClick={() => setStatusFilter('all')}>
                      All Status
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setStatusFilter('connected')}>
                      Connected
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setStatusFilter('new')}>
                      Not Connected
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                
                <Button 
                  onClick={loadTenants}
                  variant="outline"
                  className="h-12 px-6 border-2 border-gray-200 hover:border-gray-300 bg-white font-medium"
                  disabled={loading}
                >
                  <RotateCcw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Beautiful Tenants Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    <div className="h-3 bg-gray-200 rounded w-full"></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : filteredTenants.length === 0 ? (
          <Card className="shadow-lg border-0">
            <CardContent className="text-center py-16">
              <div className="space-y-4">
                <div className="p-4 bg-gray-100 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
                  <Store className="h-8 w-8 text-gray-400" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">No tenants found</h3>
                  <p className="text-gray-500 mb-6">
                    {searchQuery ? 'Try adjusting your search terms' : 'Create your first tenant to get started'}
                  </p>
                  <Button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create First Tenant
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTenants.map((tenant) => (
              <Card 
                key={tenant.tenant_id} 
                className="group hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 border-0 shadow-lg bg-white/90 backdrop-blur-sm"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${tenant.connected_provider === 'shopify' ? 'bg-green-100' : 'bg-gray-100'}`}>
                        <Store className={`h-5 w-5 ${tenant.connected_provider === 'shopify' ? 'text-green-600' : 'text-gray-600'}`} />
                      </div>
                      <div>
                        <CardTitle className="text-lg font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
                          {tenant.name}
                        </CardTitle>
                        <CardDescription className="text-sm font-medium text-gray-500">
                          {tenant.shop_domain || 'No domain set'}
                        </CardDescription>
                      </div>
                    </div>
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-100"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-48">
                        <DropdownMenuItem onClick={() => handleImpersonate(tenant.tenant_id)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Dashboard
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => console.log('Edit tenant:', tenant.tenant_id)}>
                          <Edit className="h-4 w-4 mr-2" />
                          Edit Tenant
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => handleDeleteTenant(tenant.tenant_id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete Tenant
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">Status</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
                      tenant.connected_provider === 'shopify' 
                        ? 'bg-green-100 text-green-800 border-green-200' 
                        : 'bg-gray-100 text-gray-800 border-gray-200'
                    }`}>
                      {tenant.connected_provider === 'shopify' ? 'Connected' : 'Not Connected'}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">Created</span>
                    <span className="text-sm text-gray-900 font-medium">
                      {formatDate(tenant.created_at)}
                    </span>
                  </div>
                  
                  {tenant.connected_provider === 'shopify' && (
                    <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg border border-green-200">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-sm font-medium text-green-700">Shopify Connected</span>
                    </div>
                  )}
                  
                  <div className="pt-2 border-t border-gray-100">
                    <Button
                      onClick={() => handleImpersonate(tenant.tenant_id)}
                      className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold shadow-md hover:shadow-lg transition-all duration-200"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open Dashboard
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Beautiful Pagination */}
        {pagination.totalPages > 1 && (
          <Card className="shadow-lg border-0">
            <CardContent className="p-6 flex justify-center">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                  disabled={pagination.page === 1}
                  className="font-medium"
                >
                  Previous
                </Button>
                
                <div className="flex items-center gap-2 px-4">
                  {Array.from({ length: pagination.totalPages }, (_, i) => i + 1)
                    .filter(page => 
                      page === 1 || 
                      page === pagination.totalPages || 
                      Math.abs(page - pagination.page) <= 1
                    )
                    .map((page, index, array) => (
                      <React.Fragment key={page}>
                        {index > 0 && array[index - 1] !== page - 1 && (
                          <span className="text-gray-400">...</span>
                        )}
                        <Button
                          variant={pagination.page === page ? "default" : "ghost"}
                          onClick={() => setPagination(prev => ({ ...prev, page }))}
                          className={`w-10 h-10 font-medium ${
                            pagination.page === page 
                              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md' 
                              : 'hover:bg-gray-100'
                          }`}
                        >
                          {page}
                        </Button>
                      </React.Fragment>
                    ))}
                </div>
                
                <Button
                  variant="outline"
                  onClick={() => setPagination(prev => ({ ...prev, page: Math.min(prev.totalPages, prev.page + 1) }))}
                  disabled={pagination.page === pagination.totalPages}
                  className="font-medium"
                >
                  Next
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Create Tenant Modal */}
      {showCreateModal && (
        <CreateTenantModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadTenants();
          }}
        />
      )}
    </div>
  );
};

export default TenantManager;