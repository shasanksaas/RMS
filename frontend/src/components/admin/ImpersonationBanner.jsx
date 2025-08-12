import React from 'react';
import { X, Shield, User, LogOut } from 'lucide-react';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { tenantService } from '../../services/tenantService';

const ImpersonationBanner = ({ tenantId, tenantName, onExit }) => {
  const handleExitImpersonation = async () => {
    try {
      await tenantService.endImpersonation();
      if (onExit) {
        onExit();
      }
    } catch (error) {
      console.error('Failed to exit impersonation:', error);
      // Force redirect to admin panel even if API call fails
      window.location.href = '/admin/tenants';
    }
  };

  return (
    <div className="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0">
            <Shield className="h-5 w-5 text-orange-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-orange-800">
              Admin Impersonation Active
            </p>
            <p className="text-sm text-orange-700">
              You are viewing as <strong>{tenantName || tenantId}</strong> ({tenantId})
            </p>
          </div>
        </div>
        <Button
          onClick={handleExitImpersonation}
          variant="outline"
          size="sm"
          className="text-orange-800 border-orange-300 hover:bg-orange-100"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Exit Impersonation
        </Button>
      </div>
    </div>
  );
};

export default ImpersonationBanner;