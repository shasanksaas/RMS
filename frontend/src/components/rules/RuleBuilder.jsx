import React, { useState, useEffect } from 'react';
import { Plus, Minus, Save, X, TestTube2, Settings, HelpCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';

const RuleBuilder = ({ rule = null, onSave, onCancel, isOpen }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [ruleData, setRuleData] = useState({
    name: '',
    description: '',
    condition_groups: [
      {
        conditions: [
          {
            field: '',
            operator: '',
            value: '',
            custom_field_name: ''
          }
        ],
        logic_operator: 'and'
      }
    ],
    actions: [
      {
        action_type: '',
        parameters: {}
      }
    ],
    priority: 1,
    is_active: true,
    tags: []
  });

  const [fieldOptions, setFieldOptions] = useState({
    field_types: [],
    operators: [],
    actions: []
  });

  const [testResult, setTestResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingFieldOptions, setIsLoadingFieldOptions] = useState(false);
  const [errors, setErrors] = useState({});

  // Load field options and rule data on mount
  useEffect(() => {
    if (isOpen) {
      loadFieldOptions();
      if (rule) {
        setRuleData({
          ...rule,
          condition_groups: rule.condition_groups || [{
            conditions: [{ field: '', operator: '', value: '', custom_field_name: '' }],
            logic_operator: 'and'
          }],
          actions: rule.actions || [{ action_type: '', parameters: {} }]
        });
      }
    }
  }, [isOpen, rule]);

  const loadFieldOptions = async () => {
    try {
      console.log('Loading field options...');
      setIsLoadingFieldOptions(true);
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/rules/field-types/options`, {
        headers: {
          'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Field options loaded:', data);
      console.log('Field types count:', data.field_types?.length);
      console.log('Operators count:', data.operators?.length);
      console.log('Actions count:', data.actions?.length);
      
      setFieldOptions(data);
    } catch (error) {
      console.error('Failed to load field options:', error);
      // Set default empty arrays in case of error
      setFieldOptions({
        field_types: [],
        operators: [],
        actions: []
      });
    } finally {
      setIsLoadingFieldOptions(false);
    }
  };

  const validateCurrentStep = () => {
    const newErrors = {};

    if (currentStep === 1) {
      if (!ruleData.name.trim()) newErrors.name = 'Rule name is required';
      if (!ruleData.description.trim()) newErrors.description = 'Description is required';
    }

    if (currentStep === 2) {
      ruleData.condition_groups.forEach((group, groupIndex) => {
        group.conditions.forEach((condition, condIndex) => {
          if (!condition.field) {
            newErrors[`condition_${groupIndex}_${condIndex}_field`] = 'Field is required';
          }
          if (!condition.operator) {
            newErrors[`condition_${groupIndex}_${condIndex}_operator`] = 'Operator is required';
          }
          if (!condition.value && condition.value !== 0) {
            newErrors[`condition_${groupIndex}_${condIndex}_value`] = 'Value is required';
          }
        });
      });
    }

    if (currentStep === 3) {
      ruleData.actions.forEach((action, actionIndex) => {
        if (!action.action_type) {
          newErrors[`action_${actionIndex}_type`] = 'Action type is required';
        }
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateCurrentStep()) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    setCurrentStep(currentStep - 1);
  };

  const addCondition = (groupIndex) => {
    const newConditionGroups = [...ruleData.condition_groups];
    newConditionGroups[groupIndex].conditions.push({
      field: '',
      operator: '',
      value: '',
      custom_field_name: ''
    });
    setRuleData({ ...ruleData, condition_groups: newConditionGroups });
  };

  const removeCondition = (groupIndex, conditionIndex) => {
    const newConditionGroups = [...ruleData.condition_groups];
    newConditionGroups[groupIndex].conditions.splice(conditionIndex, 1);
    setRuleData({ ...ruleData, condition_groups: newConditionGroups });
  };

  const updateCondition = (groupIndex, conditionIndex, field, value) => {
    const newConditionGroups = [...ruleData.condition_groups];
    newConditionGroups[groupIndex].conditions[conditionIndex][field] = value;
    setRuleData({ ...ruleData, condition_groups: newConditionGroups });
  };

  const addConditionGroup = () => {
    const newConditionGroups = [...ruleData.condition_groups, {
      conditions: [{ field: '', operator: '', value: '', custom_field_name: '' }],
      logic_operator: 'and'
    }];
    setRuleData({ ...ruleData, condition_groups: newConditionGroups });
  };

  const removeConditionGroup = (groupIndex) => {
    const newConditionGroups = ruleData.condition_groups.filter((_, index) => index !== groupIndex);
    setRuleData({ ...ruleData, condition_groups: newConditionGroups });
  };

  const addAction = () => {
    const newActions = [...ruleData.actions, { action_type: '', parameters: {} }];
    setRuleData({ ...ruleData, actions: newActions });
  };

  const removeAction = (actionIndex) => {
    const newActions = ruleData.actions.filter((_, index) => index !== actionIndex);
    setRuleData({ ...ruleData, actions: newActions });
  };

  const updateAction = (actionIndex, field, value) => {
    const newActions = [...ruleData.actions];
    if (field === 'action_type') {
      newActions[actionIndex].action_type = value;
      newActions[actionIndex].parameters = {}; // Reset parameters
    } else {
      newActions[actionIndex][field] = value;
    }
    setRuleData({ ...ruleData, actions: newActions });
  };

  const testRule = async () => {
    setIsLoading(true);
    try {
      const testData = {
        order_data: {
          total_amount: 150.00,
          financial_status: 'paid',
          fulfillment_status: 'fulfilled',
          order_date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(), // 10 days ago
          items: [
            { category: 'Clothing', sku: 'SHIRT-001', product_name: 'Cotton T-Shirt' }
          ],
          billing_address: { country: 'US', province: 'CA' },
          payment_method: 'credit_card'
        },
        return_data: {
          reason: 'defective',
          refund_amount: 75.00,
          items_to_return: [
            { sku: 'SHIRT-001', product_name: 'Cotton T-Shirt', quantity: 1, price: 75.00 }
          ]
        }
      };

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/rules/test-conditions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
        },
        body: JSON.stringify({
          conditions: ruleData.condition_groups,
          test_data: testData
        })
      });

      const result = await response.json();
      setTestResult(result);
    } catch (error) {
      console.error('Test failed:', error);
      setTestResult({ success: false, error: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!validateCurrentStep()) return;

    setIsLoading(true);
    try {
      await onSave(ruleData);
    } catch (error) {
      console.error('Failed to save rule:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {rule ? 'Edit Rule' : 'Create New Rule'}
              </h2>
              <p className="text-gray-500 mt-1">
                Step {currentStep} of 4: {
                  currentStep === 1 ? 'Basic Information' :
                  currentStep === 2 ? 'Conditions' :
                  currentStep === 3 ? 'Actions' : 'Review & Save'
                }
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={onCancel}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center space-x-4 mt-4">
            {[1, 2, 3, 4].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step === currentStep ? 'bg-blue-600 text-white' :
                  step < currentStep ? 'bg-green-600 text-white' :
                  'bg-gray-200 text-gray-600'
                }`}>
                  {step}
                </div>
                {step < 4 && (
                  <div className={`w-12 h-0.5 ${
                    step < currentStep ? 'bg-green-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rule Name *
                </label>
                <Input
                  value={ruleData.name}
                  onChange={(e) => setRuleData({ ...ruleData, name: e.target.value })}
                  placeholder="e.g., Auto-approve defective items"
                  className={errors.name ? 'border-red-500' : ''}
                />
                {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description *
                </label>
                <Textarea
                  value={ruleData.description}
                  onChange={(e) => setRuleData({ ...ruleData, description: e.target.value })}
                  placeholder="Describe what this rule does and when it should be applied"
                  rows={3}
                  className={errors.description ? 'border-red-500' : ''}
                />
                {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority
                  </label>
                  <Input
                    type="number"
                    value={ruleData.priority}
                    onChange={(e) => setRuleData({ ...ruleData, priority: parseInt(e.target.value) || 1 })}
                    min="1"
                    max="999"
                  />
                  <p className="text-xs text-gray-500 mt-1">Lower number = higher priority</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <div className="flex items-center space-x-2 pt-2">
                    <Switch
                      checked={ruleData.is_active}
                      onCheckedChange={(checked) => setRuleData({ ...ruleData, is_active: checked })}
                    />
                    <span className="text-sm text-gray-600">
                      {ruleData.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags (Optional)
                </label>
                <Input
                  value={ruleData.tags.join(', ')}
                  onChange={(e) => setRuleData({ 
                    ...ruleData, 
                    tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
                  })}
                  placeholder="e.g., defective, warranty, high-value"
                />
                <p className="text-xs text-gray-500 mt-1">Separate tags with commas</p>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Conditions</h3>
                <Button onClick={testRule} variant="outline" size="sm" disabled={isLoading}>
                  <TestTube2 className="h-4 w-4 mr-2" />
                  Test Conditions
                </Button>
              </div>

              {ruleData.condition_groups.map((group, groupIndex) => (
                <Card key={groupIndex} className="border border-gray-200">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium">
                        Condition Group {groupIndex + 1}
                      </CardTitle>
                      {ruleData.condition_groups.length > 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeConditionGroup(groupIndex)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">Logic:</span>
                      <Select
                        value={group.logic_operator}
                        onValueChange={(value) => {
                          const newGroups = [...ruleData.condition_groups];
                          newGroups[groupIndex].logic_operator = value;
                          setRuleData({ ...ruleData, condition_groups: newGroups });
                        }}
                      >
                        <SelectTrigger className="w-20 h-7">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="and">AND</SelectItem>
                          <SelectItem value="or">OR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {group.conditions.map((condition, conditionIndex) => (
                      <div key={conditionIndex} className="grid grid-cols-12 gap-2 items-start">
                        <div className="col-span-3">
                          <Select
                            value={condition.field}
                            onValueChange={(value) => updateCondition(groupIndex, conditionIndex, 'field', value)}
                          >
                            <SelectTrigger className={errors[`condition_${groupIndex}_${conditionIndex}_field`] ? 'border-red-500' : ''}>
                              <SelectValue placeholder="Select field" />
                            </SelectTrigger>
                            <SelectContent>
                              {fieldOptions.field_types && fieldOptions.field_types.length > 0 ? (
                                fieldOptions.field_types.map((field) => (
                                  <SelectItem key={field.value} value={field.value}>
                                    {field.label}
                                  </SelectItem>
                                ))
                              ) : (
                                <SelectItem value="" disabled>
                                  Loading field options...
                                </SelectItem>
                              )}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="col-span-3">
                          <Select
                            value={condition.operator}
                            onValueChange={(value) => updateCondition(groupIndex, conditionIndex, 'operator', value)}
                          >
                            <SelectTrigger className={errors[`condition_${groupIndex}_${conditionIndex}_operator`] ? 'border-red-500' : ''}>
                              <SelectValue placeholder="Select operator" />
                            </SelectTrigger>
                            <SelectContent>
                              {fieldOptions.operators && fieldOptions.operators.length > 0 ? (
                                fieldOptions.operators.map((op) => (
                                  <SelectItem key={op.value} value={op.value}>
                                    {op.label}
                                  </SelectItem>
                                ))
                              ) : (
                                <SelectItem value="" disabled>
                                  Loading operators...
                                </SelectItem>
                              )}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="col-span-4">
                          <Input
                            value={condition.value}
                            onChange={(e) => updateCondition(groupIndex, conditionIndex, 'value', e.target.value)}
                            placeholder="Enter value"
                            className={errors[`condition_${groupIndex}_${conditionIndex}_value`] ? 'border-red-500' : ''}
                          />
                        </div>

                        <div className="col-span-2 flex items-center space-x-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => addCondition(groupIndex)}
                            className="text-blue-600 hover:text-blue-700"
                          >
                            <Plus className="h-4 w-4" />
                          </Button>
                          {group.conditions.length > 1 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeCondition(groupIndex, conditionIndex)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Minus className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              ))}

              <Button onClick={addConditionGroup} variant="outline" className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Condition Group
              </Button>

              {testResult && (
                <Alert className={testResult.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
                  <TestTube2 className="h-4 w-4" />
                  <AlertDescription>
                    <div className="space-y-2">
                      <p className="font-medium">
                        Test Result: {testResult.result?.rule_matched ? 'Conditions Met ✓' : 'Conditions Not Met ✗'}
                      </p>
                      {testResult.result?.steps && (
                        <div className="space-y-1 text-sm">
                          {testResult.result.steps.map((step, index) => (
                            <div key={index} className={step.condition_met ? 'text-green-700' : 'text-red-700'}>
                              {step.explanation}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Actions</h3>
                <Button onClick={addAction} variant="outline" size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Action
                </Button>
              </div>

              {ruleData.actions.map((action, actionIndex) => (
                <Card key={actionIndex} className="border border-gray-200">
                  <CardContent className="pt-6">
                    <div className="grid grid-cols-12 gap-4 items-start">
                      <div className="col-span-8">
                        <Select
                          value={action.action_type}
                          onValueChange={(value) => updateAction(actionIndex, 'action_type', value)}
                        >
                          <SelectTrigger className={errors[`action_${actionIndex}_type`] ? 'border-red-500' : ''}>
                            <SelectValue placeholder="Select action" />
                          </SelectTrigger>
                          <SelectContent>
                            {fieldOptions.actions && fieldOptions.actions.length > 0 ? (
                              fieldOptions.actions.map((actionType) => (
                                <SelectItem key={actionType.value} value={actionType.value}>
                                  {actionType.label}
                                </SelectItem>
                              ))
                            ) : (
                              <SelectItem value="" disabled>
                                Loading actions...
                              </SelectItem>
                            )}
                          </SelectContent>
                        </Select>
                        {errors[`action_${actionIndex}_type`] && (
                          <p className="text-red-500 text-sm mt-1">{errors[`action_${actionIndex}_type`]}</p>
                        )}
                      </div>

                      <div className="col-span-4 flex justify-end">
                        {ruleData.actions.length > 1 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeAction(actionIndex)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Minus className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Action Parameters */}
                    {action.action_type && fieldOptions.actions.find(a => a.value === action.action_type)?.parameters?.length > 0 && (
                      <div className="mt-4 space-y-3">
                        <h4 className="text-sm font-medium text-gray-700">Parameters</h4>
                        {fieldOptions.actions.find(a => a.value === action.action_type).parameters.map((param) => (
                          <div key={param.name}>
                            <label className="block text-sm text-gray-600 mb-1">
                              {param.name} {param.required && '*'}
                            </label>
                            <Input
                              value={action.parameters[param.name] || ''}
                              onChange={(e) => {
                                const newActions = [...ruleData.actions];
                                newActions[actionIndex].parameters[param.name] = e.target.value;
                                setRuleData({ ...ruleData, actions: newActions });
                              }}
                              placeholder={`Enter ${param.name}`}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {currentStep === 4 && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Review & Save</h3>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{ruleData.name}</CardTitle>
                  <p className="text-sm text-gray-600">{ruleData.description}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Priority:</span> {ruleData.priority}
                    </div>
                    <div>
                      <span className="font-medium">Status:</span>{' '}
                      <Badge variant={ruleData.is_active ? 'default' : 'secondary'}>
                        {ruleData.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>

                  {ruleData.tags.length > 0 && (
                    <div>
                      <span className="font-medium text-sm">Tags:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {ruleData.tags.map((tag, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <span className="font-medium text-sm">Conditions:</span>
                    <div className="mt-2 p-3 bg-gray-50 rounded text-xs">
                      {ruleData.condition_groups.map((group, groupIndex) => (
                        <div key={groupIndex} className="mb-2">
                          <div className="font-medium">Group {groupIndex + 1} (Logic: {group.logic_operator.toUpperCase()})</div>
                          {group.conditions.map((condition, condIndex) => (
                            <div key={condIndex} className="ml-2 text-gray-600">
                              • {condition.field} {condition.operator} {condition.value}
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <span className="font-medium text-sm">Actions:</span>
                    <div className="mt-2 p-3 bg-gray-50 rounded text-xs">
                      {ruleData.actions.map((action, actionIndex) => (
                        <div key={actionIndex} className="text-gray-600">
                          • {action.action_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t p-6 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {currentStep > 1 && (
              <Button variant="outline" onClick={handlePrevious}>
                Previous
              </Button>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <Button variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
            {currentStep < 4 ? (
              <Button onClick={handleNext}>
                Next
              </Button>
            ) : (
              <Button onClick={handleSave} disabled={isLoading}>
                <Save className="h-4 w-4 mr-2" />
                {isLoading ? 'Saving...' : 'Save Rule'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RuleBuilder;