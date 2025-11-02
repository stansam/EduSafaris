// Trip Details Modal Module
const TripDetailsModal = (function() {
    'use strict';

    // State
    const state = {
        currentTripId: null,
        tripData: null,
        activeTab: 'overview'
    };

    // DOM Elements
    const elements = {
        overlay: null,
        close: null,
        loading: null,
        content: null,
        error: null,
        errorMessage: null,
        retryBtn: null,
        footer: null,
        registerBtn: null,
        viewItineraryBtn: null,
        
        // Content Elements
        title: null,
        destination: null,
        category: null,
        startDate: null,
        endDate: null,
        duration: null,
        spots: null,
        description: null,
        gradeLevel: null,
        maxParticipants: null,
        deadline: null,
        itinerary: null,
        price: null,
        includes: null,
        registrationStatus: null,
        registeredChildren: null,
        
        // Tabs
        tabs: [],
        tabPanes: []
    };

    // Initialize
    function init() {
        try {
            cacheDOM();
            bindEvents();
        } catch (error) {
            console.error('Failed to initialize TripDetailsModal:', error);
        }
    }

    // Cache DOM Elements
    function cacheDOM() {
        elements.overlay = document.getElementById('tripDetailsModalOverlay');
        elements.close = document.getElementById('tripDetailsModalClose');
        elements.loading = document.getElementById('tripDetailsLoading');
        elements.content = document.getElementById('tripDetailsContent');
        elements.error = document.getElementById('tripDetailsError');
        elements.errorMessage = document.getElementById('tripDetailsErrorMessage');
        elements.retryBtn = document.getElementById('tripDetailsRetryBtn');
        elements.footer = document.getElementById('tripDetailsModalFooter');
        elements.registerBtn = document.getElementById('tripDetailsRegisterBtn');
        elements.viewItineraryBtn = document.getElementById('tripDetailsViewItineraryBtn');
        
        // Content
        elements.title = document.getElementById('tripDetailsTitle');
        elements.destination = document.querySelector('#tripDetailsDestination span');
        elements.category = document.querySelector('#tripDetailsCategory span');
        elements.startDate = document.getElementById('tripDetailsStartDate');
        elements.endDate = document.getElementById('tripDetailsEndDate');
        elements.duration = document.getElementById('tripDetailsDuration');
        elements.spots = document.getElementById('tripDetailsSpots');
        elements.description = document.getElementById('tripDetailsDescription');
        elements.gradeLevel = document.getElementById('tripDetailsGradeLevel');
        elements.maxParticipants = document.getElementById('tripDetailsMaxParticipants');
        elements.deadline = document.getElementById('tripDetailsDeadline');
        elements.itinerary = document.getElementById('tripDetailsItinerary');
        elements.price = document.getElementById('tripDetailsPrice');
        elements.includes = document.getElementById('tripDetailsIncludes');
        elements.registrationStatus = document.getElementById('tripDetailsRegistrationStatus');
        elements.registeredChildren = document.getElementById('tripDetailsRegisteredChildren');
        
        // Tabs
        elements.tabs = document.querySelectorAll('.trip-details-tab');
        elements.tabPanes = document.querySelectorAll('.trip-details-tab-pane');
    }

    // Bind Events
    function bindEvents() {
        // Close modal
        if (elements.close) {
            elements.close.addEventListener('click', close);
        }
        
        if (elements.overlay) {
            elements.overlay.addEventListener('click', (e) => {
                if (e.target === elements.overlay) {
                    close();
                }
            });
        }
        
        // Retry
        if (elements.retryBtn) {
            elements.retryBtn.addEventListener('click', () => {
                if (state.currentTripId) {
                    loadTripDetails(state.currentTripId);
                }
            });
        }
        
        // Register button
        if (elements.registerBtn) {
            elements.registerBtn.addEventListener('click', () => {
                if (state.currentTripId) {
                    close();
                    if (typeof TripsManager !== 'undefined' && TripsManager.openRegisterModal) {
                        TripsManager.openRegisterModal(state.currentTripId);
                    }
                }
            });
        }
        
        // View Itinerary button
        if (elements.viewItineraryBtn) {
            elements.viewItineraryBtn.addEventListener('click', () => {
                switchTab('itinerary');
            });
        }
        
        // Tab switching
        elements.tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.getAttribute('data-tab');
                switchTab(tabName);
            });
        });
        
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && elements.overlay && elements.overlay.classList.contains('active')) {
                close();
            }
        });
    }

    // Open Modal
    function open(tripId) {
        if (!tripId) {
            console.error('Trip ID is required');
            return;
        }
        
        state.currentTripId = tripId;
        state.activeTab = 'overview';
        
        if (elements.overlay) {
            elements.overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
        
        loadTripDetails(tripId);
    }

    // Close Modal
    function close() {
        if (elements.overlay) {
            elements.overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
        
        state.currentTripId = null;
        state.tripData = null;
        state.activeTab = 'overview';
    }

    // Load Trip Details
    async function loadTripDetails(tripId) {
        showLoading();
        
        try {
            const response = await fetch(`/api/parent/trips/${tripId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Trip not found');
                }
                throw new Error(`Failed to load trip details: ${response.status}`);
            }

            const result = await response.json();

            if (result.success && result.data) {
                state.tripData = result.data;
                renderTripDetails(result.data);
                loadItinerary(tripId);
            } else {
                throw new Error(result.message || 'Failed to load trip details');
            }
        } catch (error) {
            console.error('Error loading trip details:', error);
            showError(error.message);
        }
    }

    // Load Itinerary
    async function loadItinerary(tripId) {
        try {
            const response = await fetch(`/api/parent/trips/${tripId}/itinerary`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data && result.data.itinerary) {
                    renderItinerary(result.data.itinerary);
                }
            }
        } catch (error) {
            console.error('Error loading itinerary:', error);
        }
    }

    // Render Trip Details
    function renderTripDetails(trip) {
        // Basic info
        if (elements.title) {
            elements.title.textContent = trip.title || 'Untitled Trip';
        }
        
        if (elements.destination) {
            elements.destination.textContent = trip.destination || 'N/A';
        }
        
        if (elements.category) {
            elements.category.textContent = trip.category || 'General';
        }
        
        if (elements.startDate) {
            elements.startDate.textContent = formatDate(trip.start_date);
        }
        
        if (elements.endDate) {
            elements.endDate.textContent = formatDate(trip.end_date);
        }
        
        if (elements.duration) {
            elements.duration.textContent = `${trip.duration_days || 0} days`;
        }
        
        if (elements.spots) {
            const spots = trip.spots_remaining || 0;
            elements.spots.textContent = spots;
            elements.spots.style.color = spots === 0 ? '#e74c3c' : spots < 10 ? '#f39c12' : '#27ae60';
        }
        
        // Description
        if (elements.description) {
            elements.description.textContent = trip.description || 'No description available.';
        }
        
        // Eligibility
        if (elements.gradeLevel) {
            elements.gradeLevel.textContent = trip.grade_level || 'All Grades';
        }
        
        if (elements.maxParticipants) {
            elements.maxParticipants.textContent = trip.max_participants || 'N/A';
        }
        
        // Deadline
        if (elements.deadline) {
            if (trip.registration_deadline) {
                const deadline = new Date(trip.registration_deadline);
                const daysUntil = Math.ceil((deadline - new Date()) / (1000 * 60 * 60 * 24));
                
                let deadlineText = formatDate(trip.registration_deadline);
                if (daysUntil > 0) {
                    deadlineText += ` (${daysUntil} days remaining)`;
                } else if (daysUntil === 0) {
                    deadlineText += ' (Today!)';
                } else {
                    deadlineText += ' (Expired)';
                    elements.deadline.style.background = '#fadbd8';
                    elements.deadline.style.borderColor = '#e74c3c';
                    elements.deadline.style.color = '#721c24';
                }
                
                elements.deadline.textContent = deadlineText;
            } else {
                elements.deadline.textContent = 'No deadline set';
            }
        }
        
        // Pricing
        if (elements.price) {
            elements.price.textContent = `$${formatNumber(trip.price_per_student)}`;
        }
        
        // Includes (if available)
        if (elements.includes) {
            elements.includes.innerHTML = '';
            const includes = [
                'Transportation',
                'Accommodation',
                'Meals',
                'Activities and excursions',
                'Professional supervision',
                'Travel insurance'
            ];
            
            includes.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                elements.includes.appendChild(li);
            });
        }
        
        // Registration Status
        if (trip.user_has_registrations && elements.registrationStatus) {
            elements.registrationStatus.style.display = 'block';
            
            if (elements.registeredChildren && trip.user_participants) {
                const childrenNames = trip.user_participants
                    .filter(p => p.status !== 'cancelled')
                    .map(p => p.first_name + ' ' + p.last_name)
                    .join(', ');
                elements.registeredChildren.textContent = childrenNames || 'Children registered';
            }
        } else if (elements.registrationStatus) {
            elements.registrationStatus.style.display = 'none';
        }
        
        // Footer buttons
        if (elements.registerBtn) {
            elements.registerBtn.disabled = !trip.can_register;
            if (!trip.can_register) {
                if (trip.is_full) {
                    elements.registerBtn.innerHTML = '<i class="fas fa-ban"></i> Trip Full';
                } else {
                    elements.registerBtn.innerHTML = '<i class="fas fa-ban"></i> Registration Closed';
                }
            } else {
                elements.registerBtn.innerHTML = '<i class="fas fa-user-plus"></i> Register Child';
            }
        }
        
        showContent();
    }

    // Render Itinerary
    function renderItinerary(itineraryData) {
        if (!elements.itinerary) return;
        
        elements.itinerary.innerHTML = '';
        
        if (!itineraryData || itineraryData.length === 0) {
            elements.itinerary.innerHTML = `
                <div class="trip-details-alert trip-details-alert-info">
                    <i class="fas fa-info-circle"></i>
                    <div>Detailed itinerary will be provided closer to the trip date.</div>
                </div>
            `;
            return;
        }
        
        // itineraryData.forEach((day, index) => {
        //     const item = document.createElement('div');
        //     item.className = 'trip-details-itinerary-item';
            
        //     item.innerHTML = `
        //         <div class="trip-details-itinerary-day">
        //             <span class="trip-details-itinerary-day-label">Day</span>
        //             <span class="trip-details-itinerary-day-number">${index + 1}</span>
        //         </div>
        //         <div class="trip-details-itinerary-content">
        //             <h4 class="trip-details-itinerary-title">${escapeHtml(day.title || `Day ${index + 1}`)}</h4>
        //             <p class="trip-details-itinerary-description">${escapeHtml(day.description || day.activities || 'No details available')}</p>
        //         </div>
        //     `;
            
        //     elements.itinerary.appendChild(item);
        // });

        let itineraryArray = [];

        if (Array.isArray(itineraryData)) {
            itineraryArray = itineraryData;
        } else if (itineraryData && typeof itineraryData === 'object') {
            itineraryArray = Object.entries(itineraryData).map(([key, value]) => ({
                title: key.replace(/_/g, ' ').replace(/^day/i, 'Day'),
                description: value
            }));
        }

        itineraryArray.forEach((day, index) => {
            const item = document.createElement('div');
            item.className = 'trip-details-itinerary-item';
            
            item.innerHTML = `
                <div class="trip-details-itinerary-day">
                    <span class="trip-details-itinerary-day-label">Day</span>
                    <span class="trip-details-itinerary-day-number">${index + 1}</span>
                </div>
                <div class="trip-details-itinerary-content">
                    <h4 class="trip-details-itinerary-title">${escapeHtml(day.title || `Day ${index + 1}`)}</h4>
                    <p class="trip-details-itinerary-description">${escapeHtml(day.description || 'No details available')}</p>
                </div>
            `;
            
            elements.itinerary.appendChild(item);
        });
    }

    // Switch Tab
    function switchTab(tabName) {
        state.activeTab = tabName;
        
        // Update tab buttons
        elements.tabs.forEach(tab => {
            const isActive = tab.getAttribute('data-tab') === tabName;
            tab.classList.toggle('active', isActive);
        });
        
        // Update tab panes
        elements.tabPanes.forEach(pane => {
            const isActive = pane.getAttribute('data-pane') === tabName;
            pane.classList.toggle('active', isActive);
        });
    }

    // Show Loading
    function showLoading() {
        if (elements.loading) elements.loading.style.display = 'flex';
        if (elements.content) elements.content.style.display = 'none';
        if (elements.error) elements.error.style.display = 'none';
        if (elements.footer) elements.footer.style.display = 'none';
    }

    // Show Content
    function showContent() {
        if (elements.loading) elements.loading.style.display = 'none';
        if (elements.content) elements.content.style.display = 'block';
        if (elements.error) elements.error.style.display = 'none';
        if (elements.footer) elements.footer.style.display = 'flex';
    }

    // Show Error
    function showError(message) {
        if (elements.loading) elements.loading.style.display = 'none';
        if (elements.content) elements.content.style.display = 'none';
        if (elements.error) elements.error.style.display = 'flex';
        if (elements.footer) elements.footer.style.display = 'none';
        
        if (elements.errorMessage) {
            elements.errorMessage.textContent = message || 'An error occurred';
        }
    }

    // Utility Functions
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        } catch (error) {
            return dateString;
        }
    }

    function formatNumber(number) {
        if (number === null || number === undefined) return '0.00';
        return parseFloat(number).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    // Return Public API
    return {
        init,
        open,
        close
    };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        TripDetailsModal.init();
    });
} else {
    TripDetailsModal.init();
}