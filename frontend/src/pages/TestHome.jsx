import React from 'react';
import { Link } from 'react-router-dom';
import { Package, Settings, User } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

const TestHome = () => {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">Returns Management System</h1>
        <p className="text-xl text-gray-600">Test the customer return form and exchange feature</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Customer Return Form */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Package className="h-6 w-6 text-blue-600" />
              <span>Customer Return Form</span>
            </CardTitle>
            <CardDescription>
              Test the customer return and exchange flow with real Shopify data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                <strong>Test Orders Available:</strong><br />
                #1001, #1002, #1003, #1004, #1005, #1006
              </p>
              <p className="text-sm text-gray-600">
                <strong>Features:</strong> Exchange with ProductSelector, real-time availability, price calculations
              </p>
            </div>
            <Link to="/returns/simple">
              <Button className="w-full">
                Start Customer Return Flow
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Merchant Dashboard */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-6 w-6 text-green-600" />
              <span>Merchant Dashboard</span>
            </CardTitle>
            <CardDescription>
              View and manage returns, orders, and Shopify integration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                <strong>Features:</strong> Order management, return processing, Shopify sync, policy management
              </p>
            </div>
            <Link to="/auth/shopify">
              <Button variant="outline" className="w-full">
                Login as Merchant
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Quick Test Instructions */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Quick Test Guide</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-blue-800">
          <div className="space-y-2">
            <p><strong>1. Test Customer Return Flow:</strong></p>
            <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
              <li>Click "Start Customer Return Flow"</li>
              <li>Use order #1001 with any email</li>
              <li>Select items to return</li>
              <li>Choose "Exchange" option to test the new feature</li>
              <li>Browse and select replacement products</li>
              <li>See real-time price differences and availability</li>
            </ul>
          </div>
          
          <div className="space-y-2">
            <p><strong>2. Test Merchant Features:</strong></p>
            <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
              <li>Click "Login as Merchant"</li>
              <li>View dashboard with order/return counts</li>
              <li>Check Shopify integration status</li>
              <li>Manage policies and settings</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      <div className="text-center">
        <p className="text-sm text-gray-500">
          This system is connected to live Shopify data with 6 synced orders and 1 return
        </p>
      </div>
    </div>
  );
};

export default TestHome;