"""
Public Form Configuration Controller
Provides public access to tenant form configurations for customer-facing forms
"""

from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime

from ..config.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/forms", tags=["Public Form Configuration"])

@router.get("/{tenant_id}/config")
async def get_public_form_config(tenant_id: str):
    """Get tenant's form configuration (Public access for customer forms)"""
    try:
        # Get current published config only (no drafts for public)
        published_config = await db.form_configs.find_one({
            "tenant_id": tenant_id,
            "status": "published"
        }, sort=[("version", -1)])
        
        # Default configuration
        default_config = {
            "branding": {
                "logo_url": "",
                "favicon_url": "",
                "primary_color": "#3B82F6",
                "secondary_color": "#1F2937",
                "background_color": "#FFFFFF",
                "text_color": "#111827",
                "font_family": "Inter"
            },
            "layout": {
                "preset": "wizard",
                "corner_radius": "medium",
                "spacing_density": "comfortable",
                "custom_css": ""
            },
            "form": {
                "show_phone": True,
                "show_photos": True,
                "max_photos": 3,
                "show_notes": True,
                "custom_question": {
                    "enabled": False,
                    "label": "",
                    "type": "text",
                    "options": []
                },
                "return_reasons": [
                    "Wrong size",
                    "Defective",
                    "Not as described",
                    "Changed mind",
                    "Damaged in shipping"
                ],
                "available_resolutions": ["refund", "exchange", "store_credit"],
                "return_window_days": 30,
                "policy_text": "Standard 30-day return policy applies. Items must be in original condition."
            }
        }
        
        # Use published config if available, otherwise default
        current_config = (published_config or {}).get("config", default_config)
        
        return {
            "config": current_config,
            "version": published_config.get("version") if published_config else 1,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Get public form config error for {tenant_id}: {e}")
        # Return default config on error to prevent form breaking
        return {
            "config": {
                "branding": {
                    "logo_url": "",
                    "favicon_url": "",
                    "primary_color": "#3B82F6",
                    "secondary_color": "#1F2937",
                    "background_color": "#FFFFFF",
                    "text_color": "#111827",
                    "font_family": "Inter"
                },
                "layout": {
                    "preset": "wizard",
                    "corner_radius": "medium",
                    "spacing_density": "comfortable",
                    "custom_css": ""
                },
                "form": {
                    "show_phone": True,
                    "show_photos": True,
                    "max_photos": 3,
                    "show_notes": True,
                    "custom_question": {
                        "enabled": False,
                        "label": "",
                        "type": "text",
                        "options": []
                    },
                    "return_reasons": [
                        "Wrong size",
                        "Defective",
                        "Not as described",
                        "Changed mind",
                        "Damaged in shipping"
                    ],
                    "available_resolutions": ["refund", "exchange", "store_credit"],
                    "return_window_days": 30,
                    "policy_text": "Standard 30-day return policy applies. Items must be in original condition."
                }
            },
            "version": 1,
            "status": "success"
        }