"""
Export service for generating PDF and CSV reports
"""
import os
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import tempfile

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pandas as pd

from ..models.return_request import ReturnRequest
from ..models.tenant import Tenant
from ..models.analytics import Analytics


class ExportService:
    """Service for generating reports and exports"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    async def export_returns_csv(self, returns: List[ReturnRequest], tenant: Tenant) -> bytes:
        """Export returns data to CSV format"""
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Return ID',
            'Customer Name', 
            'Customer Email',
            'Order ID',
            'Status',
            'Reason', 
            'Refund Amount',
            'Created Date',
            'Updated Date',
            'Notes',
            'Tracking Number',
            'Items'
        ])
        
        # Write data rows
        for return_req in returns:
            items_str = '; '.join([
                f"{item.product_name} (Qty: {item.quantity}, ${item.price})"
                for item in return_req.items_to_return
            ])
            
            writer.writerow([
                return_req.id,
                return_req.customer_name,
                return_req.customer_email,
                return_req.order_id,
                return_req.status.replace('_', ' ').title(),
                return_req.reason.replace('_', ' ').title(),
                f"${return_req.refund_amount:.2f}",
                return_req.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                return_req.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                return_req.notes or '',
                return_req.tracking_number or '',
                items_str
            ])
        
        # Get CSV content as bytes
        csv_content = output.getvalue().encode('utf-8')
        output.close()
        
        return csv_content
    
    async def export_returns_pdf(self, returns: List[ReturnRequest], tenant: Tenant, analytics: Optional[Analytics] = None) -> bytes:
        """Export returns data to PDF format"""
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            textColor=colors.HexColor(tenant.settings.get('brand_color', '#3b82f6'))
        )
        
        # Build PDF content
        content = []
        
        # Title
        content.append(Paragraph(f"{tenant.name} - Returns Report", title_style))
        content.append(Paragraph(f"Generated on {datetime.utcnow().strftime('%B %d, %Y')}", styles['Normal']))
        content.append(Spacer(1, 20))
        
        # Summary section if analytics provided
        if analytics:
            content.append(Paragraph("Summary", styles['Heading2']))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Returns', str(analytics.total_returns)],
                ['Total Refunds', f"${analytics.total_refunds:.2f}"],
                ['Exchange Rate', f"{analytics.exchange_rate:.1f}%"],
                ['Avg Processing Time', f"{analytics.avg_processing_time:.1f} days"],
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(summary_table)
            content.append(Spacer(1, 20))
        
        # Returns table
        content.append(Paragraph("Return Requests", styles['Heading2']))
        
        if returns:
            # Prepare table data
            table_data = [['Return ID', 'Customer', 'Status', 'Reason', 'Amount', 'Date']]
            
            for return_req in returns[:50]:  # Limit to 50 for PDF readability
                table_data.append([
                    return_req.id[:8] + '...',  # Truncate ID
                    return_req.customer_name,
                    return_req.status.replace('_', ' ').title(),
                    return_req.reason.replace('_', ' ').title(), 
                    f"${return_req.refund_amount:.2f}",
                    return_req.created_at.strftime('%m/%d/%Y')
                ])
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            content.append(table)
            
            if len(returns) > 50:
                content.append(Spacer(1, 10))
                content.append(Paragraph(f"Showing first 50 of {len(returns)} returns. Export CSV for complete data.", styles['Italic']))
        else:
            content.append(Paragraph("No returns found for the selected period.", styles['Normal']))
        
        # Top return reasons if analytics provided
        if analytics and analytics.top_return_reasons:
            content.append(Spacer(1, 20))
            content.append(Paragraph("Top Return Reasons", styles['Heading2']))
            
            reasons_data = [['Reason', 'Count', 'Percentage']]
            for reason in analytics.top_return_reasons[:10]:
                reasons_data.append([
                    reason['reason'].replace('_', ' ').title(),
                    str(reason['count']),
                    f"{reason['percentage']:.1f}%"
                ])
            
            reasons_table = Table(reasons_data)
            reasons_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            content.append(reasons_table)
        
        # Footer
        content.append(Spacer(1, 30))
        content.append(Paragraph(f"Report generated by {tenant.name} Returns Management System", styles['Italic']))
        
        # Build PDF
        doc.build(content)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    async def export_analytics_excel(self, analytics: Analytics, returns: List[ReturnRequest], tenant: Tenant) -> bytes:
        """Export comprehensive analytics to Excel format"""
        
        # Create Excel file in memory
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Total Returns', 'Total Refunds', 'Exchange Rate', 'Avg Processing Time'],
                'Value': [
                    analytics.total_returns,
                    f"${analytics.total_refunds:.2f}",
                    f"{analytics.exchange_rate:.1f}%",
                    f"{analytics.avg_processing_time:.1f} days"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Returns data sheet
            if returns:
                returns_data = []
                for ret in returns:
                    returns_data.append({
                        'Return ID': ret.id,
                        'Customer Name': ret.customer_name,
                        'Customer Email': ret.customer_email,
                        'Status': ret.status.replace('_', ' ').title(),
                        'Reason': ret.reason.replace('_', ' ').title(),
                        'Refund Amount': ret.refund_amount,
                        'Created Date': ret.created_at,
                        'Updated Date': ret.updated_at,
                        'Notes': ret.notes or '',
                        'Tracking Number': ret.tracking_number or ''
                    })
                
                returns_df = pd.DataFrame(returns_data)
                returns_df.to_excel(writer, sheet_name='Returns', index=False)
            
            # Return reasons sheet
            if analytics.top_return_reasons:
                reasons_data = []
                for reason in analytics.top_return_reasons:
                    reasons_data.append({
                        'Reason': reason['reason'].replace('_', ' ').title(),
                        'Count': reason['count'],
                        'Percentage': reason['percentage']
                    })
                
                reasons_df = pd.DataFrame(reasons_data)
                reasons_df.to_excel(writer, sheet_name='Return Reasons', index=False)
        
        excel_content = buffer.getvalue()
        buffer.close()
        
        return excel_content
    
    async def generate_custom_report(self, tenant: Tenant, report_config: Dict[str, Any]) -> bytes:
        """Generate custom report based on configuration"""
        
        report_type = report_config.get('type', 'pdf')
        date_range = report_config.get('date_range', 30)
        include_charts = report_config.get('include_charts', False)
        
        # This would integrate with data services to generate custom reports
        # For now, return a simple acknowledgment
        
        if report_type == 'pdf':
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            
            content = [
                Paragraph(f"Custom Report - {tenant.name}", styles['Title']),
                Paragraph(f"Generated on {datetime.utcnow().strftime('%B %d, %Y')}", styles['Normal']),
                Spacer(1, 20),
                Paragraph("This is a placeholder for custom report functionality.", styles['Normal']),
                Paragraph(f"Date Range: Last {date_range} days", styles['Normal']),
                Paragraph(f"Include Charts: {include_charts}", styles['Normal'])
            ]
            
            doc.build(content)
            return buffer.getvalue()
        
        else:  # CSV fallback
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Report Type', 'Custom Report'])
            writer.writerow(['Date Range', f'{date_range} days'])
            writer.writerow(['Generated', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')])
            
            return output.getvalue().encode('utf-8')
    
    def get_file_extension(self, export_type: str) -> str:
        """Get file extension for export type"""
        extensions = {
            'csv': '.csv',
            'pdf': '.pdf',
            'excel': '.xlsx',
            'json': '.json'
        }
        return extensions.get(export_type, '.txt')
    
    def get_content_type(self, export_type: str) -> str:
        """Get MIME content type for export type"""
        content_types = {
            'csv': 'text/csv',
            'pdf': 'application/pdf',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'json': 'application/json'
        }
        return content_types.get(export_type, 'application/octet-stream')