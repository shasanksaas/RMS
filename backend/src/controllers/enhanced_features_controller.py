"""
Enhanced features controller - Email, AI, Export functionality
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
import io
from datetime import datetime, timedelta

from ..services.email_service import EmailService
from ..services.ai_service import AIService  
from ..services.export_service import ExportService
from ..services.returns_service import ReturnsService
from ..services.analytics_service import AnalyticsService
from ..services.tenant_service import TenantService
from ..utils.dependencies import get_tenant_id

router = APIRouter(prefix="/enhanced", tags=["enhanced-features"])


# Email Endpoints
@router.post("/email/test")
async def send_test_email(
    request_data: Dict[str, str],
    tenant_id: str = Depends(get_tenant_id)
):
    """Send a test email to verify SMTP configuration"""
    email_service = EmailService()
    
    to_email = request_data.get('email')
    if not to_email:
        raise HTTPException(status_code=400, detail="Email address required")
    
    success = await email_service.send_test_email(to_email)
    
    return {
        "success": success,
        "message": "Test email sent successfully" if success else "Failed to send test email",
        "smtp_configured": email_service.enabled
    }


@router.get("/email/settings")
async def get_email_settings():
    """Get current email configuration status"""
    email_service = EmailService()
    
    return {
        "enabled": email_service.enabled,
        "smtp_host": email_service.smtp_host if email_service.enabled else None,
        "from_email": email_service.from_email if email_service.enabled else None,
        "configuration_required": [
            "SMTP_HOST",
            "SMTP_USERNAME", 
            "SMTP_PASSWORD",
            "FROM_EMAIL"
        ] if not email_service.enabled else []
    }


# AI Endpoints
@router.post("/ai/suggest-reasons")
async def suggest_return_reasons(
    request_data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """Get AI-powered return reason suggestions"""
    ai_service = AIService()
    
    product_name = request_data.get('product_name', '')
    product_description = request_data.get('product_description', '')
    order_date_str = request_data.get('order_date')
    
    if not product_name:
        raise HTTPException(status_code=400, detail="Product name required")
    
    # Parse order date
    try:
        order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00')) if order_date_str else datetime.utcnow()
    except:
        order_date = datetime.utcnow()
    
    suggestions = await ai_service.suggest_return_reasons(product_name, product_description, order_date)
    
    return {
        "suggestions": suggestions,
        "ai_powered": ai_service.use_openai,
        "product_analyzed": product_name
    }


@router.post("/ai/generate-upsell")
async def generate_upsell_message(
    request_data: Dict[str, str],
    tenant_id: str = Depends(get_tenant_id)
):
    """Generate AI-powered upsell message"""
    ai_service = AIService()
    tenant_service = TenantService()
    
    return_reason = request_data.get('return_reason')
    product_name = request_data.get('product_name')
    
    if not return_reason or not product_name:
        raise HTTPException(status_code=400, detail="Return reason and product name required")
    
    # Get tenant info
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    message = await ai_service.generate_upsell_message(return_reason, product_name, tenant.name)
    
    return {
        "upsell_message": message,
        "ai_powered": ai_service.use_openai,
        "return_reason": return_reason
    }


@router.get("/ai/analyze-patterns")
async def analyze_return_patterns(
    tenant_id: str = Depends(get_tenant_id),
    days: int = Query(default=30, description="Number of days to analyze")
):
    """Analyze return patterns using AI"""
    ai_service = AIService()
    
    analysis = await ai_service.analyze_return_patterns(tenant_id, days)
    
    return {
        "analysis": analysis,
        "period_days": days,
        "analyzed_at": datetime.utcnow().isoformat()
    }


# Export Endpoints
@router.get("/export/returns/csv")
async def export_returns_csv(
    tenant_id: str = Depends(get_tenant_id),
    days: int = Query(default=30, description="Number of days to include"),
    status: Optional[str] = Query(default=None, description="Filter by status")
):
    """Export returns data as CSV"""
    returns_service = ReturnsService()
    tenant_service = TenantService()
    export_service = ExportService()
    
    # Get tenant
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get returns data
    returns = await returns_service.get_tenant_returns(tenant_id)
    
    # Filter by date and status if specified
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    filtered_returns = [
        ret for ret in returns 
        if ret.created_at >= cutoff_date and (not status or ret.status == status)
    ]
    
    # Generate CSV
    csv_content = await export_service.export_returns_csv(filtered_returns, tenant)
    
    # Return as downloadable file
    filename = f"returns_export_{tenant.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        io.BytesIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/returns/pdf")
async def export_returns_pdf(
    tenant_id: str = Depends(get_tenant_id),
    days: int = Query(default=30, description="Number of days to include"),
    include_analytics: bool = Query(default=True, description="Include analytics summary")
):
    """Export returns data as PDF report"""
    returns_service = ReturnsService()
    tenant_service = TenantService()
    analytics_service = AnalyticsService()
    export_service = ExportService()
    
    # Get tenant
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get returns data
    returns = await returns_service.get_tenant_returns(tenant_id)
    
    # Filter by date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    filtered_returns = [ret for ret in returns if ret.created_at >= cutoff_date]
    
    # Get analytics if requested
    analytics = None
    if include_analytics:
        analytics = await analytics_service.get_tenant_analytics(tenant_id, days)
    
    # Generate PDF
    pdf_content = await export_service.export_returns_pdf(filtered_returns, tenant, analytics)
    
    # Return as downloadable file
    filename = f"returns_report_{tenant.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/analytics/excel")
async def export_analytics_excel(
    tenant_id: str = Depends(get_tenant_id),
    days: int = Query(default=30, description="Number of days to include")
):
    """Export comprehensive analytics as Excel file"""
    returns_service = ReturnsService()
    tenant_service = TenantService()
    analytics_service = AnalyticsService()
    export_service = ExportService()
    
    # Get data
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    returns = await returns_service.get_tenant_returns(tenant_id)
    analytics = await analytics_service.get_tenant_analytics(tenant_id, days)
    
    # Filter returns by date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    filtered_returns = [ret for ret in returns if ret.created_at >= cutoff_date]
    
    # Generate Excel
    excel_content = await export_service.export_analytics_excel(analytics, filtered_returns, tenant)
    
    # Return as downloadable file
    filename = f"analytics_export_{tenant.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(excel_content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/export/custom")
async def generate_custom_export(
    request_data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """Generate custom export based on user specifications"""
    tenant_service = TenantService()
    export_service = ExportService()
    
    # Get tenant
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Generate custom report
    report_content = await export_service.generate_custom_report(tenant, request_data)
    
    # Determine file type and name
    export_type = request_data.get('type', 'pdf')
    filename = f"custom_report_{tenant.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}{export_service.get_file_extension(export_type)}"
    
    return StreamingResponse(
        io.BytesIO(report_content),
        media_type=export_service.get_content_type(export_type),
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# Integration Status Endpoint
@router.get("/status")
async def get_enhanced_features_status():
    """Get status of all enhanced features"""
    email_service = EmailService()
    ai_service = AIService()
    
    return {
        "email": {
            "enabled": email_service.enabled,
            "smtp_configured": bool(email_service.smtp_host and email_service.smtp_username)
        },
        "ai": {
            "openai_available": ai_service.use_openai,
            "local_fallback": True,
            "features": ["return_reason_suggestions", "upsell_generation", "pattern_analysis"]
        },
        "export": {
            "available_formats": ["csv", "pdf", "excel"],
            "custom_reports": True
        },
        "shopify": {
            "oauth_configured": True,
            "offline_fallback": True
        }
    }