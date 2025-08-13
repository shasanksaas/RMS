import React, { useState } from 'react';
import { X, Store, AlertCircle, Copy } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { useToast } from '../ui/use-toast';
import { tenantService } from '../../services/tenantService';

const CreateTenantModal = ({ isOpen, onClose, onCreate }) => {
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    name: '',
    tenant_id: '',
    email: '',
    password: '',
    confirmPassword: '',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [isCustomId, setIsCustomId] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Auto-generate tenant_id when name changes (unless custom ID is being used)
    if (name === 'name' && !isCustomId && value.trim()) {
      const suggestedId = tenantService.generateTenantId(value);
      setFormData(prev => ({
        ...prev,
        tenant_id: suggestedId
      }));
    }

    // Clear errors for the field being edited
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleTenantIdChange = (e) => {
    const value = e.target.value;
    setIsCustomId(true);
    setFormData(prev => ({
      ...prev,
      tenant_id: value
    }));
    
    if (errors.tenant_id) {
      setErrors(prev => ({
        ...prev,
        tenant_id: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Store name is required';
    }

    if (!formData.tenant_id.trim()) {
      newErrors.tenant_id = 'Tenant ID is required';
    } else if (!tenantService.validateTenantId(formData.tenant_id)) {
      newErrors.tenant_id = 'Tenant ID must start with "tenant-" and contain only lowercase letters, numbers, and hyphens';
    } else if (formData.tenant_id.length < 8 || formData.tenant_id.length > 50) {
      newErrors.tenant_id = 'Tenant ID must be between 8 and 50 characters';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password.trim()) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    // Confirm password validation
    if (!formData.confirmPassword.trim()) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
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
      const tenantData = {
        name: formData.name.trim(),
        tenant_id: formData.tenant_id.trim(),
        notes: formData.notes.trim() || undefined
      };

      await onCreate(tenantData);
      
      // Reset form
      setFormData({
        name: '',
        tenant_id: '',
        notes: ''
      });
      setIsCustomId(false);
      setErrors({});
      
    } catch (error) {
      console.error('Create tenant error:', error);
      
      // Handle specific error cases
      if (error.message.includes('already exists') || error.message.includes('duplicate')) {
        setErrors({ tenant_id: 'This Tenant ID is already taken. Please choose a different one.' });
      } else {
        toast({
          title: "Failed to create tenant",
          description: error.message || "Please try again",
          variant: "destructive"
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const copyTenantId = () => {
    if (formData.tenant_id) {
      navigator.clipboard.writeText(formData.tenant_id);
      toast({
        title: "Copied!",
        description: "Tenant ID copied to clipboard",
        variant: "default"
      });
    }
  };

  const generateNewId = () => {
    const newId = tenantService.generateTenantId(formData.name || 'store');
    setFormData(prev => ({
      ...prev,
      tenant_id: newId
    }));
    setIsCustomId(false);
    if (errors.tenant_id) {
      setErrors(prev => ({
        ...prev,
        tenant_id: ''
      }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-screen overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Store className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Create New Tenant</h2>
              <p className="text-sm text-gray-600">Set up a new store for merchant signup</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Store Name */}
          <div>
            <Label htmlFor="name" className="text-sm font-medium">
              Store Name *
            </Label>
            <Input
              id="name"
              name="name"
              type="text"
              placeholder="e.g., Fashion Forward Store"
              value={formData.name}
              onChange={handleInputChange}
              className={`mt-1 ${errors.name ? 'border-red-500' : ''}`}
              disabled={loading}
            />
            {errors.name && (
              <p className="text-sm text-red-600 mt-1 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.name}
              </p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              This will be displayed to merchants during signup
            </p>
          </div>

          {/* Tenant ID */}
          <div>
            <div className="flex items-center justify-between">
              <Label htmlFor="tenant_id" className="text-sm font-medium">
                Tenant ID *
              </Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={generateNewId}
                  className="text-xs"
                >
                  Generate New
                </Button>
                {formData.tenant_id && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={copyTenantId}
                    className="text-xs"
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    Copy
                  </Button>
                )}
              </div>
            </div>
            <Input
              id="tenant_id"
              name="tenant_id"
              type="text"
              placeholder="tenant-your-store-name"
              value={formData.tenant_id}
              onChange={handleTenantIdChange}
              className={`mt-1 font-mono text-sm ${errors.tenant_id ? 'border-red-500' : ''}`}
              disabled={loading}
            />
            {errors.tenant_id && (
              <p className="text-sm text-red-600 mt-1 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                {errors.tenant_id}
              </p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              This unique ID will be used by merchants to sign up. Must start with "tenant-"
            </p>
          </div>

          {/* Notes */}
          <div>
            <Label htmlFor="notes" className="text-sm font-medium">
              Notes <span className="text-gray-400">(optional)</span>
            </Label>
            <textarea
              id="notes"
              name="notes"
              placeholder="Internal notes about this tenant..."
              value={formData.notes}
              onChange={handleInputChange}
              rows={3}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              These notes are only visible to admins
            </p>
          </div>

          {/* Info Alert */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              <strong>Next steps:</strong> After creating the tenant, share the Tenant ID with merchants so they can sign up using the merchant signup form.
            </AlertDescription>
          </Alert>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="flex-1"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                  Creating...
                </div>
              ) : (
                'Create Tenant'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateTenantModal;