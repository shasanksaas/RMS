import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Building2, ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { useToast } from '../ui/use-toast';

const ForgotPassword = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    tenantId: 'tenant-rms34',
    email: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!formData.tenantId.trim()) {
      setError('Tenant ID is required');
      return;
    }
    
    if (!formData.email.trim()) {
      setError('Email is required');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      // TODO: Implement forgot password API call
      // For now, simulate the request
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setSuccess(true);
      
      toast({
        title: "Reset Link Sent",
        description: "If an account with this email exists, you will receive a password reset link shortly.",
        variant: "default"
      });

    } catch (error) {
      console.error('Forgot password error:', error);
      setError(error.message || 'Failed to send reset link. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center space-y-2">
            <div className="mx-auto w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mb-4">
              <Mail className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
              Check Your Email
            </h1>
            <p className="text-sm sm:text-base text-gray-600">
              We've sent password reset instructions to <strong>{formData.email}</strong>
            </p>
          </div>

          <Card className="shadow-lg border-0">
            <CardContent className="pt-6">
              <div className="space-y-4 text-center">
                <p className="text-sm text-gray-600">
                  If you don't see the email, check your spam folder or try again with a different email address.
                </p>
                
                <div className="space-y-2">
                  <Button
                    onClick={() => navigate('/auth/login')}
                    className="w-full"
                    variant="default"
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Login
                  </Button>
                  
                  <Button
                    onClick={() => {
                      setSuccess(false);
                      setFormData(prev => ({ ...prev, email: '' }));
                    }}
                    variant="outline"
                    className="w-full"
                  >
                    Try Different Email
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Building2 className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Forgot Password
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            Enter your email address and we'll send you a link to reset your password
          </p>
        </div>

        {/* Reset Form Card */}
        <Card className="shadow-lg border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg sm:text-xl text-center">Reset Password</CardTitle>
            <CardDescription className="text-center text-sm">
              We'll email you reset instructions
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4 pt-2">
            {error && (
              <Alert variant="destructive" className="text-sm">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
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
                    disabled={isLoading}
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
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                size="lg"
                className="w-full h-11 text-sm sm:text-base font-medium"
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
                    Sending Reset Link...
                  </div>
                ) : (
                  'Send Reset Link'
                )}
              </Button>
            </form>

            {/* Back to Login */}
            <div className="text-center pt-4">
              <Button 
                type="button"
                variant="link" 
                className="p-0 h-auto text-sm text-blue-600 hover:text-blue-700"
                onClick={() => navigate('/auth/login')}
                disabled={isLoading}
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back to Login
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Secure password reset powered by enterprise-grade encryption
          </p>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;