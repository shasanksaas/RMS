import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, Building2, Store, ShoppingBag } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { Checkbox } from '../ui/checkbox';
import { useToast } from '../ui/use-toast';
import { useAuth } from '../../contexts/AuthContext';
import { authService } from '../../services/authService';

interface LoginFormData {
  tenantId: string;
  email: string;
  password: string;
  rememberMe: boolean;
}

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const { login: contextLogin, user } = useAuth();

  // Feature flag for OAuth tab visibility (temporarily force enabled for testing)
  const isOAuthTabEnabled = true; // process.env.REACT_APP_LOGIN_OAUTH_TAB_ENABLED === 'true';

  // Active tab state ('shopify' or 'email')
  const [activeTab, setActiveTab] = useState<'shopify' | 'email'>('shopify');

  // Email login form data
  const [formData, setFormData] = useState<LoginFormData>({
    tenantId: searchParams.get('tenant') || 'tenant-rms34',
    email: '',
    password: '',
    rememberMe: false
  });

  // Shopify OAuth form data
  const [shopDomain, setShopDomain] = useState('');

  // UI states
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isShopifyLoading, setIsShopifyLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  // Check if user is already logged in or handle post-login redirect
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token && user) {
      // User is authenticated, redirect based on role
      const redirectPath = getRedirectPath(user.role);
      console.log('🎯 REDIRECTING AUTHENTICATED USER TO:', redirectPath);
      navigate(redirectPath, { replace: true });
    }
  }, [navigate, user]);

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Handle Shopify OAuth login
  const handleShopifyLogin = async (e?: React.MouseEvent) => {
    // Prevent any default browser behavior
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    // Prevent multiple clicks
    if (isShopifyLoading) {
      console.log('🛑 Shopify login already in progress, ignoring click');
      return;
    }
    
    console.log('🔥 SHOPIFY LOGIN BUTTON CLICKED'); // Debug log
    
    if (!shopDomain.trim()) {
      setError('Please enter your shop domain');
      return;
    }

    setIsShopifyLoading(true);
    setError('');

    try {
      // Get backend URL from environment with fallback
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://multi-tenant-rms.preview.emergentagent.com';
      
      console.log('🔍 Backend URL from env:', backendUrl);
      
      // Direct redirect to Shopify OAuth
      const shopifyInstallUrl = `${backendUrl}/api/auth/shopify/install-redirect?shop=${encodeURIComponent(shopDomain.trim())}`;
      
      console.log('🚀 Redirecting to Shopify OAuth:', shopifyInstallUrl);
      
      // Add small delay to ensure state is set
      setTimeout(() => {
        window.location.href = shopifyInstallUrl;
      }, 100);

    } catch (error: any) {
      console.error('❌ Shopify login error:', error);
      setError(`Failed to connect: ${error.message}`);
      setIsShopifyLoading(false);
    }
  };

  // Handle email/password login
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setError('');
    
    console.log('🔥 EMAIL LOGIN ATTEMPT:', formData);
    
    // Client-side validation
    if (!formData.tenantId.trim()) {
      setError('Tenant ID is required');
      return;
    }
    
    if (!formData.email.trim()) {
      setError('Email is required');
      return;
    }
    
    if (!formData.password.trim()) {
      setError('Password is required');
      return;
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);
    
    const loginData = {
      tenant_id: formData.tenantId,
      email: formData.email,
      password: formData.password,
      remember_me: formData.rememberMe
    };

    try {
      console.log('🚀 EMAIL LOGIN ATTEMPT with:', {
        ...loginData,
        password: '***'
      });

      // Use AuthContext login method instead of direct authService call
      await contextLogin(loginData);

      // Show success message
      toast({
        title: "Login Successful",
        description: `Welcome back!`,
        variant: "default"
      });

      // Navigate based on user role will be handled by AuthContext
      
    } catch (error: any) {
      console.error('❌ EMAIL LOGIN ERROR:', error);
      
      let errorMessage = 'Login failed. Please check your connection and try again.';
      
      if (error.status === 401) {
        errorMessage = 'Invalid email or password. Please try again.';
      } else if (error.status === 423) {
        errorMessage = 'Account is temporarily locked. Please try again later.';
      } else if (error.status === 429) {
        errorMessage = 'Too many login attempts. Please try again later.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
      
      toast({
        title: "Login Failed",
        description: errorMessage,
        variant: "destructive"
      });
      
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Google OAuth login
  const handleGoogleLogin = async () => {
    setError('');
    setIsGoogleLoading(true);

    try {
      // Construct Google OAuth URL
      const googleAuthUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
      googleAuthUrl.searchParams.set('client_id', '286821938662-8jjcepu96llg0v1g6maskbptmp34o15u.apps.googleusercontent.com');
      googleAuthUrl.searchParams.set('redirect_uri', window.location.origin + '/auth/google/callback');
      googleAuthUrl.searchParams.set('response_type', 'code');
      googleAuthUrl.searchParams.set('scope', 'openid email profile');
      googleAuthUrl.searchParams.set('access_type', 'offline');
      googleAuthUrl.searchParams.set('prompt', 'consent');
      
      // Include tenant and return URL in state
      const state = btoa(JSON.stringify({
        tenant_id: formData.tenantId,
        return_url: searchParams.get('return_url') || '/dashboard'
      }));
      googleAuthUrl.searchParams.set('state', state);

      // Redirect to Google OAuth
      window.location.href = googleAuthUrl.toString();

    } catch (error: any) {
      console.error('Google OAuth error:', error);
      setError('Google login failed. Please try again.');
      setIsGoogleLoading(false);
    }
  };

  // Handle Shopify domain key press
  const handleShopifyKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleShopifyLogin();
    }
  };

  // Get redirect path based on user role
  const getRedirectPath = (role: string): string => {
    const returnUrl = searchParams.get('return_url');
    if (returnUrl) return returnUrl;

    switch (role) {
      case 'merchant':
        return '/app/dashboard';
      case 'admin':
        return '/admin/tenants';
      case 'customer':
        return '/returns/start';
      default:
        return '/app/dashboard';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Building2 className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Returns Manager
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            Sign in to your returns management platform
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
            {isOAuthTabEnabled && (
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
                    Shopify OAuth
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
            )}

            {/* Error Alert */}
            {error && (
              <Alert variant="destructive" className="text-sm">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Shopify OAuth Tab */}
            {(!isOAuthTabEnabled || activeTab === 'shopify') && (
              <div className="space-y-4">
                <div className="text-center space-y-2 mb-4">
                  <ShoppingBag className="h-8 w-8 text-[#95bf47] mx-auto" />
                  <h3 className="text-lg font-semibold text-gray-900">Connect Your Shopify Store</h3>
                  <p className="text-sm text-gray-600">
                    Enter your shop domain to connect your store and start managing returns
                  </p>
                </div>

                {/* Shop Domain Input */}
                <div className="space-y-2">
                  <Label htmlFor="shopDomain" className="text-sm font-medium text-gray-700">
                    Shop Domain
                  </Label>
                  <Input
                    id="shopDomain"
                    type="text"
                    placeholder="your-store or your-store.myshopify.com"
                    value={shopDomain}
                    onChange={(e) => setShopDomain(e.target.value)}
                    onKeyPress={handleShopifyKeyPress}
                    className="w-full h-11 text-sm"
                    disabled={isShopifyLoading}
                    autoFocus
                  />
                  <p className="text-xs text-gray-500">
                    Enter just the store name (e.g., "rms34") or full domain
                  </p>
                </div>

                {/* Shopify Login Button */}
                <Button
                  type="button"
                  onClick={handleShopifyLogin}
                  disabled={isShopifyLoading || !shopDomain.trim()}
                  className="w-full bg-[#95bf47] hover:bg-[#7ba337] text-white font-medium h-11 text-sm sm:text-base"
                  size="lg"
                >
                  {isShopifyLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
                      Connecting...
                    </div>
                  ) : (
                    <>
                      <svg 
                        className="w-5 h-5 mr-2" 
                        fill="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path d="M15.337 2.447c-.38-.172-.806-.245-1.245-.245-1.93 0-3.713 1.455-4.888 3.32-.852-.398-1.744-.618-2.659-.618C4.53 4.904 3 6.376 3 8.365c0 .532.134 1.047.368 1.516-.698.87-1.113 1.951-1.113 3.119 0 2.756 2.238 4.991 5 4.991h10.5c2.21 0 4-1.787 4-3.99 0-1.657-.896-3.101-2.23-3.879.147-.468.225-.957.225-1.462 0-2.756-2.238-4.991-5-4.991-.63 0-1.234.117-1.795.33-.317-1.146-1.058-2.175-2.106-2.927-.508-.365-1.09-.625-1.712-.625z"/>
                      </svg>
                      Continue with Shopify
                    </>
                  )}
                </Button>

                {/* Help Text for Shopify */}
                <div className="text-center">
                  <p className="text-xs text-gray-500">
                    By connecting, you'll be redirected to Shopify to authorize our app.
                    Your store data will be securely synced for returns management.
                  </p>
                </div>
              </div>
            )}

            {/* Email Login Tab */}
            {(!isOAuthTabEnabled || activeTab === 'email') && (
              <div className="space-y-4">
                {isOAuthTabEnabled && (
                  <div className="text-center space-y-2 mb-4">
                    <Mail className="h-8 w-8 text-blue-600 mx-auto" />
                    <h3 className="text-lg font-semibold text-gray-900">Sign In with Email</h3>
                    <p className="text-sm text-gray-600">
                      Use your email and password to access your account
                    </p>
                  </div>
                )}

                {/* Google OAuth Button */}
                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  className="w-full relative h-11 text-sm sm:text-base"
                  onClick={handleGoogleLogin}
                  disabled={isGoogleLoading || isLoading}
                >
                  {isGoogleLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full mr-2" />
                      Connecting to Google...
                    </div>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                      </svg>
                      Continue with Google
                    </>
                  )}
                </Button>

                {/* Divider */}
                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-white px-3 text-gray-500 font-medium">Or continue with email</span>
                  </div>
                </div>

                {/* Email/Password Form */}
                <form onSubmit={handleEmailLogin} className="space-y-4">
                  <fieldset disabled={isLoading} className="space-y-4">
                    {/* Tenant ID Field */}
                    <div className="space-y-2">
                      <Label htmlFor="tenantId" className="text-sm font-medium">
                        Tenant ID
                      </Label>
                      <div className="relative">
                        <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="tenantId"
                          name="tenantId"
                          type="text"
                          placeholder="tenant-example"
                          value={formData.tenantId}
                          onChange={handleInputChange}
                          className="pl-10 h-11 text-sm"
                          disabled={isLoading || isGoogleLoading}
                          required
                        />
                      </div>
                    </div>

                    {/* Email Field */}
                    <div className="space-y-2">
                      <Label htmlFor="email" className="text-sm font-medium">
                        Email Address
                      </Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          placeholder="you@example.com"
                          value={formData.email}
                          onChange={handleInputChange}
                          className="pl-10 h-11 text-sm"
                          disabled={isLoading || isGoogleLoading}
                          required
                        />
                      </div>
                    </div>

                    {/* Password Field */}
                    <div className="space-y-2">
                      <Label htmlFor="password" className="text-sm font-medium">
                        Password
                      </Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="password"
                          name="password"
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Enter your password"
                          value={formData.password}
                          onChange={handleInputChange}
                          className="pl-10 pr-10 h-11 text-sm"
                          disabled={isLoading || isGoogleLoading}
                          required
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none"
                          disabled={isLoading || isGoogleLoading}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Remember Me & Forgot Password */}
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="rememberMe"
                          name="rememberMe"
                          checked={formData.rememberMe}
                          onCheckedChange={(checked) => 
                            setFormData(prev => ({ ...prev, rememberMe: checked as boolean }))
                          }
                          disabled={isLoading || isGoogleLoading}
                        />
                        <Label htmlFor="rememberMe" className="text-xs sm:text-sm text-gray-600 cursor-pointer">
                          Remember me
                        </Label>
                      </div>
                      
                      <Button 
                        type="button" 
                        variant="link" 
                        className="p-0 h-auto text-xs sm:text-sm text-blue-600 hover:text-blue-700"
                        onClick={() => navigate('/auth/forgot-password')}
                        disabled={isLoading || isGoogleLoading}
                      >
                        Forgot password?
                      </Button>
                    </div>

                    {/* Submit Button */}
                    <Button
                      type="submit"
                      size="lg"
                      className="w-full h-11 text-sm sm:text-base font-medium"
                      disabled={isLoading || isGoogleLoading}
                    >
                      {isLoading ? (
                        <div className="flex items-center justify-center">
                          <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
                          Signing In...
                        </div>
                      ) : (
                        'Sign In'
                      )}
                    </Button>
                  </fieldset>
                </form>

                {/* Sign Up Link */}
                <div className="text-center pt-4">
                  <p className="text-xs sm:text-sm text-gray-600">
                    Don't have an account?{' '}
                    <Button 
                      type="button"
                      variant="link" 
                      className="p-0 h-auto text-xs sm:text-sm font-medium text-blue-600 hover:text-blue-700"
                      onClick={() => navigate('/auth/register')}
                      disabled={isLoading || isGoogleLoading}
                    >
                      Sign up here
                    </Button>
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Secure login protected by enterprise-grade encryption
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;