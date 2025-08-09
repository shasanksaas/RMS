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
        <Button variant="outline" className="flex items-center space-x-2">
          <Building2 className="h-4 w-4" />
          <div className="text-left">
            <div className="text-sm font-medium">{currentTenant.name}</div>
            <div className="text-xs text-gray-500">{currentTenant.plan}</div>
          </div>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64">
        <DropdownMenuLabel>Switch Store</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {tenants.map((tenant) => (
          <DropdownMenuItem
            key={tenant.id}
            onClick={() => handleTenantSwitch(tenant)}
            className="flex items-center space-x-2"
          >
            <Building2 className="h-4 w-4" />
            <div className="flex-1">
              <div className="font-medium">{tenant.name}</div>
              <div className="text-xs text-gray-500">{tenant.plan}</div>
            </div>
            {currentTenant.id === tenant.id && (
              <Check className="h-4 w-4 text-blue-600" />
            )}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <Building2 className="h-4 w-4 mr-2" />
          Add Store...
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default TenantSwitcher;