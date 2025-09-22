from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, Regexp
from wtforms.widgets import TextArea
from app.models import User

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(min=2, max=50, message='Last name must be between 2 and 50 characters')
    ])
    
    phone = StringField('Phone Number', validators=[
        Optional(),
        Regexp(r'^\+?[\d\s\-\(\)]+$', message='Please enter a valid phone number')
    ])
    
    school = StringField('School/Organization', validators=[
        Optional(),
        Length(max=100, message='School name cannot exceed 100 characters')
    ])
    
    bio = TextAreaField('Bio', validators=[
        Optional(),
        Length(max=500, message='Bio cannot exceed 500 characters')
    ], widget=TextArea())
    
    emergency_contact = StringField('Emergency Contact Name', validators=[
        Optional(),
        Length(max=100, message='Emergency contact name cannot exceed 100 characters')
    ])
    
    emergency_phone = StringField('Emergency Contact Phone', validators=[
        Optional(),
        Regexp(r'^\+?[\d\s\-\(\)]+$', message='Please enter a valid phone number')
    ])
    
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only (JPG, JPEG, PNG, GIF)')
    ])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', 
               message='Password must contain at least one lowercase letter, one uppercase letter, and one digit')
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])

class AdminUserEditForm(FlaskForm):
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(min=2, max=50, message='Last name must be between 2 and 50 characters')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('teacher', 'Teacher'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])
    
    is_active = SelectField('Status', choices=[
        ('1', 'Active'),
        ('0', 'Inactive')
    ], coerce=int, validators=[DataRequired()])