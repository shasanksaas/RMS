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
        
        // Load first policy if available
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
        loadPolicies(); // Refresh list
        
        // Show success message
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

  // Policy Zones & Location Settings Component
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
                  <SelectItem value="30">30 days</SelectItem>
                  <SelectItem value="45">45 days</SelectItem>
                  <SelectItem value="60">60 days</SelectItem>
                  <SelectItem value="90">90 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
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
              </SelectContent>
            </Select>
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
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Extended Windows</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
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
            <div>
              <Label>Extra Days</Label>
              <Input
                type="number"
                value={policyForm.return_windows?.extended_windows?.holiday_extension?.extra_days || 15}
                onChange={(e) => updatePolicyField('return_windows.extended_windows.holiday_extension.extra_days', parseInt(e.target.value))}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  const ResolutionOutcomes = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Refund Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>Enable Refunds</Label>
            <Switch
              checked={policyForm.refund_settings?.enabled || false}
              onCheckedChange={(value) => updatePolicyField('refund_settings.enabled', value)}
            />
          </div>

          {policyForm.refund_settings?.enabled && (
            <>
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
                    <SelectItem value="3">3 days</SelectItem>
                    <SelectItem value="5">5 days</SelectItem>
                    <SelectItem value="7">1 week</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Refund Methods</Label>
                <div className="space-y-2">
                  {Object.entries(policyForm.refund_settings?.refund_methods || {}).map(([method, enabled]) => (
                    <div key={method} className="flex items-center space-x-2">
                      <Switch
                        checked={enabled}
                        onCheckedChange={(value) => updatePolicyField(`refund_settings.refund_methods.${method}`, value)}
                      />
                      <Label className="capitalize">{method.replace('_', ' ')}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Fees</Label>
                <div className="flex items-center justify-between">
                  <span>Restocking Fee</span>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={policyForm.refund_settings?.fees?.restocking_fee?.enabled || false}
                      onCheckedChange={(value) => updatePolicyField('refund_settings.fees.restocking_fee.enabled', value)}
                    />
                    {policyForm.refund_settings?.fees?.restocking_fee?.enabled && (
                      <Input
                        type="number"
                        placeholder="Amount"
                        className="w-20"
                        value={policyForm.refund_settings?.fees?.restocking_fee?.amount || 15}
                        onChange={(e) => updatePolicyField('refund_settings.fees.restocking_fee.amount', parseFloat(e.target.value))}
                      />
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Exchange Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>Enable Exchanges</Label>
            <Switch
              checked={policyForm.exchange_settings?.enabled || false}
              onCheckedChange={(value) => updatePolicyField('exchange_settings.enabled', value)}
            />
          </div>

          {policyForm.exchange_settings?.enabled && (
            <div className="space-y-2">
              <Label>Exchange Types</Label>
              <div className="space-y-2">
                {Object.entries(policyForm.exchange_settings?.exchange_types || {}).map(([type, enabled]) => (
                  <div key={type} className="flex items-center space-x-2">
                    <Switch
                      checked={enabled}
                      onCheckedChange={(value) => updatePolicyField(`exchange_settings.exchange_types.${type}`, value)}
                    />
                    <Label className="capitalize">{type.replace('_', ' ')}</Label>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>  
          <CardTitle>Store Credit Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>Enable Store Credit</Label>
            <Switch
              checked={policyForm.store_credit_settings?.enabled || false}
              onCheckedChange={(value) => updatePolicyField('store_credit_settings.enabled', value)}
            />
          </div>

          {policyForm.store_credit_settings?.enabled && (
            <>
              <div className="flex items-center justify-between">
                <span>Bonus Incentives</span>
                <Switch
                  checked={policyForm.store_credit_settings?.bonus_incentives?.enabled || false}
                  onCheckedChange={(value) => updatePolicyField('store_credit_settings.bonus_incentives.enabled', value)}
                />
              </div>
              
              {policyForm.store_credit_settings?.bonus_incentives?.enabled && (
                <div>
                  <Label>Bonus Percentage</Label>
                  <Input
                    type="number"
                    value={policyForm.store_credit_settings?.bonus_incentives?.percentage_amount || 15}
                    onChange={(e) => updatePolicyField('store_credit_settings.bonus_incentives.percentage_amount', parseInt(e.target.value))}
                  />
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );

  const FraudPrevention = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            AI Fraud Detection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
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

              <div className="space-y-2">
                <Label>Fraud Actions</Label>
                <div className="grid grid-cols-3 gap-4">
                  {Object.entries(policyForm.fraud_detection?.fraud_actions || {}).map(([risk, action]) => (
                    <div key={risk}>
                      <Label className="capitalize">{risk.replace('_', ' ')}</Label>
                      <Select 
                        value={action}
                        onValueChange={(value) => updatePolicyField(`fraud_detection.fraud_actions.${risk}`, value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="auto_approve">Auto Approve</SelectItem>
                          <SelectItem value="manual_review">Manual Review</SelectItem>
                          <SelectItem value="require_receipt">Require Receipt</SelectItem>
                          <SelectItem value="reject">Auto Reject</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Behavioral Patterns</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Max Returns Per Month</Label>
            <Input
              type="number"
              value={policyForm.fraud_detection?.behavioral_patterns?.max_returns_per_month || 10}
              onChange={(e) => updatePolicyField('fraud_detection.behavioral_patterns.max_returns_per_month', parseInt(e.target.value))}
            />
          </div>
          <div>
            <Label>Max Return Value Per Month</Label>
            <Input
              type="number"
              value={policyForm.fraud_detection?.behavioral_patterns?.max_return_value_per_month || 1000}
              onChange={(e) => updatePolicyField('fraud_detection.behavioral_patterns.max_return_value_per_month', parseFloat(e.target.value))}
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
          <h1 className="text-2xl font-bold">Policy Management</h1>
          <p className="text-gray-500">Configure comprehensive return policies and workflows</p>
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
        <TabsList className="grid grid-cols-4 w-full">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="windows">Return Windows</TabsTrigger>
          <TabsTrigger value="outcomes">Outcomes</TabsTrigger>
          <TabsTrigger value="fraud">Fraud Prevention</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <PolicyOverview />
        </TabsContent>

        <TabsContent value="windows">
          <ReturnWindows />
        </TabsContent>

        <TabsContent value="outcomes">
          <ResolutionOutcomes />
        </TabsContent>

        <TabsContent value="fraud">
          <FraudPrevention />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PolicyManagement;