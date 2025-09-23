from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import TextArea

from app.models.trip import Trip


class ConsentForm(FlaskForm):
    """Form for parent consent submission"""
    student_name = StringField(
        'Student Name',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    
    medical_info = TextAreaField(
        'Medical Information',
        validators=[Optional(), Length(max=1000)],
        description='Please list any medical conditions, allergies, medications, or dietary restrictions.',
        widget=TextArea()
    )
    
    emergency_contact = StringField(
        'Emergency Contact',
        validators=[DataRequired(), Length(max=200)],
        description='Name and phone number of emergency contact'
    )
    
    signature_text = StringField(
        'Typed Signature',
        validators=[Optional(), Length(max=100)],
        description='Type your full name if not using digital signature'
    )
    
    signature_image = HiddenField(
        'Digital Signature',
        validators=[Optional()]
    )
    
    def validate(self, **kwargs):
        """Custom validation to ensure either typed or digital signature"""
        rv = FlaskForm.validate(self, **kwargs)
        if not rv:
            return False
        
        # Must have either typed signature or digital signature
        if not self.signature_text.data and not self.signature_image.data:
            self.signature_text.errors.append(
                'Please provide either a typed signature or draw your digital signature.'
            )
            return False
        
        return True


class NotificationForm(FlaskForm):
    """Form for sending notifications to parents"""
    trip_id = SelectField(
        'Trip',
        coerce=int,
        validators=[DataRequired()],
        choices=[]  # Populated in route
    )
    
    message = TextAreaField(
        'Message',
        validators=[DataRequired(), Length(min=10, max=1000)],
        description='Message to send to all parents with children on this trip',
        widget=TextArea()
    )
    
    def validate_trip_id(self, field):
        """Validate trip selection"""
        if field.data == 0:
            raise ValueError('Please select a trip')
        
        trip = Trip.query.get(field.data)
        if not trip:
            raise ValueError('Invalid trip selected')