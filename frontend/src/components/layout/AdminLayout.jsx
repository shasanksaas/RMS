import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Shield, Users, Activity, FileText, Flag, BookOpen, Menu } from 'lucide-react';
import { Button } from '../ui/button';
import UserProfile from './UserProfile';

const AdminLayout = () => {
  const location = useLocation();

  const navigation = [
    { name: 'Tenants', href: '/admin/tenants', icon: Users },
    { name: 'Operations', href: '/admin/ops', icon: Activity },
    { name: 'Audit', href: '/admin/audit', icon: FileText },
    { name: 'Feature Flags', href: '/admin/flags', icon: Flag },
    { name: 'Catalog', href: '/admin/catalog', icon: BookOpen },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-red-600 text-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-3">
            <Shield className="h-8 w-8" />
            <div>
              <h1 className="text-xl font-bold">Super Admin</h1>
              <p className="text-sm text-red-100">System Administration</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 min-h-screen">
          <div className="p-6">
            <nav className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-3 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                      isActive(item.href)
                        ? 'bg-red-50 text-red-600 border border-red-200'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          <main className="p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;