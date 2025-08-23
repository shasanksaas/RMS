import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Search, ArrowRight, Package, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';

/**
 * TENANT-SPECIFIC RETURN FORM
 * Each tenant gets their own branded return form with:
 * - Custom branding (colors, logo, messaging)
 * - Tenant-specific policies 
 * - Isolated data access
 */
const TenantReturnForm = () => {
  const { tenantId } = useParams(); // From URL: /returns/:tenantId/start
  const navigate = useNavigate();
  const [tenantConfig, setTenantConfig] = useState(null);
  const [isPreview, setIsPreview] = useState(false);
  const [formData, setFormData] = useState({
    orderNumber: '',
    email: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load tenant configuration and branding
  useEffect(() => {
    const loadTenantConfig = async () => {
      try {
        const backendUrl = process.env.REACT_APP_BACKEND_URL;
        
        // Fetch tenant-specific form configuration (public endpoint)
        const response = await fetch(`${backendUrl}/api/tenants/tenant-${tenantId}/form-config/public`);
        
        if (response.ok) {
          const data = await response.json();
          const config = data.config;
          
          // Set tenant configuration from form config
          setTenantConfig({
            name: tenantId.toUpperCase(),
            primaryColor: config.branding?.primary_color || '#3B82F6',
            secondaryColor: config.branding?.secondary_color || '#1F2937',
            backgroundColor: config.branding?.background_color || '#FFFFFF',
            textColor: config.branding?.text_color || '#111827',
            fontFamily: config.branding?.font_family || 'Inter',
            logoUrl: config.branding?.logo_url || null,
            faviconUrl: config.branding?.favicon_url || null,
            supportEmail: 'support@example.com',
            returnPolicy: config.form?.policy_text || 'Standard 30-day return policy applies.',
            layoutPreset: config.layout?.preset || 'wizard',
            cornerRadius: config.layout?.corner_radius || 'medium',
            spacingDensity: config.layout?.spacing_density || 'comfortable',
            customCSS: config.layout?.custom_css || '',
            formConfig: config.form || {}
          });
        } else {
          // Fallback configuration
          setTenantConfig({
            name: tenantId.toUpperCase(),
            primaryColor: '#3B82F6',
            secondaryColor: '#1F2937',
            backgroundColor: '#FFFFFF',
            textColor: '#111827',
            fontFamily: 'Inter',
            logoUrl: null,
            faviconUrl: null,
            supportEmail: 'support@example.com',
            returnPolicy: 'Standard 30-day return policy applies.',
            layoutPreset: 'wizard',
            cornerRadius: 'medium',
            spacingDensity: 'comfortable',
            customCSS: '',
            formConfig: {}
          });
        }
      } catch (err) {
        console.error('Failed to load tenant config:', err);
        // Set fallback configuration
        setTenantConfig({
          name: tenantId.toUpperCase(),
          primaryColor: '#3B82F6',
          secondaryColor: '#1F2937',
          backgroundColor: '#FFFFFF',
          textColor: '#111827',
          fontFamily: 'Inter',
          logoUrl: null,
          faviconUrl: null,
          supportEmail: 'support@example.com',
          returnPolicy: 'Standard 30-day return policy applies.',
          layoutPreset: 'wizard',
          cornerRadius: 'medium',
          spacingDensity: 'comfortable',
          customCSS: '',
          formConfig: {}
        });
      }
    };

    if (tenantId) {
      loadTenantConfig();
    }
  }, [tenantId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      
      // Call tenant-specific orders API
      const response = await fetch(`${backendUrl}/api/orders`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const orders = data.items || [];

      // Find matching order
      const normalizedInput = formData.orderNumber.toLowerCase().trim();
      const matchingOrder = orders.find(order => {
        const orderNum = (order.order_number || '').toLowerCase();
        const orderId = (order.id || '').toLowerCase();
        
        return orderNum === normalizedInput || 
               orderNum === `#${normalizedInput}` ||
               normalizedInput === orderNum.replace('#', '') ||
               orderId === normalizedInput;
      });

      if (matchingOrder) {
        // Navigate to tenant-specific item selection
        navigate(`/returns/${tenantId}/select`, { 
          state: { 
            order: matchingOrder,
            orderNumber: formData.orderNumber, 
            email: formData.email,
            mode: 'tenant_specific',
            tenantId: tenantId,
            tenantConfig: tenantConfig
          } 
        });
      } else {
        const availableOrders = orders.slice(0, 5).map(o => o.order_number).join(', ');
        setError(`Order not found. Available orders: ${availableOrders}`);
      }
    } catch (err) {
      console.error('Order lookup error:', err);
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!tenantConfig) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Apply tenant branding and inject custom CSS
  const brandingStyles = {
    '--primary-color': tenantConfig.primaryColor,
    '--secondary-color': tenantConfig.secondaryColor,
    '--background-color': tenantConfig.backgroundColor,
    '--text-color': tenantConfig.textColor,
    '--font-family': tenantConfig.fontFamily,
    '--corner-radius': tenantConfig.cornerRadius === 'small' ? '4px' : 
                       tenantConfig.cornerRadius === 'large' ? '12px' : '8px',
    '--spacing-density': tenantConfig.spacingDensity === 'compact' ? '0.5rem' : 
                        tenantConfig.spacingDensity === 'spacious' ? '1.5rem' : '1rem'
  };

  // Inject custom CSS if available
  useEffect(() => {
    if (tenantConfig.customCSS) {
      const styleId = `tenant-${tenantId}-custom-styles`;
      let styleElement = document.getElementById(styleId);
      
      if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = styleId;
        document.head.appendChild(styleElement);
      }
      
      styleElement.textContent = tenantConfig.customCSS;
      
      return () => {
        // Cleanup on unmount
        const element = document.getElementById(styleId);
        if (element) {
          element.remove();
        }
      };
    }
  }, [tenantConfig.customCSS, tenantId]);

  return (
    <div 
      className="max-w-2xl mx-auto space-y-6 md:space-y-8 px-4 sm:px-0" 
      style={brandingStyles}
    >
      {/* Tenant-Branded Header */}
      <div className="text-center space-y-4">
        {tenantConfig.logoUrl && (
          <img 
            src={tenantConfig.logoUrl} 
            alt={`${tenantConfig.name} Logo`}
            className="h-16 w-auto mx-auto"
          />
        )}
        <div className="w-12 h-12 md:w-16 md:h-16 rounded-full flex items-center justify-center mx-auto"
             style={{ backgroundColor: `${tenantConfig.primaryColor}20` }}>
          <Package className="h-6 w-6 md:h-8 md:w-8" style={{ color: tenantConfig.primaryColor }} />
        </div>
        <div>
          <h1 className="text-2xl md:text-4xl font-bold text-gray-900 mb-2">
            Start Your Return - {tenantConfig.name}
          </h1>
          <p className="text-lg md:text-xl text-gray-600">
            {tenantConfig.returnPolicy}
          </p>
        </div>
      </div>

      {/* Tenant-Specific Return Form */}
      <Card className="hover:shadow-md transition-shadow" style={{ borderColor: `${tenantConfig.primaryColor}40` }}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-lg md:text-xl">
            <Search className="h-5 w-5 flex-shrink-0" style={{ color: tenantConfig.primaryColor }} />
            <span>Find Your Order</span>
          </CardTitle>
          <CardDescription className="text-sm md:text-base">
            Enter your order number and email address to get started
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="border border-red-300 rounded-md p-3 bg-red-50">
                <div className="flex">
                  <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="ml-2 text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="orderNumber" className="block text-sm md:text-base font-medium mb-2">
                  Order Number
                </label>
                <input
                  id="orderNumber"
                  type="text"
                  placeholder="e.g. #1001, #1002, etc."
                  value={formData.orderNumber}
                  onChange={(e) => setFormData(prev => ({ ...prev, orderNumber: e.target.value }))}
                  required
                  className="w-full h-12 px-3 border border-gray-300 rounded-md focus:ring-2 focus:border-transparent text-base md:text-lg"
                  style={{ 
                    '--tw-ring-color': tenantConfig.primaryColor,
                    'focusRingColor': tenantConfig.primaryColor 
                  }}
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm md:text-base font-medium mb-2">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  required
                  className="w-full h-12 px-3 border border-gray-300 rounded-md focus:ring-2 focus:border-transparent text-base md:text-lg"
                  disabled={loading}
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full h-12 text-base md:text-lg font-medium text-white rounded-md transition-colors flex items-center justify-center"
              style={{ backgroundColor: tenantConfig.primaryColor }}
              disabled={loading || !formData.orderNumber || !formData.email}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Looking up your order...
                </>
              ) : (
                <>
                  Look up order
                  <ArrowRight className="ml-2 h-5 w-5" />
                </>
              )}
            </button>
          </form>
        </CardContent>
      </Card>

      {/* Tenant Contact Info */}
      <div className="text-center text-sm text-gray-500">
        <p>Need help? Contact us at {tenantConfig.supportEmail}</p>
        <p className="mt-1">Tenant ID: {tenantId}</p>
      </div>
    </div>
  );
};

export default TenantReturnForm;