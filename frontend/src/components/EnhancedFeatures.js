import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  Mail, 
  Download, 
  Brain, 
  Settings, 
  CheckCircle, 
  XCircle,
  FileText,
  FileSpreadsheet,
  Lightbulb,
  Send,
  Loader2
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EnhancedFeatures = ({ tenantId }) => {
  const [featuresStatus, setFeaturesStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Email testing state
  const [testEmail, setTestEmail] = useState('');
  const [emailSending, setEmailSending] = useState(false);

  // AI suggestions state
  const [aiProduct, setAiProduct] = useState('');
  const [aiDescription, setAiDescription] = useState('');
  const [aiSuggestions, setAiSuggestions] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  // Export state
  const [exportType, setExportType] = useState('pdf');
  const [exportDays, setExportDays] = useState(30);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    checkFeaturesStatus();
  }, []);

  const checkFeaturesStatus = async () => {
    try {
      const response = await axios.get(`${API}/enhanced/status`);
      setFeaturesStatus(response.data);
    } catch (error) {
      console.error('Error checking features status:', error);
    }
  };

  const handleTestEmail = async () => {
    if (!testEmail) return;
    
    setEmailSending(true);
    try {
      const response = await axios.post(`${API}/enhanced/email/test`, {
        email: testEmail
      }, {
        headers: { 'X-Tenant-Id': tenantId }
      });
      
      if (response.data.success) {
        alert('Test email sent successfully! Check your inbox.');
      } else {
        alert('Failed to send test email. Please check your SMTP configuration.');
      }
    } catch (error) {
      console.error('Error sending test email:', error);
      alert('Error sending test email. Please try again.');
    }
    setEmailSending(false);
  };

  const handleAISuggestions = async () => {
    if (!aiProduct) return;
    
    setAiLoading(true);
    try {
      const response = await axios.post(`${API}/enhanced/ai/suggest-reasons`, {
        product_name: aiProduct,
        product_description: aiDescription,
        order_date: new Date().toISOString()
      }, {
        headers: { 'X-Tenant-Id': tenantId }
      });
      
      setAiSuggestions(response.data);
    } catch (error) {
      console.error('Error getting AI suggestions:', error);
      alert('Error getting AI suggestions. Please try again.');
    }
    setAiLoading(false);
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      let url = '';
      let filename = '';
      
      if (exportType === 'csv') {
        url = `${API}/enhanced/export/returns/csv?days=${exportDays}`;
        filename = `returns_export_${new Date().toISOString().split('T')[0]}.csv`;
      } else if (exportType === 'pdf') {
        url = `${API}/enhanced/export/returns/pdf?days=${exportDays}&include_analytics=true`;
        filename = `returns_report_${new Date().toISOString().split('T')[0]}.pdf`;
      } else if (exportType === 'excel') {
        url = `${API}/enhanced/export/analytics/excel?days=${exportDays}`;
        filename = `analytics_export_${new Date().toISOString().split('T')[0]}.xlsx`;
      }
      
      const response = await axios.get(url, {
        headers: { 'X-Tenant-Id': tenantId },
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
    } catch (error) {
      console.error('Error exporting data:', error);
      alert('Error exporting data. Please try again.');
    }
    setExporting(false);
  };

  if (!featuresStatus) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            <span>Loading enhanced features...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-purple-600" />
            <span>Enhanced Features</span>
          </CardTitle>
          <CardDescription>
            Advanced functionality including email notifications, AI suggestions, and data exports
          </CardDescription>
        </CardHeader>
      </Card>

      <Tabs defaultValue="email" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="email" className="flex items-center space-x-2">
            <Mail className="h-4 w-4" />
            <span>Email</span>
          </TabsTrigger>
          <TabsTrigger value="ai" className="flex items-center space-x-2">
            <Brain className="h-4 w-4" />
            <span>AI Features</span>
          </TabsTrigger>
          <TabsTrigger value="export" className="flex items-center space-x-2">
            <Download className="h-4 w-4" />
            <span>Export</span>
          </TabsTrigger>
        </TabsList>

        {/* Email Configuration Tab */}
        <TabsContent value="email">
          <Card>
            <CardHeader>
              <CardTitle>Email Notifications</CardTitle>
              <CardDescription>
                Configure and test email notifications for return status updates
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Email Status */}
              <Alert className={featuresStatus.email.enabled ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'}>
                <div className="flex items-center space-x-2">
                  {featuresStatus.email.enabled ? <CheckCircle className="h-4 w-4 text-green-600" /> : <XCircle className="h-4 w-4 text-yellow-600" />}
                </div>
                <AlertDescription>
                  <div className="flex items-center justify-between">
                    <span>
                      Email notifications are {featuresStatus.email.enabled ? 'enabled' : 'disabled'}
                    </span>
                    <Badge variant={featuresStatus.email.enabled ? 'default' : 'secondary'}>
                      {featuresStatus.email.smtp_configured ? 'SMTP Configured' : 'SMTP Not Configured'}
                    </Badge>
                  </div>
                </AlertDescription>
              </Alert>

              {/* Test Email */}
              <div className="space-y-2">
                <Label htmlFor="testEmail">Test Email Address</Label>
                <div className="flex space-x-2">
                  <Input
                    id="testEmail"
                    type="email"
                    placeholder="Enter email to test configuration"
                    value={testEmail}
                    onChange={(e) => setTestEmail(e.target.value)}
                    disabled={emailSending}
                  />
                  <Button 
                    onClick={handleTestEmail}
                    disabled={!testEmail || emailSending || !featuresStatus.email.enabled}
                    className="flex items-center space-x-2"
                  >
                    <Send className="h-4 w-4" />
                    <span>{emailSending ? 'Sending...' : 'Send Test'}</span>
                  </Button>
                </div>
              </div>

              {/* Configuration Instructions */}
              {!featuresStatus.email.enabled && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">SMTP Configuration Required:</h4>
                  <p className="text-sm text-blue-800 mb-2">
                    Add the following environment variables to your backend .env file:
                  </p>
                  <code className="text-xs bg-white p-2 rounded block">
                    SMTP_HOST=smtp.gmail.com<br/>
                    SMTP_USERNAME=your-email@gmail.com<br/>
                    SMTP_PASSWORD=your-app-password<br/>
                    FROM_EMAIL=noreply@yourstore.com
                  </code>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Features Tab */}
        <TabsContent value="ai">
          <Card>
            <CardHeader>
              <CardTitle>AI-Powered Features</CardTitle>
              <CardDescription>
                Get intelligent suggestions for return reasons and automated insights
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* AI Status */}
              <Alert className="border-blue-200 bg-blue-50">
                <Lightbulb className="h-4 w-4 text-blue-600" />
                <AlertDescription>
                  <div className="flex items-center justify-between">
                    <span>
                      AI suggestions are powered by {featuresStatus.ai.openai_available ? 'OpenAI GPT' : 'local algorithms'}
                    </span>
                    <Badge variant={featuresStatus.ai.openai_available ? 'default' : 'secondary'}>
                      {featuresStatus.ai.openai_available ? 'OpenAI Active' : 'Local Fallback'}
                    </Badge>
                  </div>
                </AlertDescription>
              </Alert>

              {/* Product Analysis */}
              <div className="space-y-2">
                <Label htmlFor="aiProduct">Product Name</Label>
                <Input
                  id="aiProduct"
                  placeholder="e.g., Wireless Headphones"
                  value={aiProduct}
                  onChange={(e) => setAiProduct(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="aiDescription">Product Description (Optional)</Label>
                <Textarea
                  id="aiDescription"
                  placeholder="Brief description of the product..."
                  value={aiDescription}
                  onChange={(e) => setAiDescription(e.target.value)}
                  rows={3}
                />
              </div>

              <Button 
                onClick={handleAISuggestions}
                disabled={!aiProduct || aiLoading}
                className="flex items-center space-x-2"
              >
                <Brain className="h-4 w-4" />
                <span>{aiLoading ? 'Analyzing...' : 'Get AI Suggestions'}</span>
              </Button>

              {/* AI Suggestions Results */}
              {aiSuggestions && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium mb-3">Suggested Return Reasons:</h4>
                  <div className="space-y-2">
                    {aiSuggestions.suggestions.map((suggestion, index) => (
                      <div key={index} className="flex items-center justify-between bg-white p-3 rounded">
                        <div>
                          <span className="font-medium capitalize">
                            {suggestion.reason.replace('_', ' ')}
                          </span>
                          <p className="text-sm text-gray-600">{suggestion.explanation}</p>
                        </div>
                        <Badge variant="outline">
                          {suggestion.confidence}% confident
                        </Badge>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Powered by {aiSuggestions.ai_powered ? 'OpenAI' : 'local algorithms'}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Export Tab */}
        <TabsContent value="export">
          <Card>
            <CardHeader>
              <CardTitle>Data Export</CardTitle>
              <CardDescription>
                Export your returns data and analytics in various formats
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Export Configuration */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="exportType">Export Format</Label>
                  <Select value={exportType} onValueChange={setExportType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="csv">CSV (Spreadsheet)</SelectItem>
                      <SelectItem value="pdf">PDF Report</SelectItem>
                      <SelectItem value="excel">Excel Analytics</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="exportDays">Time Period (Days)</Label>
                  <Select value={exportDays.toString()} onValueChange={(value) => setExportDays(parseInt(value))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="7">Last 7 days</SelectItem>
                      <SelectItem value="30">Last 30 days</SelectItem>
                      <SelectItem value="90">Last 90 days</SelectItem>
                      <SelectItem value="365">Last year</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Export Button */}
              <Button 
                onClick={handleExport}
                disabled={exporting}
                className="flex items-center space-x-2 w-full"
              >
                {exportType === 'csv' ? <FileSpreadsheet className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
                <span>
                  {exporting ? 'Generating...' : `Export ${exportType.toUpperCase()}`}
                </span>
              </Button>

              {/* Export Info */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">Export Options:</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li><strong>CSV:</strong> Raw data for spreadsheet analysis</li>
                  <li><strong>PDF:</strong> Formatted report with summary and charts</li>
                  <li><strong>Excel:</strong> Comprehensive analytics with multiple sheets</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EnhancedFeatures;