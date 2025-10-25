import pytest
import json
from datetime import datetime, timedelta
from flask import url_for
from app.models import Location, Emergency, Notification, User, Participant

class TestSafetyAPI:
    """Test cases for Safety API endpoints"""
    
    def test_location_update_success(self, client, auth_headers, test_trip):
        """Test successful location update"""
        location_data = {
            'lat': 40.7128,
            'lon': -74.0060,
            'device_id': 'test_device_01',
            'accuracy': 10.0,
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        response = client.post(
            f'/safety/api/trips/{test_trip.id}/location',
            json=location_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'location_id' in data
        
        # Verify location was saved
        location = Location.query.get(data['location_id'])
        assert location is not None
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.device_id == 'test_device_01'
    
    def test_location_update_invalid_coordinates(self, client, auth_headers, test_trip):
        """Test location update with invalid coordinates"""
        location_data = {
            'lat': 200.0,  # Invalid latitude
            'lon': -74.0060,
            'device_id': 'test_device_01'
        }
        
        response = client.post(
            f'/safety/api/trips/{test_trip.id}/location',
            json=location_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_location_update_missing_fields(self, client, auth_headers, test_trip):
        """Test location update with missing required fields"""
        location_data = {
            'lat': 40.7128
            # Missing 'lon' and 'device_id'
        }
        
        response = client.post(
            f'/safety/api/trips/{test_trip.id}/location',
            json=location_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Missing required fields' in data['error']
    
    def test_rate_limiting(self, client, auth_headers, test_trip):
        """Test rate limiting for location updates"""
        location_data = {
            'lat': 40.7128,
            'lon': -74.0060,
            'device_id': 'test_device_01'
        }
        
        # Send first request - should succeed
        response1 = client.post(
            f'/safety/api/trips/{test_trip.id}/location',
            json=location_data,
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Send second request immediately - should be rate limited
        response2 = client.post(
            f'/safety/api/trips/{test_trip.id}/location',
            json=location_data,
            headers=auth_headers
        )
        assert response2.status_code == 429
    
    def test_get_latest_locations(self, client, auth_headers, test_trip):
        """Test getting latest locations for a trip"""
        # Create some test locations
        locations = []
        for i in range(3):
            location = Location(
                trip_id=test_trip.id,
                latitude=40.7128 + i * 0.001,
                longitude=-74.0060 + i * 0.001,
                device_id=f'device_{i}',
                user_id=1
            )
            locations.append(location)
        
        from app.extensions import db
        db.session.add_all(locations)
        db.session.commit()
        
        response = client.get(
            f'/safety/trips/{test_trip.id}/locations/latest',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'locations' in data
        assert len(data['locations']) == 3
    
    def test_create_emergency_alert(self, client, auth_headers, test_trip):
        """Test creating emergency alert"""
        alert_data = {
            'message': 'Medical emergency at location',
            'severity': 'high',
            'lat': 40.7128,
            'lon': -74.0060,
            'location_description': 'Near the museum entrance'
        }
        
        response = client.post(
            f'/safety/trips/{test_trip.id}/alert',
            json=alert_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'alert_id' in data
        
        # Verify alert was saved
        alert = Emergency.query.get(data['alert_id'])
        assert alert is not None
        assert alert.message == 'Medical emergency at location'
        assert alert.severity == 'high'
    
    def test_create_alert_missing_message(self, client, auth_headers, test_trip):
        """Test creating alert without message"""
        alert_data = {
            'severity': 'high'
            # Missing message
        }
        
        response = client.post(
            f'/safety/trips/{test_trip.id}/alert',
            json=alert_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Message is required' in data['error']
    
    def test_get_alerts(self, client, auth_headers, test_trip):
        """Test getting alerts for a trip"""
        # Create test alerts
        alerts = []
        for i in range(3):
            alert = Emergency(
                trip_id=test_trip.id,
                user_id=1,
                message=f'Test alert {i}',
                severity='medium'
            )
            alerts.append(alert)
        
        from app.extensions import db
        db.session.add_all(alerts)
        db.session.commit()
        
        response = client.get(
            f'/safety/trips/{test_trip.id}/alerts',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'alerts' in data
        assert len(data['alerts']) == 3
    
    def test_acknowledge_alert(self, client, auth_headers, test_trip):
        """Test acknowledging an alert"""
        # Create test alert
        alert = Emergency(
            trip_id=test_trip.id,
            user_id=1,
            message='Test alert',
            severity='medium'
        )
        
        from app.extensions import db
        db.session.add(alert)
        db.session.commit()
        
        response = client.post(
            f'/safety/trips/{test_trip.id}/alerts/{alert.id}/acknowledge',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify alert was acknowledged
        updated_alert = Emergency.query.get(alert.id)
        assert updated_alert.acknowledged is True
        assert updated_alert.acknowledged_at is not None

class TestSafetyModels:
    """Test cases for Safety models"""
    
    def test_trip_location_creation(self):
        """Test Location model creation"""
        location = Location(
            trip_id=1,
            latitude=40.7128,
            longitude=-74.0060,
            device_id='test_device',
            user_id=1
        )
        
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.device_id == 'test_device'
    
    def test_emergency_alert_creation(self):
        """Test Emergency model creation"""
        alert = Emergency(
            trip_id=1,
            user_id=1,
            message='Test emergency',
            severity='high'
        )
        
        assert alert.message == 'Test emergency'
        assert alert.severity == 'high'
        assert alert.resolved is False
    
    def test_alert_acknowledge(self):
        """Test alert acknowledgment"""
        alert = Emergency(
            trip_id=1,
            user_id=1,
            message='Test emergency',
            severity='high'
        )
        
        alert.acknowledge(2)
        
        assert alert.acknowledged is True
        assert alert.acknowledged_by_id == 2
        assert alert.acknowledged_at is not None
    
    def test_alert_resolve(self):
        """Test alert resolution"""
        alert = Emergency(
            trip_id=1,
            user_id=1,
            message='Test emergency',
            severity='high'
        )
        
        alert.resolve(2, 'Issue was resolved successfully')
        
        assert alert.resolved is True
        assert alert.resolved_by_id == 2
        assert alert.resolved_at is not None
        assert alert.resolution_notes == 'Issue was resolved successfully'

@pytest.fixture
def test_trip(db_session):
    """Create test trip for safety tests"""
    from app.models.trip import Trip
    from datetime import date
    
    trip = Trip(
        title='Test Safety Trip',
        description='Test trip for safety features',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        organizer_id=1,
        max_participants=20,
        price_per_student=100.0
    )
    
    db_session.add(trip)
    db_session.commit()
    
    return trip

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for API requests"""
    from flask_jwt_extended import create_access_token
    
    token = create_access_token(identity=test_user.id)
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }