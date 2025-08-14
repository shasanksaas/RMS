"""
Policy Validator
Validates policy configurations for correctness and completeness
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
class PolicyValidator:
    """Validates comprehensive policy configurations"""
    
    @staticmethod
    def validate_policy(policy: Dict[str, Any]) -> ValidationResult:
        """Main policy validation method"""
        
        errors = []
        warnings = []
        
        # Validate required fields
        required_fields = ["name", "tenant_id"]
        for field in required_fields:
            if not policy.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate return windows
        window_validation = PolicyValidator._validate_return_windows(
            policy.get("return_windows", {})
        )
        errors.extend(window_validation.errors)
        warnings.extend(window_validation.warnings)
        
        # Validate refund settings
        refund_validation = PolicyValidator._validate_refund_settings(
            policy.get("refund_settings", {})
        )
        errors.extend(refund_validation.errors)
        warnings.extend(refund_validation.warnings)
        
        # Validate exchange settings
        exchange_validation = PolicyValidator._validate_exchange_settings(
            policy.get("exchange_settings", {})
        )
        errors.extend(exchange_validation.errors)
        warnings.extend(exchange_validation.warnings)
        
        # Validate fraud detection
        fraud_validation = PolicyValidator._validate_fraud_detection(
            policy.get("fraud_detection", {})
        )
        errors.extend(fraud_validation.errors)
        warnings.extend(fraud_validation.warnings)
        
        # Validate policy zones
        zones_validation = PolicyValidator._validate_policy_zones(
            policy.get("policy_zones", [])
        )
        errors.extend(zones_validation.errors)
        warnings.extend(zones_validation.warnings)
        
        # Validate email communications
        email_validation = PolicyValidator._validate_email_communications(
            policy.get("email_communications", {})
        )
        errors.extend(email_validation.errors)
        warnings.extend(email_validation.warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def _validate_return_windows(windows: Dict[str, Any]) -> ValidationResult:
        """Validate return window configurations"""
        
        errors = []
        warnings = []
        
        standard_window = windows.get("standard_window", {})
        
        # Validate window type
        window_type = standard_window.get("type", "limited")
        if window_type not in ["limited", "unlimited"]:
            errors.append("Invalid return window type. Must be 'limited' or 'unlimited'")
        
        # Validate days for limited windows
        if window_type == "limited":
            days = standard_window.get("days", [])
            if not days or not isinstance(days, list):
                errors.append("Limited return windows must specify days as a list")
            elif any(not isinstance(d, int) or d <= 0 for d in days):
                errors.append("Return window days must be positive integers")
            elif max(days) > 365:
                warnings.append("Return window exceeds 365 days - consider unlimited instead")
        
        # Validate calculation_from
        calculation_from = standard_window.get("calculation_from", "order_date")
        valid_calculations = ["order_date", "fulfillment_date", "delivery_date", "first_delivery_attempt"]
        if calculation_from not in valid_calculations:
            errors.append(f"Invalid calculation_from. Must be one of: {valid_calculations}")
        
        # Validate extended windows
        extended_windows = windows.get("extended_windows", {})
        
        # Holiday extension validation
        holiday_ext = extended_windows.get("holiday_extension", {})
        if holiday_ext.get("enabled", False):
            extra_days = holiday_ext.get("extra_days", 0)
            if not isinstance(extra_days, int) or extra_days < 0:
                errors.append("Holiday extension extra_days must be a non-negative integer")
            
            applicable_months = holiday_ext.get("applicable_months", [])
            valid_months = ["January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            invalid_months = [m for m in applicable_months if m not in valid_months]
            if invalid_months:
                errors.append(f"Invalid months in holiday extension: {invalid_months}")
        
        # Category specific windows validation
        category_windows = windows.get("category_specific_windows", {})
        if category_windows.get("enabled", False):
            rules = category_windows.get("rules", [])
            for rule in rules:
                if not isinstance(rule.get("days"), int) or rule["days"] <= 0:
                    errors.append("Category specific window days must be positive integers")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def _validate_refund_settings(settings: Dict[str, Any]) -> ValidationResult:
        """Validate refund settings"""
        
        errors = []
        warnings = []
        
        if not settings.get("enabled", True):
            warnings.append("Refunds are disabled - customers can only exchange or get store credit")
        
        # Validate processing events
        processing_events = settings.get("processing_events", [])
        valid_events = ["immediate", "label_created", "pre_transit", "in_transit",
                       "out_for_delivery", "delivered", "manual_approval"]
        
        invalid_events = [e for e in processing_events if e not in valid_events]
        if invalid_events:
            errors.append(f"Invalid processing events: {invalid_events}")
        
        # Validate processing delay
        processing_delay = settings.get("processing_delay", {})
        if processing_delay.get("enabled", False):
            delay_days = processing_delay.get("delay_days", [])
            if not delay_days or not isinstance(delay_days, list):
                errors.append("Processing delay must specify delay_days as a list")
            elif any(not isinstance(d, int) or d < 0 for d in delay_days):
                errors.append("Delay days must be non-negative integers")
        
        # Validate refund methods
        refund_methods = settings.get("refund_methods", {})
        if not any(refund_methods.values()):
            errors.append("At least one refund method must be enabled")
        
        # Validate fees
        fees = settings.get("fees", {})
        
        # Restocking fee validation
        restocking = fees.get("restocking_fee", {})
        if restocking.get("enabled", False):
            fee_type = restocking.get("type", "flat_rate")
            if fee_type not in ["flat_rate", "percentage"]:
                errors.append("Restocking fee type must be 'flat_rate' or 'percentage'")
            
            if fee_type == "flat_rate":
                amount = restocking.get("amount", 0)
                if not isinstance(amount, (int, float)) or amount < 0:
                    errors.append("Restocking fee amount must be a non-negative number")
            elif fee_type == "percentage":
                percentage = restocking.get("percentage_amount", 0)
                if not isinstance(percentage, (int, float)) or percentage < 0 or percentage > 100:
                    errors.append("Restocking fee percentage must be between 0 and 100")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def _validate_exchange_settings(settings: Dict[str, Any]) -> ValidationResult:
        """Validate exchange settings"""
        
        errors = []
        warnings = []
        
        if not settings.get("enabled", True):
            warnings.append("Exchanges are disabled")
            return ValidationResult(True, [], warnings)
        
        # Validate exchange types
        exchange_types = settings.get("exchange_types", {})
        if not any(exchange_types.values()):
            warnings.append("No exchange types are enabled")
        
        # Validate instant exchanges
        instant_exchanges = settings.get("instant_exchanges", {})
        if instant_exchanges.get("enabled", False):
            auth_method = instant_exchanges.get("authorization_method", "")
            valid_methods = ["one_dollar", "full_value", "credit_check"]
            if auth_method not in valid_methods:
                errors.append(f"Invalid authorization method. Must be one of: {valid_methods}")
            
            return_deadline = instant_exchanges.get("return_deadline_days", [])
            if return_deadline and any(not isinstance(d, int) or d <= 0 for d in return_deadline):
                errors.append("Return deadline days must be positive integers")
        
        # Validate price difference handling
        price_diff = settings.get("price_difference_handling", {})
        max_diff = price_diff.get("max_price_difference", 0)
        if max_diff and (not isinstance(max_diff, (int, float)) or max_diff < 0):
            errors.append("Maximum price difference must be a non-negative number")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def _validate_fraud_detection(settings: Dict[str, Any]) -> ValidationResult:
        """Validate fraud detection settings"""
        
        errors = []
        warnings = []
        
        ai_models = settings.get("ai_models", {})
        if ai_models.get("enabled", False):
            # Validate risk scoring
            risk_scoring = ai_models.get("risk_scoring", {})
            
            # Parse risk ranges
            try:
                low_risk = risk_scoring.get("low_risk", "0-30")
                medium_risk = risk_scoring.get("medium_risk", "31-70")
                high_risk = risk_scoring.get("high_risk", "71-100")
                
                # Validate range format
                for risk_name, risk_range in [("low", low_risk), ("medium", medium_risk), ("high", high_risk)]:
                    if "-" not in risk_range:
                        errors.append(f"Invalid {risk_name} risk range format. Use 'min-max'")
                    else:
                        try:
                            min_val, max_val = map(int, risk_range.split("-"))
                            if min_val >= max_val or min_val < 0 or max_val > 100:
                                errors.append(f"Invalid {risk_name} risk range values")
                        except ValueError:
                            errors.append(f"Invalid {risk_name} risk range values")
            
            except Exception:
                errors.append("Invalid risk scoring configuration")
        
        # Validate behavioral patterns
        patterns = settings.get("behavioral_patterns", {})
        
        max_returns = patterns.get("max_returns_per_month", 0)
        if max_returns and (not isinstance(max_returns, int) or max_returns <= 0):
            errors.append("Max returns per month must be a positive integer")
        
        max_value = patterns.get("max_return_value_per_month", 0)
        if max_value and (not isinstance(max_value, (int, float)) or max_value <= 0):
            errors.append("Max return value per month must be a positive number")
        
        # Validate fraud actions
        fraud_actions = settings.get("fraud_actions", {})
        valid_actions = ["auto_approve", "manual_review", "restrict_outcomes", "reject",
                        "require_receipt", "photo_verification", "block_customer"]
        
        for risk_level, action in fraud_actions.items():
            if action not in valid_actions:
                errors.append(f"Invalid fraud action '{action}' for {risk_level}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def _validate_policy_zones(zones: List[Dict[str, Any]]) -> ValidationResult:
        """Validate policy zones"""
        
        errors = []
        warnings = []
        
        if not zones:
            warnings.append("No policy zones configured - using default zone")
            return ValidationResult(True, [], warnings)
        
        zone_names = set()
        
        for i, zone in enumerate(zones):
            zone_name = zone.get("zone_name", "")
            
            if not zone_name:
                errors.append(f"Zone {i+1} is missing zone_name")
            elif zone_name in zone_names:
                errors.append(f"Duplicate zone name: {zone_name}")
            else:
                zone_names.add(zone_name)
            
            # Validate countries
            countries = zone.get("countries_included", [])
            if countries and not isinstance(countries, list):
                errors.append(f"Zone {zone_name}: countries_included must be a list")
            
            # Validate postal codes
            postal_codes = zone.get("postal_codes", {})
            if postal_codes:
                include_ranges = postal_codes.get("include_ranges", [])
                exclude_specific = postal_codes.get("exclude_specific", [])
                
                # Validate range format
                for postal_range in include_ranges:
                    if not isinstance(postal_range, str) or "-" not in postal_range:
                        errors.append(f"Zone {zone_name}: Invalid postal code range format")
            
            # Validate carrier restrictions
            carrier_restrictions = zone.get("carrier_restrictions", {})
            if carrier_restrictions:
                allowed_carriers = carrier_restrictions.get("allowed_carriers", [])
                preferred_carrier = carrier_restrictions.get("preferred_carrier", "")
                
                if preferred_carrier and preferred_carrier not in allowed_carriers:
                    warnings.append(f"Zone {zone_name}: Preferred carrier not in allowed carriers list")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def _validate_email_communications(settings: Dict[str, Any]) -> ValidationResult:
        """Validate email communication settings"""
        
        errors = []
        warnings = []
        
        # Validate branding
        branding = settings.get("branding", {})
        if branding:
            logo_url = branding.get("logo_url", "")
            if logo_url and not logo_url.startswith(("http://", "https://")):
                errors.append("Logo URL must be a valid HTTP/HTTPS URL")
            
            # Validate color codes
            primary_color = branding.get("primary_color", "")
            if primary_color and not primary_color.startswith("#"):
                errors.append("Primary color must be a valid hex color code")
        
        # Validate templates
        templates = settings.get("templates", {})
        required_templates = ["return_confirmation", "return_processed", "refund_issued"]
        
        for template_name in required_templates:
            template = templates.get(template_name, {})
            if template.get("enabled", False):
                subject = template.get("subject", "")
                if not subject:
                    warnings.append(f"Template {template_name} has no subject line")
                
                delay_minutes = template.get("delay_minutes", 0)
                if delay_minutes and (not isinstance(delay_minutes, int) or delay_minutes < 0):
                    errors.append(f"Template {template_name}: delay_minutes must be a non-negative integer")
        
        # Validate SMS notifications
        sms_settings = settings.get("sms_notifications", {})
        if sms_settings.get("enabled", False) and not templates:
            warnings.append("SMS notifications enabled but no templates configured")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )