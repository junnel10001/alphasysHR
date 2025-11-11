"""
Email Service for AlphaHR

This service provides email functionality for sending invitation emails,
notifications, and other HR-related communications.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Configuration for email service."""
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool = True
    from_email: str = "noreply@alphahr.com"
    from_name: str = "AlphaHR System"


class EmailProvider(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
    async def send_email(self, to_email: str, subject: str, body: str, **kwargs) -> bool:
        """Send an email."""
        pass


class SMTPEmailProvider(EmailProvider):
    """SMTP-based email provider."""
    
    def __init__(self, config: EmailConfig):
        self.config = config
    
    async def send_email(self, to_email: str, subject: str, body: str, **kwargs) -> bool:
        """Send email using SMTP."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


class MockEmailProvider(EmailProvider):
    """Mock email provider for development/testing."""
    
    def __init__(self):
        self.sent_emails = []
    
    async def send_email(self, to_email: str, subject: str, body: str, **kwargs) -> bool:
        """Mock send email - just log it."""
        email_data = {
            "to": to_email,
            "subject": subject,
            "body": body,
            "sent_at": datetime.utcnow(),
            **kwargs
        }
        self.sent_emails.append(email_data)
        logger.info(f"MOCK EMAIL: To={to_email}, Subject={subject}")
        logger.debug(f"Email body: {body}")
        return True


class EmailService:
    """Main email service class."""
    
    def __init__(self, provider: Optional[EmailProvider] = None):
        if provider is None:
            # Try to configure SMTP from environment, fall back to mock for development
            try:
                # Get email config directly here to avoid circular import issues
                config = EmailConfig(
                    smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                    smtp_port=int(os.getenv("SMTP_PORT", "587")),
                    smtp_username=os.getenv("SMTP_USERNAME", ""),
                    smtp_password=os.getenv("SMTP_PASSWORD", ""),
                    smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
                    from_email=os.getenv("FROM_EMAIL", "noreply@alphahr.com"),
                    from_name=os.getenv("FROM_NAME", "AlphaHR System")
                )
                if config.smtp_username and config.smtp_password:
                    self.provider = SMTPEmailProvider(config)
                    logger.info("Email service configured with SMTP provider")
                else:
                    self.provider = MockEmailProvider()
                    logger.warning("Using mock email provider. Configure SMTP credentials for production.")
            except Exception as e:
                logger.error(f"Failed to configure SMTP provider: {e}. Using mock provider.")
                self.provider = MockEmailProvider()
        else:
            self.provider = provider
    
    async def send_invitation_email(self, 
                                 to_email: str, 
                                 invited_by_name: str,
                                 role_name: str,
                                 department_name: Optional[str] = None,
                                 invitation_link: str = "",
                                 expires_at: Optional[datetime] = None,
                                 **kwargs) -> bool:
        """Send invitation email to a new user."""
        
        subject = f"You're invited to join AlphaHR as {role_name}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h2 style="color: #007bff; margin-bottom: 20px;">Welcome to AlphaHR!</h2>
                
                <p>Dear Candidate,</p>
                
                <p>You have been invited to join AlphaHR by <strong>{invited_by_name}</strong> 
                for the position of <strong>{role_name}</strong>.</p>
                
                {f'<p>Department: <strong>{department_name}</strong></p>' if department_name else ''}
                
                <p>Please click the link below to accept your invitation and complete your registration:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invitation_link}" 
                       style="background-color: #007bff; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Accept Invitation
                    </a>
                </div>
                
                {f'<p><strong>Note:</strong> This invitation expires on {expires_at.strftime("%B %d, %Y at %I:%M %p")}.</p>' if expires_at else ''}
                
                <p>If you have any questions, please contact your administrator.</p>
                
                <hr style="margin: 30px 0; border: 1px solid #dee2e6;">
                
                <p style="color: #6c757d; font-size: 14px;">
                    This is an automated message from AlphaHR. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.provider.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            template_name="invitation",
            **kwargs
        )
    
    async def send_welcome_email(self, 
                              to_email: str, 
                              user_name: str,
                              company_name: str = "AlphaHR",
                              **kwargs) -> bool:
        """Send welcome email after user registration."""
        
        subject = f"Welcome to {company_name}!"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h2 style="color: #28a745; margin-bottom: 20px;">Welcome aboard!</h2>
                
                <p>Dear {user_name},</p>
                
                <p>Welcome to {company_name}! Your account has been successfully created and you can now access the HR system.</p>
                
                <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4>Getting Started:</h4>
                    <ul>
                        <li>Log in to your account using your credentials</li>
                        <li>Complete your profile information</li>
                        <li>Explore the dashboard and available features</li>
                        <li>Contact your manager if you need assistance</li>
                    </ul>
                </div>
                
                <p>We're excited to have you as part of our team!</p>
                
                <hr style="margin: 30px 0; border: 1px solid #dee2e6;">
                
                <p style="color: #6c757d; font-size: 14px;">
                    Best regards,<br>
                    The {company_name} Team
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.provider.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            template_name="welcome",
            **kwargs
        )
    
    async def send_password_reset_email(self, 
                                    to_email: str, 
                                    reset_link: str,
                                    expires_at: Optional[datetime] = None,
                                    **kwargs) -> bool:
        """Send password reset email."""
        
        subject = "Password Reset Request - AlphaHR"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h2 style="color: #dc3545; margin-bottom: 20px;">Password Reset Request</h2>
                
                <p>We received a request to reset your password for your AlphaHR account.</p>
                
                <p>Click the link below to reset your password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="background-color: #dc3545; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                {f'<p><strong>Note:</strong> This link expires on {expires_at.strftime("%B %d, %Y at %I:%M %p")}.</p>' if expires_at else ''}
                
                <p>If you didn't request this password reset, please ignore this email or contact your administrator.</p>
                
                <hr style="margin: 30px 0; border: 1px solid #dee2e6;">
                
                <p style="color: #6c757d; font-size: 14px;">
                    This is an automated message from AlphaHR. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.provider.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            template_name="password_reset",
            **kwargs
        )
    
    async def send_notification_email(self, 
                                to_email: str, 
                                subject: str,
                                message: str,
                                notification_type: str = "general",
                                **kwargs) -> bool:
        """Send general notification email."""
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h2 style="color: #007bff; margin-bottom: 20px;">{subject}</h2>
                
                <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    {message}
                </div>
                
                <hr style="margin: 30px 0; border: 1px solid #dee2e6;">
                
                <p style="color: #6c757d; font-size: 14px;">
                    This is an automated message from AlphaHR. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.provider.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            template_name=notification_type,
            **kwargs
        )
    
    def get_mock_emails(self) -> list:
        """Get list of mock sent emails (for testing)."""
        if isinstance(self.provider, MockEmailProvider):
            return self.provider.sent_emails
        return []


# Global email service instance
email_service = EmailService()


def get_email_service() -> EmailService:
    """Dependency injection for email service."""
    return email_service


def configure_email_service(config: EmailConfig) -> None:
    """Configure the email service with SMTP settings."""
    global email_service
    provider = SMTPEmailProvider(config)
    email_service = EmailService(provider)
    logger.info("Email service configured with SMTP provider")


def configure_mock_email_service() -> None:
    """Configure the email service to use mock provider."""
    global email_service
    email_service = EmailService(MockEmailProvider())
    logger.info("Email service configured with mock provider")


# Configuration from environment variables
def get_email_config_from_env() -> EmailConfig:
    """Get email configuration from environment variables."""
    return EmailConfig(
        smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        from_email=os.getenv("FROM_EMAIL", "noreply@alphahr.com"),
        from_name=os.getenv("FROM_NAME", "AlphaHR System")
    )

