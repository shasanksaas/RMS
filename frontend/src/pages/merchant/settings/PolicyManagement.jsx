import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Textarea } from '../../../components/ui/textarea';
import { Switch } from '../../../components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Badge } from '../../../components/ui/badge';
import { Separator } from '../../../components/ui/separator';
import { useAuth } from '../../../contexts/AuthContext';
import { 
  Settings, 
  Save, 
  Eye, 
  Play, 
  Plus, 
  Trash2, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Globe,
  CreditCard,
  Package,
  Mail,
  Shield,
  BarChart3,
  Zap,
  MapPin,
  Truck,
  DollarSign,
  Gift,
  ShoppingBag,
  Star,
  Users,
  Bot,
  FileText,
  Workflow,
  Database
} from 'lucide-react';

const PolicyManagement = () => {
  const { user } = useAuth();
  const [policies, setPolicies] = useState([]);
  const [currentPolicy, setCurrentPolicy] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Initialize with comprehensive default policy
  const [policyForm, setPolicyForm] = useState({
    name: 'Comprehensive Return Policy',
    description: 'Complete return management policy with all features',
    
    // Policy Zones & Location Settings
    policy_zones: [
      {
        zone_name: 'North America',
        countries_included: ['US', 'CA'],
        states_provinces: ['NY', 'CA', 'TX', 'FL', 'ON', 'BC'],
        postal_codes: {
          include_ranges: ['00000-99999'],
          exclude_specific: []
        },
        destination_warehouse: 'warehouse_main',
        backup_destinations: ['warehouse_backup'],
        generate_labels: true,
        bypass_manual_review: false,
        generate_packing_slips: true,
        customs_handling: {
          enabled: true,
          auto_complete_forms: true,
          duty_responsibility: 'customer'
        },
        carrier_restrictions: {
          allowed_carriers: ['UPS', 'FedEx', 'USPS'],
          preferred_carrier: 'UPS',
          international_only_carriers: ['DHL']
        }
      }
    ],
    
    // Return Window Configurations
    return_windows: {
      standard_window: {
        type: 'limited',
        days: [30],
        calculation_from: 'order_date',
        business_days_only: false,
        exclude_weekends: false,
        exclude_holidays: true,
        holiday_calendar: 'us'
      },
      extended_windows: {
        holiday_extension: {
          enabled: true,
          extra_days: 15,
          applicable_months: ['November', 'December', 'January']
        },
        loyalty_member_extension: {
          enabled: true,
          bronze_extra_days: 7,
          silver_extra_days: 14,
          gold_extra_days: 30,
          platinum_extra_days: 60
        },
        first_time_buyer_extension: {
          enabled: true,
          extra_days: 10
        }
      },
      category_specific_windows: {
        enabled: true,
        rules: [
          { category: 'Electronics', days: 14 },
          { category: 'Clothing', days: 30 },
          { category: 'Jewelry', days: 7 },
          { category: 'Home_Goods', days: 45 }
        ]
      },
      price_based_windows: {
        enabled: true,
        tiers: [
          { min_price: 0, max_price: 50, days: 14 },
          { min_price: 50, max_price: 200, days: 30 },
          { min_price: 200, max_price: 999999, days: 45 }
        ]
      }
    },
    
    // Product Eligibility & Exclusions
    product_eligibility: {
      default_returnable: true,
      tag_based_rules: {
        final_sale_tags: ['final_sale', 'clearance', 'outlet'],
        exchange_only_tags: ['exchange_only', 'hygiene'],
        non_returnable_tags: ['custom', 'personalized', 'digital'],
        expedited_tags: ['vip_item', 'premium']
      },
      category_exclusions: {
        excluded_categories: [
          'Digital_Downloads',
          'Gift_Cards', 
          'Perishable_Food',
          'Intimate_Apparel',
          'Swimwear',
          'Custom_Made'
        ]
      },
      condition_requirements: {
        unworn_unused_only: true,
        original_packaging_required: true,
        tags_attached_required: true,
        hygiene_seal_intact: true,
        accessories_included: true,
        manual_receipt_required: false
      },
      value_based_rules: {
        min_return_value: 5.00,
        max_return_value: 10000.00,
        high_value_manual_review: true,
        high_value_threshold: 500.00
      }
    },
    
    // Refund Settings
    refund_settings: {
      enabled: true,
      processing_events: ['delivered'],
      processing_delay: { 
        enabled: true, 
        delay_days: [3], 
        business_days_only: true 
      },
      refund_methods: {
        original_payment_method: true,
        store_credit: true,
        bank_transfer: false,
        check_by_mail: false,
        paypal: true,
        crypto: false
      },
      partial_refunds: {
        enabled: true,
        damage_deduction: {
          minor_damage_percent: 10,
          moderate_damage_percent: 25,
          major_damage_percent: 50
        }
      },
      fees: {
        restocking_fee: { 
          enabled: true, 
          amount: 15.00, 
          type: 'flat_rate',
          waive_for_defective: true,
          waive_for_vip: true
        },
        return_shipping_deduction: { 
          enabled: true, 
          amount: 'flat_rate', 
          flat_rate_amount: 7.95 
        }
      }
    },
    
    // Exchange Settings
    exchange_settings: {
      enabled: true,
      same_product_only: false,
      advanced_exchanges: true,
      exchange_types: {
        size_color_variant: true,
        different_product: true,
        upgrade_product: true,
        downgrade_product: true
      },
      instant_exchanges: {
        enabled: true,
        authorization_method: 'one_dollar',
        return_deadline_days: [14]
      }
    },
    
    // Store Credit Settings
    store_credit_settings: {
      enabled: true,
      provider: 'shopify',
      bonus_incentives: {
        enabled: true,
        bonus_type: 'percentage',
        percentage_amount: 15,
        minimum_order_for_bonus: 25.00
      }
    },
    
    // Fraud Detection
    fraud_detection: {
      ai_models: {
        enabled: true,
        risk_scoring: {
          low_risk: '0-30',
          medium_risk: '31-70',
          high_risk: '71-100'
        }
      },
      behavioral_patterns: {
        max_returns_per_month: 10,
        max_return_value_per_month: 1000.00
      }
    },
    
    // Shipping & Logistics
    shipping_logistics: {
      label_generation: {
        providers: ['EasyPost'],
        carrier_integration: {
          domestic_carriers: ['UPS', 'FedEx', 'USPS']
        }
      },
      return_methods: {
        mail_return: true,
        drop_off_locations: {
          carrier_locations: true
        }
      }
    }
  });

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/policies/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Tenant-Id': user.tenant_id
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPolicies(data.items || []);
        
        if (data.items && data.items.length > 0) {
          loadPolicy(data.items[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading policies:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPolicy = async (policyId) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/policies/${policyId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Tenant-Id': user.tenant_id
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentPolicy(data.policy);
        setPolicyForm(data.policy);
      }
    } catch (error) {
      console.error('Error loading policy:', error);
    }
  };

  const savePolicy = async () => {
    try {
      setSaving(true);
      
      const url = currentPolicy 
        ? `${process.env.REACT_APP_BACKEND_URL}/api/policies/${currentPolicy.id}`
        : `${process.env.REACT_APP_BACKEND_URL}/api/policies/`;
      
      const method = currentPolicy ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Tenant-Id': user.tenant_id
        },
        body: JSON.stringify(policyForm)
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentPolicy(data.policy);
        loadPolicies();
        alert('Policy saved successfully!');
      } else {
        const error = await response.json();
        alert(`Error saving policy: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error saving policy:', error);
      alert('Error saving policy');
    } finally {
      setSaving(false);
    }
  };

  const testPolicy = async () => {
    if (!currentPolicy) return;
    
    try {
      const testData = {
        return_data: {
          total_value: 100,
          items: [{ sku: 'TEST-SKU', category: 'Clothing', tags: [] }],
          reason: 'wrong_size'
        },
        order_data: {
          created_at: new Date().toISOString(),
          total_price: 100
        }
      };

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/policies/${currentPolicy.id}/evaluate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Tenant-Id': user.tenant_id
        },
        body: JSON.stringify(testData)
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Policy Test Result: ${data.evaluation_result.outcome}\nResolution Types: ${data.evaluation_result.resolution_types.join(', ')}`);
      }
    } catch (error) {
      console.error('Error testing policy:', error);
    }
  };

  const updatePolicyField = (path, value) => {
    const keys = path.split('.');
    const newForm = { ...policyForm };
    let current = newForm;
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) current[keys[i]] = {};
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    setPolicyForm(newForm);
  };

  // Policy Overview Component
  const PolicyOverview = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Policy Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="policy-name">Policy Name</Label>
            <Input
              id="policy-name"
              value={policyForm.name}
              onChange={(e) => updatePolicyField('name', e.target.value)}
              placeholder="Enter policy name"
            />
          </div>
          <div>
            <Label htmlFor="policy-description">Description</Label>
            <Textarea
              id="policy-description"
              value={policyForm.description}
              onChange={(e) => updatePolicyField('description', e.target.value)}
              placeholder="Describe this policy"
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Policy Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Switch
                checked={policyForm.is_active || false}
                onCheckedChange={(value) => updatePolicyField('is_active', value)}
              />
              <Label>Active Policy</Label>
            </div>
            <Badge variant={policyForm.is_active ? 'success' : 'secondary'}>
              {policyForm.is_active ? 'Active' : 'Inactive'}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Policy Zones Component
  const PolicyZones = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Policy Zones & Location Settings
          </CardTitle>
          <CardDescription>
            Configure geographic zones, shipping destinations, and location-specific rules
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {policyForm.policy_zones?.map((zone, zoneIndex) => (
            <div key={zoneIndex} className="border rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Zone {zoneIndex + 1}: {zone.zone_name}</h4>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => {
                    const newZones = [...policyForm.policy_zones];
                    newZones.splice(zoneIndex, 1);
                    updatePolicyField('policy_zones', newZones);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
              
              <div>
                <Label>Zone Name</Label>
                <Input
                  value={zone.zone_name}
                  onChange={(e) => {
                    const newZones = [...policyForm.policy_zones];
                    newZones[zoneIndex].zone_name = e.target.value;
                    updatePolicyField('policy_zones', newZones);
                  }}
                  placeholder="Enter zone name"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Countries Included</Label>
                  <Input
                    value={zone.countries_included?.join(', ') || ''}
                    onChange={(e) => {
                      const newZones = [...policyForm.policy_zones];
                      newZones[zoneIndex].countries_included = e.target.value.split(',').map(s => s.trim()).filter(s => s);
                      updatePolicyField('policy_zones', newZones);
                    }}
                    placeholder="US, CA, UK, AU (country codes)"
                  />
                </div>
                <div>
                  <Label>States/Provinces</Label>
                  <Input
                    value={zone.states_provinces?.join(', ') || ''}
                    onChange={(e) => {
                      const newZones = [...policyForm.policy_zones];
                      newZones[zoneIndex].states_provinces = e.target.value.split(',').map(s => s.trim()).filter(s => s);
                      updatePolicyField('policy_zones', newZones);
                    }}
                    placeholder="NY, CA, TX, FL"
                  />
                </div>
              </div>

              <div>
                <Label>Postal Code Ranges (Include)</Label>
                <Input
                  value={zone.postal_codes?.include_ranges?.join(', ') || ''}
                  onChange={(e) => {
                    const newZones = [...policyForm.policy_zones];
                    if (!newZones[zoneIndex].postal_codes) newZones[zoneIndex].postal_codes = {};
                    newZones[zoneIndex].postal_codes.include_ranges = e.target.value.split(',').map(s => s.trim()).filter(s => s);
                    updatePolicyField('policy_zones', newZones);
                  }}
                  placeholder="00000-99999, 10000-19999"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Destination Warehouse</Label>
                  <Select 
                    value={zone.destination_warehouse || 'warehouse_main'}
                    onValueChange={(value) => {
                      const newZones = [...policyForm.policy_zones];
                      newZones[zoneIndex].destination_warehouse = value;
                      updatePolicyField('policy_zones', newZones);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="warehouse_main">Main Warehouse</SelectItem>
                      <SelectItem value="warehouse_east">East Coast Warehouse</SelectItem>
                      <SelectItem value="warehouse_west">West Coast Warehouse</SelectItem>
                      <SelectItem value="warehouse_intl">International Warehouse</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Preferred Carrier</Label>
                  <Select 
                    value={zone.carrier_restrictions?.preferred_carrier || 'UPS'}
                    onValueChange={(value) => {
                      const newZones = [...policyForm.policy_zones];
                      if (!newZones[zoneIndex].carrier_restrictions) newZones[zoneIndex].carrier_restrictions = {};
                      newZones[zoneIndex].carrier_restrictions.preferred_carrier = value;
                      updatePolicyField('policy_zones', newZones);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="UPS">UPS</SelectItem>
                      <SelectItem value="FedEx">FedEx</SelectItem>
                      <SelectItem value="USPS">USPS</SelectItem>
                      <SelectItem value="DHL">DHL</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-3">
                <h5 className="font-medium">Zone Features</h5>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={zone.generate_labels || false}
                      onCheckedChange={(value) => {
                        const newZones = [...policyForm.policy_zones];
                        newZones[zoneIndex].generate_labels = value;
                        updatePolicyField('policy_zones', newZones);
                      }}
                    />
                    <Label>Generate Return Labels</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={zone.generate_packing_slips || false}
                      onCheckedChange={(value) => {
                        const newZones = [...policyForm.policy_zones];
                        newZones[zoneIndex].generate_packing_slips = value;
                        updatePolicyField('policy_zones', newZones);
                      }}
                    />
                    <Label>Generate Packing Slips</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={zone.bypass_manual_review || false}
                      onCheckedChange={(value) => {
                        const newZones = [...policyForm.policy_zones];
                        newZones[zoneIndex].bypass_manual_review = value;
                        updatePolicyField('policy_zones', newZones);
                      }}
                    />
                    <Label>Bypass Manual Review</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={zone.customs_handling?.enabled || false}
                      onCheckedChange={(value) => {
                        const newZones = [...policyForm.policy_zones];
                        if (!newZones[zoneIndex].customs_handling) newZones[zoneIndex].customs_handling = {};
                        newZones[zoneIndex].customs_handling.enabled = value;
                        updatePolicyField('policy_zones', newZones);
                      }}
                    />
                    <Label>Auto Customs Handling</Label>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          <Button 
            variant="outline" 
            onClick={() => {
              const newZone = {
                zone_name: `Zone ${policyForm.policy_zones.length + 1}`,
                countries_included: [],
                states_provinces: [],
                postal_codes: { include_ranges: [], exclude_specific: [] },
                destination_warehouse: 'warehouse_main',
                backup_destinations: [],
                generate_labels: true,
                bypass_manual_review: false,
                generate_packing_slips: true,
                customs_handling: { enabled: false },
                carrier_restrictions: { preferred_carrier: 'UPS' }
              };
              updatePolicyField('policy_zones', [...policyForm.policy_zones, newZone]);
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add New Zone
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  // Return Windows Component
  const ReturnWindows = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Standard Return Window
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Window Type</Label>
              <Select 
                value={policyForm.return_windows?.standard_window?.type || 'limited'}
                onValueChange={(value) => updatePolicyField('return_windows.standard_window.type', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="limited">Limited Time</SelectItem>
                  <SelectItem value="unlimited">Unlimited</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Days Allowed</Label>
              <Select 
                value={policyForm.return_windows?.standard_window?.days?.[0]?.toString() || '30'}
                onValueChange={(value) => updatePolicyField('return_windows.standard_window.days', [parseInt(value)])}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">7 days</SelectItem>
                  <SelectItem value="14">14 days</SelectItem>
                  <SelectItem value="15">15 days</SelectItem>
                  <SelectItem value="30">30 days</SelectItem>
                  <SelectItem value="45">45 days</SelectItem>
                  <SelectItem value="60">60 days</SelectItem>
                  <SelectItem value="90">90 days</SelectItem>
                  <SelectItem value="180">180 days</SelectItem>
                  <SelectItem value="365">365 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Calculate From</Label>
              <Select 
                value={policyForm.return_windows?.standard_window?.calculation_from || 'order_date'}
                onValueChange={(value) => updatePolicyField('return_windows.standard_window.calculation_from', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="order_date">Order Date</SelectItem>
                  <SelectItem value="fulfillment_date">Fulfillment Date</SelectItem>
                  <SelectItem value="delivery_date">Delivery Date</SelectItem>
                  <SelectItem value="first_delivery_attempt">First Delivery Attempt</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Holiday Calendar</Label>
              <Select 
                value={policyForm.return_windows?.standard_window?.holiday_calendar || 'us'}
                onValueChange={(value) => updatePolicyField('return_windows.standard_window.holiday_calendar', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="us">US Holidays</SelectItem>
                  <SelectItem value="uk">UK Holidays</SelectItem>
                  <SelectItem value="custom">Custom Calendar</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Switch
                checked={policyForm.return_windows?.standard_window?.business_days_only || false}
                onCheckedChange={(value) => updatePolicyField('return_windows.standard_window.business_days_only', value)}
              />
              <Label>Business Days Only</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                checked={policyForm.return_windows?.standard_window?.exclude_holidays || false}
                onCheckedChange={(value) => updatePolicyField('return_windows.standard_window.exclude_holidays', value)}
              />
              <Label>Exclude Holidays</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                checked={policyForm.return_windows?.standard_window?.exclude_weekends || false}
                onCheckedChange={(value) => updatePolicyField('return_windows.standard_window.exclude_weekends', value)}
              />
              <Label>Exclude Weekends</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Extended Windows</CardTitle>
          <CardDescription>Configure special extensions for holidays, loyalty members, and first-time buyers</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Holiday Extension */}
          <div className="border rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Holiday Extension</Label>
                <p className="text-sm text-gray-500">Extra days during holiday seasons</p>
              </div>
              <Switch
                checked={policyForm.return_windows?.extended_windows?.holiday_extension?.enabled || false}
                onCheckedChange={(value) => updatePolicyField('return_windows.extended_windows.holiday_extension.enabled', value)}
              />
            </div>
            
            {policyForm.return_windows?.extended_windows?.holiday_extension?.enabled && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Extra Days</Label>
                  <Input
                    type="number"
                    value={policyForm.return_windows?.extended_windows?.holiday_extension?.extra_days || 15}
                    onChange={(e) => updatePolicyField('return_windows.extended_windows.holiday_extension.extra_days', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <Label>Applicable Months</Label>
                  <Input
                    value={policyForm.return_windows?.extended_windows?.holiday_extension?.applicable_months?.join(', ') || 'November, December, January'}
                    onChange={(e) => updatePolicyField('return_windows.extended_windows.holiday_extension.applicable_months', e.target.value.split(',').map(s => s.trim()))}
                    placeholder="November, December, January"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Loyalty Member Extension */}
          <div className="border rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Loyalty Member Extension</Label>
                <p className="text-sm text-gray-500">Extended windows based on loyalty tier</p>
              </div>
              <Switch
                checked={policyForm.return_windows?.extended_windows?.loyalty_member_extension?.enabled || false}
                onCheckedChange={(value) => updatePolicyField('return_windows.extended_windows.loyalty_member_extension.enabled', value)}
              />
            </div>
            
            {policyForm.return_windows?.extended_windows?.loyalty_member_extension?.enabled && (
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <Label>Bronze (+days)</Label>
                  <Input
                    type="number"
                    value={policyForm.return_windows?.extended_windows?.loyalty_member_extension?.bronze_extra_days || 7}
                    onChange={(e) => updatePolicyField('return_windows.extended_windows.loyalty_member_extension.bronze_extra_days', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <Label>Silver (+days)</Label>
                  <Input
                    type="number"
                    value={policyForm.return_windows?.extended_windows?.loyalty_member_extension?.silver_extra_days || 14}
                    onChange={(e) => updatePolicyField('return_windows.extended_windows.loyalty_member_extension.silver_extra_days', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <Label>Gold (+days)</Label>
                  <Input
                    type="number"
                    value={policyForm.return_windows?.extended_windows?.loyalty_member_extension?.gold_extra_days || 30}
                    onChange={(e) => updatePolicyField('return_windows.extended_windows.loyalty_member_extension.gold_extra_days', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <Label>Platinum (+days)</Label>
                  <Input
                    type="number"
                    value={policyForm.return_windows?.extended_windows?.loyalty_member_extension?.platinum_extra_days || 60}
                    onChange={(e) => updatePolicyField('return_windows.extended_windows.loyalty_member_extension.platinum_extra_days', parseInt(e.target.value))}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Category Specific Windows */}
          <div className="border rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Category Specific Windows</Label>
                <p className="text-sm text-gray-500">Different return windows per product category</p>
              </div>
              <Switch
                checked={policyForm.return_windows?.category_specific_windows?.enabled || false}
                onCheckedChange={(value) => updatePolicyField('return_windows.category_specific_windows.enabled', value)}
              />
            </div>
            
            {policyForm.return_windows?.category_specific_windows?.enabled && (
              <div className="space-y-3">
                {policyForm.return_windows?.category_specific_windows?.rules?.map((rule, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <Input
                      value={rule.category}
                      onChange={(e) => {
                        const newRules = [...policyForm.return_windows.category_specific_windows.rules];
                        newRules[index].category = e.target.value;
                        updatePolicyField('return_windows.category_specific_windows.rules', newRules);
                      }}
                      placeholder="Category name"
                      className="flex-1"
                    />
                    <Input
                      type="number"
                      value={rule.days}
                      onChange={(e) => {
                        const newRules = [...policyForm.return_windows.category_specific_windows.rules];
                        newRules[index].days = parseInt(e.target.value);
                        updatePolicyField('return_windows.category_specific_windows.rules', newRules);
                      }}
                      placeholder="Days"
                      className="w-20"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newRules = [...policyForm.return_windows.category_specific_windows.rules];
                        newRules.splice(index, 1);
                        updatePolicyField('return_windows.category_specific_windows.rules', newRules);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const newRules = [...(policyForm.return_windows?.category_specific_windows?.rules || [])];
                    newRules.push({ category: '', days: 30 });
                    updatePolicyField('return_windows.category_specific_windows.rules', newRules);
                  }}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Category Rule
                </Button>
              </div>
            )}
          </div>

          {/* Price Based Windows */}
          <div className="border rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Price Based Windows</Label>
                <p className="text-sm text-gray-500">Different return windows based on order value</p>
              </div>
              <Switch
                checked={policyForm.return_windows?.price_based_windows?.enabled || false}
                onCheckedChange={(value) => updatePolicyField('return_windows.price_based_windows.enabled', value)}
              />
            </div>
            
            {policyForm.return_windows?.price_based_windows?.enabled && (
              <div className="space-y-3">
                {policyForm.return_windows?.price_based_windows?.tiers?.map((tier, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <Input
                      type="number"
                      step="0.01"
                      value={tier.min_price}
                      onChange={(e) => {
                        const newTiers = [...policyForm.return_windows.price_based_windows.tiers];
                        newTiers[index].min_price = parseFloat(e.target.value);
                        updatePolicyField('return_windows.price_based_windows.tiers', newTiers);
                      }}
                      placeholder="Min $"
                      className="w-24"
                    />
                    <span>-</span>
                    <Input
                      type="number"
                      step="0.01"
                      value={tier.max_price}
                      onChange={(e) => {
                        const newTiers = [...policyForm.return_windows.price_based_windows.tiers];
                        newTiers[index].max_price = parseFloat(e.target.value);
                        updatePolicyField('return_windows.price_based_windows.tiers', newTiers);
                      }}
                      placeholder="Max $"
                      className="w-24"
                    />
                    <Input
                      type="number"
                      value={tier.days}
                      onChange={(e) => {
                        const newTiers = [...policyForm.return_windows.price_based_windows.tiers];
                        newTiers[index].days = parseInt(e.target.value);
                        updatePolicyField('return_windows.price_based_windows.tiers', newTiers);
                      }}
                      placeholder="Days"
                      className="w-20"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newTiers = [...policyForm.return_windows.price_based_windows.tiers];
                        newTiers.splice(index, 1);
                        updatePolicyField('return_windows.price_based_windows.tiers', newTiers);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const newTiers = [...(policyForm.return_windows?.price_based_windows?.tiers || [])];
                    newTiers.push({ min_price: 0, max_price: 100, days: 30 });
                    updatePolicyField('return_windows.price_based_windows.tiers', newTiers);
                  }}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Price Tier
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Product Eligibility Component
  const ProductEligibility = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Product Eligibility & Exclusions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <Label>Default Products Returnable</Label>
            <Switch
              checked={policyForm.product_eligibility?.default_returnable !== false}
              onCheckedChange={(value) => updatePolicyField('product_eligibility.default_returnable', value)}
            />
          </div>

          {/* Tag-Based Rules */}
          <div className="space-y-4">
            <h4 className="font-medium">Tag-Based Rules</h4>
            
            <div>
              <Label>Final Sale Tags (Non-Returnable)</Label>
              <Input
                value={policyForm.product_eligibility?.tag_based_rules?.final_sale_tags?.join(', ') || 'final_sale, clearance, outlet'}
                onChange={(e) => updatePolicyField('product_eligibility.tag_based_rules.final_sale_tags', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
                placeholder="final_sale, clearance, outlet"
              />
            </div>
            
            <div>
              <Label>Exchange Only Tags</Label>
              <Input
                value={policyForm.product_eligibility?.tag_based_rules?.exchange_only_tags?.join(', ') || 'exchange_only, hygiene'}
                onChange={(e) => updatePolicyField('product_eligibility.tag_based_rules.exchange_only_tags', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
                placeholder="exchange_only, hygiene"
              />
            </div>
            
            <div>
              <Label>Non-Returnable Tags</Label>
              <Input
                value={policyForm.product_eligibility?.tag_based_rules?.non_returnable_tags?.join(', ') || 'custom, personalized, digital'}
                onChange={(e) => updatePolicyField('product_eligibility.tag_based_rules.non_returnable_tags', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
                placeholder="custom, personalized, digital"
              />
            </div>

            <div>
              <Label>Expedited Processing Tags</Label>
              <Input
                value={policyForm.product_eligibility?.tag_based_rules?.expedited_tags?.join(', ') || 'vip_item, premium'}
                onChange={(e) => updatePolicyField('product_eligibility.tag_based_rules.expedited_tags', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
                placeholder="vip_item, premium"
              />
            </div>
          </div>

          {/* Category Exclusions */}
          <div className="space-y-4">
            <h4 className="font-medium">Category Exclusions</h4>
            <div>
              <Label>Excluded Categories</Label>
              <Textarea
                value={policyForm.product_eligibility?.category_exclusions?.excluded_categories?.join('\n') || 'Digital_Downloads\nGift_Cards\nPerishable_Food\nIntimate_Apparel\nSwimwear\nCustom_Made\nLive_Plants\nHazardous_Materials\nPrescription_Items'}
                onChange={(e) => updatePolicyField('product_eligibility.category_exclusions.excluded_categories', e.target.value.split('\n').filter(s => s.trim()))}
                placeholder="One category per line"
                rows={6}
              />
            </div>
          </div>

          {/* Condition Requirements */}
          <div className="space-y-4">
            <h4 className="font-medium">Condition Requirements</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.product_eligibility?.condition_requirements?.unworn_unused_only || false}
                  onCheckedChange={(value) => updatePolicyField('product_eligibility.condition_requirements.unworn_unused_only', value)}
                />
                <Label>Unworn/Unused Only</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.product_eligibility?.condition_requirements?.original_packaging_required || false}
                  onCheckedChange={(value) => updatePolicyField('product_eligibility.condition_requirements.original_packaging_required', value)}
                />
                <Label>Original Packaging Required</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.product_eligibility?.condition_requirements?.tags_attached_required || false}
                  onCheckedChange={(value) => updatePolicyField('product_eligibility.condition_requirements.tags_attached_required', value)}
                />
                <Label>Tags Must Be Attached</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.product_eligibility?.condition_requirements?.hygiene_seal_intact || false}
                  onCheckedChange={(value) => updatePolicyField('product_eligibility.condition_requirements.hygiene_seal_intact', value)}
                />
                <Label>Hygiene Seal Intact</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.product_eligibility?.condition_requirements?.accessories_included || false}
                  onCheckedChange={(value) => updatePolicyField('product_eligibility.condition_requirements.accessories_included', value)}
                />
                <Label>All Accessories Included</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.product_eligibility?.condition_requirements?.manual_receipt_required || false}
                  onCheckedChange={(value) => updatePolicyField('product_eligibility.condition_requirements.manual_receipt_required', value)}
                />
                <Label>Manual Receipt Required</Label>
              </div>
            </div>
          </div>

          {/* Value-Based Rules */}
          <div className="space-y-4">
            <h4 className="font-medium">Value-Based Rules</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Minimum Return Value ($)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={policyForm.product_eligibility?.value_based_rules?.min_return_value || 5.00}
                  onChange={(e) => updatePolicyField('product_eligibility.value_based_rules.min_return_value', parseFloat(e.target.value))}
                />
              </div>
              <div>
                <Label>Maximum Return Value ($)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={policyForm.product_eligibility?.value_based_rules?.max_return_value || 10000.00}
                  onChange={(e) => updatePolicyField('product_eligibility.value_based_rules.max_return_value', parseFloat(e.target.value))}
                />
              </div>
              <div>
                <Label>High Value Threshold ($)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={policyForm.product_eligibility?.value_based_rules?.high_value_threshold || 500.00}
                  onChange={(e) => updatePolicyField('product_eligibility.value_based_rules.high_value_threshold', parseFloat(e.target.value))}
                />
              </div>
              <div className="flex items-center space-x-2 pt-6">
                <Switch
                  checked={policyForm.product_eligibility?.value_based_rules?.high_value_manual_review || false}
                  onCheckedChange={(value) => updatePolicyField('product_eligibility.value_based_rules.high_value_manual_review', value)}
                />
                <Label>High Value Manual Review</Label>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Return Outcomes Component
  const ReturnOutcomes = () => (
    <div className="space-y-6">
      {/* Refund Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Refund Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <Label>Enable Refunds</Label>
            <Switch
              checked={policyForm.refund_settings?.enabled !== false}
              onCheckedChange={(value) => updatePolicyField('refund_settings.enabled', value)}
            />
          </div>

          {policyForm.refund_settings?.enabled !== false && (
            <>
              {/* Processing Events */}
              <div>
                <Label>Process Refund When</Label>
                <Select 
                  value={policyForm.refund_settings?.processing_events?.[0] || 'delivered'}
                  onValueChange={(value) => updatePolicyField('refund_settings.processing_events', [value])}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="immediate">Immediate</SelectItem>
                    <SelectItem value="label_created">Label Created</SelectItem>
                    <SelectItem value="pre_transit">Pre Transit</SelectItem>
                    <SelectItem value="in_transit">In Transit</SelectItem>
                    <SelectItem value="out_for_delivery">Out for Delivery</SelectItem>
                    <SelectItem value="delivered">Delivered to Warehouse</SelectItem>
                    <SelectItem value="manual_approval">Manual Approval</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Processing Delay */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Processing Delay (Days)</Label>
                  <Select 
                    value={policyForm.refund_settings?.processing_delay?.delay_days?.[0]?.toString() || '3'}
                    onValueChange={(value) => updatePolicyField('refund_settings.processing_delay.delay_days', [parseInt(value)])}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">Immediate</SelectItem>
                      <SelectItem value="1">1 day</SelectItem>
                      <SelectItem value="2">2 days</SelectItem>
                      <SelectItem value="3">3 days</SelectItem>
                      <SelectItem value="5">5 days</SelectItem>
                      <SelectItem value="7">1 week</SelectItem>
                      <SelectItem value="14">2 weeks</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2 pt-6">
                  <Switch
                    checked={policyForm.refund_settings?.processing_delay?.business_days_only || false}
                    onCheckedChange={(value) => updatePolicyField('refund_settings.processing_delay.business_days_only', value)}
                  />
                  <Label>Business Days Only</Label>
                </div>
              </div>

              {/* Refund Methods */}
              <div className="space-y-3">
                <Label>Available Refund Methods</Label>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(policyForm.refund_settings?.refund_methods || {}).map(([method, enabled]) => (
                    <div key={method} className="flex items-center space-x-2">
                      <Switch
                        checked={enabled}
                        onCheckedChange={(value) => updatePolicyField(`refund_settings.refund_methods.${method}`, value)}
                      />
                      <Label className="capitalize">{method.replace(/_/g, ' ')}</Label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Fees */}
              <div className="space-y-4">
                <h4 className="font-medium">Fees & Deductions</h4>
                
                {/* Restocking Fee */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Restocking Fee</Label>
                    <Switch
                      checked={policyForm.refund_settings?.fees?.restocking_fee?.enabled || false}
                      onCheckedChange={(value) => updatePolicyField('refund_settings.fees.restocking_fee.enabled', value)}
                    />
                  </div>
                  
                  {policyForm.refund_settings?.fees?.restocking_fee?.enabled && (
                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <Label>Type</Label>
                        <Select 
                          value={policyForm.refund_settings?.fees?.restocking_fee?.type || 'flat_rate'}
                          onValueChange={(value) => updatePolicyField('refund_settings.fees.restocking_fee.type', value)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="flat_rate">Flat Rate</SelectItem>
                            <SelectItem value="percentage">Percentage</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Amount</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={policyForm.refund_settings?.fees?.restocking_fee?.amount || 15.00}
                          onChange={(e) => updatePolicyField('refund_settings.fees.restocking_fee.amount', parseFloat(e.target.value))}
                        />
                      </div>
                      <div className="flex items-center space-x-2 pt-6">
                        <Switch
                          checked={policyForm.refund_settings?.fees?.restocking_fee?.waive_for_defective || false}
                          onCheckedChange={(value) => updatePolicyField('refund_settings.fees.restocking_fee.waive_for_defective', value)}
                        />
                        <Label className="text-sm">Waive for Defective</Label>
                      </div>
                    </div>
                  )}
                </div>

                {/* Return Shipping Deduction */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Return Shipping Deduction</Label>
                    <Switch
                      checked={policyForm.refund_settings?.fees?.return_shipping_deduction?.enabled || false}
                      onCheckedChange={(value) => updatePolicyField('refund_settings.fees.return_shipping_deduction.enabled', value)}
                    />
                  </div>
                  
                  {policyForm.refund_settings?.fees?.return_shipping_deduction?.enabled && (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label>Deduction Type</Label>
                        <Select 
                          value={policyForm.refund_settings?.fees?.return_shipping_deduction?.amount || 'flat_rate'}
                          onValueChange={(value) => updatePolicyField('refund_settings.fees.return_shipping_deduction.amount', value)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="actual_cost">Actual Cost</SelectItem>
                            <SelectItem value="flat_rate">Flat Rate</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Flat Rate Amount ($)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={policyForm.refund_settings?.fees?.return_shipping_deduction?.flat_rate_amount || 7.95}
                          onChange={(e) => updatePolicyField('refund_settings.fees.return_shipping_deduction.flat_rate_amount', parseFloat(e.target.value))}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Partial Refunds */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Partial Refunds (Damage/Wear Deductions)</h4>
                  <Switch
                    checked={policyForm.refund_settings?.partial_refunds?.enabled || false}
                    onCheckedChange={(value) => updatePolicyField('refund_settings.partial_refunds.enabled', value)}
                  />
                </div>
                
                {policyForm.refund_settings?.partial_refunds?.enabled && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label>Minor Damage (%)</Label>
                      <Input
                        type="number"
                        value={policyForm.refund_settings?.partial_refunds?.damage_deduction?.minor_damage_percent || 10}
                        onChange={(e) => updatePolicyField('refund_settings.partial_refunds.damage_deduction.minor_damage_percent', parseInt(e.target.value))}
                      />
                    </div>
                    <div>
                      <Label>Moderate Damage (%)</Label>
                      <Input
                        type="number"
                        value={policyForm.refund_settings?.partial_refunds?.damage_deduction?.moderate_damage_percent || 25}
                        onChange={(e) => updatePolicyField('refund_settings.partial_refunds.damage_deduction.moderate_damage_percent', parseInt(e.target.value))}
                      />
                    </div>
                    <div>
                      <Label>Major Damage (%)</Label>
                      <Input
                        type="number"
                        value={policyForm.refund_settings?.partial_refunds?.damage_deduction?.major_damage_percent || 50}
                        onChange={(e) => updatePolicyField('refund_settings.partial_refunds.damage_deduction.major_damage_percent', parseInt(e.target.value))}
                      />
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Exchange Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Exchange Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <Label>Enable Exchanges</Label>
            <Switch
              checked={policyForm.exchange_settings?.enabled !== false}
              onCheckedChange={(value) => updatePolicyField('exchange_settings.enabled', value)}
            />
          </div>

          {policyForm.exchange_settings?.enabled !== false && (
            <>
              <div className="space-y-3">
                <Label>Exchange Types</Label>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(policyForm.exchange_settings?.exchange_types || {}).map(([type, enabled]) => (
                    <div key={type} className="flex items-center space-x-2">
                      <Switch
                        checked={enabled}
                        onCheckedChange={(value) => updatePolicyField(`exchange_settings.exchange_types.${type}`, value)}
                      />
                      <Label className="capitalize">{type.replace(/_/g, ' ')}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Instant Exchanges</Label>
                    <p className="text-sm text-gray-500">Ship replacement before receiving return</p>
                  </div>
                  <Switch
                    checked={policyForm.exchange_settings?.instant_exchanges?.enabled || false}
                    onCheckedChange={(value) => updatePolicyField('exchange_settings.instant_exchanges.enabled', value)}
                  />
                </div>
                
                {policyForm.exchange_settings?.instant_exchanges?.enabled && (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Authorization Method</Label>
                      <Select 
                        value={policyForm.exchange_settings?.instant_exchanges?.authorization_method || 'one_dollar'}
                        onValueChange={(value) => updatePolicyField('exchange_settings.instant_exchanges.authorization_method', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="one_dollar">$1 Authorization</SelectItem>
                          <SelectItem value="full_value">Full Value Hold</SelectItem>
                          <SelectItem value="credit_check">Credit Check</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Return Deadline (Days)</Label>
                      <Input
                        type="number"
                        value={policyForm.exchange_settings?.instant_exchanges?.return_deadline_days?.[0] || 14}
                        onChange={(e) => updatePolicyField('exchange_settings.instant_exchanges.return_deadline_days', [parseInt(e.target.value)])}
                      />
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Store Credit Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gift className="h-5 w-5" />
            Store Credit Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <Label>Enable Store Credit</Label>
            <Switch
              checked={policyForm.store_credit_settings?.enabled !== false}
              onCheckedChange={(value) => updatePolicyField('store_credit_settings.enabled', value)}
            />
          </div>

          {policyForm.store_credit_settings?.enabled !== false && (
            <>
              <div>
                <Label>Provider</Label>
                <Select 
                  value={policyForm.store_credit_settings?.provider || 'shopify'}
                  onValueChange={(value) => updatePolicyField('store_credit_settings.provider', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="shopify">Shopify</SelectItem>
                    <SelectItem value="rise_ai">Rise.ai</SelectItem>
                    <SelectItem value="yotpo">Yotpo</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Bonus Incentives</Label>
                    <p className="text-sm text-gray-500">Offer extra credit for choosing store credit</p>
                  </div>
                  <Switch
                    checked={policyForm.store_credit_settings?.bonus_incentives?.enabled || false}
                    onCheckedChange={(value) => updatePolicyField('store_credit_settings.bonus_incentives.enabled', value)}
                  />
                </div>
                
                {policyForm.store_credit_settings?.bonus_incentives?.enabled && (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Bonus Type</Label>
                      <Select 
                        value={policyForm.store_credit_settings?.bonus_incentives?.bonus_type || 'percentage'}
                        onValueChange={(value) => updatePolicyField('store_credit_settings.bonus_incentives.bonus_type', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="flat_rate">Flat Rate ($)</SelectItem>
                          <SelectItem value="percentage">Percentage (%)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Bonus Amount</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={policyForm.store_credit_settings?.bonus_incentives?.percentage_amount || 15}
                        onChange={(e) => updatePolicyField('store_credit_settings.bonus_incentives.percentage_amount', parseFloat(e.target.value))}
                      />
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );

  // Advanced Settings Component
  const AdvancedSettings = () => (
    <div className="space-y-6">
      {/* Fraud Detection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />  
            Fraud Detection & Prevention
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Label>Enable AI Fraud Detection</Label>
              <p className="text-sm text-gray-500">Automatically detect suspicious return patterns</p>
            </div>
            <Switch
              checked={policyForm.fraud_detection?.ai_models?.enabled || false}
              onCheckedChange={(value) => updatePolicyField('fraud_detection.ai_models.enabled', value)}
            />
          </div>

          {policyForm.fraud_detection?.ai_models?.enabled && (
            <>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Low Risk Threshold</Label>
                  <Input
                    value={policyForm.fraud_detection?.ai_models?.risk_scoring?.low_risk || '0-30'}
                    onChange={(e) => updatePolicyField('fraud_detection.ai_models.risk_scoring.low_risk', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Medium Risk Threshold</Label>
                  <Input
                    value={policyForm.fraud_detection?.ai_models?.risk_scoring?.medium_risk || '31-70'}
                    onChange={(e) => updatePolicyField('fraud_detection.ai_models.risk_scoring.medium_risk', e.target.value)}
                  />
                </div>
                <div>
                  <Label>High Risk Threshold</Label>
                  <Input
                    value={policyForm.fraud_detection?.ai_models?.risk_scoring?.high_risk || '71-100'}
                    onChange={(e) => updatePolicyField('fraud_detection.ai_models.risk_scoring.high_risk', e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Behavioral Patterns</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Max Returns Per Month</Label>
                    <Input
                      type="number"
                      value={policyForm.fraud_detection?.behavioral_patterns?.max_returns_per_month || 10}
                      onChange={(e) => updatePolicyField('fraud_detection.behavioral_patterns.max_returns_per_month', parseInt(e.target.value))}
                    />
                  </div>
                  <div>
                    <Label>Max Return Value Per Month ($)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={policyForm.fraud_detection?.behavioral_patterns?.max_return_value_per_month || 1000}
                      onChange={(e) => updatePolicyField('fraud_detection.behavioral_patterns.max_return_value_per_month', parseFloat(e.target.value))}
                    />
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Shipping & Logistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Truck className="h-5 w-5" />
            Shipping & Logistics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label>Label Generation Provider</Label>
            <Select 
              value={policyForm.shipping_logistics?.label_generation?.providers?.[0] || 'EasyPost'}
              onValueChange={(value) => updatePolicyField('shipping_logistics.label_generation.providers', [value])}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="EasyPost">EasyPost</SelectItem>
                <SelectItem value="ShipStation">ShipStation</SelectItem>
                <SelectItem value="Shippo">Shippo</SelectItem>
                <SelectItem value="Direct_Carrier">Direct Carrier</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Domestic Carriers</Label>
            <Input
              value={policyForm.shipping_logistics?.label_generation?.carrier_integration?.domestic_carriers?.join(', ') || 'UPS, FedEx, USPS, DHL'}
              onChange={(e) => updatePolicyField('shipping_logistics.label_generation.carrier_integration.domestic_carriers', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
              placeholder="UPS, FedEx, USPS, DHL"
            />
          </div>

          <div>
            <Label>International Carriers</Label>
            <Input
              value={policyForm.shipping_logistics?.label_generation?.carrier_integration?.international_carriers?.join(', ') || 'DHL, FedEx_Intl, UPS_Intl'}
              onChange={(e) => updatePolicyField('shipping_logistics.label_generation.carrier_integration.international_carriers', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
              placeholder="DHL, FedEx_Intl, UPS_Intl"
            />
          </div>

          <div className="space-y-3">
            <Label>Return Methods</Label>
            <div className="flex items-center space-x-2">
              <Switch
                checked={policyForm.shipping_logistics?.return_methods?.mail_return !== false}
                onCheckedChange={(value) => updatePolicyField('shipping_logistics.return_methods.mail_return', value)}
              />
              <Label>Mail Return</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                checked={policyForm.shipping_logistics?.return_methods?.drop_off_locations?.carrier_locations || false}
                onCheckedChange={(value) => updatePolicyField('shipping_logistics.return_methods.drop_off_locations.carrier_locations', value)}
              />
              <Label>Carrier Drop-off Locations</Label>
            </div>
          </div>

          <div className="space-y-3">
            <Label>Packaging Requirements</Label>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.shipping_logistics?.packaging_requirements?.original_packaging_preferred || false}
                  onCheckedChange={(value) => updatePolicyField('shipping_logistics.packaging_requirements.original_packaging_preferred', value)}
                />
                <Label>Original Packaging Preferred</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.shipping_logistics?.packaging_requirements?.accept_any_packaging || false}
                  onCheckedChange={(value) => updatePolicyField('shipping_logistics.packaging_requirements.accept_any_packaging', value)}
                />
                <Label>Accept Any Packaging</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.shipping_logistics?.packaging_requirements?.fragile_item_requirements || false}
                  onCheckedChange={(value) => updatePolicyField('shipping_logistics.packaging_requirements.fragile_item_requirements', value)}
                />
                <Label>Fragile Item Requirements</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.shipping_logistics?.packaging_requirements?.hazmat_restrictions || false}
                  onCheckedChange={(value) => updatePolicyField('shipping_logistics.packaging_requirements.hazmat_restrictions', value)}
                />
                <Label>Hazmat Restrictions</Label>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <Label>Tracking & Notifications</Label>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.shipping_logistics?.tracking?.real_time_tracking || false}
                  onCheckedChange={(value) => updatePolicyField('shipping_logistics.tracking.real_time_tracking', value)}
                />
                <Label>Real-time Tracking</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.shipping_logistics?.tracking?.sms_notifications || false}
                  onCheckedChange={(value) => updatePolicyField('shipping_logistics.tracking.sms_notifications', value)}
                />
                <Label>SMS Notifications</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.shipping_logistics?.tracking?.email_notifications || false}
                  onCheckedChange={(value) => updatePolicyField('shipping_logistics.tracking.email_notifications', value)}
                />
                <Label>Email Notifications</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={policyForm.shipping_logistics?.tracking?.delivery_confirmation || false}
                  onCheckedChange={(value) => updatePolicyField('shipping_logistics.tracking.delivery_confirmation', value)}
                />
                <Label>Delivery Confirmation</Label>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Communication & Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Communication & Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Primary Brand Color</Label>
              <Input
                type="color"
                value={policyForm.email_communications?.branding?.primary_color || '#3B82F6'}
                onChange={(e) => updatePolicyField('email_communications.branding.primary_color', e.target.value)}
              />
            </div>
            <div>
              <Label>Secondary Brand Color</Label>
              <Input
                type="color"
                value={policyForm.email_communications?.branding?.secondary_color || '#64748B'}
                onChange={(e) => updatePolicyField('email_communications.branding.secondary_color', e.target.value)}
              />
            </div>
          </div>

          <div>
            <Label>Company Logo URL</Label>
            <Input
              value={policyForm.email_communications?.branding?.logo_url || ''}
              onChange={(e) => updatePolicyField('email_communications.branding.logo_url', e.target.value)}
              placeholder="https://example.com/logo.png"
            />
          </div>

          <div>
            <Label>Font Family</Label>
            <Select 
              value={policyForm.email_communications?.branding?.font_family || 'Arial'}
              onValueChange={(value) => updatePolicyField('email_communications.branding.font_family', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Arial">Arial</SelectItem>
                <SelectItem value="Helvetica">Helvetica</SelectItem>
                <SelectItem value="Times New Roman">Times New Roman</SelectItem>
                <SelectItem value="Georgia">Georgia</SelectItem>
                <SelectItem value="Verdana">Verdana</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-3">
            <Label>Email Template Settings</Label>
            <div className="space-y-2">
              {Object.entries(policyForm.email_communications?.templates || {}).map(([template, config]) => (
                <div key={template} className="flex items-center justify-between border rounded p-3">
                  <div>
                    <Label className="capitalize">{template.replace(/_/g, ' ')}</Label>
                    <p className="text-sm text-gray-500">{config.subject}</p>
                  </div>
                  <Switch
                    checked={config.enabled !== false}
                    onCheckedChange={(value) => updatePolicyField(`email_communications.templates.${template}.enabled`, value)}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label>SMS Notifications</Label>
              <p className="text-sm text-gray-500">Send SMS updates for return status</p>
            </div>
            <Switch
              checked={policyForm.email_communications?.sms_notifications?.enabled || false}
              onCheckedChange={(value) => updatePolicyField('email_communications.sms_notifications.enabled', value)}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Comprehensive Policy Management</h1>
          <p className="text-gray-500">Configure all aspects of your return policy with advanced features</p>
        </div>
        <div className="flex gap-2">
          {currentPolicy && (
            <Button variant="outline" onClick={testPolicy}>
              <Play className="h-4 w-4 mr-2" />
              Test Policy
            </Button>
          )}
          <Button onClick={savePolicy} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save Policy'}
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-6 w-full">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="zones">Zones & Locations</TabsTrigger>
          <TabsTrigger value="windows">Return Windows</TabsTrigger>
          <TabsTrigger value="eligibility">Product Eligibility</TabsTrigger>
          <TabsTrigger value="outcomes">Return Outcomes</TabsTrigger>
          <TabsTrigger value="advanced">Advanced Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <PolicyOverview />
        </TabsContent>

        <TabsContent value="zones">
          <PolicyZones />
        </TabsContent>

        <TabsContent value="windows">
          <ReturnWindows />
        </TabsContent>

        <TabsContent value="eligibility">
          <ProductEligibility />
        </TabsContent>

        <TabsContent value="outcomes">
          <ReturnOutcomes />
        </TabsContent>

        <TabsContent value="advanced">
          <AdvancedSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PolicyManagement;