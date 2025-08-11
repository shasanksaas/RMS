import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, Building2, User, UserCheck } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { useToast } from '../ui/use-toast';
import { authService } from '../../services/authService';

interface RegisterFormData {
  tenantId: string;
  email: string;
  password: string;
  confirmPassword: string;
  role: 'customer' | 'merchant' | 'admin';
  firstName: string;
  lastName: string;
}

const Register: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const [formData, setFormData] = useState<RegisterFormData>({
    tenantId: searchParams.get('tenant') || 'tenant-rms34',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'customer',
    firstName: '',
    lastName: ''
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState<{
    score: number;
    feedback: string[];
  }>({ score: 0, feedback: [] });

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  // Password strength checker
  useEffect(() => {
    if (formData.password) {
      const strength = checkPasswordStrength(formData.password);
      setPasswordStrength(strength);
    } else {
      setPasswordStrength({ score: 0, feedback: [] });
    }
  }, [formData.password]);

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle role selection
  const handleRoleChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      role: value as 'customer' | 'merchant' | 'admin'
    }));
  };

  // Password strength checker
  const checkPasswordStrength = (password: string) => {
    let score = 0;
    const feedback: string[] = [];

    if (password.length >= 8) score += 1;
    else feedback.push('At least 8 characters');

    if (/[A-Z]/.test(password)) score += 1;
    else feedback.push('One uppercase letter');

    if (/[a-z]/.test(password)) score += 1;
    else feedback.push('One lowercase letter');

    if (/\d/.test(password)) score += 1;
    else feedback.push('One number');

    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    else feedback.push('One special character');

    return { score, feedback };
  };

  // Get password strength color and text
  const getPasswordStrengthInfo = () => {
    const { score } = passwordStrength;
    if (score < 2) return { color: 'text-red-600', text: 'Weak', bgColor: 'bg-red-600' };
    if (score < 3) return { color: 'text-orange-600', text: 'Fair', bgColor: 'bg-orange-600' };
    if (score < 4) return { color: 'text-yellow-600', text: 'Good', bgColor: 'bg-yellow-600' };
    if (score < 5) return { color: 'text-blue-600', text: 'Strong', bgColor: 'bg-blue-600' };
    return { color: 'text-green-600', text: 'Very Strong', bgColor: 'bg-green-600' };
  };

  // Handle registration
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    if (!formData.tenantId.trim()) {
      setError('Tenant ID is required');
      return;
    }

    if (!formData.email.trim()) {
      setError('Email is required');
      return;
    }

    if (!formData.firstName.trim()) {
      setError('First name is required');
      return;
    }

    if (!formData.lastName.trim()) {
      setError('Last name is required');
      return;
    }

    if (!formData.password.trim()) {
      setError('Password is required');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    // Password strength validation
    if (passwordStrength.score < 3) {
      setError('Please choose a stronger password');
      return;
    }

    setIsLoading(true);

    try {
      const user = await authService.register({
        tenant_id: formData.tenantId,
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirmPassword,
        role: formData.role,
        first_name: formData.firstName,
        last_name: formData.lastName,
        auth_provider: 'email'
      });

      // Show success message
      toast({
        title: "Registration Successful",
        description: `Welcome ${user.first_name}! Your account has been created successfully.`,
        variant: "default"
      });

      // Auto-login after registration
      try {
        const tokenResponse = await authService.login({
          tenant_id: formData.tenantId,
          email: formData.email,
          password: formData.password,
          remember_me: false
        });

        // Store tokens and user info
        localStorage.setItem('auth_token', tokenResponse.access_token);
        localStorage.setItem('currentTenant', formData.tenantId);
        localStorage.setItem('user_info', JSON.stringify(tokenResponse.user));

        // Navigate based on user role
        const redirectPath = getRedirectPath(tokenResponse.user.role);
        navigate(redirectPath, { replace: true });

      } catch (loginError) {
        // Registration succeeded but auto-login failed
        console.error('Auto-login failed:', loginError);
        navigate('/auth/login?message=Please log in with your new account', { replace: true });
      }

    } catch (error: any) {
      console.error('Registration error:', error);
      
      if (error.status === 409) {
        setError('An account with this email already exists. Please try logging in instead.');
      } else if (error.status === 400) {
        setError(error.message || 'Invalid registration data. Please check your inputs.');
      } else if (error.message) {
        setError(error.message);
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Google OAuth registration
  const handleGoogleRegister = async () => {
    setError('');
    setIsGoogleLoading(true);

    try {
      // Construct Google OAuth URL with registration context
      const googleAuthUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
      googleAuthUrl.searchParams.set('client_id', '286821938662-8jjcepu96llg0v1g6maskbptmp34o15u.apps.googleusercontent.com');
      googleAuthUrl.searchParams.set('redirect_uri', window.location.origin + '/auth/google/callback');
      googleAuthUrl.searchParams.set('response_type', 'code');
      googleAuthUrl.searchParams.set('scope', 'openid email profile');
      googleAuthUrl.searchParams.set('access_type', 'offline');
      googleAuthUrl.searchParams.set('prompt', 'consent');
      
      // Include tenant, role, and return URL in state
      const state = btoa(JSON.stringify({
        tenant_id: formData.tenantId,
        role: formData.role,
        return_url: searchParams.get('return_url') || '/dashboard',
        action: 'register'
      }));
      googleAuthUrl.searchParams.set('state', state);

      // Redirect to Google OAuth
      window.location.href = googleAuthUrl.toString();

    } catch (error: any) {
      console.error('Google OAuth registration error:', error);
      setError('Google registration failed. Please try again.');
      setIsGoogleLoading(false);
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
        return '/admin/dashboard';
      case 'customer':
        return '/returns/start';
      default:
        return '/dashboard';
    }
  };

  const strengthInfo = getPasswordStrengthInfo();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Building2 className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Create Account
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            Join our returns management platform
          </p>
        </div>

        {/* Register Card */}
        <Card className="shadow-lg border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg sm:text-xl text-center">Sign Up</CardTitle>
            <CardDescription className="text-center text-sm">
              Create your account to get started
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4 pt-2">
            {/* Error Alert */}
            {error && (
              <Alert variant="destructive" className="text-sm">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Google OAuth Button */}
            <Button
              type="button"
              variant="outline"
              size="lg"
              className="w-full relative h-11 text-sm sm:text-base"
              onClick={handleGoogleRegister}
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
                  Sign up with Google
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

            {/* Registration Form */}
            <form onSubmit={handleRegister} className="space-y-4">
              {/* Tenant ID and Role Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

                {/* Role Field */}
                <div className="space-y-2">
                  <Label htmlFor="role" className="text-sm font-medium">
                    Account Type
                  </Label>
                  <Select
                    value={formData.role}
                    onValueChange={handleRoleChange}
                    disabled={isLoading || isGoogleLoading}
                  >
                    <SelectTrigger className="h-11 text-sm">
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="customer">
                        <div className="flex items-center">
                          <User className="h-4 w-4 mr-2" />
                          Customer
                        </div>
                      </SelectItem>
                      <SelectItem value="merchant">
                        <div className="flex items-center">
                          <Building2 className="h-4 w-4 mr-2" />
                          Merchant
                        </div>
                      </SelectItem>
                      <SelectItem value="admin">
                        <div className="flex items-center">
                          <UserCheck className="h-4 w-4 mr-2" />
                          Admin
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Name Fields Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* First Name Field */}
                <div className="space-y-2">
                  <Label htmlFor="firstName" className="text-sm font-medium">
                    First Name
                  </Label>
                  <Input
                    id="firstName"
                    name="firstName"
                    type="text"
                    placeholder="John"
                    value={formData.firstName}
                    onChange={handleInputChange}
                    className="h-11 text-sm"
                    disabled={isLoading || isGoogleLoading}
                    required
                  />
                </div>

                {/* Last Name Field */}
                <div className="space-y-2">
                  <Label htmlFor="lastName" className="text-sm font-medium">
                    Last Name
                  </Label>
                  <Input
                    id="lastName"
                    name="lastName"
                    type="text"
                    placeholder="Doe"
                    value={formData.lastName}
                    onChange={handleInputChange}
                    className="h-11 text-sm"
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
                    placeholder="Create a strong password"
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
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>

                {/* Password Strength Indicator */}
                {formData.password && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600">Password strength:</span>
                      <span className={strengthInfo.color}>{strengthInfo.text}</span>
                    </div>
                    <div className="flex space-x-1">
                      {[1, 2, 3, 4, 5].map((level) => (
                        <div
                          key={level}
                          className={`h-1 flex-1 rounded-full ${
                            level <= passwordStrength.score
                              ? strengthInfo.bgColor
                              : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                    {passwordStrength.feedback.length > 0 && (
                      <p className="text-xs text-gray-600">
                        Missing: {passwordStrength.feedback.join(', ')}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Confirm Password Field */}
              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-sm font-medium">
                  Confirm Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className="pl-10 pr-10 h-11 text-sm"
                    disabled={isLoading || isGoogleLoading}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none"
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                size="lg"
                className="w-full h-11 text-sm sm:text-base font-medium"
                disabled={isLoading || isGoogleLoading || passwordStrength.score < 3}
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
                    Creating Account...
                  </div>
                ) : (
                  'Create Account'
                )}
              </Button>
            </form>

            {/* Sign In Link */}
            <div className="text-center pt-4">
              <p className="text-xs sm:text-sm text-gray-600">
                Already have an account?{' '}
                <Button 
                  type="button"
                  variant="link" 
                  className="p-0 h-auto text-xs sm:text-sm font-medium text-blue-600 hover:text-blue-700"
                  onClick={() => navigate('/auth/login')}
                  disabled={isLoading || isGoogleLoading}
                >
                  Sign in here
                </Button>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            By creating an account, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;