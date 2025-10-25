/**
 * Safety Tracking JavaScript Module
 * Handles real-time location updates, emergency alerts, and map visualization
 */

class SafetyTracker {
    constructor(config) {
        this.tripId = config.tripId;
        this.userRole = config.userRole;
        this.socket = null;
        this.map = null;
        this.markers = new Map();
        this.alertMarkers = new Map();
        this.isConnected = false;
        this.lastUpdate = null;
        
        // Initialize components
        this.initSocket();
        this.initMap();
        this.initEventHandlers();
        this.loadInitialData(config.initialLocations);
        this.setupFallbackPolling();
    }
    
    initSocket() {
        // Initialize Socket.IO connection
        this.socket = io('/safety');
        
        this.socket.on('connect', () => {
            console.log('Connected to safety namespace');
            this.isConnected = true;
            this.updateConnectionStatus();
            this.joinTripRoom();
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from safety namespace');
            this.isConnected = false;
            this.updateConnectionStatus();
        });
        
        this.socket.on('error', (data) => {
            console.error('Socket error:', data.message);
            this.showNotification('Connection Error', data.message, 'error');
        });
        
        this.socket.on('joined_room', (data) => {
            console.log('Joined room:', data.room);
            this.requestTripStatus();
        });
        
        this.socket.on('trip_location_update', (data) => {
            this.handleLocationUpdate(data);
        });
        
        this.socket.on('trip_alert', (data) => {
            this.handleEmergencyAlert(data);
        });
        
        this.socket.on('alert_update', (data) => {
            this.handleAlertUpdate(data);
        });
        
        this.socket.on('trip_status', (data) => {
            this.handleTripStatus(data);
        });
    }
    
    initMap() {
        // Initialize Leaflet map
        this.map = L.map('map').setView([40.7128, -74.0060], 10); // Default to NYC
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
        
        // Add map click handler for emergency alerts
        if (this.userRole === 'teacher' || this.userRole === 'admin') {
            this.map.on('click', (e) => {
                this.showEmergencyModal(e.latlng);
            });
        }
    }
    
    initEventHandlers() {
        // Emergency alert button
        const emergencyBtn = document.getElementById('emergency-btn');
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', () => {
                this.showEmergencyModal();
            });
        }
        
        // Emergency modal handlers
        const emergencyForm = document.getElementById('emergency-form');
        const cancelBtn = document.getElementById('cancel-alert');
        const modal = document.getElementById('emergency-modal');
        
        if (emergencyForm) {
            emergencyForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendEmergencyAlert();
            });
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                modal.classList.add('hidden');
            });
        }
        
        // Close modal on outside click
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                }
            });
        }
    }
    
    joinTripRoom() {
        if (this.socket && this.isConnected) {
            this.socket.emit('join_trip_room', { trip_id: this.tripId });
        }
    }
    
    requestTripStatus() {
        if (this.socket && this.isConnected) {
            this.socket.emit('request_trip_status', { trip_id: this.tripId });
        }
    }
    
    handleLocationUpdate(data) {
        console.log('Location update:', data);
        
        // Update marker on map
        this.updateDeviceMarker(data);
        
        // Update device list
        this.updateDeviceList(data);
        
        // Update last update time
        this.lastUpdate = new Date();
        this.updateLastUpdateDisplay();
        
        // Update active devices count
        this.updateActiveDevicesCount();
    }
    
    handleEmergencyAlert(data) {
        console.log('Emergency alert:', data);
        
        // Add alert marker to map
        if (data.lat && data.lon) {
            this.addAlertMarker(data);
        }
        
        // Show notification
        this.showNotification(
            `${data.severity.toUpperCase()} ALERT`,
            data.message,
            'error'
        );
        
        // Add to alerts list
        this.addAlertToList(data);
        
        // Update alerts count
        this.updateActiveAlertsCount();
        
        // Play alert sound (if enabled)
        this.playAlertSound(data.severity);
    }
    
    handleAlertUpdate(data) {
        console.log('Alert update:', data);
        // Handle alert acknowledgment, resolution, etc.
    }
    
    handleTripStatus(data) {
        console.log('Trip status:', data);
        
        // Update map with latest locations
        data.latest_locations.forEach(location => {
            this.updateDeviceMarker(location);
        });
        
        // Update alerts
        data.active_alerts.forEach(alert => {
            if (alert.latitude && alert.longitude) {
                this.addAlertMarker(alert);
            }
        });
        
        this.updateActiveDevicesCount();
        this.updateActiveAlertsCount();
    }
    
    updateDeviceMarker(locationData) {
        const deviceId = locationData.device_id;
        const lat = locationData.lat || locationData.latitude;
        const lon = locationData.lon || locationData.longitude;
        
        if (!lat || !lon) return;
        
        // Remove existing marker
        if (this.markers.has(deviceId)) {
            this.map.removeLayer(this.markers.get(deviceId));
        }
        
        // Create new marker
        const marker = L.circleMarker([lat, lon], {
            radius: 8,
            fillColor: this.getDeviceColor(locationData.device_type || 'mobile'),
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        });
        
        // Add popup with device info
        const popupContent = this.createDevicePopup(locationData);
        marker.bindPopup(popupContent);
        
        // Add to map and store reference
        marker.addTo(this.map);
        this.markers.set(deviceId, marker);
        
        // Auto-fit map if first location
        if (this.markers.size === 1) {
            this.map.setView([lat, lon], 13);
        }
    }
    
    addAlertMarker(alertData) {
        const alertId = alertData.id;
        const lat = alertData.lat || alertData.latitude;
        const lon = alertData.lon || alertData.longitude;
        
        if (!lat || !lon) return;
        
        // Create alert marker with pulsing effect
        const alertIcon = L.divIcon({
            className: 'device-marker emergency',
            iconSize: [20, 20],
            html: '⚠️'
        });
        
        const marker = L.marker([lat, lon], { icon: alertIcon });
        
        // Add popup with alert info
        const popupContent = this.createAlertPopup(alertData);
        marker.bindPopup(popupContent);
        
        // Add to map and store reference
        marker.addTo(this.map);
        this.alertMarkers.set(alertId, marker);
        
        // Pan to alert location
        this.map.setView([lat, lon], 15);
    }
    
    createDevicePopup(locationData) {
        const timestamp = new Date(locationData.timestamp).toLocaleString();
        return `
            <div class="device-popup">
                <h4>${locationData.device_id}</h4>
                <p><strong>Type:</strong> ${locationData.device_type || 'mobile'}</p>
                <p><strong>Last Update:</strong> ${timestamp}</p>
                ${locationData.speed ? `<p><strong>Speed:</strong> ${locationData.speed} km/h</p>` : ''}
                ${locationData.battery_level ? `<p><strong>Battery:</strong> ${locationData.battery_level}%</p>` : ''}
                ${locationData.accuracy ? `<p><strong>Accuracy:</strong> ${locationData.accuracy}m</p>` : ''}
            </div>
        `;
    }
    
    createAlertPopup(alertData) {
        const timestamp = new Date(alertData.timestamp || alertData.created_at).toLocaleString();
        return `
            <div class="alert-popup">
                <h4>${alertData.severity.toUpperCase()} ALERT</h4>
                <p>${alertData.message}</p>
                ${alertData.location_description ? `<p><strong>Location:</strong> ${alertData.location_description}</p>` : ''}
                <p><strong>Reported:</strong> ${timestamp}</p>
                ${alertData.user_name ? `<p><strong>By:</strong> ${alertData.user_name}</p>` : ''}
            </div>
        `;
    }
    
    getDeviceColor(deviceType) {
        const colors = {
            'mobile': '#3b82f6',
            'bus': '#059669',
            'gps_tracker': '#8b5cf6',
            'tablet': '#f59e0b'
        };
        return colors[deviceType] || colors['mobile'];
    }
    
    updateConnectionStatus() {
        const dot = document.getElementById('connection-dot');
        const status = document.getElementById('connection-status');
        
        if (dot && status) {
            if (this.isConnected) {
                dot.classList.add('connected');
                status.textContent = 'Connected - Real-time updates';
            } else {
                dot.classList.remove('connected');
                status.textContent = 'Disconnected - Using fallback polling';
            }
        }
    }
    
    updateLastUpdateDisplay() {
        const element = document.getElementById('last-update');
        if (element && this.lastUpdate) {
            const timeAgo = this.getTimeAgo(this.lastUpdate);
            element.textContent = timeAgo;
        }
    }
    
    updateActiveDevicesCount() {
        const element = document.getElementById('active-devices');
        if (element) {
            element.textContent = this.markers.size;
        }
    }
    
    updateActiveAlertsCount() {
        const element = document.getElementById('active-alerts');
        if (element) {
            element.textContent = this.alertMarkers.size;
        }
    }
    
    updateDeviceList(locationData) {
        const container = document.getElementById('devices-container');
        if (!container) return;
        
        const deviceId = locationData.device_id;
        let deviceElement = container.querySelector(`[data-device-id="${deviceId}"]`);
        
        if (!deviceElement) {
            deviceElement = this.createDeviceListItem(locationData);
            container.appendChild(deviceElement);
        } else {
            this.updateDeviceListItem(deviceElement, locationData);
        }
    }
    
    createDeviceListItem(locationData) {
        const div = document.createElement('div');
        div.className = 'device-item';
        div.setAttribute('data-device-id', locationData.device_id);
        
        div.innerHTML = `
            <div>
                <div class="font-medium">${locationData.device_id}</div>
                <div class="text-sm text-gray-500">${(locationData.device_type || 'mobile').charAt(0).toUpperCase() + (locationData.device_type || 'mobile').slice(1)}</div>
            </div>
            <div class="text-right">
                ${locationData.battery_level ? `<div class="text-sm">${locationData.battery_level}%</div>` : ''}
                <div class="text-xs text-gray-500 timestamp">${new Date(locationData.timestamp).toLocaleTimeString()}</div>
            </div>
        `;
        
        return div;
    }
    
    updateDeviceListItem(element, locationData) {
        const timestampEl = element.querySelector('.timestamp');
        const batteryEl = element.querySelector('.text-sm');
        
        if (timestampEl) {
            timestampEl.textContent = new Date(locationData.timestamp).toLocaleTimeString();
        }
        
        if (batteryEl && locationData.battery_level) {
            batteryEl.textContent = `${locationData.battery_level}%`;
        }
    }
    
    showEmergencyModal(latlng = null) {
        const modal = document.getElementById('emergency-modal');
        if (modal) {
            modal.classList.remove('hidden');
            
            // Store coordinates if provided
            if (latlng) {
                modal.setAttribute('data-lat', latlng.lat);
                modal.setAttribute('data-lng', latlng.lng);
            }
        }
    }
    
    async sendEmergencyAlert() {
        const modal = document.getElementById('emergency-modal');
        const severity = document.getElementById('severity').value;
        const message = document.getElementById('alert-message').value;
        const locationDesc = document.getElementById('location-desc').value;
        
        if (!message.trim()) {
            alert('Please enter an alert message');
            return;
        }
        
        const alertData = {
            message: message.trim(),
            severity: severity,
            location_description: locationDesc.trim()
        };
        
        // Include coordinates if selected on map
        const lat = modal.getAttribute('data-lat');
        const lng = modal.getAttribute('data-lng');
        if (lat && lng) {
            alertData.lat = parseFloat(lat);
            alertData.lon = parseFloat(lng);
        }
        
        try {
            const response = await fetch(`/safety/trips/${this.tripId}/alert`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(alertData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Alert Sent', 'Emergency alert has been sent to all participants', 'success');
                modal.classList.add('hidden');
                document.getElementById('emergency-form').reset();
                modal.removeAttribute('data-lat');
                modal.removeAttribute('data-lng');
            } else {
                throw new Error(result.error || 'Failed to send alert');
            }
            
        } catch (error) {
            console.error('Error sending alert:', error);
            this.showNotification('Error', 'Failed to send emergency alert', 'error');
        }
    }
    
    addAlertToList(alertData) {
        const container = document.getElementById('alerts-container');
        if (!container) return;
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert-item ${alertData.severity}`;
        alertDiv.setAttribute('data-alert-id', alertData.id);
        
        const timestamp = new Date(alertData.timestamp).toLocaleTimeString();
        
        alertDiv.innerHTML = `
            <div class="font-medium">${alertData.severity.charAt(0).toUpperCase() + alertData.severity.slice(1)} Alert</div>
            <div class="text-sm text-gray-600">${alertData.message}</div>
            <div class="text-xs text-gray-500 mt-1">${timestamp}</div>
        `;
        
        container.insertBefore(alertDiv, container.firstChild);
    }
    
    showNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert-notification ${type}`;
        
        notification.innerHTML = `
            <div class="font-medium">${title}</div>
            <div class="text-sm mt-1">${message}</div>
            <button class="absolute top-2 right-2 text-gray-400 hover:text-gray-600" onclick="this.parentElement.remove()">
                ×
            </button>
        `;
        
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
    
    playAlertSound(severity) {
        // Simple beep sound for alerts
        if (window.AudioContext || window.webkitAudioContext) {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(severity === 'critical' ? 800 : 400, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.2);
        }
    }
    
    setupFallbackPolling() {
        // Fallback AJAX polling when WebSocket is not available
        setInterval(() => {
            if (!this.isConnected) {
                this.pollForUpdates();
            }
        }, 10000); // Poll every 10 seconds
    }
    
    async pollForUpdates() {
        try {
            const response = await fetch(`/safety/trips/${this.tripId}/locations/latest?limit=10`);
            const data = await response.json();
            
            if (data.locations) {
                data.locations.forEach(location => {
                    this.handleLocationUpdate(location);
                });
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }
    
    loadInitialData(initialLocations) {
        if (initialLocations && initialLocations.length > 0) {
            initialLocations.forEach(location => {
                this.updateDeviceMarker(location);
            });
        }
    }
    
    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        
        if (seconds < 60) return `${seconds}s ago`;
        
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    }
}

// Driver Device Example
class DriverTracker {
    constructor(tripId, deviceId, jwtToken) {
        this.tripId = tripId;
        this.deviceId = deviceId;
        this.jwtToken = jwtToken;
        this.trackingInterval = null;
        this.isTracking = false;
        
        this.startButton = document.getElementById('start-tracking');
        this.stopButton = document.getElementById('stop-tracking');
        
        if (this.startButton) {
            this.startButton.addEventListener('click', () => this.startTracking());
        }
        
        if (this.stopButton) {
            this.stopButton.addEventListener('click', () => this.stopTracking());
        }
    }
    
    startTracking() {
        if (this.isTracking) return;
        
        this.isTracking = true;
        this.updateUI();
        
        // Send location immediately
        this.sendLocation();
        
        // Start periodic updates every 15 seconds
        this.trackingInterval = setInterval(() => {
            this.sendLocation();
        }, 15000);
    }
    
    stopTracking() {
        if (!this.isTracking) return;
        
        this.isTracking = false;
        this.updateUI();
        
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
            this.trackingInterval = null;
        }
    }
    
    sendLocation() {
        if (!navigator.geolocation) {
            console.error('Geolocation not supported');
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const locationData = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    speed: position.coords.speed,
                    heading: position.coords.heading,
                    altitude: position.coords.altitude,
                    device_id: this.deviceId,
                    device_type: 'mobile',
                    timestamp: Date.now()
                };
                
                // Add battery level if available
                if (navigator.getBattery) {
                    navigator.getBattery().then((battery) => {
                        locationData.battery_level = Math.round(battery.level * 100);
                        this.postLocation(locationData);
                    });
                } else {
                    this.postLocation(locationData);
                }
            },
            (error) => {
                console.error('Geolocation error:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 30000
            }
        );
    }
    
    async postLocation(locationData) {
        try {
            const response = await fetch(`/safety/api/trips/${this.tripId}/location`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.jwtToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(locationData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('Location sent successfully');
                this.updateLastSentTime();
            } else {
                console.error('Failed to send location:', result.error);
            }
            
        } catch (error) {
            console.error('Error sending location:', error);
        }
    }
    
    updateUI() {
        if (this.startButton) {
            this.startButton.disabled = this.isTracking;
        }
        
        if (this.stopButton) {
            this.stopButton.disabled = !this.isTracking;
        }
        
        const statusEl = document.getElementById('tracking-status');
        if (statusEl) {
            statusEl.textContent = this.isTracking ? 'Tracking Active' : 'Tracking Stopped';
            statusEl.className = this.isTracking ? 'text-green-600' : 'text-red-600';
        }
    }
    
    updateLastSentTime() {
        const element = document.getElementById('last-sent');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }
}

// Export classes for global use
window.SafetyTracker = SafetyTracker;
window.DriverTracker = DriverTracker;