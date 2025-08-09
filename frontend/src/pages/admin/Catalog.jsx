import React from 'react';
import { BookOpen, Settings, Mail, Workflow } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';

const AdminCatalog = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Templates Catalog</h1>
        <p className="text-gray-500">Manage email templates, workflows, and rule presets</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Mail className="h-5 w-5" />
              <span>Email Templates</span>
            </CardTitle>
            <CardDescription>Customer notification templates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm text-gray-600">12 templates</p>
              <Button variant="outline" className="w-full" size="sm">
                Manage Templates
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Workflow className="h-5 w-5" />
              <span>Workflow Templates</span>
            </CardTitle>
            <CardDescription>Pre-built workflow automation</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm text-gray-600">8 templates</p>
              <Button variant="outline" className="w-full" size="sm">
                Manage Workflows
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileTemplate className="h-5 w-5" />
              <span>Rule Presets</span>
            </CardTitle>
            <CardDescription>Common return rule configurations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm text-gray-600">6 presets</p>
              <Button variant="outline" className="w-full" size="sm">
                Manage Rules
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BookOpen className="h-5 w-5" />
            <span>Template Management</span>
          </CardTitle>
          <CardDescription>Centralized template and preset management</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <FileTemplate className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Template Catalog</h3>
            <p className="text-gray-600">
              Template management features are currently in development.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminCatalog;