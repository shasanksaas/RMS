"""
Email notification service with SMTP support
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from jinja2 import Template
from datetime import datetime

from ..models.return_request import ReturnRequest, ReturnStatus
from ..models.tenant import Tenant


class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        # SMTP Configuration from environment
        self.smtp_host = os.environ.get('SMTP_HOST', 'localhost')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.smtp_use_tls = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@returns-manager.com')
        self.from_name = os.environ.get('FROM_NAME', 'Returns Manager')
        
        self.enabled = bool(self.smtp_host and self.smtp_username and self.smtp_password)
        
        if not self.enabled:
            print("Warning: Email service disabled - missing SMTP configuration")
    
    async def send_return_status_notification(self, return_request: ReturnRequest, tenant: Tenant, previous_status: Optional[str] = None):
        """Send email notification for return status change"""
        if not self.enabled:
            print(f"Email notification skipped for return {return_request.id} - service disabled")
            return False
        
        try:
            # Generate email content based on status
            subject, html_content, text_content = self._generate_return_email_content(
                return_request, tenant, previous_status
            )
            
            # Send email
            return await self._send_email(
                to_email=return_request.customer_email,
                to_name=return_request.customer_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
        
        except Exception as e:
            print(f"Error sending return notification email: {e}")
            return False
    
    async def send_merchant_notification(self, return_request: ReturnRequest, tenant: Tenant, notification_type: str):
        """Send notification to merchant about return events"""
        if not self.enabled:
            return False
        
        try:
            # Get merchant email (in real app, this would be from tenant settings)
            merchant_email = tenant.settings.get('notification_email', 'merchant@example.com')
            
            subject, html_content, text_content = self._generate_merchant_email_content(
                return_request, tenant, notification_type
            )
            
            return await self._send_email(
                to_email=merchant_email,
                to_name=tenant.name,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
        
        except Exception as e:
            print(f"Error sending merchant notification email: {e}")
            return False
    
    def _generate_return_email_content(self, return_request: ReturnRequest, tenant: Tenant, previous_status: Optional[str] = None) -> tuple:
        """Generate email content for return status notifications"""
        
        # Email templates based on status
        templates = {
            ReturnStatus.REQUESTED: {
                'subject': 'Return Request Received - #{order_number}',
                'message': 'We have received your return request and will review it shortly.',
                'next_steps': 'We will review your request within 1-2 business days and send you an update.'
            },
            ReturnStatus.APPROVED: {
                'subject': 'Return Request Approved - #{order_number}',
                'message': 'Great news! Your return request has been approved.',
                'next_steps': 'We will email you a prepaid return shipping label within 24 hours.'
            },
            ReturnStatus.DENIED: {
                'subject': 'Return Request Update - #{order_number}',
                'message': 'After reviewing your request, we are unable to process this return.',
                'next_steps': 'If you have questions about this decision, please contact our support team.'
            },
            ReturnStatus.IN_TRANSIT: {
                'subject': 'Return Package in Transit - #{order_number}',
                'message': 'We have received your return package and it is on its way to our facility.',
                'next_steps': 'We will inspect your items and process your refund within 3-5 business days.'
            },
            ReturnStatus.RECEIVED: {
                'subject': 'Return Package Received - #{order_number}',
                'message': 'Your return package has been received at our facility.',
                'next_steps': 'We are now inspecting your items and will process your refund shortly.'
            },
            ReturnStatus.REFUNDED: {
                'subject': 'Refund Processed - #{order_number}',
                'message': 'Your refund has been processed successfully!',
                'next_steps': 'You should see the refund in your original payment method within 3-5 business days.'
            },
            ReturnStatus.EXCHANGED: {
                'subject': 'Exchange Processed - #{order_number}',
                'message': 'Your exchange has been processed and your new item is being prepared for shipment.',
                'next_steps': 'You will receive tracking information for your replacement item within 24 hours.'
            }
        }
        
        template_data = templates.get(return_request.status, templates[ReturnStatus.REQUESTED])
        
        # Format subject
        subject = template_data['subject'].format(order_number=return_request.id[:8])
        
        # Generate HTML content
        html_template = Template("""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }
                .header { background-color: {{ brand_color }}; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .return-details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .footer { background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; }
                .status-badge { 
                    display: inline-block; 
                    padding: 5px 15px; 
                    border-radius: 20px; 
                    background-color: {{ status_color }}; 
                    color: white; 
                    font-weight: bold; 
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{{ tenant_name }}</h2>
                <p>{{ custom_message }}</p>
            </div>
            
            <div class="content">
                <h3>Hello {{ customer_name }},</h3>
                
                <p>{{ message }}</p>
                
                <div class="return-details">
                    <h4>Return Details:</h4>
                    <p><strong>Return ID:</strong> {{ return_id }}</p>
                    <p><strong>Status:</strong> <span class="status-badge">{{ status_display }}</span></p>
                    <p><strong>Return Amount:</strong> ${{ refund_amount }}</p>
                    <p><strong>Reason:</strong> {{ reason_display }}</p>
                    {% if tracking_number %}
                    <p><strong>Tracking Number:</strong> {{ tracking_number }}</p>
                    {% endif %}
                </div>
                
                <h4>What's Next?</h4>
                <p>{{ next_steps }}</p>
                
                {% if notes %}
                <h4>Additional Notes:</h4>
                <p>{{ notes }}</p>
                {% endif %}
            </div>
            
            <div class="footer">
                <p>Thank you for choosing {{ tenant_name }}!</p>
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </body>
        </html>
        """)
        
        # Status colors
        status_colors = {
            ReturnStatus.REQUESTED: '#ffc107',
            ReturnStatus.APPROVED: '#28a745',
            ReturnStatus.DENIED: '#dc3545',
            ReturnStatus.IN_TRANSIT: '#007bff',
            ReturnStatus.RECEIVED: '#6f42c1',
            ReturnStatus.REFUNDED: '#28a745',
            ReturnStatus.EXCHANGED: '#17a2b8'
        }
        
        html_content = html_template.render(
            tenant_name=tenant.name,
            custom_message=tenant.settings.get('custom_message', 'Returns made easy'),
            brand_color=tenant.settings.get('brand_color', '#3b82f6'),
            customer_name=return_request.customer_name,
            message=template_data['message'],
            return_id=return_request.id,
            status_display=return_request.status.replace('_', ' ').title(),
            status_color=status_colors.get(return_request.status, '#6c757d'),
            refund_amount=f"{return_request.refund_amount:.2f}",
            reason_display=return_request.reason.replace('_', ' ').title(),
            tracking_number=return_request.tracking_number,
            next_steps=template_data['next_steps'],
            notes=return_request.notes
        )
        
        # Generate plain text content
        text_content = f"""
        {tenant.name}
        
        Hello {return_request.customer_name},
        
        {template_data['message']}
        
        Return Details:
        - Return ID: {return_request.id}
        - Status: {return_request.status.replace('_', ' ').title()}
        - Return Amount: ${return_request.refund_amount:.2f}
        - Reason: {return_request.reason.replace('_', ' ').title()}
        {f'- Tracking Number: {return_request.tracking_number}' if return_request.tracking_number else ''}
        
        What's Next?
        {template_data['next_steps']}
        
        {f'Additional Notes: {return_request.notes}' if return_request.notes else ''}
        
        Thank you for choosing {tenant.name}!
        """
        
        return subject, html_content, text_content
    
    def _generate_merchant_email_content(self, return_request: ReturnRequest, tenant: Tenant, notification_type: str) -> tuple:
        """Generate email content for merchant notifications"""
        
        subject = f"Return Request {notification_type.title()} - {return_request.customer_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Return Request {notification_type.title()}</h2>
            
            <h3>Customer Information:</h3>
            <p><strong>Name:</strong> {return_request.customer_name}</p>
            <p><strong>Email:</strong> {return_request.customer_email}</p>
            
            <h3>Return Details:</h3>
            <p><strong>Return ID:</strong> {return_request.id}</p>
            <p><strong>Status:</strong> {return_request.status.replace('_', ' ').title()}</p>
            <p><strong>Reason:</strong> {return_request.reason.replace('_', ' ').title()}</p>
            <p><strong>Amount:</strong> ${return_request.refund_amount:.2f}</p>
            
            {f'<p><strong>Notes:</strong> {return_request.notes}</p>' if return_request.notes else ''}
            
            <h3>Items to Return:</h3>
            <ul>
            {''.join([f'<li>{item.product_name} - Qty: {item.quantity} - ${item.price}</li>' for item in return_request.items_to_return])}
            </ul>
            
            <p>Please review this return request in your dashboard.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Return Request {notification_type.title()}
        
        Customer: {return_request.customer_name} ({return_request.customer_email})
        Return ID: {return_request.id}
        Status: {return_request.status.replace('_', ' ').title()}
        Reason: {return_request.reason.replace('_', ' ').title()}
        Amount: ${return_request.refund_amount:.2f}
        
        {f'Notes: {return_request.notes}' if return_request.notes else ''}
        
        Items to Return:
        {chr(10).join([f'- {item.product_name} - Qty: {item.quantity} - ${item.price}' for item in return_request.items_to_return])}
        """
        
        return subject, html_content, text_content
    
    async def _send_email(self, to_email: str, to_name: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = f"{to_name} <{to_email}>"
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}: {subject}")
            return True
        
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_return_requested_email(self, customer_email: str, return_record: Dict, order: Dict) -> bool:
        """Send email notification when return is requested"""
        if not self.enabled:
            print("Email notification skipped - service disabled")
            return False
        
        try:
            subject = f"Return Request Received - Order #{order['order_number']}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #3b82f6; color: white; padding: 20px; text-align: center;">
                    <h2>Return Request Received</h2>
                </div>
                
                <div style="padding: 20px;">
                    <h3>Hello {return_record['customer_name']},</h3>
                    
                    <p>We have received your return request and will review it shortly.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4>Return Details:</h4>
                        <p><strong>Return ID:</strong> {return_record['id']}</p>
                        <p><strong>Order Number:</strong> #{return_record['order_number']}</p>
                        <p><strong>Status:</strong> {return_record['status'].title()}</p>
                        <p><strong>Estimated Refund:</strong> ${return_record['estimated_refund']:.2f}</p>
                    </div>
                    
                    <h4>What's Next?</h4>
                    <p>We will review your request within 1-2 business days and send you an update via email.</p>
                </div>
                
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px;">
                    <p>Thank you for your business!</p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Return Request Received
            
            Hello {return_record['customer_name']},
            
            We have received your return request and will review it shortly.
            
            Return Details:
            - Return ID: {return_record['id']}
            - Order Number: #{return_record['order_number']}
            - Status: {return_record['status'].title()}
            - Estimated Refund: ${return_record['estimated_refund']:.2f}
            
            What's Next?
            We will review your request within 1-2 business days and send you an update via email.
            
            Thank you for your business!
            """
            
            return await self._send_email(customer_email, return_record['customer_name'], subject, html_content, text_content)
            
        except Exception as e:
            print(f"Failed to send return requested email: {e}")
            return False

    async def send_return_approved_email(self, customer_email: str, return_record: Dict, order: Dict, label_url: str = None) -> bool:
        """Send email notification when return is approved"""
        if not self.enabled:
            print("Email notification skipped - service disabled")
            return False
        
        try:
            subject = f"Return Request Approved - Order #{order['order_number']}"
            
            label_section = ""
            if label_url:
                label_section = f"""
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h4 style="color: #155724;">Return Label Ready</h4>
                    <p>Your prepaid return label is ready! <a href="{label_url}" style="color: #155724; font-weight: bold;">Download Return Label</a></p>
                </div>
                """
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
                    <h2>Return Request Approved</h2>
                </div>
                
                <div style="padding: 20px;">
                    <h3>Great news, {return_record['customer_name']}!</h3>
                    
                    <p>Your return request has been approved.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4>Return Details:</h4>
                        <p><strong>Return ID:</strong> {return_record['id']}</p>
                        <p><strong>Order Number:</strong> #{return_record['order_number']}</p>
                        <p><strong>Status:</strong> Approved</p>
                        <p><strong>Refund Amount:</strong> ${return_record['estimated_refund']:.2f}</p>
                    </div>
                    
                    {label_section}
                    
                    <h4>What's Next?</h4>
                    <p>Pack your items securely and send them back using the return method you selected. We'll process your refund within 3-5 business days after we receive your items.</p>
                </div>
                
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px;">
                    <p>Thank you for your business!</p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Return Request Approved
            
            Great news, {return_record['customer_name']}!
            
            Your return request has been approved.
            
            Return Details:
            - Return ID: {return_record['id']}
            - Order Number: #{return_record['order_number']}
            - Status: Approved
            - Refund Amount: ${return_record['estimated_refund']:.2f}
            
            {'Return Label: ' + label_url if label_url else ''}
            
            What's Next?
            Pack your items securely and send them back using the return method you selected. We'll process your refund within 3-5 business days after we receive your items.
            
            Thank you for your business!
            """
            
            return await self._send_email(customer_email, return_record['customer_name'], subject, html_content, text_content)
            
        except Exception as e:
            print(f"Failed to send return approved email: {e}")
            return False

    async def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify SMTP configuration"""
        if not self.enabled:
            return False
        
        subject = "Test Email - Returns Manager"
        html_content = """
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email from your Returns Manager system.</p>
            <p>If you received this email, your SMTP configuration is working correctly!</p>
        </body>
        </html>
        """
        text_content = "This is a test email from your Returns Manager system. SMTP configuration is working!"
        
        return await self._send_email(to_email, "Test User", subject, html_content, text_content)