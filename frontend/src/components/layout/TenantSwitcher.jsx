import React, { useState, useEffect } from 'react';
import { ChevronDown, Building2, Check } from 'lucide-react';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';

const TenantSwitcher = () => {
  const [currentTenant, setCurrentTenant] = useState(null);
  const [tenants, setTenants] = useState([]);

  // Mock data - will be replaced with real API calls
  useEffect(() => {
    setTenants([
      { id: 'tenant-fashion-store', name: 'Fashion Forward', plan: 'Pro' },
      { id: 'tenant-tech-gadgets', name: 'TechHub Electronics', plan: 'Enterprise' },
    ]);
    setCurrentTenant({ id: 'tenant-fashion-store', name: 'Fashion Forward', plan: 'Pro' });
  }, []);

  const handleTenantSwitch = (tenant) => {
    setCurrentTenant(tenant);
    // In real app, this would update the global tenant context
    console.log('Switching to tenant:', tenant.id);
  };

  if (!currentTenant) return null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="flex items-center space-x-2 w-full sm:w-auto min-w-0 touch-manipulation">
          <Building2 className="h-4 w-4 flex-shrink-0" />
          <div className="text-left min-w-0 flex-1">
            <div className="text-sm font-medium truncate">{currentTenant.name}</div>
            <div className="text-xs text-gray-500 truncate">{currentTenant.plan}</div>
          </div>
          <ChevronDown className="h-4 w-4 flex-shrink-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64" align="end">
        <DropdownMenuLabel>Switch Store</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {tenants.map((tenant) => (
          <DropdownMenuItem
            key={tenant.id}
            onClick={() => handleTenantSwitch(tenant)}
            className="flex items-center space-x-2 touch-manipulation"
          >
            <Building2 className="h-4 w-4 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{tenant.name}</div>
              <div className="text-xs text-gray-500 truncate">{tenant.plan}</div>
            </div>
            {currentTenant.id === tenant.id && (
              <Check className="h-4 w-4 text-blue-600 flex-shrink-0" />
            )}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem className="touch-manipulation">
          <Building2 className="h-4 w-4 mr-2" />
          Add Store...
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default TenantSwitcher;