import React, { useState } from 'react';
import { CheckCircle, ArrowRight, Rocket } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';

const OnboardingWizard = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 5;

  const steps = [
    { id: 1, title: 'Welcome', description: 'Get started with your return management setup' },
    { id: 2, title: 'Brand Setup', description: 'Configure your store branding and contact info' },
    { id: 3, title: 'Return Policy', description: 'Set your return window and rules' },
    { id: 4, title: 'Email Setup', description: 'Configure email notifications' },
    { id: 5, title: 'Complete', description: 'Your return portal is ready!' }
  ];

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Progress Header */}
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
          <Rocket className="h-8 w-8 text-blue-600" />
        </div>
        <div>
          <h1 className="text-4xl font-bold text-gray-900">Setup Wizard</h1>
          <p className="text-xl text-gray-600">Get your return management system ready in just a few steps</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          {steps.map((step) => (
            <div key={step.id} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                step.id < currentStep ? 'bg-green-500 text-white' :
                step.id === currentStep ? 'bg-blue-500 text-white' :
                'bg-gray-200 text-gray-500'
              }`}>
                {step.id < currentStep ? <CheckCircle className="h-4 w-4" /> : step.id}
              </div>
              {step.id < totalSteps && (
                <div className={`w-24 h-1 mx-2 ${
                  step.id < currentStep ? 'bg-green-500' : 'bg-gray-200'
                }`} />
              )}
            </div>
          ))}
        </div>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">{steps[currentStep - 1].title}</h2>
          <p className="text-gray-600">{steps[currentStep - 1].description}</p>
        </div>
      </div>

      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle>Step {currentStep} of {totalSteps}</CardTitle>
          <CardDescription>Complete this step to continue</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Onboarding Wizard</h3>
            <p className="text-gray-600 mb-4">
              The guided setup wizard is currently in development. This will help you configure your return management system step by step.
            </p>
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Coming soon:</p>
              <ul className="text-sm text-gray-500 space-y-1">
                <li>• Brand and contact information setup</li>
                <li>• Return policy configuration</li>
                <li>• Email service connection</li>
                <li>• Shopify integration</li>
                <li>• Sample return test</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button 
          variant="outline" 
          onClick={handlePrevious} 
          disabled={currentStep === 1}
        >
          Previous
        </Button>
        
        <Button onClick={handleNext} disabled={currentStep === totalSteps}>
          {currentStep === totalSteps ? 'Complete' : 'Next'}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

export default OnboardingWizard;