import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Shield, Users, Activity, FileText, Flag, BookOpen, Menu } from 'lucide-react';
import { Button } from '../ui/button';
import UserProfile from './UserProfile';

const AdminLayout = () => {
  const location = useLocation();

  const navigation = [
    { name: 'Tenants', href: '/admin/tenants', icon: Users, description: 'Manage tenant accounts' },
    { name: 'Operations', href: '/admin/ops', icon: Activity, description: 'Monitor system operations' },
    { name: 'Audit', href: '/admin/audit', icon: FileText, description: 'View audit logs' },
    { name: 'Feature Flags', href: '/admin/flags', icon: Flag, description: 'Configure features' },
    { name: 'Catalog', href: '/admin/catalog', icon: BookOpen, description: 'Manage product catalog' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-gray-200">
      {/* Beautiful Header */}
      <div className="bg-gradient-to-r from-red-600 via-red-700 to-red-800 text-white shadow-xl border-b border-red-500">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-red-500/20 backdrop-blur-sm rounded-xl border border-red-400/30 shadow-lg">
                <Shield className="h-8 w-8 text-red-100" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white drop-shadow-sm">Super Admin</h1>
                <p className="text-red-100 font-medium">System Administration Portal</p>
              </div>
            </div>
            
            {/* Admin Profile & Logout */}
            <div className="flex items-center space-x-6">
              <div className="hidden md:flex items-center space-x-2 text-red-100">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium">Administrator Portal</span>
              </div>
              <div className="border-l border-red-400/50 pl-6">
                <UserProfile />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Beautiful Sidebar */}
        <div className="w-72 bg-white/90 backdrop-blur-sm border-r border-gray-200/60 min-h-screen shadow-xl">
          <div className="p-6">
            <div className="mb-6">
              <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Navigation</h2>
            </div>
            
            <nav className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`group flex items-center space-x-4 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                      active
                        ? 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg transform scale-[1.02]'
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 hover:shadow-md hover:transform hover:scale-[1.01]'
                    }`}
                  >
                    <div className={`p-2 rounded-lg transition-all duration-200 ${
                      active 
                        ? 'bg-red-400/20' 
                        : 'bg-gray-100 group-hover:bg-gray-200'
                    }`}>
                      <Icon className={`h-5 w-5 ${
                        active ? 'text-red-100' : 'text-gray-600 group-hover:text-gray-700'
                      }`} />
                    </div>
                    <div className="flex-1">
                      <div className={`font-semibold ${active ? 'text-white' : 'text-gray-900'}`}>
                        {item.name}
                      </div>
                      <div className={`text-xs mt-0.5 ${
                        active ? 'text-red-100' : 'text-gray-500 group-hover:text-gray-600'
                      }`}>
                        {item.description}
                      </div>
                    </div>
                  </Link>
                );
              })}
            </nav>
            
            {/* Admin Info Card */}
            <div className="mt-8 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Shield className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-blue-900">Admin Access</p>
                  <p className="text-xs text-blue-600">Full system privileges</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 bg-gray-50/50">
          <main className="p-0">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;