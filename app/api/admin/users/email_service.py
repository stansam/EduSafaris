from flask import current_app
from flask_mail import Mail, Message
from threading import Thread


def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail = Mail(app)
            mail.send(msg)
        except Exception as e:
            # Log the error
            app.logger.error(f"Failed to send email: {str(e)}")
            raise


def send_email(subject, recipients, text_body, html_body=None, sender=None, async_send=True):
    """
    Send email with text and optional HTML body
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        text_body: Plain text email body
        html_body: HTML email body (optional)
        sender: Sender email address (uses default if not provided)
        async_send: Send asynchronously (default: True)
    """
    if not sender:
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@edusafaris.com')
    
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    
    if html_body:
        msg.html = html_body
    
    if async_send:
        # Send email in background thread
        Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
    else:
        mail = Mail(current_app)
        mail.send(msg)


def send_password_reset_email(email, token):
    """
    Send password reset email
    
    Args:
        email: Recipient email address
        token: Password reset token
    """
    reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
    
    subject = "Reset Your EduSafaris Password"
    
    text_body = f"""
    Hi there,
    
    You requested to reset your password for your EduSafaris account.
    
    Please click the link below to reset your password:
    {reset_url}
    
    This link will expire in 24 hours.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    The EduSafaris Team
    """
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; 
                       color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset</h1>
            </div>
            <div class="content">
                <p>Hi there,</p>
                <p>You requested to reset your password for your EduSafaris account.</p>
                <p>Click the button below to reset your password:</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #4CAF50;">{reset_url}</p>
                <p><strong>This link will expire in 24 hours.</strong></p>
                <p>If you didn't request this, please ignore this email. Your password will remain unchanged.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 EduSafaris. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    send_email(subject, [email], text_body, html_body)


def send_email_verification(email, token):
    """
    Send email verification link
    
    Args:
        email: Recipient email address
        token: Verification token
    """
    verify_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={token}"
    
    subject = "Verify Your EduSafaris Email Address"
    
    text_body = f"""
    Welcome to EduSafaris!
    
    Please verify your email address by clicking the link below:
    {verify_url}
    
    This link will expire in 48 hours.
    
    If you didn't create an account with EduSafaris, please ignore this email.
    
    Best regards,
    The EduSafaris Team
    """
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; 
                       color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to EduSafaris!</h1>
            </div>
            <div class="content">
                <p>Thank you for signing up!</p>
                <p>Please verify your email address to activate your account:</p>
                <p style="text-align: center;">
                    <a href="{verify_url}" class="button">Verify Email Address</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #4CAF50;">{verify_url}</p>
                <p><strong>This link will expire in 48 hours.</strong></p>
                <p>If you didn't create an account with EduSafaris, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 EduSafaris. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    send_email(subject, [email], text_body, html_body)


def send_account_status_notification(email, full_name, is_activated):
    """
    Send notification when account is activated/deactivated by admin
    
    Args:
        email: Recipient email address
        full_name: User's full name
        is_activated: Boolean indicating if account was activated or deactivated
    """
    if is_activated:
        subject = "Your EduSafaris Account Has Been Activated"
        action = "activated"
        message = "Your account is now active and you can log in to access all features."
    else:
        subject = "Your EduSafaris Account Has Been Deactivated"
        action = "deactivated"
        message = "Your account has been deactivated. If you believe this is an error, please contact support."
    
    text_body = f"""
    Hi {full_name},
    
    Your EduSafaris account has been {action}.
    
    {message}
    
    If you have any questions, please contact our support team.
    
    Best regards,
    The EduSafaris Team
    """
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: {'#4CAF50' if is_activated else '#f44336'}; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Account {action.capitalize()}</h1>
            </div>
            <div class="content">
                <p>Hi {full_name},</p>
                <p>Your EduSafaris account has been <strong>{action}</strong>.</p>
                <p>{message}</p>
                <p>If you have any questions, please contact our support team at support@edusafaris.com</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 EduSafaris. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    send_email(subject, [email], text_body, html_body)


def send_role_change_notification(email, full_name, old_role, new_role):
    """
    Send notification when user role is changed
    
    Args:
        email: Recipient email address
        full_name: User's full name
        old_role: Previous role
        new_role: New role
    """
    subject = "Your EduSafaris Role Has Been Updated"
    
    text_body = f"""
    Hi {full_name},
    
    Your role on EduSafaris has been changed from {old_role} to {new_role}.
    
    Your new permissions and features are now active.
    
    If you have any questions about your new role, please contact our support team.
    
    Best regards,
    The EduSafaris Team
    """
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .role-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #2196F3; }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Role Updated</h1>
            </div>
            <div class="content">
                <p>Hi {full_name},</p>
                <p>Your role on EduSafaris has been updated:</p>
                <div class="role-box">
                    <p><strong>Previous Role:</strong> {old_role.capitalize()}</p>
                    <p><strong>New Role:</strong> {new_role.capitalize()}</p>
                </div>
                <p>Your new permissions and features are now active.</p>
                <p>If you have any questions about your new role, please contact our support team at support@edusafaris.com</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 EduSafaris. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    send_email(subject, [email], text_body, html_body)