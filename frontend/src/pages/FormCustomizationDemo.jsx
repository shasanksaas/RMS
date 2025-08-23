import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Upload, Eye, Save, Copy, ExternalLink, Palette, Layout, Settings, Globe, Code } from 'lucide-react';
import { Alert, AlertDescription } from '../components/ui/alert';

/**
 * FORM CUSTOMIZATION DEMO
 * Standalone demo to show the complete form customization interface
 */
const FormCustomizationDemo = () => {
  const [config, setConfig] = useState({
    // Branding
    branding: {
      logo_url: 'https://via.placeholder.com/150x50/3B82F6/FFFFFF?text=LOGO',
      favicon_url: '',
      primary_color: '#3B82F6',
      secondary_color: '#1F2937',
      background_color: '#FFFFFF',
      text_color: '#111827',
      font_family: 'Inter'
    },
    // Layout & Theme
    layout: {
      preset: 'wizard',
      corner_radius: 'medium',
      spacing_density: 'comfortable',
      custom_css: '/* Custom styles */\n.return-form {\n  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);\n}'
    },
    // Form Configuration
    form: {
      show_phone: true,
      show_photos: true,
      max_photos: 3,
      show_notes: true,
      custom_question: {
        enabled: true,
        label: 'What would you like us to improve?',
        type: 'text',
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
      policy_text: 'Standard 30-day return policy applies. Items must be in original condition with original packaging and tags.'
    }
  });

  const [activeTab, setActiveTab] = useState('branding');
  const [isDraft, setIsDraft] = useState(true);

  const fontOptions = [
    { value: 'Inter', label: 'Inter (Recommended)' },
    { value: 'Roboto', label: 'Roboto' },
    { value: 'Open Sans', label: 'Open Sans' },
    { value: 'Lato', label: 'Lato' },
    { value: 'Source Sans Pro', label: 'Source Sans Pro' },
    { value: 'system-ui', label: 'System Default' }
  ];

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

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const generateEmbedCode = () => {
    const baseUrl = window.location.origin;
    return `<iframe src="${baseUrl}/returns/demo-store/start" width="100%" height="600" frameborder="0"></iframe>`;
  };

  const previewUrl = `${window.location.origin}/returns/demo-store/start?preview=true`;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Return Form Customization</h1>
              <p className="mt-2 text-gray-600">Customize your customer-facing return form with branding and configuration options.</p>
            </div>
            <div className="flex items-center space-x-3">
              {isDraft && (
                <Badge variant="secondary">Draft Changes</Badge>
              )}
              <Badge variant="outline">v1.2</Badge>
              <Button variant="outline">
                <Save className="h-4 w-4 mr-2" />
                Save Draft
              </Button>
              <Button>
                <Eye className="h-4 w-4 mr-2" />
                Publish
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Configuration Panel */}
          <div className="lg:col-span-2 space-y-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
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
                        <img src={config.branding.logo_url} alt="Logo" className="h-12 w-auto border rounded" />
                        <div className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer">
                          <Upload className="h-4 w-4" />
                          <span>Upload Logo</span>
                        </div>
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
                            className="w-10 h-10 rounded border cursor-pointer"
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
                            className="w-10 h-10 rounded border cursor-pointer"
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

                    {/* Custom CSS */}
                    <div className="space-y-2">
                      <Label>Custom CSS <Badge variant="secondary">Pro</Badge></Label>
                      <Textarea
                        value={config.layout.custom_css}
                        onChange={(e) => handleConfigChange('layout', 'custom_css', e.target.value)}
                        placeholder="/* Add custom CSS here (max 2KB) */"
                        rows={8}
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
                    <div className="space-y-2">
                      <Label>Tenant-Specific URL</Label>
                      <div className="flex items-center space-x-2">
                        <Input
                          readOnly
                          value={`${window.location.origin}/returns/demo-store/start`}
                          className="flex-1 font-mono text-sm"
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => copyToClipboard(`${window.location.origin}/returns/demo-store/start`)}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => window.open(`${window.location.origin}/returns/demo-store/start`, '_blank')}
                        >
                          <ExternalLink className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Universal URL with Tenant Parameter</Label>
                      <div className="flex items-center space-x-2">
                        <Input
                          readOnly
                          value={`${window.location.origin}/returns/start?tenant=demo-store`}
                          className="flex-1 font-mono text-sm"
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => copyToClipboard(`${window.location.origin}/returns/start?tenant=demo-store`)}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
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
                <div className="aspect-[3/4] border rounded-lg overflow-hidden bg-white relative">
                  {/* Preview Content */}
                  <div className="p-4 space-y-4" style={{ 
                    fontFamily: config.branding.font_family,
                    color: config.branding.text_color 
                  }}>
                    <div className="text-center">
                      <img src={config.branding.logo_url} alt="Logo" className="h-8 w-auto mx-auto mb-2" />
                      <h2 className="text-lg font-bold">Start Your Return</h2>
                      <p className="text-sm text-gray-600">We'll help you return your items</p>
                    </div>
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Order Number</label>
                      <input 
                        type="text" 
                        placeholder="#1001" 
                        className="w-full p-2 border rounded text-sm"
                        style={{ borderColor: config.branding.primary_color + '40' }}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Email</label>
                      <input 
                        type="email" 
                        placeholder="your@email.com" 
                        className="w-full p-2 border rounded text-sm"
                        style={{ borderColor: config.branding.primary_color + '40' }}
                      />
                    </div>
                    
                    {config.form.show_phone && (
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Phone</label>
                        <input 
                          type="tel" 
                          placeholder="(555) 123-4567" 
                          className="w-full p-2 border rounded text-sm"
                          style={{ borderColor: config.branding.primary_color + '40' }}
                        />
                      </div>
                    )}
                    
                    <button 
                      className="w-full py-2 px-4 text-white font-medium rounded text-sm"
                      style={{ backgroundColor: config.branding.primary_color }}
                    >
                      Look up order
                    </button>
                    
                    <div className="text-xs text-gray-500 mt-4">
                      {config.form.policy_text}
                    </div>
                  </div>
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
    </div>
  );
};

export default FormCustomizationDemo;