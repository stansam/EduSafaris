"""
Import all models to ensure they are registered with SQLAlchemy
"""
from app.models.base import BaseModel
from app.models.user import User
from app.models.trip import Trip
from app.models.vendor import Vendor
from app.models.school import School
from app.models.service_booking import ServiceBooking
from app.models.trip_registration import TripRegistration
from app.models.participant import Participant
from app.models.consent import Consent
from app.models.location import Location
from app.models.payment import BasePayment, ServicePayment, RegistrationPayment, AdvertisementPayment
from app.models.notification import Notification
from app.models.emergency import Emergency
from app.models.advertisement import Advertisement
from app.models.document import Document
from app.models.review import Review
from app.models.message import Message
from app.models.activity_log import ActivityLog

__all__ = [
    'BaseModel',
    'User', 
    'Trip', 
    'Vendor', 
    'School',
    'ServiceBooking', 
    'TripRegistration', 
    'Participant', 
    'Consent', 
    'Location', 
    'BasePayment', 
    'ServicePayment', 
    'RegistrationPayment', 
    'AdvertisementPayment', 
    'Notification', 
    'Emergency', 
    'Advertisement'
    'Document',
    'Review',
    'Message',
    'ActivityLog'
]