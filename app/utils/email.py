from flask import current_app
from app.utils.utils import send_email

def send_password_reset_email(user, token):
    """Send password reset email"""
    reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5000')}/auth/reset_password/{token}"
    
    return send_email(
        to=user.email,
        subject='Password Reset Request',
        template='password_reset',
        user=user,
        reset_url=reset_url
    )

def send_verification_email(user, token):
    """Send email verification email"""
    verify_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5000')}/auth/verify_email/{token}"
    
    return send_email(
        to=user.email,
        subject='Please Verify Your Email',
        template='email_verification',
        user=user,
        verify_url=verify_url
    )