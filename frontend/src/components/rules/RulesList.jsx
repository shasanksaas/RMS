import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  Filter, 
  Plus, 
  Edit3, 
  Trash2, 
  MoreVertical, 
  Play, 
  Pause, 
  TestTube2,
  Tag,
  Clock,
  CheckCircle,
  XCircle,
  Settings
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Switch } from '../ui/switch';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../ui/dropdown-menu';
import { Alert, AlertDescription } from '../ui/alert';

const RulesList = ({ onCreateRule, onEditRule, onDeleteRule }) => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [tagFilter, setTagFilter] = useState('');
  const [sortBy, setSortBy] = useState('priority');
  const [sortOrder, setSortOrder] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [availableTags, setAvailableTags] = useState([]);
  const [simulationResult, setSimulationResult] = useState(null);

  const itemsPerPage = 20;

  // Debounced search
  const [searchDebounceTimer, setSearchDebounceTimer] = useState(null);
  
  const debouncedSearch = useCallback((term) => {
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }
    
    const timer = setTimeout(() => {
      setSearchTerm(term);
      setCurrentPage(1); // Reset to first page on search
    }, 300);
    
    setSearchDebounceTimer(timer);
  }, [searchDebounceTimer]);

  // Load rules
  const loadRules = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage,
        limit: itemsPerPage,
        sort_by: sortBy,
        sort_order: sortOrder,
        status_filter: statusFilter
      });

      if (searchTerm) params.append('search', searchTerm);
      if (tagFilter) params.append('tag_filter', tagFilter);

      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/rules/?${params}`,
        {
          headers: {
            'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
          }
        }
      );

      if (!response.ok) throw new Error('Failed to load rules');

      const data = await response.json();
      setRules(data.items || []);
      setTotalPages(data.pagination?.total_pages || 1);
      setTotalCount(data.pagination?.total_count || 0);

      // Extract unique tags
      const tags = new Set();
      data.items?.forEach(rule => {
        rule.tags?.forEach(tag => tags.add(tag));
      });
      setAvailableTags(Array.from(tags));

    } catch (error) {
      console.error('Failed to load rules:', error);
      setRules([]);
    } finally {
      setLoading(false);
    }
  }, [currentPage, searchTerm, statusFilter, tagFilter, sortBy, sortOrder]);

  // Load rules on component mount and when filters change
  useEffect(() => {
    loadRules();
  }, [loadRules]);

  // Toggle rule status
  const toggleRuleStatus = async (ruleId, currentStatus) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/rules/${ruleId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
          },
          body: JSON.stringify({ is_active: !currentStatus })
        }
      );

      if (!response.ok) throw new Error('Failed to update rule status');

      // Reload rules to reflect changes
      await loadRules();
    } catch (error) {
      console.error('Failed to toggle rule status:', error);
    }
  };

  // Delete rule with confirmation
  const handleDeleteRule = async (ruleId, ruleName) => {
    if (window.confirm(`Are you sure you want to delete the rule "${ruleName}"? This action cannot be undone.`)) {
      try {
        const response = await fetch(
          `${process.env.REACT_APP_BACKEND_URL}/api/rules/${ruleId}`,
          {
            method: 'DELETE',
            headers: {
              'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
            }
          }
        );

        if (!response.ok) throw new Error('Failed to delete rule');

        // Reload rules
        await loadRules();
        
        if (onDeleteRule) {
          onDeleteRule(ruleId);
        }
      } catch (error) {
        console.error('Failed to delete rule:', error);
      }
    }
  };

  // Test rules simulation
  const testRulesSimulation = async () => {
    try {
      const testData = {
        order_data: {
          total_amount: 150.00,
          financial_status: 'paid',
          fulfillment_status: 'fulfilled',
          order_date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
          items: [{ category: 'Clothing', sku: 'SHIRT-001', product_name: 'Cotton T-Shirt' }],
          billing_address: { country: 'US', province: 'CA' },
          payment_method: 'credit_card'
        },
        return_data: {
          reason: 'defective',
          refund_amount: 75.00,
          items_to_return: [
            { sku: 'SHIRT-001', product_name: 'Cotton T-Shirt', quantity: 1, price: 75.00 }
          ]
        }
      };

      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/rules/simulate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
          },
          body: JSON.stringify(testData)
        }
      );

      if (!response.ok) throw new Error('Failed to run simulation');

      const result = await response.json();
      setSimulationResult(result);
    } catch (error) {
      console.error('Simulation failed:', error);
      setSimulationResult({ success: false, error: error.message });
    }
  };

  const getStatusIcon = (isActive) => {
    return isActive ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : (
      <XCircle className="h-4 w-4 text-gray-400" />
    );
  };

  const getStatusBadge = (isActive) => {
    return (
      <Badge variant={isActive ? 'default' : 'secondary'} className="text-xs">
        {isActive ? 'Active' : 'Inactive'}
      </Badge>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Return Rules</h1>
          <p className="text-gray-500">Automate your return approval process</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={testRulesSimulation}>
            <TestTube2 className="h-4 w-4 mr-2" />
            Test Rules
          </Button>
          <Button onClick={onCreateRule}>
            <Plus className="h-4 w-4 mr-2" />
            Add Rule
          </Button>
        </div>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search rules..."
                className="pl-10"
                onChange={(e) => debouncedSearch(e.target.value)}
              />
            </div>

            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Rules</SelectItem>
                <SelectItem value="active">Active Only</SelectItem>
                <SelectItem value="inactive">Inactive Only</SelectItem>
              </SelectContent>
            </Select>

            {/* Tag Filter */}
            <Select value={tagFilter} onValueChange={setTagFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by tag" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Tags</SelectItem>
                {availableTags.map((tag) => (
                  <SelectItem key={tag} value={tag}>
                    {tag}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Sort */}
            <Select value={`${sortBy}-${sortOrder}`} onValueChange={(value) => {
              const [field, order] = value.split('-');
              setSortBy(field);
              setSortOrder(order);
            }}>
              <SelectTrigger>
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="priority-asc">Priority (Low to High)</SelectItem>
                <SelectItem value="priority-desc">Priority (High to Low)</SelectItem>
                <SelectItem value="name-asc">Name (A to Z)</SelectItem>
                <SelectItem value="name-desc">Name (Z to A)</SelectItem>
                <SelectItem value="created_at-desc">Newest First</SelectItem>
                <SelectItem value="created_at-asc">Oldest First</SelectItem>
                <SelectItem value="updated_at-desc">Recently Modified</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Simulation Result */}
      {simulationResult && (
        <Alert className={simulationResult.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
          <TestTube2 className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium">
                Simulation Result: {simulationResult.result?.final_status === 'approved' ? 'Auto-Approved' : 
                                   simulationResult.result?.final_status === 'denied' ? 'Auto-Declined' : 'Manual Review Required'}
              </p>
              {simulationResult.result && (
                <div className="text-sm space-y-1">
                  <p>Rules Evaluated: {simulationResult.result.total_rules_evaluated}</p>
                  <p>Rules Matched: {simulationResult.result.rules_matched}</p>
                  {simulationResult.result.matched_rule_names?.length > 0 && (
                    <p>Matched Rules: {simulationResult.result.matched_rule_names.join(', ')}</p>
                  )}
                </div>
              )}
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setSimulationResult(null)}
                className="mt-2"
              >
                Dismiss
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Rules List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Rules ({totalCount})</span>
            </CardTitle>
            {loading && <div className="text-sm text-gray-500">Loading...</div>}
          </div>
        </CardHeader>
        <CardContent>
          {rules.length === 0 && !loading ? (
            <div className="text-center py-12">
              <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Rules Found</h3>
              <p className="text-gray-600 mb-4">
                {searchTerm || statusFilter !== 'all' || tagFilter ? 
                  'No rules match your current filters.' : 
                  'Create your first rule to automate return processing.'
                }
              </p>
              {!searchTerm && statusFilter === 'all' && !tagFilter && (
                <Button onClick={onCreateRule}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create First Rule
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Table Header - Desktop */}
              <div className="hidden md:grid md:grid-cols-12 gap-4 text-sm font-medium text-gray-500 border-b pb-2">
                <div className="col-span-4">Rule Name</div>
                <div className="col-span-3">Conditions</div>
                <div className="col-span-2">Actions</div>
                <div className="col-span-1">Priority</div>
                <div className="col-span-1">Status</div>
                <div className="col-span-1">Actions</div>
              </div>

              {/* Rules */}
              {rules.map((rule) => (
                <div key={rule.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  {/* Mobile Layout */}
                  <div className="md:hidden space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(rule.is_active)}
                          <h3 className="font-medium text-gray-900">{rule.name}</h3>
                          {getStatusBadge(rule.is_active)}
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{rule.description}</p>
                      </div>
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onEditRule(rule)}>
                            <Edit3 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => toggleRuleStatus(rule.id, rule.is_active)}>
                            {rule.is_active ? (
                              <>
                                <Pause className="h-4 w-4 mr-2" />
                                Deactivate
                              </>
                            ) : (
                              <>
                                <Play className="h-4 w-4 mr-2" />
                                Activate
                              </>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteRule(rule.id, rule.name)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Priority:</span> {rule.priority}
                      </div>
                      <div>
                        <span className="font-medium">Updated:</span> {formatDate(rule.updated_at)}
                      </div>
                    </div>

                    <div className="text-sm">
                      <div className="font-medium text-gray-700 mb-1">Conditions:</div>
                      <div className="text-gray-600 text-xs bg-gray-100 p-2 rounded">
                        {rule.conditions_summary}
                      </div>
                    </div>

                    <div className="text-sm">
                      <div className="font-medium text-gray-700 mb-1">Actions:</div>
                      <div className="text-gray-600 text-xs bg-gray-100 p-2 rounded">
                        {rule.actions_summary}
                      </div>
                    </div>

                    {rule.tags && rule.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {rule.tags.map((tag, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            <Tag className="h-3 w-3 mr-1" />
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Desktop Layout */}
                  <div className="hidden md:grid md:grid-cols-12 gap-4 items-center">
                    <div className="col-span-4">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(rule.is_active)}
                        <div>
                          <h3 className="font-medium text-gray-900">{rule.name}</h3>
                          <p className="text-sm text-gray-600 truncate">{rule.description}</p>
                          {rule.tags && rule.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {rule.tags.slice(0, 2).map((tag, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                              {rule.tags.length > 2 && (
                                <Badge variant="outline" className="text-xs">
                                  +{rule.tags.length - 2}
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="col-span-3">
                      <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded text-xs">
                        {rule.conditions_summary}
                      </div>
                    </div>

                    <div className="col-span-2">
                      <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded text-xs">
                        {rule.actions_summary}
                      </div>
                    </div>

                    <div className="col-span-1">
                      <Badge variant="outline" className="text-xs">
                        {rule.priority}
                      </Badge>
                    </div>

                    <div className="col-span-1">
                      <div className="flex items-center space-x-2">
                        <Switch
                          checked={rule.is_active}
                          onCheckedChange={() => toggleRuleStatus(rule.id, rule.is_active)}
                          size="sm"
                        />
                      </div>
                    </div>

                    <div className="col-span-1">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onEditRule(rule)}>
                            <Edit3 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteRule(rule.id, rule.name)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <div className="text-sm text-gray-600">
                Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, totalCount)} of {totalCount} rules
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <span className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default RulesList;