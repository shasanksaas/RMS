import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Building2 } from 'lucide-react';
import { authService } from '../../services/authService';
import { useToast } from '../ui/use-toast';

const GoogleCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const [status, setStatus] = useState('processing'); // processing, success, error
  const [message, setMessage] = useState('Processing Google authentication...');

  useEffect(() => {
    const handleGoogleCallback = async () => {
      try {
        // Get authorization code and state from URL
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');

        // Check for OAuth errors
        if (error) {
          throw new Error(`OAuth error: ${error}`);
        }

        if (!code) {
          throw new Error('No authorization code received from Google');
        }

        // Parse state parameter to get tenant_id and other data
        let stateData = {};
        if (state) {
          try {
            stateData = JSON.parse(atob(state));
          } catch (e) {
            console.warn('Could not parse state parameter:', e);
            stateData = { tenant_id: 'tenant-rms34', return_url: '/dashboard' };
          }
        }

        const tenantId = stateData.tenant_id || 'tenant-rms34';
        const returnUrl = stateData.return_url || '/dashboard';
        const action = stateData.action || 'login'; // login or register
        const role = stateData.role || 'customer';

        setMessage('Exchanging authorization code...');

        // Exchange authorization code for user authentication
        const response = await authService.loginWithGoogle({
          tenant_id: tenantId,
          auth_code: code,
          role: action === 'register' ? role : undefined
        });

        // Store authentication data
        localStorage.setItem('auth_token', response.access_token);
        localStorage.setItem('currentTenant', tenantId);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
        localStorage.setItem('user_info', JSON.stringify(response.user));

        setStatus('success');
        setMessage('Authentication successful! Redirecting...');

        // Show success toast
        toast({
          title: "Welcome!",
          description: `Hello ${response.user.first_name || response.user.email}! You've been successfully authenticated with Google.`,
          variant: "success"
        });

        // Determine redirect path based on user role
        let redirectPath = returnUrl;
        if (!returnUrl || returnUrl === '/dashboard') {
          switch (response.user.role) {
            case 'merchant':
              redirectPath = '/app/dashboard';
              break;
            case 'admin':
              redirectPath = '/admin/dashboard';
              break;
            case 'customer':
              redirectPath = '/returns/start';
              break;
            default:
              redirectPath = '/app/dashboard';
          }
        }

        // Redirect after a short delay to show success message
        setTimeout(() => {
          navigate(redirectPath, { replace: true });
        }, 1500);

      } catch (error) {
        console.error('Google OAuth callback error:', error);
        
        setStatus('error');
        setMessage(error.message || 'Authentication failed. Please try again.');

        // Show error toast
        toast({
          title: "Authentication Failed",
          description: error.message || 'Something went wrong with Google authentication. Please try again.',
          variant: "destructive"
        });

        // Redirect to login page after delay
        setTimeout(() => {
          navigate('/auth/login?error=oauth_failed', { replace: true });
        }, 3000);
      }
    };

    handleGoogleCallback();
  }, [searchParams, navigate, toast]);

  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return (
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
        );
      case 'success':
        return (
          <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'error':
        return (
          <div className="h-8 w-8 bg-red-100 rounded-full flex items-center justify-center">
            <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        );
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'processing':
        return 'text-blue-600';
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-lg border-0 p-6 text-center">
          {/* Header */}
          <div className="mb-6">
            <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
              <Building2 className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Google Authentication
            </h1>
          </div>

          {/* Status Display */}
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              {getStatusIcon()}
            </div>
            
            <p className={`text-lg font-medium ${getStatusColor()}`}>
              {status === 'processing' && 'Processing...'}
              {status === 'success' && 'Success!'}
              {status === 'error' && 'Error'}
            </p>
            
            <p className="text-sm text-gray-600 leading-relaxed">
              {message}
            </p>

            {status === 'processing' && (
              <div className="mt-4">
                <div className="flex space-x-1 justify-center">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            )}

            {status === 'error' && (
              <div className="mt-6">
                <button
                  onClick={() => navigate('/auth/login', { replace: true })}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Back to Login
                </button>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Secure authentication powered by Google OAuth 2.0
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GoogleCallback;