import React, { useState, useEffect } from 'react';
import { Save, Building, Mail, Clock, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Textarea } from '../../../components/ui/textarea';
import { Alert, AlertDescription } from '../../../components/ui/alert';

const General = () => {
  const [settings, setSettings] = useState({
    storeName: 'Fashion Forward',
    storeEmail: 'support@fashionforward.com',
    returnWindow: 30,
    autoApprove: true,
    requirePhotos: false,
    customMessage: 'We\'re here to help with your return!'
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleSave = async () => {
    setSaving(true);
    setMessage({ type: '', text: '' });

    // Simulate save operation
    setTimeout(() => {
      setMessage({ type: 'success', text: 'Settings saved successfully!' });
      setSaving(false);
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    }, 1000);
  };

  return (
    <div className="space-y-4 md:space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">General Settings</h1>
        <p className="text-gray-500 text-sm md:text-base">Configure your basic store and return policy settings</p>
      </div>

      {message.text && (
        <Alert className={`border ${message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <div className="flex items-center">
            {message.type === 'success' ? (
              <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
            ) : (
              <XCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
            )}
            <AlertDescription className={`ml-2 ${message.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
              {message.text}
            </AlertDescription>
          </div>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <Building className="h-5 w-5 flex-shrink-0" />
              <span>Store Information</span>
            </CardTitle>
            <CardDescription className="text-sm">Basic information about your store</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="storeName" className="text-sm font-medium">Store Name</Label>
              <Input
                id="storeName"
                value={settings.storeName}
                onChange={(e) => setSettings({...settings, storeName: e.target.value})}
                className="mt-1 touch-manipulation"
              />
            </div>
            <div>
              <Label htmlFor="storeEmail" className="text-sm font-medium">Support Email</Label>
              <Input
                id="storeEmail"
                type="email"
                value={settings.storeEmail}
                onChange={(e) => setSettings({...settings, storeEmail: e.target.value})}
                className="mt-1 touch-manipulation"
              />
              <p className="text-xs text-gray-500 mt-1">Customers will receive return updates from this email</p>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <Clock className="h-5 w-5 flex-shrink-0" />
              <span>Return Policy</span>
            </CardTitle>
            <CardDescription className="text-sm">Configure your return policy defaults</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="returnWindow" className="text-sm font-medium">Return Window (Days)</Label>
              <Input
                id="returnWindow"
                type="number"
                value={settings.returnWindow}
                onChange={(e) => setSettings({...settings, returnWindow: parseInt(e.target.value) || 30})}
                min="1"
                max="365"
                className="mt-1 touch-manipulation"
              />
            </div>
            <div className="space-y-3">
              <div className="flex items-start space-x-3 touch-manipulation">
                <input
                  type="checkbox"
                  id="autoApprove"
                  checked={settings.autoApprove}
                  onChange={(e) => setSettings({...settings, autoApprove: e.target.checked})}
                  className="rounded mt-1"
                />
                <div className="min-w-0 flex-1">
                  <Label htmlFor="autoApprove" className="text-sm font-medium cursor-pointer">Auto-approve eligible returns</Label>
                </div>
              </div>
              <div className="flex items-start space-x-3 touch-manipulation">
                <input
                  type="checkbox"
                  id="requirePhotos"
                  checked={settings.requirePhotos}
                  onChange={(e) => setSettings({...settings, requirePhotos: e.target.checked})}
                  className="rounded mt-1"
                />
                <div className="min-w-0 flex-1">
                  <Label htmlFor="requirePhotos" className="text-sm font-medium cursor-pointer">Require photos for return requests</Label>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-lg">
            <Mail className="h-5 w-5 flex-shrink-0" />
            <span>Customer Communication</span>
          </CardTitle>
          <CardDescription className="text-sm">Customize messages shown to customers</CardDescription>
        </CardHeader>
        <CardContent>
          <div>
            <Label htmlFor="customMessage" className="text-sm font-medium">Welcome Message</Label>
            <Textarea
              id="customMessage"
              value={settings.customMessage}
              onChange={(e) => setSettings({...settings, customMessage: e.target.value})}
              rows={3}
              placeholder="Enter a custom welcome message for your return portal..."
              className="mt-1 touch-manipulation resize-y"
            />
            <p className="text-xs text-gray-500 mt-1">This message will be shown to customers on your return portal</p>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving} className="w-full sm:w-auto touch-manipulation">
          {saving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default General;