import React from 'react';
import { CreditCard, Crown, Zap, Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';

const Billing = () => {
  const plans = [
    {
      name: 'Starter',
      price: 19,
      current: false,
      features: ['Up to 100 returns/month', 'Basic analytics', 'Email support']
    },
    {
      name: 'Growth', 
      price: 49,
      current: true,
      features: ['Up to 500 returns/month', 'Advanced analytics', 'AI suggestions', 'Priority support']
    },
    {
      name: 'Enterprise',
      price: 99,
      current: false,
      features: ['Unlimited returns', 'Custom workflows', 'White-label portal', 'Dedicated support']
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Billing & Plans</h1>
          <p className="text-gray-500">Manage your subscription and usage</p>
        </div>
        <Badge variant="secondary">Test Mode</Badge>
      </div>

      {/* Current Plan */}
      <Card className="border-green-200 bg-green-50">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Crown className="h-5 w-5 text-green-600" />
            <span>Current Plan: Growth</span>
          </CardTitle>
          <CardDescription>Your subscription renews on February 15, 2024</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h4 className="font-medium">Monthly Usage</h4>
              <p className="text-2xl font-bold text-green-600">87 / 500</p>
              <p className="text-sm text-gray-600">Returns processed</p>
            </div>
            <div>
              <h4 className="font-medium">Next Billing</h4>
              <p className="text-2xl font-bold">$49</p>
              <p className="text-sm text-gray-600">Due Feb 15, 2024</p>
            </div>
            <div>
              <h4 className="font-medium">Features</h4>
              <div className="flex items-center space-x-2">
                <Zap className="h-4 w-4 text-yellow-600" />
                <span className="text-sm">AI Suggestions Active</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Available Plans */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card key={plan.name} className={plan.current ? 'border-blue-500 shadow-lg' : ''}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{plan.name}</CardTitle>
                {plan.current && <Badge>Current</Badge>}
              </div>
              <div className="text-3xl font-bold">${plan.price}<span className="text-lg text-gray-500">/mo</span></div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-green-600" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
              <Button 
                className="w-full mt-6" 
                variant={plan.current ? 'outline' : 'default'}
                disabled={plan.current}
              >
                {plan.current ? 'Current Plan' : plan.price > 49 ? 'Upgrade' : 'Downgrade'}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <CreditCard className="h-5 w-5" />
            <span>Billing Integration</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <CreditCard className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Stripe Integration Coming Soon</h3>
            <p className="text-gray-600">
              Full billing management with Stripe integration is currently in development.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Billing;