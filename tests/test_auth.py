import unittest
from flask import url_for
from flask_testing import TestCase
from app import create_app, db
from app.models import User
from app.utils import send_password_reset_email
import json

class AuthTestCase(TestCase):
    """Test cases for authentication functionality"""
    
    def create_app(self):
        """Create test app with testing configuration"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['MAIL_SUPPRESS_SEND'] = True  # Don't send emails during tests
        return app
    
    def setUp(self):
        """Set up test database and sample data"""
        db.create_all()
        
        # Create test user
        self.test_user = User(
            username='testuser',
            email='test@example.com'
        )
        self.test_user.set_password('testpassword123')
        db.session.add(self.test_user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
    
    # Registration Tests
    
    def test_register_get(self):
        """Test GET request to registration page"""
        response = self.client.get(url_for('auth.register'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Account', response.data)
    
    def test_register_valid_user(self):
        """Test successful user registration"""
        response = self.client.post(url_for('auth.register'), data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'terms': True
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)
        
        # Check user was created
        user = User.query.filter_by(email='newuser@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'newuser')
        self.assertFalse(user.is_verified)  # Should not be verified initially
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        response = self.client.post(url_for('auth.register'), data={
            'username': 'anotheruser',
            'email': 'test@example.com',  # Already exists
            'password': 'password123',
            'confirm_password': 'password123',
            'terms': True
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email already registered', response.data)
    
    def test_register_duplicate_username(self):
        """Test registration with duplicate username"""
        response = self.client.post(url_for('auth.register'), data={
            'username': 'testuser',  # Already exists
            'email': 'newemail@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'terms': True
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Username already taken', response.data)
    
    def test_register_password_mismatch(self):
        """Test registration with password mismatch"""
        response = self.client.post(url_for('auth.register'), data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'differentpassword',
            'terms': True
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Passwords must match', response.data)
    
    def test_register_without_terms(self):
        """Test registration without accepting terms"""
        response = self.client.post(url_for('auth.register'), data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'terms': False
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You must agree to the terms', response.data)
    
    # Login Tests
    
    def test_login_get(self):
        """Test GET request to login page"""
        response = self.client.get(url_for('auth.login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome Back', response.data)
    
    def test_login_valid_user(self):
        """Test successful login"""
        response = self.client.post(url_for('auth.login'), data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
    
    def test_login_invalid_email(self):
        """Test login with invalid email"""
        response = self.client.post(url_for('auth.login'), data={
            'email': 'nonexistent@example.com',
            'password': 'testpassword123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_login_invalid_password(self):
        """Test login with invalid password"""
        response = self.client.post(url_for('auth.login'), data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_login_inactive_user(self):
        """Test login with inactive user"""
        self.test_user.is_active = False
        db.session.commit()
        
        response = self.client.post(url_for('auth.login'), data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'account has been deactivated', response.data)
    
    # Logout Tests
    
    def test_logout_authenticated_user(self):
        """Test logout for authenticated user"""
        # Login first
        self.client.post(url_for('auth.login'), data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        # Then logout
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out', response.data)
    
    # Password Reset Tests
    
    def test_reset_request_get(self):
        """Test GET request to password reset page"""
        response = self.client.get(url_for('auth.reset_request'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reset Password', response.data)
    
    def test_reset_request_valid_email(self):
        """Test password reset request with valid email"""
        response = self.client.post(url_for('auth.reset_request'), data={
            'email': 'test@example.com'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign In', response.data)  # Redirected to login
    
    def test_reset_request_invalid_email(self):
        """Test password reset request with invalid email"""
        response = self.client.post(url_for('auth.reset_request'), data={
            'email': 'nonexistent@example.com'
        }, follow_redirects=True)
        
        # Should still show success message for security
        self.assertEqual(response.status_code, 200)
    
    def test_reset_password_valid_token(self):
        """Test password reset with valid token"""
        token = self.test_user.generate_reset_token()
        
        response = self.client.post(
            url_for('auth.reset_password', token=token),
            data={
                'password': 'newpassword123',
                'confirm_password': 'newpassword123'
            },
            follow_redirects=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'password has been updated', response.data)
        
        # Verify password was changed
        updated_user = User.query.get(self.test_user.id)
        self.assertTrue(updated_user.check_password('newpassword123'))
    
    def test_reset_password_invalid_token(self):
        """Test password reset with invalid token"""
        response = self.client.get(
            url_for('auth.reset_password', token='invalid_token'),
            follow_redirects=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'invalid or expired token', response.data)
    
    # Email Verification Tests
    
    def test_verify_email_valid_token(self):
        """Test email verification with valid token"""
        self.test_user.is_verified = False
        db.session.commit()
        
        token = self.test_user.generate_verification_token()
        
        response = self.client.get(
            url_for('auth.verify_email', token=token),
            follow_redirects=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'email has been verified', response.data)
        
        # Check user is now verified
        updated_user = User.query.get(self.test_user.id)
        self.assertTrue(updated_user.is_verified)
    
    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token"""
        response = self.client.get(
            url_for('auth.verify_email', token='invalid_token'),
            follow_redirects=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'invalid or expired', response.data)
    
    # JWT API Tests
    
    def test_api_login_success(self):
        """Test successful API login with JWT"""
        response = self.client.post(
            url_for('auth.api_login'),
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'testpassword123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'test@example.com')
    
    def test_api_login_invalid_credentials(self):
        """Test API login with invalid credentials"""
        response = self.client.post(
            url_for('auth.api_login'),
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_login_missing_data(self):
        """Test API login with missing data"""
        response = self.client.post(
            url_for('auth.api_login'),
            data=json.dumps({
                'email': 'test@example.com'
                # Missing password
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_register_success(self):
        """Test successful API registration"""
        response = self.client.post(
            url_for('auth.api_register'),
            data=json.dumps({
                'username': 'apiuser',
                'email': 'apiuser@example.com',
                'password': 'apipassword123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'apiuser')
        
        # Verify user was created
        user = User.query.filter_by(email='apiuser@example.com').first()
        self.assertIsNotNone(user)
    
    def test_api_register_duplicate_email(self):
        """Test API registration with duplicate email"""
        response = self.client.post(
            url_for('auth.api_register'),
            data=json.dumps({
                'username': 'newuser',
                'email': 'test@example.com',  # Already exists
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertIn('Email already registered', data['error'])
    
    # Rate Limiting Tests
    
    def test_password_reset_rate_limiting(self):
        """Test password reset rate limiting"""
        # Make multiple rapid requests
        for _ in range(4):  # Exceed the limit of 3
            self.client.post(url_for('auth.reset_request'), data={
                'email': 'test@example.com'
            })
        
        # Next request should be rate limited
        response = self.client.post(url_for('auth.reset_request'), data={
            'email': 'test@example.com'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Too many reset requests', response.data)
    
    # Token Security Tests
    
    def test_token_expiration(self):
        """Test token expiration (simulated)"""
        # This would require mocking time or using expired tokens
        # For now, we test with max_age=0 to force expiration
        token = self.test_user.generate_reset_token()
        
        # Verify token with 0 max_age (immediately expired)
        expired_user = User.verify_reset_token(token, max_age=0)
        self.assertIsNone(expired_user)

if __name__ == '__main__':
    unittest.main()