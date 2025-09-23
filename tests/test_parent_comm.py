import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import base64
from flask import url_for
from flask_testing import TestCase

from app import create_app, db
from app.models.user import User
from app.models.trip import Trip
from app.models.participant import Participant
from app.models.consent import Consent
from app.models.notification import Notification


class ParentCommTestCase(TestCase):
    
    def create_app(self):
        """Create app for testing"""
        config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        }
        return create_app(config)
    
    def setUp(self):
        """Set up test fixtures"""
        db.create_all()
        
        # Create test users
        self.parent = User(
            email='parent@test.com',
            first_name='John',
            last_name='Parent',
            role='parent'
        )
        self.parent.password = 'password123'
        
        self.teacher = User(
            email='teacher@test.com',
            first_name='Jane',
            last_name='Teacher',
            role='teacher'
        )
        self.teacher.password = 'password123'
        
        db.session.add(self.parent)
        db.session.add(self.teacher)
        db.session.commit()
        
        # Create test trip
        self.trip = Trip(
            title='Science Museum Visit',
            description='Educational trip to the science museum',
            destination='Science Museum',
            start_date='2024-03-15',
            end_date='2024-03-15',
            price_per_student=50.00,
            max_participants=30,
            organizer_id=self.teacher.id
        )
        db.session.add(self.trip)
        db.session.commit()
        
        # Create test participant
        self.participant = Participant(
            first_name='Child',
            last_name='Student',
            trip_id=self.trip.id,
            user_id=self.parent.id,
            status='confirmed'
        )
        db.session.add(self.participant)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
    
    def login_user(self, user):
        """Helper to log in a user"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    
    def test_parent_trips_requires_login(self):
        """Test that parent trips page requires login"""
        response = self.client.get(url_for('parent_comm.parent_trips'))
        self.assert401(response)
    
    def test_parent_trips_access_control(self):
        """Test that only parents can access parent trips"""
        self.login_user(self.teacher)
        response = self.client.get(url_for('parent_comm.parent_trips'))
        self.assertRedirects(response, url_for('main.index'))
    
    def test_parent_trips_display(self):
        """Test parent trips page displays correctly"""
        self.login_user(self.parent)
        response = self.client.get(url_for('parent_comm.parent_trips'))
        self.assert200(response)
        self.assertIn(self.trip.title.encode(), response.data)
        self.assertIn(self.participant.full_name.encode(), response.data)
    
    def test_consent_form_get(self):
        """Test consent form GET request"""
        self.login_user(self.parent)
        response = self.client.get(
            url_for('parent_comm.consent_form', trip_id=self.trip.id)
        )
        self.assert200(response)
        self.assertIn(self.trip.title.encode(), response.data)
        self.assertIn(self.participant.full_name.encode(), response.data)
    
    def test_consent_form_post_typed_signature(self):
        """Test consent form submission with typed signature"""
        self.login_user(self.parent)
        
        form_data = {
            'student_name': self.participant.full_name,
            'medical_info': 'No allergies',
            'emergency_contact': 'Emergency Contact - 555-1234',
            'signature_text': 'John Parent'
        }
        
        response = self.client.post(
            url_for('parent_comm.consent_form', trip_id=self.trip.id),
            data=form_data
        )
        
        self.assertRedirects(response, url_for('parent_comm.parent_trips'))
        
        # Check consent was created
        consent = Consent.query.filter_by(participant_id=self.participant.id).first()
        self.assertIsNotNone(consent)
        self.assertTrue(consent.is_signed)
        self.assertEqual(consent.signer_name, 'John Parent')
    
    @patch('app.parent_comm.routes.os.makedirs')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('base64.b64decode')
    def test_consent_form_post_digital_signature(self, mock_b64decode, mock_open, mock_makedirs):
        """Test consent form submission with digital signature"""
        self.login_user(self.parent)
        
        # Mock base64 signature data
        mock_signature = b'fake_png_data'
        mock_b64decode.return_value = mock_signature
        
        form_data = {
            'student_name': self.participant.full_name,
            'medical_info': 'Asthma',
            'emergency_contact': 'Emergency Contact - 555-1234',
            'signature_image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        }
        
        with patch('app.parent_comm.routes.current_app') as mock_app:
            mock_app.static_folder = '/tmp/static'
            
            response = self.client.post(
                url_for('parent_comm.consent_form', trip_id=self.trip.id),
                data=form_data
            )
            
            self.assertRedirects(response, url_for('parent_comm.parent_trips'))
            
            # Check consent was created
            consent = Consent.query.filter_by(participant_id=self.participant.id).first()
            self.assertIsNotNone(consent)
            self.assertTrue(consent.is_signed)
            self.assertIn('uploads/consents/', consent.signature_data)
    
    def test_consent_already_signed(self):
        """Test accessing consent form when already signed"""
        # Create existing signed consent
        consent = Consent(
            participant_id=self.participant.id,
            parent_id=self.parent.id,
            consent_type='trip_participation',
            title=f'Trip Participation Consent - {self.trip.title}',
            content='Consent content',
            is_signed=True
        )
        db.session.add(consent)
        db.session.commit()
        
        self.login_user(self.parent)
        response = self.client.get(
            url_for('parent_comm.consent_form', trip_id=self.trip.id)
        )
        
        self.assertRedirects(response, url_for('parent_comm.parent_trips'))
    
    def test_notifications_page(self):
        """Test notifications page"""
        # Create test notification
        notification = Notification(
            title='Test Notification',
            message='Test message',
            notification_type='trip_update',
            sender_id=self.teacher.id,
            recipient_id=self.parent.id
        )
        db.session.add(notification)
        db.session.commit()
        
        self.login_user(self.parent)
        response = self.client.get(url_for('parent_comm.notifications'))
        self.assert200(response)
        self.assertIn(b'Test Notification', response.data)
    
    def test_mark_notification_read(self):
        """Test marking notification as read"""
        notification = Notification(
            title='Test Notification',
            message='Test message',
            notification_type='trip_update',
            sender_id=self.teacher.id,
            recipient_id=self.parent.id,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        
        self.login_user(self.parent)
        response = self.client.post(
            url_for('parent_comm.mark_notification_read', notification_id=notification.id)
        )
        
        self.assert200(response)
        self.assertIn(b'success', response.data)
        
        # Check notification was marked as read
        notification = Notification.query.get(notification.id)
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_date)
    
    def test_send_notification_access_control(self):
        """Test send notification requires teacher/admin role"""
        self.login_user(self.parent)
        response = self.client.get(url_for('parent_comm.send_notification'))
        self.assertRedirects(response, url_for('main.index'))
    
    @patch('app.parent_comm.routes.socketio')
    @patch('app.parent_comm.routes.send_email')
    @patch('app.parent_comm.routes.send_sms')
    def test_send_notification_post(self, mock_sms, mock_email, mock_socketio):
        """Test sending notification to parents"""
        self.login_user(self.teacher)
        
        form_data = {
            'trip_id': self.trip.id,
            'message': 'Important trip update for all parents'
        }
        
        response = self.client.post(
            url_for('parent_comm.send_notification'),
            data=form_data
        )
        
        self.assert200(response)  # Should render form again with success message
        
        # Check notification was created
        notification = Notification.query.filter_by(
            recipient_id=self.parent.id,
            sender_id=self.teacher.id
        ).first()
        self.assertIsNotNone(notification)
        self.assertIn('Important trip update', notification.message)
        
        # Check SocketIO was called
        mock_socketio.emit.assert_called()
    
    def test_consent_pdf_generation(self):
        """Test consent PDF generation"""
        # Create signed consent
        consent = Consent(
            participant_id=self.participant.id,
            parent_id=self.parent.id,
            consent_type='trip_participation',
            title=f'Trip Participation Consent - {self.trip.title}',
            content='Consent content',
            is_signed=True,
            signer_name='John Parent'
        )
        db.session.add(consent)
        db.session.commit()
        
        self.login_user(self.parent)
        response = self.client.get(
            url_for('parent_comm.consent_pdf', participant_id=self.participant.id)
        )
        
        self.assert200(response)
        self.assertIn(self.trip.title.encode(), response.data)
        self.assertIn(b'John Parent', response.data)
    
    def test_invalid_participant_access(self):
        """Test access control for invalid participant"""
        # Create another parent
        other_parent = User(
            email='other@test.com',
            first_name='Other',
            last_name='Parent',
            role='parent'
        )
        other_parent.password = 'password123'
        db.session.add(other_parent)
        db.session.commit()
        
        self.login_user(other_parent)
        response = self.client.get(
            url_for('parent_comm.consent_form', trip_id=self.trip.id)
        )
        
        self.assertRedirects(response, url_for('parent_comm.parent_trips'))


if __name__ == '__main__':
    unittest.main()