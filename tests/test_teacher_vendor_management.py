import unittest
import json
from decimal import Decimal
from datetime import datetime, date, timedelta
from app import create_app, db
from app.models import User, Vendor, Trip, Booking, Payment, Review
from flask_login import login_user


class TeacherVendorAPITestCase(unittest.TestCase):
    """Test case for teacher vendor management APIs"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users
        self.teacher = User(
            email='teacher@test.com',
            first_name='Test',
            last_name='Teacher',
            role='teacher',
            is_active=True,
            is_verified=True
        )
        self.teacher.password = 'password123'
        db.session.add(self.teacher)
        
        self.vendor_user = User(
            email='vendor@test.com',
            first_name='Test',
            last_name='Vendor',
            role='vendor',
            is_active=True,
            is_verified=True
        )
        self.vendor_user.password = 'password123'
        db.session.add(self.vendor_user)
        
        # Create test vendor
        self.vendor = Vendor(
            business_name='Test Transport',
            business_type='transportation',
            contact_email='vendor@test.com',
            contact_phone='254712345678',
            city='Nairobi',
            is_verified=True,
            is_active=True,
            user_id=self.vendor_user.id,
            base_price=Decimal('5000.00'),
            average_rating=4.5
        )
        db.session.add(self.vendor)
        
        # Create test trip
        self.trip = Trip(
            title='Test Trip',
            destination='Nairobi',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            status='planning',
            organizer_id=self.teacher.id
        )
        db.session.add(self.trip)
        
        db.session.commit()
    
    def tearDown(self):
        """Tear down test fixtures"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login_teacher(self):
        """Helper method to login as teacher"""
        with self.client:
            self.client.post('/api/auth/login', json={
                'email': 'teacher@test.com',
                'password': 'password123'
            })
    
    def test_search_vendors_success(self):
        """Test successful vendor search"""
        self.login_teacher()
        
        response = self.client.get('/api/teacher/vendors/search?q=transport')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('vendors', data['data'])
        self.assertIn('pagination', data['data'])
    
    def test_search_vendors_with_filters(self):
        """Test vendor search with filters"""
        self.login_teacher()
        
        response = self.client.get(
            '/api/teacher/vendors/search?type=transportation&city=Nairobi&verified=true&min_rating=4'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        vendors = data['data']['vendors']
        
        # Verify filters applied
        for vendor in vendors:
            self.assertTrue(vendor['is_verified'])
            self.assertGreaterEqual(vendor['average_rating'], 4)
    
    def test_search_vendors_pagination(self):
        """Test vendor search pagination"""
        # Create multiple vendors
        for i in range(25):
            vendor = Vendor(
                business_name=f'Test Vendor {i}',
                business_type='transportation',
                contact_email=f'vendor{i}@test.com',
                contact_phone=f'25471234567{i}',
                is_active=True,
                user_id=self.vendor_user.id
            )
            db.session.add(vendor)
        db.session.commit()
        
        self.login_teacher()
        
        response = self.client.get('/api/teacher/vendors/search?page=1&per_page=10')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['data']['vendors']), 10)
        self.assertTrue(data['data']['pagination']['has_next'])
    
    def test_get_vendor_profile_success(self):
        """Test getting vendor profile"""
        self.login_teacher()
        
        response = self.client.get(f'/api/teacher/vendors/{self.vendor.id}')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['id'], self.vendor.id)
        self.assertIn('stats', data['data'])
    
    def test_get_vendor_profile_not_found(self):
        """Test getting non-existent vendor profile"""
        self.login_teacher()
        
        response = self.client.get('/api/teacher/vendors/99999')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', data)
    
    def test_request_quote_success(self):
        """Test successful quote request"""
        self.login_teacher()
        
        quote_data = {
            'trip_id': self.trip.id,
            'booking_type': 'transportation',
            'service_description': 'Need transport for 50 students',
            'special_requirements': 'Air conditioned bus'
        }
        
        response = self.client.post(
            f'/api/teacher/vendors/{self.vendor.id}/quote',
            json=quote_data,
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'pending')
        self.assertEqual(data['data']['booking_type'], 'transportation')
    
    def test_request_quote_missing_fields(self):
        """Test quote request with missing fields"""
        self.login_teacher()
        
        quote_data = {
            'trip_id': self.trip.id
            # Missing required fields
        }
        
        response = self.client.post(
            f'/api/teacher/vendors/{self.vendor.id}/quote',
            json=quote_data,
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
    
    def test_request_quote_invalid_trip(self):
        """Test quote request with invalid trip"""
        self.login_teacher()
        
        quote_data = {
            'trip_id': 99999,
            'booking_type': 'transportation',
            'service_description': 'Need transport'
        }
        
        response = self.client.post(
            f'/api/teacher/vendors/{self.vendor.id}/quote',
            json=quote_data,
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 404)
    
    def test_create_booking_success(self):
        """Test successful booking creation"""
        self.login_teacher()
        
        booking_data = {
            'vendor_id': self.vendor.id,
            'trip_id': self.trip.id,
            'booking_type': 'transportation',
            'service_description': 'Bus transportation',
            'quoted_amount': '50000.00'
        }
        
        response = self.client.post(
            '/api/teacher/vendors/bookings',
            json=booking_data,
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'pending')
    
    def test_create_booking_invalid_amount(self):
        """Test booking creation with invalid amount"""
        self.login_teacher()
        
        booking_data = {
            'vendor_id': self.vendor.id,
            'trip_id': self.trip.id,
            'booking_type': 'transportation',
            'service_description': 'Bus transportation',
            'quoted_amount': '-100.00'  # Invalid negative amount
        }
        
        response = self.client.post(
            '/api/teacher/vendors/bookings',
            json=booking_data,
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
    
    def test_confirm_booking_success(self):
        """Test successful booking confirmation"""
        self.login_teacher()
        
        # Create booking
        booking = Booking(
            status='pending',
            booking_type='transportation',
            service_description='Test booking',
            quoted_amount=Decimal('10000.00'),
            trip_id=self.trip.id,
            vendor_id=self.vendor.id
        )
        db.session.add(booking)
        db.session.commit()
        
        response = self.client.put(
            f'/api/teacher/vendors/bookings/{booking.id}/confirm',
            json={'final_amount': '12000.00'},
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'confirmed')
    
    def test_cancel_booking_success(self):
        """Test successful booking cancellation"""
        self.login_teacher()
        
        # Create booking
        booking = Booking(
            status='pending',
            booking_type='transportation',
            service_description='Test booking',
            quoted_amount=Decimal('10000.00'),
            trip_id=self.trip.id,
            vendor_id=self.vendor.id
        )
        db.session.add(booking)
        db.session.commit()
        
        response = self.client.put(
            f'/api/teacher/vendors/bookings/{booking.id}/cancel',
            json={'reason': 'Plans changed'},
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'cancelled')
    
    def test_rate_vendor_success(self):
        """Test successful vendor rating"""
        self.login_teacher()
        
        # Create completed booking
        booking = Booking(
            status='completed',
            booking_type='transportation',
            service_description='Test booking',
            quoted_amount=Decimal('10000.00'),
            trip_id=self.trip.id,
            vendor_id=self.vendor.id,
            completed_date=datetime.now()
        )
        db.session.add(booking)
        db.session.commit()
        
        rating_data = {
            'rating': 5,
            'title': 'Excellent service',
            'review': 'Very professional and punctual',
            'value_rating': 5,
            'safety_rating': 5
        }
        
        response = self.client.post(
            f'/api/teacher/vendors/bookings/{booking.id}/rate',
            json=rating_data,
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['booking']['rating'], 5)
    
    def test_rate_vendor_invalid_rating(self):
        """Test vendor rating with invalid rating value"""
        self.login_teacher()
        
        # Create completed booking
        booking = Booking(
            status='completed',
            booking_type='transportation',
            service_description='Test booking',
            quoted_amount=Decimal('10000.00'),
            trip_id=self.trip.id,
            vendor_id=self.vendor.id
        )
        db.session.add(booking)
        db.session.commit()
        
        rating_data = {
            'rating': 6,  # Invalid rating
            'review': 'Test review'
        }
        
        response = self.client.post(
            f'/api/teacher/vendors/bookings/{booking.id}/rate',
            json=rating_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_check_availability_success(self):
        """Test successful availability check"""
        self.login_teacher()
        
        availability_data = {
            'vendor_id': self.vendor.id,
            'start_date': (date.today() + timedelta(days=10)).isoformat(),
            'end_date': (date.today() + timedelta(days=15)).isoformat()
        }
        
        response = self.client.post(
            '/api/teacher/vendors/availability',
            json=availability_data,
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('is_available', data['data'])
    
    def test_get_teacher_bookings(self):
        """Test getting teacher's bookings"""
        self.login_teacher()
        
        # Create test bookings
        for i in range(3):
            booking = Booking(
                status='pending',
                booking_type='transportation',
                service_description=f'Booking {i}',
                quoted_amount=Decimal('10000.00'),
                trip_id=self.trip.id,
                vendor_id=self.vendor.id
            )
            db.session.add(booking)
        db.session.commit()
        
        response = self.client.get('/api/teacher/vendors/bookings')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['data']['bookings']), 3)
    
    def test_get_vendor_statistics(self):
        """Test getting vendor statistics"""
        self.login_teacher()
        
        response = self.client.get('/api/teacher/vendors/stats')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('total_bookings', data['data'])
        self.assertIn('by_status', data['data'])
        self.assertIn('total_spent', data['data'])
    
    def test_unauthorized_access(self):
        """Test unauthorized access to APIs"""
        response = self.client.get('/api/teacher/vendors/search')
        self.assertEqual(response.status_code, 401)
    
    def test_non_teacher_access(self):
        """Test non-teacher access to APIs"""
        # Login as vendor (not teacher)
        with self.client:
            self.client.post('/api/auth/login', json={
                'email': 'vendor@test.com',
                'password': 'password123'
            })
            
            response = self.client.get('/api/teacher/vendors/search')
            self.assertEqual(response.status_code, 403)


if __name__ == '__main__':
    unittest.main()