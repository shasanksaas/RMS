import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Package, Wifi, WifiOff, Settings, BarChart3, ShoppingCart, ArrowLeft, Users, CreditCard, Workflow, Undo2, Menu, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import TenantSwitcher from './TenantSwitcher';
import UserProfile from './UserProfile';
import SearchBar from './SearchBar';
import ImpersonationBanner from '../admin/ImpersonationBanner';
import { useAuth } from '../../contexts/AuthContext';

const MerchantLayout = ({ isOnline }) => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user } = useAuth();

  const navigation = [
    { name: 'Dashboard', href: '/app/dashboard', icon: BarChart3 },
    { name: 'Returns', href: '/app/returns', icon: Undo2 },
    { name: 'Orders', href: '/app/orders', icon: ShoppingCart },
    { name: 'Rules', href: '/app/rules', icon: Settings },
    { name: 'Workflows', href: '/app/workflows', icon: Workflow },
    { name: 'Analytics', href: '/app/analytics', icon: BarChart3 },
    { name: 'Billing', href: '/app/billing', icon: CreditCard },
  ];

  const settingsNavigation = [
    { name: 'General', href: '/app/settings/general' },
    { name: 'Branding', href: '/app/settings/branding' },
    { name: 'Email', href: '/app/settings/email' },
    { name: 'Integrations', href: '/app/settings/integrations' },
    { name: 'Policies', href: '/app/settings/policies' },
    { name: 'Team', href: '/app/settings/team' },
  ];

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 py-2 md:py-4">
          <div className="flex items-center justify-between">
            {/* Left: Logo & Mobile Menu */}
            <div className="flex items-center space-x-2 md:space-x-4">
              <Button
                variant="ghost"
                size="sm"
                className="md:hidden p-2 hover:bg-gray-100 rounded-md touch-manipulation"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                aria-label="Toggle menu"
              >
                {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </Button>
              
              <div className="flex items-center space-x-2 md:space-x-3">
                <Package className="h-6 w-6 md:h-8 md:w-8 text-blue-600 flex-shrink-0" />
                <div className="hidden sm:block">
                  <h1 className="text-lg md:text-xl font-bold text-gray-900">Returns Manager</h1>
                  <p className="text-xs md:text-sm text-gray-500">Merchant Dashboard</p>
                </div>
              </div>

              {/* Online/Offline Indicator */}
              <div className={`flex items-center space-x-1 md:space-x-2 px-2 md:px-3 py-1 rounded-full text-xs md:text-sm ${
                isOnline ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {isOnline ? (
                  <>
                    <Wifi className="h-3 w-3 md:h-4 md:w-4" />
                    <span className="hidden sm:inline">Online</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-3 w-3 md:h-4 md:w-4" />
                    <span className="hidden sm:inline">Offline</span>
                  </>
                )}
              </div>
            </div>

            {/* Right: Search, Tenant Switcher, Profile */}
            <div className="flex items-center space-x-2 md:space-x-4">
              <div className="hidden lg:block">
                <SearchBar />
              </div>
              <div className="hidden sm:block">
                <TenantSwitcher />
              </div>
              <UserProfile />
            </div>
          </div>
          
          {/* Mobile Search Bar */}
          <div className="lg:hidden mt-3">
            <SearchBar />
          </div>

          {/* Mobile Tenant Switcher */}
          <div className="sm:hidden mt-3">
            <TenantSwitcher />
          </div>
          
          {!isOnline && (
            <Alert className="mt-4 border-yellow-200 bg-yellow-50">
              <WifiOff className="h-4 w-4" />
              <AlertDescription className="text-yellow-800 text-sm">
                You're currently offline. Data may be outdated. Changes won't be saved until you're back online.
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 transition-transform duration-300 ease-in-out fixed md:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-200 md:z-0 overflow-y-auto`}>
          <div className="p-4 md:p-6 space-y-6">
            {/* Main Navigation */}
            <nav className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-3 px-3 md:px-4 py-3 text-sm font-medium rounded-lg transition-colors touch-manipulation ${
                      isActive(item.href)
                        ? 'bg-blue-50 text-blue-600 border border-blue-200'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Settings Section */}
            <div>
              <h3 className="px-3 md:px-4 text-xs font-semibold text-gray-400 uppercase tracking-wide">Settings</h3>
              <nav className="mt-2 space-y-1">
                {settingsNavigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center px-3 md:px-4 py-3 text-sm font-medium rounded-lg transition-colors touch-manipulation ${
                      isActive(item.href)
                        ? 'bg-blue-50 text-blue-600 border border-blue-200'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <span>{item.name}</span>
                  </Link>
                ))}
              </nav>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 md:ml-0">
          <main className="p-3 md:p-6">
            {/* Impersonation Banner */}
            {user && user.isImpersonating && (
              <ImpersonationBanner 
                tenantId={user.tenant_id}
                tenantName={`Tenant ${user.tenant_id}`}
                onExit={() => window.location.href = '/admin/tenants'}
              />
            )}
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};

export default MerchantLayout;