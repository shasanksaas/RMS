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
  
  // Policy form state with ALL comprehensive options
  const [policyForm, setPolicyForm] = useState({
    name: '',
    description: '',
    
    // 1. POLICY ZONES & LOCATION SETTINGS
    policy_zones: [
      {
        zone_name: 'Default Zone',
        countries_included: ['US', 'CA'],
        states_provinces: ['NY', 'CA', 'TX', 'FL'],
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
    
    // 2. RETURN WINDOW CONFIGURATIONS
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
          enabled: false,
          extra_days: 15,
          applicable_months: ['November', 'December', 'January']
        },
        loyalty_member_extension: {
          enabled: false,
          bronze_extra_days: 7,
          silver_extra_days: 14,
          gold_extra_days: 30,
          platinum_extra_days: 60
        },
        first_time_buyer_extension: {
          enabled: false,
          extra_days: 10
        }
      },
      category_specific_windows: {
        enabled: false,
        rules: [
          { category: 'Electronics', days: 14 },
          { category: 'Clothing', days: 30 },
          { category: 'Jewelry', days: 7 },
          { category: 'Home_Goods', days: 45 }
        ]
      },
      price_based_windows: {
        enabled: false,
        tiers: [
          { min_price: 0, max_price: 50, days: 14 },
          { min_price: 50, max_price: 200, days: 30 },
          { min_price: 200, max_price: 999999, days: 45 }
        ]
      }
    },
    
    // 3. PRODUCT ELIGIBILITY & EXCLUSIONS
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
          'Custom_Made',
          'Live_Plants',
          'Hazardous_Materials',
          'Prescription_Items'
        ]
      },
      condition_requirements: {
        unworn_unused_only: true,
        original_packaging_required: false,
        tags_attached_required: false,
        hygiene_seal_intact: true,
        accessories_included: true,
        manual_receipt_required: false
      },
      value_based_rules: {
        min_return_value: 5.00,
        max_return_value: 10000.00,
        high_value_manual_review: true,
        high_value_threshold: 500.00
      },
      age_restrictions: {
        max_days_since_purchase: 365,
        perishable_max_days: 3,
        electronics_max_days: 30
      },
      quantity_restrictions: {
        max_items_per_return: 50,
        max_returns_per_order: 3,
        partial_quantity_allowed: true
      }
    },
    
    // 4. RETURN OUTCOMES & RESOLUTIONS
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
        },
        wear_deduction: {
          light_wear_percent: 5,
          moderate_wear_percent: 15,
          heavy_wear_percent: 30
        }
      },
      fees: {
        restocking_fee: { 
          enabled: false, 
          amount: 15.00, 
          type: 'flat_rate',
          percentage_amount: 10,
          waive_for_defective: true,
          waive_for_vip: true
        },
        processing_fee: { 
          enabled: false, 
          amount: 5.00 
        },
        return_shipping_deduction: { 
          enabled: true, 
          deduct_from_refund: true,
          amount: 'flat_rate', 
          flat_rate_amount: 7.95 
        }
      },
      tax_handling: {
        refund_taxes: true,
        refund_duties: false,
        refund_shipping: false,
        refund_gift_wrap: true
      }
    },
    
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
        enabled: false,
        authorization_method: 'one_dollar',
        return_deadline_days: [14],
        require_for_all: false,
        require_for_high_value: true,
        high_value_threshold: 200.00
      },
      price_difference_handling: {
        customer_pays_more: true,
        refund_difference: true,
        store_credit_difference: true,
        max_price_difference: 500.00
      },
      shipping_methods: {
        standard_shipping: 'Standard',
        expedited_shipping: 'Express',
        overnight_shipping: 'Overnight',
        customer_choice: true
      },
      inventory_allocation: {
        reserve_inventory: true,
        reservation_duration_hours: 72,
        multi_location_fulfillment: true,
        preferred_locations: ['warehouse_1', 'store_2']
      },
      exchanges_of_exchanges: {
        enabled: true,
        max_sequential_exchanges: 2,
        reset_return_window: false
      }
    },
    
    store_credit_settings: {
      enabled: true,
      provider: 'shopify',
      bonus_incentives: {
        enabled: false,
        bonus_type: 'percentage',
        flat_rate_amount: 10.00,
        percentage_amount: 15,
        max_bonus_amount: 50.00,
        minimum_order_for_bonus: 25.00
      },
      credit_features: {
        stackable_with_discounts: true,
        transferable: false,
        expiration_enabled: true,
        expiration_days: [365],
        reminder_notifications: true,
        reminder_days_before_expiry: [30, 14, 7, 1]
      },
      redemption_rules: {
        minimum_spend_required: false,
        minimum_spend_amount: 0.00,
        exclude_categories: ['Gift_Cards', 'Digital'],
        exclude_sale_items: false,
        online_only: false,
        in_store_only: false
      }
    },
    
    keep_item_settings: {
      enabled: false,
      triggers: {
        low_value_threshold: 15.00,
        damage_reported: true,
        wrong_item_sent: true,
        goodwill_gesture: true,
        high_shipping_cost: true
      },
      conditions: {
        require_photo_evidence: true,
        require_manager_approval: false,
        automatic_approval_under: 10.00,
        customer_history_check: true,
        max_keep_items_per_customer: 3,
        max_keep_items_timeframe_days: 365
      },
      donation_option: {
        enabled: true,
        partner_charities: ['charity_1', 'charity_2'],
        customer_choice: true,
        tax_receipt: true
      }
    },
    
    shop_now_settings: {
      enabled: false,
      immediate_shopping: true,
      bonus_incentives: {
        enabled: false,
        bonus_type: 'percentage',
        flat_rate_amount: 20.00,
        percentage_amount: 20,
        minimum_spend_for_bonus: 50.00
      },
      shopping_experience: {
        full_catalog_access: true,
        recommended_products: true,
        upsell_opportunities: true,
        cross_sell_opportunities: true,
        honor_original_discounts: true,
        apply_current_promotions: true
      },
      shop_later: {
        enabled: true,
        conversion_options: ['shop_now', 'store_credit', 'refund'],
        conversion_deadline_days: 14,
        conversion_incentives: true,
        reminder_emails: true
      }
    },
    
    // 5. ADVANCED WORKFLOW AUTOMATION
    workflow_conditions: {
      customer_attributes: [
        'customer_tag',
        'customer_id',
        'email_address',
        'total_orders',
        'lifetime_value',
        'return_history_count',
        'account_age_days',
        'loyalty_tier',
        'geographic_location'
      ],
      order_attributes: [
        'order_number',
        'order_tag',
        'order_total_value',
        'order_date',
        'fulfillment_date',
        'delivery_date',
        'payment_method',
        'discount_codes_used',
        'channel_source'
      ],
      product_attributes: [
        'product_id',
        'product_sku',
        'product_title',
        'product_type',
        'product_vendor',
        'product_category',
        'product_price',
        'product_tags'
      ],
      return_attributes: [
        'return_reason',
        'return_reason_note',
        'customer_note',
        'return_value',
        'item_count',
        'photos_provided',
        'return_method'
      ],
      temporal_conditions: [
        'day_of_week',
        'time_of_day',
        'month_of_year',
        'season',
        'holiday_period',
        'business_hours'
      ]
    },
    
    // 6. FRAUD DETECTION & PREVENTION
    fraud_detection: {
      ai_models: {
        enabled: false,
        risk_scoring: {
          low_risk: '0-30',
          medium_risk: '31-70',
          high_risk: '71-100'
        },
        detection_categories: [
          'serial_returners',
          'bracketing_behavior',
          'geographic_anomalies',
          'velocity_abuse',
          'return_without_purchase',
          'damaged_item_claims',
          'sizing_abuse',
          'friendly_fraud'
        ]
      },
      behavioral_patterns: {
        max_returns_per_month: 10,
        max_return_value_per_month: 1000.00,
        suspicious_return_percentage: 50,
        rapid_return_timeframe_hours: 24,
        geographic_inconsistencies: true,
        multiple_addresses: true,
        payment_method_mismatches: true
      },
      blocklist_management: {
        customer_blocklist: true,
        email_blocklist: true,
        phone_blocklist: true,
        address_blocklist: true,
        ip_address_blocklist: true,
        automatic_blocking: true,
        temporary_suspensions: true,
        manual_override_allowed: true
      },
      fraud_actions: {
        low_risk: 'auto_approve',
        medium_risk: 'manual_review',
        high_risk: 'require_receipt',
        confirmed_fraud: 'block_customer'
      }
    },
    
    // 7. SHIPPING & LOGISTICS
    shipping_logistics: {
      label_generation: {
        providers: ['EasyPost', 'ShipStation', 'Shippo'],
        carrier_integration: {
          domestic_carriers: ['UPS', 'FedEx', 'USPS', 'DHL'],
          international_carriers: ['DHL', 'FedEx_Intl', 'UPS_Intl'],
          regional_carriers: ['Canada_Post', 'Royal_Mail']
        },
        label_formats: ['PDF', 'ZPL', 'PNG'],
        label_sizes: ['4x6', '8.5x11']
      },
      return_methods: {
        mail_return: true,
        drop_off_locations: {
          carrier_locations: true,
          retail_partners: ['Staples', 'Walgreens', 'CVS'],
          lockers: ['Amazon_Hub', 'FedEx_Office'],
          branded_locations: []
        },
        pickup_service: {
          scheduled_pickup: true,
          on_demand_pickup: false,
          pickup_fees: 'customer_pays'
        }
      },
      packaging_requirements: {
        original_packaging_preferred: true,
        accept_any_packaging: true,
        provide_packaging: false,
        packaging_instructions: '',
        fragile_item_requirements: true,
        hazmat_restrictions: true
      },
      tracking: {
        real_time_tracking: true,
        sms_notifications: true,
        email_notifications: true,
        webhook_notifications: true,
        delivery_confirmation: true,
        photo_on_delivery: false
      }
    },
    
    // 8. COMMUNICATION & NOTIFICATIONS
    email_communications: {
      branding: {
        logo_url: '',
        primary_color: '#3B82F6',
        secondary_color: '#64748B',
        font_family: 'Arial',
        custom_css: '',
        footer_text: '',
        social_links: {
          facebook: '',
          twitter: '',
          instagram: ''
        }
      },
      templates: {
        return_confirmation: {
          enabled: true,
          trigger: 'return_submitted',
          delay_minutes: 0,
          subject: 'Your return request #{rma_number} is confirmed',
          personalization: true,
          attachments: ['return_label', 'instructions']
        },
        return_received: {
          enabled: true,
          trigger: 'package_delivered_to_warehouse',
          subject: "We've received your return #{rma_number}"
        },
        return_processed: {
          enabled: true,
          trigger: 'return_completed',
          subject: 'Your return has been processed #{rma_number}'
        },
        refund_issued: {
          enabled: true,
          trigger: 'refund_processed',
          subject: 'Your refund of {amount} has been issued'
        }
      },
      sms_notifications: {
        enabled: false,
        return_updates: true,
        shipping_updates: true,
        urgent_notifications_only: true
      }
    },
    
    // 9. REPORTING & ANALYTICS
    reporting_analytics: {
      dashboard_metrics: {
        return_rate: {
          overall_rate: true,
          category_breakdown: true,
          time_period_comparison: true,
          benchmark_comparison: false
        },
        financial_impact: {
          total_return_value: true,
          processing_costs: true,
          revenue_recovered: true,
          net_loss: true
        },
        processing_metrics: {
          average_processing_time: true,
          sla_compliance: true,
          staff_productivity: false,
          automation_rate: true
        },
        customer_metrics: {
          customer_satisfaction: true,
          repeat_return_rate: true,
          post_return_purchase_rate: true,
          nps_score: false
        }
      },
      custom_reports: {
        report_builder: true,
        scheduled_reports: false,
        export_formats: ['CSV', 'Excel', 'PDF'],
        api_access: true,
        real_time_data: true
      },
      predictive_analytics: {
        return_forecasting: false,
        seasonal_trends: true,
        product_risk_scoring: false,
        customer_risk_scoring: false,
        inventory_impact_prediction: false
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