import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Store, Mail } from 'lucide-react';

const DualPathLogin: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'shopify' | 'email'>('shopify');
  const [shopDomain, setShopDomain] = useState('');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            🚀 DUAL-PATH LOGIN WORKING! 🚀
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            Choose your sign-in method
          </p>
        </div>

        {/* Login Card with Tabs */}
        <Card className="shadow-lg border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg sm:text-xl text-center">Welcome Back</CardTitle>
            <CardDescription className="text-center text-sm">
              Choose your preferred sign-in method
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4 pt-2">
            {/* Tab Navigation */}
            <div className="flex rounded-lg bg-gray-100 p-1 mb-6">
              <button
                type="button"
                onClick={() => setActiveTab('shopify')}
                className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-all ${
                  activeTab === 'shopify'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <Store className="h-4 w-4" />
                  Connect with Shopify
                </div>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('email')}
                className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-all ${
                  activeTab === 'email'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <Mail className="h-4 w-4" />
                  Login with Email
                </div>
              </button>
            </div>

            {/* Shopify Tab */}
            {activeTab === 'shopify' && (
              <div className="space-y-4">
                <div className="text-center space-y-2 mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Connect Your Shopify Store</h3>
                  <p className="text-sm text-gray-600">
                    Enter your shop domain to connect your store
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="shopDomain" className="text-sm font-medium text-gray-700">
                    Shop Domain
                  </Label>
                  <Input
                    id="shopDomain"
                    type="text"
                    placeholder="your-store.myshopify.com"
                    value={shopDomain}
                    onChange={(e) => setShopDomain(e.target.value)}
                    className="w-full h-11 text-sm"
                  />
                </div>

                <Button
                  disabled={!shopDomain.trim()}
                  className="w-full bg-[#95bf47] hover:bg-[#7ba337] text-white font-medium h-11 text-sm sm:text-base"
                  size="lg"
                >
                  Continue with Shopify
                </Button>
              </div>
            )}

            {/* Email Tab */}
            {activeTab === 'email' && (
              <div className="space-y-4">
                <div className="text-center space-y-2 mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Sign In with Email</h3>
                  <p className="text-sm text-gray-600">
                    Use your email and password to access your account
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">
                    Email Address
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    className="h-11 text-sm"
                  />
                </div>

                <Button
                  className="w-full h-11 text-sm sm:text-base font-medium"
                >
                  Sign In
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DualPathLogin;