import React from 'react';
import { Flag, ToggleLeft, ToggleRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';

const AdminFeatureFlags = () => {
  const flags = [
    { name: 'workflows', label: 'Workflow Engine', enabled: false, description: 'Advanced workflow automation' },
    { name: 'ai_suggestions', label: 'AI Suggestions', enabled: true, description: 'AI-powered return suggestions' },
    { name: 'team_features', label: 'Team Features', enabled: false, description: 'Team collaboration tools' },
    { name: 'advanced_analytics', label: 'Advanced Analytics', enabled: false, description: 'Enhanced reporting features' }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Feature Flags</h1>
        <p className="text-gray-500">Control feature availability across the platform</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Flag className="h-5 w-5" />
            <span>Feature Control</span>
          </CardTitle>
          <CardDescription>Enable or disable features for all tenants</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {flags.map((flag) => (
              <div key={flag.name} className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-semibold">{flag.label}</h3>
                  <p className="text-sm text-gray-500">{flag.description}</p>
                </div>
                <div className="flex items-center space-x-3">
                  <Badge className={flag.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                    {flag.enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                  {flag.enabled ? 
                    <ToggleRight className="h-6 w-6 text-green-600 cursor-pointer" /> : 
                    <ToggleLeft className="h-6 w-6 text-gray-400 cursor-pointer" />
                  }
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminFeatureFlags;