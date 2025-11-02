from flask import render_template, url_for, flash, redirect, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from flask_jwt_extended import create_access_token
from app.auth import auth_bp
from app.auth.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm
from app.models import User
from app.extensions import db
from app.utils import send_password_reset_email, send_verification_email
import datetime
from collections import defaultdict
import time
from app.auth.activity_log import (
    log_registration, log_login, log_logout,
    log_password_reset_request, log_password_reset_completed,
    log_email_verification
)

reset_attempts = defaultdict(list)

def is_rate_limited(email, max_attempts=3, window_minutes=15):
    """Simple rate limiting for password reset requests"""
    now = time.time()
    window_start = now - (window_minutes * 60)
    
    # Clean old attempts
    reset_attempts[email] = [attempt for attempt in reset_attempts[email] if attempt > window_start]
    
    # Check if rate limited
    if len(reset_attempts[email]) >= max_attempts:
        return True
    
    return False

def add_reset_attempt(email):
    """Add a reset attempt for rate limiting"""
    reset_attempts[email].append(time.time())

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with email verification"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        try:
            # Create new user
            user = User(
                first_name=form.username.data,
                password=form.password.data,
                email=form.email.data.lower(),
                role='parent'
            )
            # user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()

            try:
                log_registration(user, 'parent')
            except Exception as log_error:
                current_app.logger.error(f'Activity log error: {str(log_error)}')
            
            # Send verification email
            token = user.generate_verification_token()
            if send_verification_email(user, token):
                flash('Registration successful! Please check your email to verify your account.', 'success')
            else:
                flash('Registration successful! However, we could not send verification email.', 'warning')
            
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {str(e)}')
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with session management"""
    if current_user.is_authenticated:
        return redirect(current_user.get_dashboard_url())
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.verify_password(form.password.data):
            if not user.is_active:
                try:
                    log_login(user, success=False, error_message='Account deactivated')
                except Exception as log_error:
                    current_app.logger.error(f'Activity log error: {str(log_error)}')
                
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html', title='Sign In', form=form)
            
            # Login user
            login_user(user, remember=form.remember_me.data)
            
            # Update last login time
            user.last_login = datetime.datetime.now()
            db.session.commit()
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = user.get_dashboard_url()
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page)
        else:
            # Log failed login attempt
            try:
                log_login(None, success=False, error_message='Invalid credentials')
            except Exception as log_error:
                current_app.logger.error(f'Activity log error: {str(log_error)}')
            
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.first_name
    user_to_log = current_user._get_current_object()
    
    try:
        log_logout(user_to_log)
    except Exception as log_error:
        current_app.logger.error(f'Activity log error: {str(log_error)}')

    logout_user()
    flash(f'You have been logged out, {username}.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RequestResetForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower()
        
        # Check rate limiting
        if is_rate_limited(email):
            flash('Too many reset requests. Please try again later.', 'warning')
            return render_template('auth/reset_request.html', title='Reset Password', form=form)
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate and send reset token
            token = user.generate_reset_token()
            if send_password_reset_email(user, token):
                add_reset_attempt(email)
                flash('A password reset link has been sent to your email.', 'info')
            else:
                flash('Failed to send reset email. Please try again later.', 'error')
        else:
            try:
                log_password_reset_request(None)
            except Exception as log_error:
                current_app.logger.error(f'Activity log error: {str(log_error)}')

            flash('If an account with that email exists, a reset link has been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_request.html', title='Reset Password', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('auth.reset_request'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        try:
            user.set_password(form.password.data)
            db.session.commit()

            try:
                log_password_reset_completed(user)
            except Exception as log_error:
                current_app.logger.error(f'Activity log error: {str(log_error)}')

            flash('Your password has been updated! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Password reset error: {str(e)}')
            flash('An error occurred while resetting your password.', 'error')
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form)

@auth_bp.route('/verify_email/<token>')
def verify_email(token):
    """Verify email address"""
    if current_user.is_authenticated and current_user.is_verified:
        flash('Your email is already verified.', 'info')
        return redirect(current_user.get_dashboard_url())
    
    user = User.verify_verification_token(token)
    if not user:
        flash('That is an invalid or expired verification link.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        user.is_verified = True
        db.session.commit()
        
        try:
            log_email_verification(user)
        except Exception as log_error:
            current_app.logger.error(f'Activity log error: {str(log_error)}')

        flash('Your email has been verified! You can now access all features.', 'success')
        
        if current_user.is_authenticated:
            return redirect(current_user.get_dashboard_url())
        else:
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Email verification error: {str(e)}')
        flash('An error occurred while verifying your email.', 'error')
        return redirect(url_for('auth.login'))

    
@auth_bp.route('/register/teacher')
def register_teacher():
    """Render teacher registration form"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('auth/register_teacher.html')

@auth_bp.route('/register/vendor')
def register_vendor():
    """Render vendor registration form"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('auth/register_vendor.html')