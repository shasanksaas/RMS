import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { authService } from '../../services/authService';

const GoogleCallback: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState<string>('Processing Google authentication...');
  const [userInfo, setUserInfo] = useState<any>(null);

  useEffect(() => {
    handleGoogleCallback();
  }, []);

  const handleGoogleCallback = async () => {
    try {
      // Get authorization code from URL
      const code = searchParams.get('code');
      const error = searchParams.get('error');
      const state = searchParams.get('state');

      // Handle OAuth errors
      if (error) {
        console.error('Google OAuth error:', error);
        setStatus('error');
        
        switch (error) {
          case 'access_denied':
            setMessage('Google authentication was cancelled. You can try again if needed.');
            break;
          case 'invalid_request':
            setMessage('Invalid authentication request. Please try logging in again.');
            break;
          default:
            setMessage(`Google authentication failed: ${error}`);
        }
        return;
      }

      // Check for authorization code
      if (!code) {
        setStatus('error');
        setMessage('No authorization code received from Google. Please try again.');
        return;
      }

      // Parse state parameter
      let stateData: any = {};
      if (state) {
        try {
          stateData = JSON.parse(atob(state));
        } catch (e) {
          console.error('Failed to parse state parameter:', e);
        }
      }

      const tenantId = stateData.tenant_id || 'tenant-rms34';
      const returnUrl = stateData.return_url || '/dashboard';

      console.log('🔄 Processing Google OAuth callback with code:', code.substring(0, 10) + '...');

      // Exchange code for tokens with backend
      const tokenResponse = await authService.googleOAuthLogin({
        tenant_id: tenantId,
        auth_code: code,
        role: 'customer' // Default role, can be adjusted based on business logic
      });

      // Store authentication data
      localStorage.setItem('auth_token', tokenResponse.access_token);
      localStorage.setItem('currentTenant', tenantId);
      if (tokenResponse.refresh_token) {
        localStorage.setItem('refresh_token', tokenResponse.refresh_token);
      }
      localStorage.setItem('user_info', JSON.stringify(tokenResponse.user));

      // Update component state
      setUserInfo(tokenResponse.user);
      setStatus('success');
      setMessage(`Welcome, ${tokenResponse.user.first_name || tokenResponse.user.email}!`);

      // Redirect after a short delay
      setTimeout(() => {
        const redirectPath = getRedirectPath(tokenResponse.user.role, returnUrl);
        navigate(redirectPath, { replace: true });
      }, 2000);

    } catch (error: any) {
      console.error('❌ Google OAuth callback error:', error);
      setStatus('error');
      
      if (error.status === 400) {
        setMessage('Invalid Google authentication code. Please try logging in again.');
      } else if (error.status === 409) {
        setMessage('An account with this email already exists. Please use a different Google account or try email login.');
      } else if (error.status === 403) {
        setMessage('Your Google account is not authorized to access this tenant. Please contact your administrator.');
      } else if (error.message) {
        setMessage(`Authentication failed: ${error.message}`);
      } else {
        setMessage('Google authentication failed. Please try again or use email login.');
      }
    }
  };

  const getRedirectPath = (role: string, returnUrl: string): string => {
    // Use return URL if valid
    if (returnUrl && returnUrl !== '/dashboard') {
      return returnUrl;
    }

    // Default redirect based on role
    switch (role) {
      case 'merchant':
        return '/app/dashboard';
      case 'admin':
        return '/admin/dashboard';
      case 'customer':
        return '/returns/start';
      default:
        return '/dashboard';
    }
  };

  const handleRetry = () => {
    navigate('/auth/login', { replace: true });
  };

  const handleGoToApp = () => {
    const redirectPath = userInfo ? getRedirectPath(userInfo.role, '/dashboard') : '/dashboard';
    navigate(redirectPath, { replace: true });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md">
        <Card className="shadow-lg border-0">
          <CardHeader className="text-center pb-4">
            <div className="mx-auto mb-4 w-16 h-16 rounded-full flex items-center justify-center">
              {status === 'loading' && (
                <div className="bg-blue-100">
                  <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
                </div>
              )}
              {status === 'success' && (
                <div className="bg-green-100">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
              )}
              {status === 'error' && (
                <div className="bg-red-100">
                  <XCircle className="h-8 w-8 text-red-600" />
                </div>
              )}
            </div>
            
            <CardTitle className="text-xl sm:text-2xl">
              {status === 'loading' && 'Authenticating...'}
              {status === 'success' && 'Welcome!'}
              {status === 'error' && 'Authentication Failed'}
            </CardTitle>
            
            <CardDescription className="text-sm sm:text-base">
              {status === 'loading' && 'Please wait while we verify your Google account'}
              {status === 'success' && 'You have been successfully authenticated'}
              {status === 'error' && 'We encountered an issue during authentication'}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4 pt-2">
            {/* Status Message */}
            <Alert variant={status === 'error' ? 'destructive' : 'default'} className="text-sm">
              <AlertDescription>{message}</AlertDescription>
            </Alert>

            {/* User Info (Success) */}
            {status === 'success' && userInfo && (
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex items-center space-x-3">
                  {userInfo.profile_image_url && (
                    <img 
                      src={userInfo.profile_image_url} 
                      alt="Profile" 
                      className="w-10 h-10 rounded-full"
                    />
                  )}
                  <div>
                    <p className="font-medium text-sm">
                      {userInfo.full_name || userInfo.first_name || userInfo.email}
                    </p>
                    <p className="text-xs text-gray-600">{userInfo.email}</p>
                    <p className="text-xs text-gray-500 capitalize">{userInfo.role}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {status === 'loading' && (
              <div className="text-center py-4">
                <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Verifying your account...</span>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              {status === 'success' && (
                <>
                  <Button 
                    onClick={handleGoToApp}
                    className="flex-1 h-11 text-sm font-medium"
                  >
                    Continue to App
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => navigate('/auth/login')}
                    className="flex-1 h-11 text-sm"
                  >
                    Login Page
                  </Button>
                </>
              )}

              {status === 'error' && (
                <>
                  <Button 
                    onClick={handleRetry}
                    className="flex-1 h-11 text-sm font-medium"
                  >
                    Try Again
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => navigate('/auth/login')}
                    className="flex-1 h-11 text-sm"
                  >
                    Use Email Login
                  </Button>
                </>
              )}
            </div>

            {/* Additional Help */}
            {status === 'error' && (
              <div className="text-center pt-4">
                <p className="text-xs text-gray-500">
                  If you continue to have issues, please{' '}
                  <Button 
                    variant="link" 
                    className="p-0 h-auto text-xs text-blue-600 hover:text-blue-700"
                    onClick={() => window.location.href = 'mailto:support@returns-manager.com'}
                  >
                    contact support
                  </Button>
                </p>
              </div>
            )}

            {/* Auto-redirect notice */}
            {status === 'success' && (
              <div className="text-center">
                <p className="text-xs text-gray-500">
                  You will be redirected automatically in a moment...
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Security Notice */}
        <div className="text-center mt-6">
          <p className="text-xs text-gray-500">
            Your authentication is secured with Google OAuth 2.0
          </p>
        </div>
      </div>
    </div>
  );
};

export default GoogleCallback;