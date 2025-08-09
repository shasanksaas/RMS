"""
Label issuing service with AWS S3 integration (sandbox mode for demo)
"""
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import tempfile
import io

# Mock PDF generation for sandbox mode
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from ..models.return_request import ReturnRequest
from ..models.tenant import Tenant


class LabelService:
    """Service for generating and storing shipping labels"""
    
    def __init__(self):
        # AWS S3 Configuration (for production)
        self.aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')  
        self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        self.s3_bucket = os.environ.get('AWS_S3_BUCKET', 'returns-management-labels')
        
        # Check if S3 is configured
        self.s3_enabled = bool(self.aws_access_key and self.aws_secret_key)
        
        # Sandbox mode - store files locally for demo
        self.sandbox_mode = not self.s3_enabled
        self.local_storage_path = "/tmp/returns_labels"
        
        if self.sandbox_mode:
            os.makedirs(self.local_storage_path, exist_ok=True)
            print("⚠️  Label service running in SANDBOX mode - using local storage")
        else:
            print("✅ Label service configured for AWS S3 production storage")
    
    async def generate_return_label(self, return_request: ReturnRequest, tenant: Tenant) -> Dict[str, Any]:
        """Generate a return shipping label"""
        try:
            # Generate label PDF
            label_content = await self._generate_label_pdf(return_request, tenant)
            
            # Store label file
            if self.s3_enabled:
                label_url = await self._store_label_s3(return_request.id, label_content)
            else:
                label_url = await self._store_label_local(return_request.id, label_content)
            
            # Generate tracking number (mock for sandbox)
            tracking_number = self._generate_tracking_number()
            
            return {
                "success": True,
                "label_url": label_url,
                "tracking_number": tracking_number,
                "format": "pdf",
                "expires_at": None,  # Labels don't expire in sandbox
                "carrier": "USPS" if self.sandbox_mode else "Production Carrier"
            }
        
        except Exception as e:
            print(f"Error generating label: {e}")
            return {
                "success": False,
                "error": str(e),
                "label_url": None,
                "tracking_number": None
            }
    
    async def _generate_label_pdf(self, return_request: ReturnRequest, tenant: Tenant) -> bytes:
        """Generate label PDF content"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Build label content
        content = []
        
        # Header
        content.append(Paragraph(f"RETURN SHIPPING LABEL", styles['Title']))
        content.append(Spacer(1, 20))
        
        # Return information
        return_info_data = [
            ['Return ID:', return_request.id[:8] + '...'],
            ['Customer:', return_request.customer_name],
            ['Email:', return_request.customer_email],
            ['Reason:', return_request.reason.replace('_', ' ').title()],
            ['Amount:', f"${return_request.refund_amount:.2f}"],
            ['Date:', return_request.created_at.strftime('%Y-%m-%d')]
        ]
        
        return_table = Table(return_info_data)
        return_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(return_table)
        content.append(Spacer(1, 30))
        
        # Shipping addresses (mock data for sandbox)
        content.append(Paragraph("SHIP FROM (Customer):", styles['Heading2']))
        content.append(Paragraph("John Customer<br/>123 Customer St<br/>Customer City, ST 12345", styles['Normal']))
        content.append(Spacer(1, 20))
        
        content.append(Paragraph("SHIP TO (Returns Center):", styles['Heading2']))
        content.append(Paragraph(f"{tenant.name} Returns<br/>456 Returns Ave<br/>Returns City, ST 67890", styles['Normal']))
        content.append(Spacer(1, 30))
        
        # Barcode placeholder
        content.append(Paragraph("TRACKING NUMBER:", styles['Heading2']))
        content.append(Paragraph("1Z999AA1234567890", styles['Normal']))  # Mock tracking
        content.append(Spacer(1, 20))
        
        # Instructions
        content.append(Paragraph("RETURN INSTRUCTIONS:", styles['Heading2']))
        instructions = [
            "1. Package items securely in original packaging if possible",
            "2. Print and attach this label to the outside of the package", 
            "3. Drop off at any USPS location or schedule pickup",
            "4. Keep receipt for tracking purposes",
            "5. Refund will be processed within 3-5 business days after receipt"
        ]
        
        for instruction in instructions:
            content.append(Paragraph(instruction, styles['Normal']))
            content.append(Spacer(1, 5))
        
        # Footer
        content.append(Spacer(1, 30))
        content.append(Paragraph(f"Generated by {tenant.name} Returns Management System", styles['Italic']))
        
        # Build PDF
        doc.build(content)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    async def _store_label_s3(self, return_id: str, label_content: bytes) -> str:
        """Store label in AWS S3 (production)"""
        try:
            import boto3
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            # Generate S3 key
            s3_key = f"labels/{return_id}/{uuid.uuid4()}.pdf"
            
            # Upload to S3
            s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=label_content,
                ContentType='application/pdf',
                ACL='private'  # Secure by default
            )
            
            # Generate presigned URL (valid for 24 hours)
            label_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': s3_key},
                ExpiresIn=86400  # 24 hours
            )
            
            return label_url
        
        except Exception as e:
            print(f"S3 storage error: {e}")
            # Fallback to local storage
            return await self._store_label_local(return_id, label_content)
    
    async def _store_label_local(self, return_id: str, label_content: bytes) -> str:
        """Store label locally (sandbox mode)""" 
        filename = f"return_label_{return_id}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(self.local_storage_path, filename)
        
        # Write PDF to local file
        with open(filepath, 'wb') as f:
            f.write(label_content)
        
        # Return local file URL (for demo purposes)
        return f"file://{filepath}"
    
    def _generate_tracking_number(self) -> str:
        """Generate mock tracking number"""
        if self.sandbox_mode:
            # Generate realistic-looking tracking number
            return f"1Z999AA{uuid.uuid4().hex[:10].upper()}"
        else:
            # In production, this would come from actual carrier API
            return f"PROD{uuid.uuid4().hex[:12].upper()}"
    
    async def track_label(self, tracking_number: str) -> Dict[str, Any]:
        """Track shipping label status"""
        if self.sandbox_mode:
            # Mock tracking data
            return {
                "tracking_number": tracking_number,
                "status": "in_transit",
                "carrier": "USPS",
                "estimated_delivery": "2025-01-20",
                "tracking_events": [
                    {
                        "date": "2025-01-18T10:00:00Z",
                        "status": "picked_up",
                        "location": "Customer Location"
                    },
                    {
                        "date": "2025-01-18T15:30:00Z", 
                        "status": "in_transit",
                        "location": "Local Facility"
                    }
                ]
            }
        else:
            # In production, integrate with carrier tracking APIs
            return {
                "tracking_number": tracking_number,
                "status": "unknown",
                "error": "Production tracking not implemented"
            }
    
    async def cancel_label(self, tracking_number: str) -> bool:
        """Cancel shipping label"""
        if self.sandbox_mode:
            print(f"Mock label cancellation for: {tracking_number}")
            return True
        else:
            # In production, cancel through carrier API
            return False
    
    def get_supported_carriers(self) -> list:
        """Get list of supported carriers"""
        if self.sandbox_mode:
            return ["USPS", "UPS", "FedEx"]
        else:
            # Return actual integrated carriers
            return ["Production Carrier"]