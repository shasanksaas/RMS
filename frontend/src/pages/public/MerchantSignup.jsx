import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Store, 
  User, 
  Mail, 
  Lock, 
  Eye, 
  EyeOff, 
  Building2,
  CheckCircle,
  AlertCircle,
  ArrowRight
} from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { useToast } from '../../components/ui/use-toast';
import TenantStatusBadge from '../../components/tenant/TenantStatusBadge';

import { tenantService } from '../../services/tenantService';
import { useAuth } from '../../contexts/AuthContext';

const MerchantSignup = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const { isAuthenticated, user } = useAuth();

  // Form state
  const [formData, setFormData] = useState({
    tenant_id: searchParams.get('tenant_id') || '',
    email: '',
    password: '',
    confirm_password: '',
    first_name: '',
    last_name: '',
    store_name: ''
  });

  // UI state
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [tenantInfo, setTenantInfo] = useState(null);
  const [tenantStatus, setTenantStatus] = useState(null);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      const redirectPath = user.role === 'merchant' ? '/app/dashboard' 
                         : user.role === 'admin' ? '/admin/dashboard' 
                         : '/returns/start';
      navigate(redirectPath);
    }
  }, [isAuthenticated, user, navigate]);

  // Validate tenant_id when it changes
  useEffect(() => {
    if (formData.tenant_id.trim()) {
      validateTenantId(formData.tenant_id.trim());
    } else {
      setTenantInfo(null);
      setTenantStatus(null);
    }
  }, [formData.tenant_id]);

  const validateTenantId = async (tenantId) => {
    if (!tenantService.validateTenantId(tenantId)) {
      setTenantStatus({ valid: false, message: 'Invalid Tenant ID format' });
      return;
    }

    try {
      setTenantStatus({ valid: true, message: 'Checking...' });
      
      // Check tenant status
      const status = await tenantService.checkTenantStatus(tenantId);
      setTenantStatus(status);

      // Get tenant info for signup customization
      if (status.valid && status.available) {
        try {
          const info = await tenantService.getTenantSignupInfo(tenantId);
          setTenantInfo(info);
          
          // Pre-fill store name if available
          if (info.store_name && !formData.store_name) {
            setFormData(prev => ({
              ...prev,
              store_name: info.store_name
            }));
          }
        } catch (error) {
          console.warn('Failed to get tenant info:', error);
        }
      }
    } catch (error) {
      console.error('Tenant validation error:', error);
      setTenantStatus({ 
        valid: false, 
        available: false, 
        message: 'Unable to verify Tenant ID' 
      });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear errors for the field being edited
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Tenant ID validation
    if (!formData.tenant_id.trim()) {
      newErrors.tenant_id = 'Tenant ID is required';
    } else if (!tenantService.validateTenantId(formData.tenant_id)) {
      newErrors.tenant_id = 'Invalid Tenant ID format';
    } else if (!tenantStatus?.valid || !tenantStatus?.available) {
      newErrors.tenant_id = tenantStatus?.message || 'Invalid Tenant ID';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number';
    }

    // Confirm password validation
    if (!formData.confirm_password) {
      newErrors.confirm_password = 'Please confirm your password';
    } else if (formData.password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
    }

    // Name validation
    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const signupData = {
        tenant_id: formData.tenant_id.trim(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
        confirm_password: formData.confirm_password,
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        store_name: formData.store_name.trim() || undefined
      };

      const response = await tenantService.merchantSignup(signupData);
      
      // Store authentication data
      localStorage.setItem('auth_token', response.data.access_token);
      localStorage.setItem('currentTenant', response.tenant_id);
      if (response.data.refresh_token) {
        localStorage.setItem('refresh_token', response.data.refresh_token);
      }
      localStorage.setItem('user_info', JSON.stringify(response.data.user));

      // Success toast
      toast({
        title: "Account Created Successfully!",
        description: (
          <div>
            <p>Welcome to your returns management dashboard!</p>
            {response.is_first_merchant && (
              <p className="mt-1 font-semibold">🎉 You're the first merchant for this store!</p>
            )}
          </div>
        ),
        variant: "default"
      });

      // Redirect to appropriate dashboard
      const redirectUrl = response.redirect_url || '/app/dashboard';
      navigate(redirectUrl, { replace: true });
      
    } catch (error) {
      console.error('Signup error:', error);
      
      let errorMessage = 'Account creation failed. Please try again.';
      
      if (error.message.includes('already exists')) {
        errorMessage = 'An account with this email already exists. Please try logging in instead.';
        setErrors({ email: 'This email is already registered' });
      } else if (error.message.includes('not found')) {
        errorMessage = 'Tenant ID not found. Please check and try again.';
        setErrors({ tenant_id: 'Tenant ID not found' });
      } else if (error.message.includes('not accepting')) {
        errorMessage = 'This tenant is not accepting new signups.';
        setErrors({ tenant_id: 'Signup not available for this tenant' });
      }

      toast({
        title: "Signup Failed",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const getTenantStatusIndicator = () => {
    if (!formData.tenant_id.trim()) return null;

    if (!tenantStatus) {
      return (
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full" />
          <span className="text-sm">Checking...</span>
        </div>
      );
    }

    if (tenantStatus.valid && tenantStatus.available) {
      return (
        <div className="flex items-center space-x-2 text-green-600">
          <CheckCircle className="h-4 w-4" />
          <span className="text-sm">Tenant ID verified</span>
          {tenantStatus.tenant_name && (
            <span className="text-sm text-gray-600">• {tenantStatus.tenant_name}</span>
          )}
        </div>
      );
    } else {
      return (
        <div className="flex items-center space-x-2 text-red-600">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">{tenantStatus.message}</span>
        </div>
      );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Store className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Join as Merchant
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            Create your merchant account to manage returns
          </p>
        </div>

        {/* Tenant Info Card */}
        {tenantInfo && (
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <Building2 className="h-8 w-8 text-blue-600" />
                <div>
                  <h3 className="font-semibold text-blue-900">{tenantInfo.tenant_name}</h3>
                  <p className="text-sm text-blue-700">Joining this store</p>
                </div>
              </div>
              {tenantInfo.custom_message && (
                <p className="mt-3 text-sm text-blue-800">{tenantInfo.custom_message}</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Signup Form */}
        <Card className="shadow-lg border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg sm:text-xl text-center">Create Account</CardTitle>
            <CardDescription className="text-center text-sm">
              Fill in your details to get started
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4 pt-2">
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Tenant ID Field */}
              <div className="space-y-2">
                <Label htmlFor="tenant_id" className="text-sm font-medium">
                  Tenant ID *
                </Label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="tenant_id"
                    name="tenant_id"
                    type="text"
                    placeholder="tenant-your-store-id"
                    value={formData.tenant_id}
                    onChange={handleInputChange}
                    className={`pl-10 h-11 text-sm font-mono ${errors.tenant_id ? 'border-red-500' : ''}`}
                    disabled={loading}
                    required
                  />
                </div>
                {getTenantStatusIndicator()}
                {errors.tenant_id && (
                  <p className="text-sm text-red-600 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-1" />
                    {errors.tenant_id}
                  </p>
                )}
              </div>

              {/* Name Fields */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="first_name" className="text-sm font-medium">
                    First Name *
                  </Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="first_name"
                      name="first_name"
                      type="text"
                      placeholder="John"
                      value={formData.first_name}
                      onChange={handleInputChange}
                      className={`pl-10 h-11 text-sm ${errors.first_name ? 'border-red-500' : ''}`}
                      disabled={loading}
                      required
                    />
                  </div>
                  {errors.first_name && (
                    <p className="text-xs text-red-600">{errors.first_name}</p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="last_name" className="text-sm font-medium">
                    Last Name *
                  </Label>
                  <Input
                    id="last_name"
                    name="last_name"
                    type="text"
                    placeholder="Doe"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    className={`h-11 text-sm ${errors.last_name ? 'border-red-500' : ''}`}
                    disabled={loading}
                    required
                  />
                  {errors.last_name && (
                    <p className="text-xs text-red-600">{errors.last_name}</p>
                  )}
                </div>
              </div>

              {/* Email Field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium">
                  Email Address *
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
                    className={`pl-10 h-11 text-sm ${errors.email ? 'border-red-500' : ''}`}
                    disabled={loading}
                    required
                  />
                </div>
                {errors.email && (
                  <p className="text-sm text-red-600 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-1" />
                    {errors.email}
                  </p>
                )}
              </div>

              {/* Store Name Field */}
              <div className="space-y-2">
                <Label htmlFor="store_name" className="text-sm font-medium">
                  Store Name <span className="text-gray-400">(optional)</span>
                </Label>
                <div className="relative">
                  <Store className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="store_name"
                    name="store_name"
                    type="text"
                    placeholder="Your Store Name"
                    value={formData.store_name}
                    onChange={handleInputChange}
                    className="pl-10 h-11 text-sm"
                    disabled={loading}
                  />
                </div>
              </div>

              {/* Password Fields */}
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium">
                    Password *
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Create a strong password"
                      value={formData.password}
                      onChange={handleInputChange}
                      className={`pl-10 pr-10 h-11 text-sm ${errors.password ? 'border-red-500' : ''}`}
                      disabled={loading}
                      required
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="text-sm text-red-600 flex items-center">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      {errors.password}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm_password" className="text-sm font-medium">
                    Confirm Password *
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="confirm_password"
                      name="confirm_password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      placeholder="Confirm your password"
                      value={formData.confirm_password}
                      onChange={handleInputChange}
                      className={`pl-10 pr-10 h-11 text-sm ${errors.confirm_password ? 'border-red-500' : ''}`}
                      disabled={loading}
                      required
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {errors.confirm_password && (
                    <p className="text-sm text-red-600 flex items-center">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      {errors.confirm_password}
                    </p>
                  )}
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                size="lg"
                className="w-full h-11 text-sm sm:text-base font-medium"
                disabled={loading || !tenantStatus?.valid || !tenantStatus?.available}
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
                    Creating Account...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    Create Merchant Account
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </div>
                )}
              </Button>
            </form>

            {/* Login Link */}
            <div className="text-center pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => navigate('/auth/login')}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                  disabled={loading}
                >
                  Sign in here
                </button>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            By creating an account, you agree to our terms of service and privacy policy
          </p>
        </div>
      </div>
    </div>
  );
};

export default MerchantSignup;