import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink, Copy, Store, Settings, Users, Globe } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

/**
 * FORM GENERATOR DASHBOARD
 * Shows all available deployment options for return forms
 */
const FormGenerator = () => {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [copiedUrl, setCopiedUrl] = useState('');

  // Load all tenants
  useEffect(() => {
    const loadTenants = async () => {
      try {
        const backendUrl = process.env.REACT_APP_BACKEND_URL;
        const response = await fetch(`${backendUrl}/api/tenants`);
        
        if (response.ok) {
          const data = await response.json();
          setTenants(data.tenants || []);
        }
      } catch (error) {
        console.error('Failed to load tenants:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTenants();
  }, []);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedUrl(text);
    setTimeout(() => setCopiedUrl(''), 2000);
  };

  const baseUrl = window.location.origin;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">Return Form Generator</h1>
        <p className="text-xl text-gray-600">
          Deploy return forms with multiple tenant isolation strategies
        </p>
      </div>

      {/* Deployment Options */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Option 1: Universal Form */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Globe className="h-6 w-6 text-blue-600" />
              <span>Universal Form</span>
            </CardTitle>
            <CardDescription>
              Single form with dynamic tenant detection
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Main URL:</p>
              <div className="flex items-center space-x-2">
                <code className="text-xs bg-gray-100 p-2 rounded flex-1">
                  {baseUrl}/returns/start
                </code>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => copyToClipboard(`${baseUrl}/returns/start`)}
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium">Detection Methods:</p>
              <ul className="text-xs space-y-1 text-gray-600">
                <li>• Subdomain: store1.yourapp.com</li>
                <li>• Query param: ?tenant=store1</li>
                <li>• Path: /returns/store1/start</li>
                <li>• LocalStorage: selectedTenant</li>
              </ul>
            </div>

            <div className="flex space-x-2">
              <Link to="/returns/start" className="flex-1">
                <Button className="w-full" size="sm">
                  <ExternalLink className="h-3 w-3 mr-1" />
                  Test Form
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Option 2: Tenant-Specific Forms */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Store className="h-6 w-6 text-green-600" />
              <span>Tenant-Specific</span>
            </CardTitle>
            <CardDescription>
              Branded forms for each tenant with isolation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Features:</p>
              <ul className="text-xs space-y-1 text-gray-600">
                <li>• Custom branding & colors</li>
                <li>• Tenant-specific policies</li>
                <li>• Isolated data access</li>
                <li>• Custom CSS support</li>
              </ul>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium">URL Pattern:</p>
              <code className="text-xs bg-gray-100 p-2 rounded block">
                {baseUrl}/returns/[tenant-id]/start
              </code>
            </div>

            <Button className="w-full" size="sm" variant="outline">
              <Settings className="h-3 w-3 mr-1" />
              Configure Tenants
            </Button>
          </CardContent>
        </Card>

        {/* Option 3: Subdomain Strategy */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="h-6 w-6 text-purple-600" />
              <span>Subdomain Strategy</span>
            </CardTitle>
            <CardDescription>
              Each tenant gets their own subdomain
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Examples:</p>
              <div className="text-xs space-y-1">
                <code className="bg-gray-100 p-1 rounded block">
                  store1.yourapp.com/returns/start
                </code>
                <code className="bg-gray-100 p-1 rounded block">
                  store2.yourapp.com/returns/start
                </code>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium">Benefits:</p>
              <ul className="text-xs space-y-1 text-gray-600">
                <li>• Complete isolation</li>
                <li>• Custom domains possible</li>
                <li>• SEO-friendly</li>
                <li>• Brand consistency</li>
              </ul>
            </div>

            <Button className="w-full" size="sm" variant="outline">
              <Globe className="h-3 w-3 mr-1" />
              DNS Configuration
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Tenant List */}
      <Card>
        <CardHeader>
          <CardTitle>Available Tenants & Forms</CardTitle>
          <CardDescription>
            {loading ? 'Loading tenants...' : `${tenants.length} tenants found`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            </div>
          ) : tenants.length === 0 ? (
            <p className="text-center py-8 text-gray-500">No tenants found</p>
          ) : (
            <div className="space-y-4">
              {tenants.map((tenant) => (
                <div key={tenant.tenant_id} className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold">{tenant.name}</h3>
                      <p className="text-sm text-gray-600">ID: {tenant.tenant_id}</p>
                      {tenant.shop && (
                        <p className="text-xs text-gray-500">Shopify: {tenant.shop}</p>
                      )}
                    </div>
                    <div className="flex space-x-2">
                      <Link to={`/returns/${tenant.tenant_id}/start`}>
                        <Button size="sm" variant="outline">
                          <ExternalLink className="h-3 w-3 mr-1" />
                          Test Form
                        </Button>
                      </Link>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div>
                      <p className="font-medium mb-1">Universal:</p>
                      <div className="flex items-center space-x-2">
                        <code className="bg-gray-100 p-1 rounded text-xs flex-1">
                          {baseUrl}/returns/start?tenant={tenant.tenant_id.replace('tenant-', '')}
                        </code>
                        <Button 
                          size="sm" 
                          variant="ghost"
                          onClick={() => copyToClipboard(`${baseUrl}/returns/start?tenant=${tenant.tenant_id.replace('tenant-', '')}`)}
                          className="h-6 w-6 p-0"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    <div>
                      <p className="font-medium mb-1">Tenant-Specific:</p>
                      <div className="flex items-center space-x-2">
                        <code className="bg-gray-100 p-1 rounded text-xs flex-1">
                          {baseUrl}/returns/{tenant.tenant_id}/start
                        </code>
                        <Button 
                          size="sm" 
                          variant="ghost"
                          onClick={() => copyToClipboard(`${baseUrl}/returns/${tenant.tenant_id}/start`)}
                          className="h-6 w-6 p-0"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    <div>
                      <p className="font-medium mb-1">Subdomain:</p>
                      <div className="flex items-center space-x-2">
                        <code className="bg-gray-100 p-1 rounded text-xs flex-1">
                          {tenant.tenant_id.replace('tenant-', '')}.yourapp.com/returns/start
                        </code>
                        <Button 
                          size="sm" 
                          variant="ghost"
                          onClick={() => copyToClipboard(`${tenant.tenant_id.replace('tenant-', '')}.yourapp.com/returns/start`)}
                          className="h-6 w-6 p-0"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {copiedUrl && copiedUrl.includes(tenant.tenant_id) && (
                    <p className="text-xs text-green-600">✓ Copied to clipboard!</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Implementation Guide */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Implementation Guide</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-blue-800">
          <div>
            <h4 className="font-semibold mb-2">Current Status:</h4>
            <ul className="space-y-1 text-sm">
              <li>✅ Universal form with dynamic tenant detection (ACTIVE)</li>
              <li>✅ Tenant-specific forms with custom branding (ACTIVE)</li>
              <li>✅ Database tenant isolation (ACTIVE)</li>
              <li>⚡ Subdomain routing (REQUIRES DNS CONFIGURATION)</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Recommended Deployment:</h4>
            <ol className="space-y-1 text-sm list-decimal list-inside">
              <li>Use <strong>Universal Form</strong> for MVP and testing</li>
              <li>Deploy <strong>Tenant-Specific Forms</strong> for branded experience</li>
              <li>Configure <strong>Subdomains</strong> for enterprise customers</li>
              <li>All approaches maintain data isolation and security</li>
            </ol>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default FormGenerator;