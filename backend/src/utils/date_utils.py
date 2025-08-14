"""
Date utility functions for policy calculations
"""
from datetime import datetime, timedelta
from typing import Optional
import re

def parse_date(date_input) -> Optional[datetime]:
    """Parse various date formats into datetime object"""
    
    if isinstance(date_input, datetime):
        return date_input
    
    if isinstance(date_input, str):
        # Common date formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_input, fmt)
            except ValueError:
                continue
    
    return None

def calculate_business_days(start_date: datetime, end_date: datetime) -> int:
    """Calculate business days between two dates (excluding weekends)"""
    
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    business_days = 0
    current_date = start_date
    
    while current_date < end_date:
        if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days

def is_business_day(date: datetime) -> bool:
    """Check if date is a business day (not weekend)"""
    return date.weekday() < 5

def add_business_days(start_date: datetime, business_days: int) -> datetime:
    """Add business days to a date (skipping weekends)"""
    
    current_date = start_date
    days_added = 0
    
    while days_added < business_days:
        current_date += timedelta(days=1)
        if is_business_day(current_date):
            days_added += 1
    
    return current_date