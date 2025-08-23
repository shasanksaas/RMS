"""
Form Configuration Controller
Handles tenant-specific form customization, branding, and configuration
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import Dict, Any, Optional, List
import logging
import time
import os
import uuid
from datetime import datetime
import json
import re

from ..middleware.tenant_isolation import get_tenant_from_request
from ..config.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants", tags=["Form Configuration"])

# CSS sanitization patterns
UNSAFE_CSS_PATTERNS = [
    r'javascript:',
    r'expression\s*\(',
    r'@import',
    r'url\s*\(\s*[\'"]?(?!data:image)',  # Allow data URLs for images
    r'<script',
    r'</script>',
    r'onclick',
    r'onload',
    r'onerror'
]

def sanitize_css(css_content: str, max_size: int = 2048) -> str:
    """Sanitize CSS content for security"""
    if not css_content:
        return ""
    
    # Limit size
    if len(css_content) > max_size:
        css_content = css_content[:max_size]
    
    # Remove unsafe patterns
    for pattern in UNSAFE_CSS_PATTERNS:
        css_content = re.sub(pattern, '', css_content, flags=re.IGNORECASE)
    
    return css_content

@router.get("/{tenant_id}/form-config")
async def get_form_config(
    tenant_id: str,
    current_tenant_id: str = Depends(get_tenant_from_request)
):
    """Get tenant's form configuration"""
    try:
        # Security check
        if tenant_id != current_tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get current published config
        published_config = await db.form_configs.find_one({
            "tenant_id": tenant_id,
            "status": "published"
        }, sort=[("version", -1)])
        
        # Get draft config if any
        draft_config = await db.form_configs.find_one({
            "tenant_id": tenant_id,
            "status": "draft"
        })
        
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
        
        # Use draft config if available, otherwise published, otherwise default
        current_config = (draft_config or published_config or {}).get("config", default_config)
        
        return {
            "config": current_config,
            "published_version": published_config.get("version") if published_config else None,
            "has_draft": draft_config is not None,
            "last_updated": (published_config or {}).get("updated_at"),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get form config error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch form configuration")

@router.post("/{tenant_id}/form-config/draft")
async def save_draft_config(
    tenant_id: str,
    config_data: Dict[str, Any],
    current_tenant_id: str = Depends(get_tenant_from_request)
):
    """Save form configuration as draft"""
    try:
        # Security check
        if tenant_id != current_tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        config = config_data.get("config", {})
        
        # Sanitize CSS
        if "layout" in config and "custom_css" in config["layout"]:
            config["layout"]["custom_css"] = sanitize_css(
                config["layout"]["custom_css"], 
                max_size=2048
            )
        
        # Upsert draft config
        await db.form_configs.update_one(
            {"tenant_id": tenant_id, "status": "draft"},
            {
                "$set": {
                    "tenant_id": tenant_id,
                    "config": config,
                    "status": "draft",
                    "updated_at": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        return {"success": True, "message": "Draft saved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save draft config error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save draft configuration")

@router.post("/{tenant_id}/form-config/publish")
async def publish_config(
    tenant_id: str,
    config_data: Dict[str, Any],
    current_tenant_id: str = Depends(get_tenant_from_request)
):
    """Publish form configuration"""
    try:
        # Security check
        if tenant_id != current_tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        config = config_data.get("config", {})
        
        # Sanitize CSS
        if "layout" in config and "custom_css" in config["layout"]:
            config["layout"]["custom_css"] = sanitize_css(
                config["layout"]["custom_css"], 
                max_size=2048
            )
        
        # Get next version number
        latest_version = await db.form_configs.find_one(
            {"tenant_id": tenant_id, "status": "published"},
            sort=[("version", -1)]
        )
        next_version = (latest_version.get("version", 0) if latest_version else 0) + 1
        
        # Archive current published version
        if latest_version:
            await db.form_configs.update_one(
                {"_id": latest_version["_id"]},
                {"$set": {"status": "archived"}}
            )
        
        # Create new published version
        new_config = {
            "tenant_id": tenant_id,
            "config": config,
            "status": "published",
            "version": next_version,
            "published_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        result = await db.form_configs.insert_one(new_config)
        
        # Remove draft
        await db.form_configs.delete_many({
            "tenant_id": tenant_id, 
            "status": "draft"
        })
        
        return {
            "success": True, 
            "version": next_version,
            "message": f"Configuration published as version {next_version}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publish config error: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish configuration")

@router.post("/{tenant_id}/upload-asset")
async def upload_asset(
    tenant_id: str,
    file: UploadFile = File(...),
    asset_type: str = Form(...),
    current_tenant_id: str = Depends(get_tenant_from_request)
):
    """Upload logo, favicon, or other assets"""
    try:
        # Security check
        if tenant_id != current_tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Validate file type
        allowed_types = {
            'logo': ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/svg+xml'],
            'favicon': ['image/png', 'image/x-icon', 'image/vnd.microsoft.icon']
        }
        
        if asset_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid asset type")
        
        if file.content_type not in allowed_types[asset_type]:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Limit file size (2MB)
        file_content = await file.read()
        if len(file_content) > 2 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 2MB)")
        
        # Create uploads directory
        upload_dir = "/app/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{tenant_id}_{asset_type}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Return URL (in production, this would be a CDN URL)
        file_url = f"/uploads/{unique_filename}"
        
        return {
            "success": True,
            "url": file_url,
            "filename": unique_filename,
            "size": len(file_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload asset error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload asset")

@router.get("/{tenant_id}/form-config/versions")
async def get_config_versions(
    tenant_id: str,
    current_tenant_id: str = Depends(get_tenant_from_request)
):
    """Get all configuration versions for rollback"""
    try:
        # Security check
        if tenant_id != current_tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        versions = []
        async for config in db.form_configs.find(
            {"tenant_id": tenant_id, "status": {"$in": ["published", "archived"]}},
            sort=[("version", -1)]
        ).limit(10):  # Last 10 versions
            versions.append({
                "version": config["version"],
                "status": config["status"],
                "published_at": config.get("published_at"),
                "created_at": config["created_at"]
            })
        
        return {"versions": versions}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get config versions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch configuration versions")

@router.post("/{tenant_id}/form-config/rollback/{version}")
async def rollback_config(
    tenant_id: str,
    version: int,
    current_tenant_id: str = Depends(get_tenant_from_request)
):
    """Rollback to a previous configuration version"""
    try:
        # Security check
        if tenant_id != current_tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Find the version to rollback to
        target_config = await db.form_configs.find_one({
            "tenant_id": tenant_id,
            "version": version,
            "status": {"$in": ["published", "archived"]}
        })
        
        if not target_config:
            raise HTTPException(status_code=404, detail="Configuration version not found")
        
        # Archive current published version
        await db.form_configs.update_many(
            {"tenant_id": tenant_id, "status": "published"},
            {"$set": {"status": "archived"}}
        )
        
        # Create new published version with rollback config
        next_version = version + 1000  # Add 1000 to indicate rollback
        new_config = {
            "tenant_id": tenant_id,
            "config": target_config["config"],
            "status": "published",
            "version": next_version,
            "rollback_from": version,
            "published_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        await db.form_configs.insert_one(new_config)
        
        return {
            "success": True,
            "version": next_version,
            "rollback_from": version,
            "message": f"Configuration rolled back to version {version}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rollback config error: {e}")
        raise HTTPException(status_code=500, detail="Failed to rollback configuration")