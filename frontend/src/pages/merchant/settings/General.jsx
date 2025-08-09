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
    storeName: '',
    storeEmail: '',
    returnWindow: 30,
    autoApprove: true,
    requirePhotos: false,
    customMessage: ''
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // Get backend URL from environment
  const backendUrl = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
  const tenantId = 'tenant-fashion-store'; // TODO: Get from auth context

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/tenants/${tenantId}/settings`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        const data = await response.json();
        const settingsData = data.settings || {};
        
        setSettings({
          storeName: settingsData.store_name || 'Fashion Forward',
          storeEmail: settingsData.support_email || 'support@fashionforward.com',
          returnWindow: settingsData.return_window_days || 30,
          autoApprove: settingsData.auto_approve_eligible_returns || true,
          requirePhotos: settingsData.require_photos || false,
          customMessage: settingsData.welcome_message || 'We\'re here to help with your return!'
        });
      } else {
        console.error('Failed to load settings:', response.status);
        setMessage({ type: 'error', text: 'Failed to load settings' });
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      setMessage({ type: 'error', text: 'Error loading settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage({ type: '', text: '' });

      const payload = {
        store_name: settings.storeName,
        support_email: settings.storeEmail,
        return_window_days: settings.returnWindow,
        auto_approve_eligible_returns: settings.autoApprove,
        require_photos: settings.requirePhotos,
        welcome_message: settings.customMessage
      };

      const response = await fetch(`${backendUrl}/api/tenants/${tenantId}/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Settings saved successfully!' });
        setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      } else {
        const errorData = await response.json();
        setMessage({ type: 'error', text: errorData.detail || 'Failed to save settings' });
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage({ type: 'error', text: 'Error saving settings' });
    } finally {
      setSaving(false);
    }
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