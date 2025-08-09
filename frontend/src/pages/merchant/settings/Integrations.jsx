import React from 'react';
import { Plug, ShoppingBag, CreditCard, Truck } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';

const Integrations = () => {
  const integrations = [
    {
      name: 'Shopify',
      description: 'Sync orders and customer data',
      icon: ShoppingBag,
      status: 'connected',
      color: 'bg-green-100 text-green-800'
    },
    {
      name: 'Stripe',
      description: 'Process refunds automatically',
      icon: CreditCard,
      status: 'available',
      color: 'bg-gray-100 text-gray-800'
    },
    {
      name: 'Shipping Carriers',
      description: 'Generate return labels',
      icon: Truck,
      status: 'available', 
      color: 'bg-gray-100 text-gray-800'
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-500">Connect with your favorite tools and services</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations.map((integration) => {
          const Icon = integration.icon;
          return (
            <Card key={integration.name}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Icon className="h-8 w-8 text-gray-600" />
                  <Badge className={integration.color}>
                    {integration.status}
                  </Badge>
                </div>
                <CardTitle>{integration.name}</CardTitle>
                <CardDescription>{integration.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  variant={integration.status === 'connected' ? 'outline' : 'default'}
                  className="w-full"
                  disabled={integration.status === 'available'}
                >
                  {integration.status === 'connected' ? 'Configure' : 
                   integration.status === 'available' ? 'Coming Soon' : 'Connect'}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Plug className="h-5 w-5" />
            <span>Integration Hub</span>
          </CardTitle>
          <CardDescription>More integrations coming soon</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-gray-600">
              We're constantly adding new integrations. Have a specific tool in mind? Let us know!
            </p>
            <Button variant="outline" className="mt-4">
              Request Integration
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Integrations;