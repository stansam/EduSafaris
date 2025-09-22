import os
import smtplib
import requests
from functools import wraps
from flask import current_app, render_template, flash, redirect, url_for, request
from flask_login import current_user
from flask_mail import Message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from weasyprint import HTML, CSS
from io import BytesIO
from app.extensions import mail

def roles_required(*roles):
    """Decorator to require specific user roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login', next=request.url))
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def send_email(to, subject, template, **kwargs):
    """
    Send email using Flask-Mail
    
    Args:
        to: Recipient email address (string or list)
        subject: Email subject
        template: Template name (without .html extension)
        **kwargs: Template variables
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Render HTML template
        msg.html = render_template(f'emails/{template}.html', **kwargs)
        
        # Try to render text template (optional)
        try:
            msg.body = render_template(f'emails/{template}.txt', **kwargs)
        except:
            # If no text template exists, create a simple text version
            msg.body = f"Please view this email in an HTML-capable email client.\n\nSubject: {subject}"
        
        mail.send(msg)
        current_app.logger.info(f'Email sent successfully to {to}')
        return True
        
    except Exception as e:
        current_app.logger.error(f'Failed to send email to {to}: {str(e)}')
        return False

def send_sms(phone, message):
    """
    Send SMS using configured SMS API
    
    Args:
        phone: Phone number in international format
        message: SMS message text
    """
    try:
        # This is a placeholder implementation
        # Replace with your SMS provider's API
        api_key = current_app.config.get('SMS_API_KEY')
        
        if not api_key:
            current_app.logger.warning('SMS API key not configured')
            return False
        
        # Example implementation for a generic SMS API
        # Adapt this to your SMS provider's API specification
        api_url = "https://api.sms-provider.com/send"
        
        payload = {
            'api_key': api_key,
            'to': phone,
            'message': message,
            'from': 'EduSafaris'
        }
        
        response = requests.post(api_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            current_app.logger.info(f'SMS sent successfully to {phone}')
            return True
        else:
            current_app.logger.error(f'SMS failed with status {response.status_code}: {response.text}')
            return False
            
    except Exception as e:
        current_app.logger.error(f'Failed to send SMS to {phone}: {str(e)}')
        return False

def generate_invoice_pdf(booking):
    """
    Generate PDF invoice for a booking
    
    Args:
        booking: Booking model instance
        
    Returns:
        BytesIO object containing the PDF data
    """
    try:
        # Render HTML template for invoice
        html_content = render_template('invoices/booking_invoice.html', booking=booking)
        
        # Create PDF from HTML
        pdf_buffer = BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        current_app.logger.info(f'Invoice PDF generated for booking {booking.id}')
        return pdf_buffer
        
    except Exception as e:
        current_app.logger.error(f'Failed to generate invoice PDF for booking {booking.id}: {str(e)}')
        return None

def format_currency(amount, currency='USD'):
    """Format currency amount for display"""
    if currency == 'USD':
        return f"${amount:,.2f}"
    elif currency == 'KES':
        return f"KSh {amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_phone(phone):
    """Format phone number for display"""
    if not phone:
        return ''
    
    # Remove non-numeric characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone

def validate_file_upload(file, allowed_extensions, max_size_mb=5):
    """
    Validate file upload
    
    Args:
        file: Uploaded file object
        allowed_extensions: Set of allowed file extensions
        max_size_mb: Maximum file size in MB
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file selected"
    
    # Check file extension
    if '.' not in file.filename:
        return False, "File must have an extension"
    
    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension not in allowed_extensions:
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size (if the file object supports it)
    try:
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if size > max_size_bytes:
            return False, f"File too large. Maximum size: {max_size_mb}MB"
    except:
        # If we can't check size, continue anyway
        pass
    
    return True, None

def generate_reference_number(prefix='REF'):
    """Generate a unique reference number"""
    import uuid
    import datetime
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4()).split('-')[0].upper()
    
    return f"{prefix}-{timestamp}-{unique_id}"

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    
    from datetime import date
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    from werkzeug.utils import secure_filename
    
    # Use werkzeug's secure_filename and additional sanitization
    safe_name = secure_filename(filename)
    
    # Remove any remaining problematic characters
    safe_name = re.sub(r'[^\w\s.-]', '', safe_name)
    safe_name = re.sub(r'[-\s]+', '-', safe_name)
    
    return safe_name.strip('-')

def process_csv_participants(csv_file, trip):
    """
    Process CSV file to create trip participants
    
    Args:
        csv_file: Uploaded CSV file
        trip: Trip model instance
        
    Returns:
        tuple: (success_count, error_list)
    """
    import csv
    from io import StringIO
    from app.models import Participant
    from app.extensions import db
    
    success_count = 0
    errors = []
    
    try:
        # Read CSV content
        csv_content = csv_file.read().decode('utf-8')
        csv_file = StringIO(csv_content)
        
        reader = csv.DictReader(csv_file)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is headers
            try:
                # Validate required fields
                if not row.get('first_name') or not row.get('last_name'):
                    errors.append(f"Row {row_num}: First name and last name are required")
                    continue
                
                # Create participant
                participant = Participant(
                    first_name=row['first_name'].strip(),
                    last_name=row['last_name'].strip(),
                    email=row.get('email', '').strip() or None,
                    phone=row.get('phone', '').strip() or None,
                    grade_level=row.get('grade_level', '').strip() or None,
                    student_id=row.get('student_id', '').strip() or None,
                    medical_conditions=row.get('medical_conditions', '').strip() or None,
                    allergies=row.get('allergies', '').strip() or None,
                    dietary_restrictions=row.get('dietary_restrictions', '').strip() or None,
                    emergency_contact_1_name=row.get('emergency_contact_1_name', '').strip() or None,
                    emergency_contact_1_phone=row.get('emergency_contact_1_phone', '').strip() or None,
                    emergency_contact_1_relationship=row.get('emergency_contact_1_relationship', '').strip() or None,
                    trip_id=trip.id
                )
                
                db.session.add(participant)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        if success_count > 0:
            db.session.commit()
            
    except Exception as e:
        errors.append(f"Failed to process CSV file: {str(e)}")
        db.session.rollback()
    
    return success_count, errors