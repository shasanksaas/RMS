import React from 'react';
import { Users, UserPlus, Shield } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';

const Team = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Team & Roles</h1>
            <p className="text-gray-500">Manage team members and permissions</p>
          </div>
          <Badge variant="secondary">Feature Flag</Badge>
        </div>
        <Button disabled>
          <UserPlus className="h-4 w-4 mr-2" />
          Invite Team Member
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Team Management</span>
          </CardTitle>
          <CardDescription>Collaborate with your team on return management</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Team Features</h3>
            <p className="text-gray-600 mb-4">
              Team collaboration features are currently disabled. This feature is available in higher tier plans.
            </p>
            <Badge variant="secondary">Available in Enterprise Plan</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Team;