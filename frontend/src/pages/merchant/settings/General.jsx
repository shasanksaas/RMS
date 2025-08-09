import React, { useState } from 'react';
import { Save, Building, Mail, Clock } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Textarea } from '../../../components/ui/textarea';

const General = () => {
  const [settings, setSettings] = useState({
    storeName: 'Fashion Forward',
    storeEmail: 'support@fashionforward.com',
    returnWindow: 30,
    autoApprove: true,
    requirePhotos: false,
    customMessage: 'We\'re here to help with your return!'
  });

  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
    alert('Settings saved successfully!');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">General Settings</h1>
        <p className="text-gray-500">Configure your basic store and return policy settings</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building className="h-5 w-5" />
              <span>Store Information</span>
            </CardTitle>
            <CardDescription>Basic information about your store</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="storeName">Store Name</Label>
              <Input
                id="storeName"
                value={settings.storeName}
                onChange={(e) => setSettings({...settings, storeName: e.target.value})}
              />
            </div>
            <div>
              <Label htmlFor="storeEmail">Support Email</Label>
              <Input
                id="storeEmail"
                type="email"
                value={settings.storeEmail}
                onChange={(e) => setSettings({...settings, storeEmail: e.target.value})}
              />
              <p className="text-xs text-gray-500 mt-1">Customers will receive return updates from this email</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="h-5 w-5" />
              <span>Return Policy</span>
            </CardTitle>
            <CardDescription>Configure your return policy defaults</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="returnWindow">Return Window (Days)</Label>
              <Input
                id="returnWindow"
                type="number"
                value={settings.returnWindow}
                onChange={(e) => setSettings({...settings, returnWindow: parseInt(e.target.value) || 30})}
                min="1"
                max="365"
              />
            </div>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="autoApprove"
                  checked={settings.autoApprove}
                  onChange={(e) => setSettings({...settings, autoApprove: e.target.checked})}
                  className="rounded"
                />
                <Label htmlFor="autoApprove">Auto-approve eligible returns</Label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="requirePhotos"
                  checked={settings.requirePhotos}
                  onChange={(e) => setSettings({...settings, requirePhotos: e.target.checked})}
                  className="rounded"
                />
                <Label htmlFor="requirePhotos">Require photos for return requests</Label>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Mail className="h-5 w-5" />
            <span>Customer Communication</span>
          </CardTitle>
          <CardDescription>Customize messages shown to customers</CardDescription>
        </CardHeader>
        <CardContent>
          <div>
            <Label htmlFor="customMessage">Welcome Message</Label>
            <Textarea
              id="customMessage"
              value={settings.customMessage}
              onChange={(e) => setSettings({...settings, customMessage: e.target.value})}
              rows={3}
              placeholder="Enter a custom welcome message for your return portal..."
            />
            <p className="text-xs text-gray-500 mt-1">This message will be shown to customers on your return portal</p>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving}>
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