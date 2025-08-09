import React from 'react';
import { Mail, Send, Settings } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';

const Email = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Email Settings</h1>
        <p className="text-gray-500">Configure email notifications and templates</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Mail className="h-5 w-5" />
            <span>Email Configuration</span>
          </CardTitle>
          <CardDescription>Set up your email delivery service</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Send className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Email Service Coming Soon</h3>
            <p className="text-gray-600">
              Email configuration and template management features are currently in development.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Email;