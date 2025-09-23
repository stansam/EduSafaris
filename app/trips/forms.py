from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DateField, IntegerField, DecimalField, SelectField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, Email, Optional, NumberRange, ValidationError
from datetime import date

class TripForm(FlaskForm):
    title = StringField('Trip Title', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    destination = StringField('Destination', validators=[DataRequired(), Length(min=1, max=200)])
    
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    registration_deadline = DateField('Registration Deadline', validators=[Optional()])
    
    max_participants = IntegerField('Maximum Participants', 
                                  validators=[DataRequired(), NumberRange(min=1, max=500)])
    min_participants = IntegerField('Minimum Participants', 
                                  validators=[DataRequired(), NumberRange(min=1, max=500)])
    price_per_student = DecimalField('Price per Student', validators=[DataRequired(), NumberRange(min=0)])
    
    category = SelectField('Category', choices=[
        ('', 'Select Category'),
        ('science', 'Science'),
        ('history', 'History'),
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
        ('art', 'Art'),
        ('nature', 'Nature'),
        ('other', 'Other')
    ], validators=[Optional()])
    
    grade_level = SelectField('Grade Level', choices=[
        ('', 'Select Grade Level'),
        ('K-2', 'Kindergarten - 2nd Grade'),
        ('3-5', '3rd - 5th Grade'),
        ('6-8', '6th - 8th Grade'),
        ('9-12', '9th - 12th Grade'),
        ('mixed', 'Mixed Grades')
    ], validators=[Optional()])
    
    medical_info_required = BooleanField('Medical Information Required', default=True)
    consent_required = BooleanField('Consent Forms Required', default=True)
    
    itinerary = TextAreaField('Itinerary (JSON format)', validators=[Optional()])
    
    def validate_end_date(self, field):
        if field.data and self.start_date.data and field.data <= self.start_date.data:
            raise ValidationError('End date must be after start date.')
    
    def validate_registration_deadline(self, field):
        if field.data and self.start_date.data and field.data >= self.start_date.data:
            raise ValidationError('Registration deadline must be before start date.')
    
    def validate_min_participants(self, field):
        if field.data and self.max_participants.data and field.data > self.max_participants.data:
            raise ValidationError('Minimum participants cannot exceed maximum participants.')


class VendorSelectForm(FlaskForm):
    vendor_id = HiddenField('Vendor ID', validators=[DataRequired()])
    booking_type = SelectField('Service Type', choices=[
        ('transportation', 'Transportation'),
        ('accommodation', 'Accommodation'),
        ('activity', 'Activity'),
        ('catering', 'Catering'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    service_description = TextAreaField('Service Description', 
                                      validators=[DataRequired(), Length(min=10, max=500)])
    special_requirements = TextAreaField('Special Requirements', validators=[Optional(), Length(max=500)])
    quoted_amount = DecimalField('Quoted Amount', validators=[Optional(), NumberRange(min=0)])


class ParticipantForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    grade_level = StringField('Grade Level', validators=[Optional(), Length(max=20)])
    student_id = StringField('Student ID', validators=[Optional(), Length(max=50)])
    
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    
    # Medical Information
    medical_conditions = TextAreaField('Medical Conditions', validators=[Optional()])
    medications = TextAreaField('Current Medications', validators=[Optional()])
    allergies = TextAreaField('Allergies', validators=[Optional()])
    dietary_restrictions = TextAreaField('Dietary Restrictions', validators=[Optional()])
    
    # Emergency Contacts
    emergency_contact_1_name = StringField('Emergency Contact 1 Name', 
                                         validators=[DataRequired(), Length(min=1, max=100)])
    emergency_contact_1_phone = StringField('Emergency Contact 1 Phone', 
                                          validators=[DataRequired(), Length(min=1, max=20)])
    emergency_contact_1_relationship = StringField('Relationship', 
                                                 validators=[DataRequired(), Length(min=1, max=50)])
    
    def validate_date_of_birth(self, field):
        if field.data and field.data > date.today():
            raise ValidationError('Date of birth cannot be in the future.')


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[Optional(), Length(max=100)])


class CSVUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[
        DataRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])