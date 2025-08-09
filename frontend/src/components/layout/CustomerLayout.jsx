import React from 'react';
import { Outlet } from 'react-router-dom';
import { Package, ArrowLeft } from 'lucide-react';
import { Button } from '../ui/button';

const CustomerLayout = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Package className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Return Center</h1>
                <p className="text-sm text-gray-500">Easy returns and exchanges</p>
              </div>
            </div>

            {/* Help Link */}
            <Button variant="ghost" size="sm">
              Need Help?
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Outlet />
      </div>

      {/* Footer */}
      <footer className="mt-16 py-8 border-t bg-white">
        <div className="max-w-4xl mx-auto px-4 text-center text-sm text-gray-500">
          <p>© 2024 Return Center. All rights reserved.</p>
          <div className="mt-2 space-x-6">
            <a href="#" className="hover:text-gray-700">Privacy Policy</a>
            <a href="#" className="hover:text-gray-700">Terms of Service</a>
            <a href="#" className="hover:text-gray-700">Contact Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default CustomerLayout;