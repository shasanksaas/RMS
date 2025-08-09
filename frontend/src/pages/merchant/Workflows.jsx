import React from 'react';
import { Workflow, Plus, Play } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';

const Workflows = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Workflows</h1>
            <p className="text-gray-500">Automate complex return processes</p>
          </div>
          <Badge variant="secondary">Feature Flag</Badge>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" disabled>
            <Play className="h-4 w-4 mr-2" />
            Run Workflow
          </Button>
          <Button disabled>
            <Plus className="h-4 w-4 mr-2" />
            Create Workflow
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Workflow className="h-5 w-5" />
            <span>Workflow Builder</span>
          </CardTitle>
          <CardDescription>
            Design custom workflows for complex return scenarios
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Workflow className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Workflows Feature</h3>
            <p className="text-gray-600 mb-4">
              This advanced feature is currently disabled. Contact support to enable workflow functionality for your account.
            </p>
            <Badge variant="secondary">Available in Enterprise Plan</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Workflows;