import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';

const AdminLogin = () => {
  const [formData, setFormData] = useState({
    tenantId: 'tenant-rms34', // Default admin tenant
    email: '',
    password: '',
    rememberMe: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setError('');

    // Client-side validation
    if (!formData.email.trim()) {
      setError('Email is required');
      return;
    }

    if (!formData.password.trim()) {
      setError('Password is required');
      return;
    }

    setIsLoading(true);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      
      const response = await fetch(`${backendUrl}/api/users/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': formData.tenantId
        },
        body: JSON.stringify({
          tenant_id: formData.tenantId,
          email: formData.email,
          password: formData.password,
          remember_me: formData.rememberMe
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Verify admin role
        if (data.user.role !== 'admin') {
          setError('Access denied: Admin privileges required');
          return;
        }

        // Store auth data
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('currentTenant', formData.tenantId);
        localStorage.setItem('user_info', JSON.stringify(data.user));

        console.log('✅ Admin login successful:', data.user);

        // Redirect to admin dashboard
        navigate('/admin/tenants', { replace: true });

      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed. Please check your credentials.');
      }

    } catch (error) {
      console.error('❌ Admin login error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const fillTestCredentials = () => {
    setFormData({
      tenantId: 'tenant-rms34',
      email: 'admin@returns-manager.com',
      password: 'AdminPassword123!',
      rememberMe: false
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-md w-full space-y-8 p-8">
        
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Admin Portal
          </h1>
          <p className="text-gray-300">
            Returns Manager - Administrator Access
          </p>
        </div>

        {/* Admin Login Card */}
        <Card className="bg-white/10 backdrop-blur border-white/20">
          <CardHeader className="text-center pb-6">
            <CardTitle className="text-xl font-semibold text-white">
              Administrator Login
            </CardTitle>
            <CardDescription className="text-gray-300">
              Enter your admin credentials to access the management dashboard
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleAdminLogin} className="space-y-4">
              
              {/* Tenant ID Field */}
              <div className="space-y-2">
                <Label htmlFor="tenantId" className="text-sm font-medium text-gray-200">
                  Tenant Context
                </Label>
                <Input
                  id="tenantId"
                  name="tenantId"
                  type="text"
                  value={formData.tenantId}
                  onChange={handleInputChange}
                  className="bg-white/10 border-white/20 text-white placeholder:text-gray-400"
                  disabled={isLoading}
                  required
                />
                <p className="text-xs text-gray-400">
                  Admin tenant context (usually tenant-rms34)
                </p>
              </div>

              {/* Email Field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium text-gray-200">
                  Admin Email
                </Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="admin@returns-manager.com"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="bg-white/10 border-white/20 text-white placeholder:text-gray-400"
                  disabled={isLoading}
                  autoFocus
                  required
                />
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium text-gray-200">
                  Password
                </Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="Enter admin password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="bg-white/10 border-white/20 text-white placeholder:text-gray-400"
                  disabled={isLoading}
                  required
                />
              </div>

              {/* Remember Me */}
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="rememberMe"
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                  disabled={isLoading}
                />
                <Label htmlFor="rememberMe" className="text-sm text-gray-300">
                  Keep me signed in
                </Label>
              </div>

              {/* Error Alert */}
              {error && (
                <Alert variant="destructive" className="bg-red-900/50 border-red-500">
                  <AlertDescription className="text-red-200">
                    {error}
                  </AlertDescription>
                </Alert>
              )}

              {/* Login Button */}
              <Button
                type="submit"
                disabled={isLoading || !formData.email || !formData.password}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium py-3 text-base"
                size="lg"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
                    Signing In...
                  </div>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                    </svg>
                    Sign In as Admin
                  </>
                )}
              </Button>

              {/* Test Credentials Button */}
              <Button
                type="button"
                variant="outline"
                onClick={fillTestCredentials}
                className="w-full border-white/20 text-gray-300 hover:bg-white/10 hover:text-white"
                disabled={isLoading}
              >
                Fill Test Credentials
              </Button>

            </form>

            {/* Footer */}
            <div className="mt-6 text-center">
              <p className="text-xs text-gray-400">
                Merchant Login: <a href="/auth/login" className="text-blue-400 hover:text-blue-300">Use Shopify OAuth →</a>
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Secure admin access to Returns Manager system
              </p>
            </div>

          </CardContent>
        </Card>

        {/* Admin Features Preview */}
        <div className="grid grid-cols-1 gap-4 mt-8">
          <div className="bg-white/5 backdrop-blur rounded-lg p-4 border border-white/10">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-white">Merchant Management</h3>
                <p className="text-sm text-gray-300">View and manage all merchants, their stores, and integrations</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/5 backdrop-blur rounded-lg p-4 border border-white/10">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-white">System Analytics</h3>
                <p className="text-sm text-gray-300">Complete overview of returns, integrations, and performance metrics</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;