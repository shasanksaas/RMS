import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Textarea } from '../../../components/ui/textarea';
import { Switch } from '../../../components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Badge } from '../../../components/ui/badge';
import { Upload, Eye, Save, Copy, ExternalLink, Palette, Layout, Settings, Globe, Code } from 'lucide-react';
import { Alert, AlertDescription } from '../../../components/ui/alert';

const FormCustomization = () => {
  const [config, setConfig] = useState({
    // Branding
    branding: {
      logo_url: '',
      favicon_url: '',
      primary_color: '#3B82F6',
      secondary_color: '#1F2937',
      background_color: '#FFFFFF',
      text_color: '#111827',
      font_family: 'Inter'
    },
    // Layout & Theme
    layout: {
      preset: 'wizard', // wizard | compact
      corner_radius: 'medium', // small | medium | large
      spacing_density: 'comfortable', // compact | comfortable | spacious
      custom_css: ''
    },
    // Form Configuration
    form: {
      show_phone: true,
      show_photos: true,
      max_photos: 3,
      show_notes: true,
      custom_question: {
        enabled: false,
        label: '',
        type: 'text', // text | select | yes-no
        options: []
      },
      return_reasons: [
        'Wrong size',
        'Defective',
        'Not as described',
        'Changed mind',
        'Damaged in shipping'
      ],
      available_resolutions: ['refund', 'exchange', 'store_credit'],
      return_window_days: 30,
      policy_text: 'Standard 30-day return policy applies. Items must be in original condition.'
    }
  });

  const [previewUrl, setPreviewUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const [publishedVersion, setPublishedVersion] = useState(null);
  const [isDraft, setIsDraft] = useState(false);

  const fontOptions = [
    { value: 'Inter', label: 'Inter (Recommended)' },
    { value: 'Roboto', label: 'Roboto' },
    { value: 'Open Sans', label: 'Open Sans' },
    { value: 'Lato', label: 'Lato' },
    { value: 'Source Sans Pro', label: 'Source Sans Pro' },
    { value: 'system-ui', label: 'System Default' }
  ];

  const cornerRadiusOptions = [
    { value: 'small', label: 'Small (4px)' },
    { value: 'medium', label: 'Medium (8px)' },
    { value: 'large', label: 'Large (12px)' }
  ];

  const spacingOptions = [
    { value: 'compact', label: 'Compact' },
    { value: 'comfortable', label: 'Comfortable' },
    { value: 'spacious', label: 'Spacious' }
  ];

  // Load existing configuration
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const backendUrl = process.env.REACT_APP_BACKEND_URL;
        const tenantId = localStorage.getItem('currentTenantId') || 'tenant-rms34';
        
        const response = await fetch(`${backendUrl}/api/tenants/${tenantId}/form-config`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'X-Tenant-Id': tenantId
          }
        });

        if (response.ok) {
          const data = await response.json();
          setConfig(prev => ({ ...prev, ...data.config }));
          setPublishedVersion(data.published_version);
          setIsDraft(data.has_draft);
        }

        // Set preview URL based on current tenant
        const baseUrl = window.location.origin;
        const currentTenant = tenantId.replace('tenant-', '');
        setPreviewUrl(`${baseUrl}/returns/${currentTenant}/start?preview=true`);
      } catch (error) {
        console.error('Failed to load form configuration:', error);
      }
    };

    loadConfig();
  }, []);

  const handleConfigChange = (section, field, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
    setIsDraft(true);
  };

  const handleNestedConfigChange = (section, subsection, field, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [subsection]: {
          ...prev[section][subsection],
          [field]: value
        }
      }
    }));
    setIsDraft(true);
  };

  const handleFileUpload = async (type, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const tenantId = localStorage.getItem('currentTenantId') || 'tenant-rms34';
      
      const response = await fetch(`${backendUrl}/api/tenants/${tenantId}/upload-asset`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Tenant-Id': tenantId
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        handleConfigChange('branding', `${type}_url`, data.url);
      }
    } catch (error) {
      console.error('File upload failed:', error);
    }
  };

  const saveDraft = async () => {
    setSaving(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const tenantId = localStorage.getItem('currentTenantId') || 'tenant-rms34';
      
      const response = await fetch(`${backendUrl}/api/tenants/${tenantId}/form-config/draft`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({ config })
      });

      if (response.ok) {
        setIsDraft(true);
        // Show success message
      }
    } catch (error) {
      console.error('Save draft failed:', error);
    } finally {
      setSaving(false);
    }
  };

  const publishConfig = async () => {
    setSaving(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const tenantId = localStorage.getItem('currentTenantId') || 'tenant-rms34';
      
      const response = await fetch(`${backendUrl}/api/tenants/${tenantId}/form-config/publish`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({ config })
      });

      if (response.ok) {
        const data = await response.json();
        setPublishedVersion(data.version);
        setIsDraft(false);
        // Show success message
      }
    } catch (error) {
      console.error('Publish failed:', error);
    } finally {
      setSaving(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const generateEmbedCode = () => {
    const tenantId = localStorage.getItem('currentTenantId') || 'tenant-rms34';
    const baseUrl = window.location.origin;
    return `<iframe src="${baseUrl}/returns/${tenantId.replace('tenant-', '')}/start" width="100%" height="600" frameborder="0"></iframe>`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Return Form Customization</h2>
          <p className="text-gray-600">Customize your customer-facing return form with branding and configuration options.</p>
        </div>
        <div className="flex items-center space-x-3">
          {isDraft && (
            <Badge variant="secondary">Draft Changes</Badge>
          )}
          {publishedVersion && (
            <Badge variant="outline">v{publishedVersion}</Badge>
          )}
          <Button onClick={saveDraft} disabled={saving} variant="outline">
            <Save className="h-4 w-4 mr-2" />
            Save Draft
          </Button>
          <Button onClick={publishConfig} disabled={saving}>
            <Eye className="h-4 w-4 mr-2" />
            Publish
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-2 space-y-6">
          <Tabs defaultValue="branding" className="w-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="branding" className="flex items-center space-x-1">
                <Palette className="h-4 w-4" />
                <span>Branding</span>
              </TabsTrigger>
              <TabsTrigger value="layout" className="flex items-center space-x-1">
                <Layout className="h-4 w-4" />
                <span>Layout</span>
              </TabsTrigger>
              <TabsTrigger value="form" className="flex items-center space-x-1">
                <Settings className="h-4 w-4" />
                <span>Form</span>
              </TabsTrigger>
              <TabsTrigger value="links" className="flex items-center space-x-1">
                <Globe className="h-4 w-4" />
                <span>Links</span>
              </TabsTrigger>
              <TabsTrigger value="embed" className="flex items-center space-x-1">
                <Code className="h-4 w-4" />
                <span>Embed</span>
              </TabsTrigger>
            </TabsList>

            {/* Branding Tab */}
            <TabsContent value="branding" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Brand Assets</CardTitle>
                  <CardDescription>Upload your logo and set brand colors</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Logo Upload */}
                  <div className="space-y-2">
                    <Label>Logo</Label>
                    <div className="flex items-center space-x-4">
                      {config.branding.logo_url && (
                        <img src={config.branding.logo_url} alt="Logo" className="h-12 w-auto" />
                      )}
                      <label className="cursor-pointer">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => e.target.files[0] && handleFileUpload('logo', e.target.files[0])}
                          className="hidden"
                        />
                        <div className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
                          <Upload className="h-4 w-4" />
                          <span>Upload Logo</span>
                        </div>
                      </label>
                    </div>
                  </div>

                  {/* Colors */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Primary Color</Label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="color"
                          value={config.branding.primary_color}
                          onChange={(e) => handleConfigChange('branding', 'primary_color', e.target.value)}
                          className="w-10 h-10 rounded border"
                        />
                        <Input
                          value={config.branding.primary_color}
                          onChange={(e) => handleConfigChange('branding', 'primary_color', e.target.value)}
                          placeholder="#3B82F6"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Secondary Color</Label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="color"
                          value={config.branding.secondary_color}
                          onChange={(e) => handleConfigChange('branding', 'secondary_color', e.target.value)}
                          className="w-10 h-10 rounded border"
                        />
                        <Input
                          value={config.branding.secondary_color}
                          onChange={(e) => handleConfigChange('branding', 'secondary_color', e.target.value)}
                          placeholder="#1F2937"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Font Family */}
                  <div className="space-y-2">
                    <Label>Font Family</Label>
                    <Select value={config.branding.font_family} onValueChange={(value) => handleConfigChange('branding', 'font_family', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select font" />
                      </SelectTrigger>
                      <SelectContent>
                        {fontOptions.map(font => (
                          <SelectItem key={font.value} value={font.value}>
                            {font.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Layout Tab */}
            <TabsContent value="layout" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Layout & Theme</CardTitle>
                  <CardDescription>Configure the appearance and layout of your form</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Layout Preset */}
                  <div className="space-y-2">
                    <Label>Layout Preset</Label>
                    <Select value={config.layout.preset} onValueChange={(value) => handleConfigChange('layout', 'preset', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select layout" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="wizard">Wizard (Multi-step)</SelectItem>
                        <SelectItem value="compact">Compact (Single page)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Corner Radius */}
                  <div className="space-y-2">
                    <Label>Corner Radius</Label>
                    <Select value={config.layout.corner_radius} onValueChange={(value) => handleConfigChange('layout', 'corner_radius', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select corner radius" />
                      </SelectTrigger>
                      <SelectContent>
                        {cornerRadiusOptions.map(option => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Spacing Density */}
                  <div className="space-y-2">
                    <Label>Spacing Density</Label>
                    <Select value={config.layout.spacing_density} onValueChange={(value) => handleConfigChange('layout', 'spacing_density', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select spacing" />
                      </SelectTrigger>
                      <SelectContent>
                        {spacingOptions.map(option => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Custom CSS */}
                  <div className="space-y-2">
                    <Label>Custom CSS <Badge variant="secondary">Pro</Badge></Label>
                    <Textarea
                      value={config.layout.custom_css}
                      onChange={(e) => handleConfigChange('layout', 'custom_css', e.target.value)}
                      placeholder="/* Add custom CSS here (max 2KB) */"
                      rows={6}
                      className="font-mono text-sm"
                    />
                    <p className="text-xs text-gray-500">
                      Custom CSS is sanitized and limited to 2KB. No JavaScript allowed.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Form Configuration Tab */}
            <TabsContent value="form" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Form Fields</CardTitle>
                  <CardDescription>Configure which fields to show on the return form</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Field Toggles */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label>Show Phone Number Field</Label>
                      <Switch
                        checked={config.form.show_phone}
                        onCheckedChange={(checked) => handleConfigChange('form', 'show_phone', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Show Photo Upload</Label>
                      <Switch
                        checked={config.form.show_photos}
                        onCheckedChange={(checked) => handleConfigChange('form', 'show_photos', checked)}
                      />
                    </div>
                    {config.form.show_photos && (
                      <div className="ml-6 space-y-2">
                        <Label>Maximum Photos</Label>
                        <Input
                          type="number"
                          min="1"
                          max="10"
                          value={config.form.max_photos}
                          onChange={(e) => handleConfigChange('form', 'max_photos', parseInt(e.target.value))}
                          className="w-24"
                        />
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <Label>Show Notes Field</Label>
                      <Switch
                        checked={config.form.show_notes}
                        onCheckedChange={(checked) => handleConfigChange('form', 'show_notes', checked)}
                      />
                    </div>
                  </div>

                  {/* Return Window */}
                  <div className="space-y-2">
                    <Label>Return Window (Days)</Label>
                    <Input
                      type="number"
                      min="1"
                      max="365"
                      value={config.form.return_window_days}
                      onChange={(e) => handleConfigChange('form', 'return_window_days', parseInt(e.target.value))}
                      className="w-32"
                    />
                  </div>

                  {/* Policy Text */}
                  <div className="space-y-2">
                    <Label>Return Policy Text</Label>
                    <Textarea
                      value={config.form.policy_text}
                      onChange={(e) => handleConfigChange('form', 'policy_text', e.target.value)}
                      placeholder="Enter your return policy text..."
                      rows={3}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Links Tab */}
            <TabsContent value="links" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Form URLs</CardTitle>
                  <CardDescription>Your customized return form is available at these URLs</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {(() => {
                    const tenantId = localStorage.getItem('currentTenantId') || 'tenant-rms34';
                    const baseUrl = window.location.origin;
                    const tenantSlug = tenantId.replace('tenant-', '');
                    
                    return (
                      <>
                        <div className="space-y-2">
                          <Label>Your Customer Return Form URL</Label>
                          <div className="flex items-center space-x-2">
                            <Input
                              readOnly
                              value={`${baseUrl}/returns/${tenantSlug}/start`}
                              className="flex-1 font-mono text-sm bg-blue-50 border-blue-200"
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => copyToClipboard(`${baseUrl}/returns/${tenantSlug}/start`)}
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => window.open(`${baseUrl}/returns/${tenantSlug}/start`, '_blank')}
                            >
                              <ExternalLink className="h-3 w-3" />
                            </Button>
                          </div>
                          <p className="text-xs text-blue-600">
                            ✅ This URL is specifically for your customers and will show your branding
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label>Universal URL (Alternative)</Label>
                          <div className="flex items-center space-x-2">
                            <Input
                              readOnly
                              value={`${baseUrl}/returns/start?tenant=${tenantSlug}`}
                              className="flex-1 font-mono text-sm"
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => copyToClipboard(`${baseUrl}/returns/start?tenant=${tenantSlug}`)}
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </>
                    );
                  })()}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Embed Tab */}
            <TabsContent value="embed" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Embed Code</CardTitle>
                  <CardDescription>Copy this code to embed the return form on your website</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>HTML Embed Code</Label>
                    <div className="space-y-2">
                      <Textarea
                        readOnly
                        value={generateEmbedCode()}
                        rows={3}
                        className="font-mono text-sm"
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => copyToClipboard(generateEmbedCode())}
                        className="w-full"
                      >
                        <Copy className="h-3 w-3 mr-2" />
                        Copy Embed Code
                      </Button>
                    </div>
                  </div>

                  <Alert>
                    <AlertDescription>
                      This iframe will automatically use your published configuration. 
                      Changes won't appear until you publish them.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Live Preview Panel */}
        <div className="lg:col-span-1">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Eye className="h-4 w-4" />
                <span>Live Preview</span>
              </CardTitle>
              <CardDescription>See how your form will look</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="aspect-[3/4] border rounded-lg overflow-hidden">
                <iframe
                  src={previewUrl}
                  className="w-full h-full"
                  title="Form Preview"
                />
              </div>
              <Button
                size="sm"
                variant="outline"
                className="w-full mt-3"
                onClick={() => window.open(previewUrl, '_blank')}
              >
                <ExternalLink className="h-3 w-3 mr-2" />
                Open Full Preview
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default FormCustomization;