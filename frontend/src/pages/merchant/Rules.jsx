import React from 'react';
import { Settings, Plus, Play, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';

const Rules = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Return Rules</h1>
          <p className="text-gray-500">Automate your return approval process</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline">
            <Play className="h-4 w-4 mr-2" />
            Test Rules
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Rule
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5" />
            <span>Rules Engine</span>
          </CardTitle>
          <CardDescription>
            Create intelligent rules to automatically approve or flag returns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Rules Engine Coming Soon</h3>
            <p className="text-gray-600">
              Advanced rule builder and simulation features are currently in development.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Rules;