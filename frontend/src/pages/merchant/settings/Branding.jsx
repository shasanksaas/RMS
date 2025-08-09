import React, { useState } from 'react';
import { Palette, Upload, Eye, Save } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';

const Branding = () => {
  const [branding, setBranding] = useState({
    primaryColor: '#3b82f6',
    logoUrl: '',
    customCSS: ''
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Branding Settings</h1>
        <p className="text-gray-500">Customize the look and feel of your return portal</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Palette className="h-5 w-5" />
              <span>Colors & Theme</span>
            </CardTitle>
            <CardDescription>Customize colors to match your brand</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="primaryColor">Primary Color</Label>
              <div className="flex items-center space-x-3 mt-2">
                <input
                  type="color"
                  id="primaryColor"
                  value={branding.primaryColor}
                  onChange={(e) => setBranding({...branding, primaryColor: e.target.value})}
                  className="w-12 h-10 rounded border border-gray-300"
                />
                <Input
                  value={branding.primaryColor}
                  onChange={(e) => setBranding({...branding, primaryColor: e.target.value})}
                  placeholder="#3b82f6"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Upload className="h-5 w-5" />
              <span>Logo & Assets</span>
            </CardTitle>
            <CardDescription>Upload your logo and brand assets</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
              <Upload className="h-8 w-8 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Logo Upload</h3>
              <p className="text-gray-600 mb-4">Upload your logo to customize the return portal</p>
              <Button variant="outline">Choose File</Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Eye className="h-5 w-5" />
            <span>Preview</span>
          </CardTitle>
          <CardDescription>Preview how your branding will look</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg p-6" style={{ backgroundColor: `${branding.primaryColor}10` }}>
            <div className="flex items-center space-x-4 mb-6">
              <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                <span className="text-xs text-gray-500">Logo</span>
              </div>
              <div>
                <h3 className="text-xl font-bold" style={{ color: branding.primaryColor }}>
                  Return Center
                </h3>
                <p className="text-gray-600">Easy returns and exchanges</p>
              </div>
            </div>
            <Button style={{ backgroundColor: branding.primaryColor, color: 'white' }}>
              Sample Button
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button>
          <Save className="h-4 w-4 mr-2" />
          Save Branding
        </Button>
      </div>
    </div>
  );
};

export default Branding;