class TripDetailsManager {
    constructor(tripId) {
        this.tripId = tripId;
        this.apiBaseUrl = '/api/trip';
        this.tripData = null;
    }

    /**
     * Fetch trip details from the API
     */
    async fetchTripDetails() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${this.tripId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.tripData = data.trip;
                return this.tripData;
            } else {
                throw new Error(data.error || 'Failed to fetch trip details');
            }
        } catch (error) {
            console.error('Error fetching trip details:', error);
            this.showError('Failed to load trip details. Please try again later.');
            throw error;
        }
    }

    /**
     * Populate the hero section
     */
    populateHero() {
        if (!this.tripData) return;
        const heroCont = document.querySelector('.trip-hero-section');
        if (heroCont && this.tripData.image_url) {
            heroCont.style.background = `
                linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)),
                url("${this.tripData.image_url}")
                `;

            // optionally preserve sizing and positioning
            heroCont.style.backgroundSize = 'cover';
            heroCont.style.backgroundPosition = 'center';
            heroCont.style.backgroundRepeat = 'no-repeat';
        }

        // Update category badge
        const categoryBadge = document.querySelector('.trip-category-badge');
        if (categoryBadge && this.tripData.category) {
            categoryBadge.textContent = this.tripData.category;
        }

        // Update title
        const heroTitle = document.querySelector('.trip-hero-title');
        if (heroTitle && this.tripData.title) {
            heroTitle.textContent = this.tripData.title;
        }

        // Update location
        const locationInfo = document.querySelector('.trip-location-info span');
        if (locationInfo && this.tripData.destination) {
            locationInfo.textContent = this.tripData.destination;
        }

        // Update rating (if you have rating data in your model)
        // For now, keeping the static rating from the template
    }

    /**
     * Populate the content section
     */
    populateContent() {
        if (!this.tripData) return;

        // Update overview description
        const overviewText = document.querySelector('.trip-overview-text');
        if (overviewText && this.tripData.description) {
            overviewText.textContent = this.tripData.description;
        }

        // Update quick info grid
        this.updateQuickInfo();

        // Update itinerary if available
        if (this.tripData.itinerary) {
            this.updateItinerary();
        }
    }

    /**
     * Update quick info grid with dynamic data
     */
    updateQuickInfo() {
        const quickInfoItems = document.querySelectorAll('.trip-info-item');
        
        if (quickInfoItems.length >= 3) {
            // Duration
            const durationValue = quickInfoItems[0].querySelector('.trip-info-value');
            if (durationValue && this.tripData.duration_days) {
                durationValue.textContent = `${this.tripData.duration_days} ${this.tripData.duration_days === 1 ? 'Day' : 'Days'}`;
            }

            // Group Size
            const groupSizeValue = quickInfoItems[1].querySelector('.trip-info-value');
            if (groupSizeValue) {
                groupSizeValue.textContent = `${this.tripData.min_participants}-${this.tripData.max_participants} Students`;
            }

            // Grade Level
            const gradeLevelValue = quickInfoItems[2].querySelector('.trip-info-value');
            if (gradeLevelValue && this.tripData.grade_level) {
                gradeLevelValue.textContent = this.tripData.grade_level;
            }
        }
    }

    /**
     * Update itinerary from JSON data
     */
    updateItinerary() {
        const itineraryList = document.querySelector('.trip-itinerary-list');
        if (!itineraryList || !this.tripData.itinerary) return;

        // Clear existing itinerary
        itineraryList.innerHTML = '';

        // Check if itinerary is an array or object
        const itineraryData = Array.isArray(this.tripData.itinerary) 
            ? this.tripData.itinerary 
            : Object.values(this.tripData.itinerary);

        itineraryData.forEach((day, index) => {
            const dayElement = this.createItineraryDay(index + 1, day);
            itineraryList.appendChild(dayElement);
        });
    }

    /**
     * Create an itinerary day element
     */
    createItineraryDay(dayNumber, dayData) {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'trip-itinerary-day';

        const dayNumberDiv = document.createElement('div');
        dayNumberDiv.className = 'trip-day-number';
        dayNumberDiv.textContent = dayNumber;

        const dayContentDiv = document.createElement('div');
        dayContentDiv.className = 'trip-day-content';

        const title = document.createElement('h3');
        // title.textContent = dayData.title || dayData.name || `Day ${dayNumber}`;

        const description = document.createElement('p');
        // description.textContent = dayData.description || dayData.details || '';

        if (typeof dayData === 'string') {
            title.textContent = `Day ${dayNumber}`;
            description.textContent = dayData;
        } else {
            title.textContent = dayData.title || dayData.name || `Day ${dayNumber}`;
            description.textContent = dayData.description || dayData.details || '';
        }

        dayContentDiv.appendChild(title);
        dayContentDiv.appendChild(description);

        dayDiv.appendChild(dayNumberDiv);
        dayDiv.appendChild(dayContentDiv);

        return dayDiv;
    }

    /**
     * Add status banner if needed
     */
    addStatusBanner() {
        if (!this.tripData) return;

        const statusBanner = document.createElement('div');
        statusBanner.className = 'trip-status-banner';

        if (this.tripData.is_full) {
            statusBanner.innerHTML = '<i class="fas fa-users"></i> This trip is currently full';
            statusBanner.classList.add('trip-status-full');
        } else if (!this.tripData.registration_open) {
            statusBanner.innerHTML = '<i class="fas fa-calendar-times"></i> Registration is closed';
            statusBanner.classList.add('trip-status-closed');
        } else if (this.tripData.available_spots <= 5) {
            statusBanner.innerHTML = `<i class="fas fa-exclamation-circle"></i> Only ${this.tripData.available_spots} spots remaining!`;
            statusBanner.classList.add('trip-status-limited');
        }

        if (statusBanner.innerHTML) {
            const heroSection = document.querySelector('.trip-hero-section');
            if (heroSection) {
                heroSection.insertAdjacentElement('afterend', statusBanner);
            }
        }
    }

    /**
     * Add pricing and dates information
     */
    addPricingInfo() {
        if (!this.tripData) return;

        const pricingDiv = document.createElement('div');
        pricingDiv.className = 'trip-pricing-info';
        pricingDiv.innerHTML = `
            <div class="trip-pricing-details">
                <div class="trip-price">
                    <span class="trip-price-label">Price per Student:</span>
                    <span class="trip-price-amount">Kshs. ${this.tripData.price_per_student.toFixed(2)}</span>
                </div>
                <div class="trip-dates">
                    <div class="trip-date-item">
                        <i class="fas fa-calendar-check fa-3x"></i>
                        <span><strong>Trip Dates:</strong><span class="trip-date-actual"> ${this.formatDate(this.tripData.start_date)} - ${this.formatDate(this.tripData.end_date)}</span></span>
                    </div>
                    ${this.tripData.registration_deadline ? `
                    <div class="trip-date-item">
                        <i class="fas fa-clock fa-4x"></i>
                        <span><strong>Register by:</strong> ${this.formatDate(this.tripData.registration_deadline)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;

        // const contentSection = document.querySelector('.trip-hero-section');
        // if (contentSection) {
        //     contentSection.insertBefore(pricingDiv, contentSection.firstChild);
        // }

        const heroContent = document.querySelector('.trip-rating-info');
        if (heroContent) {
            heroContent.insertAdjacentElement('afterend', pricingDiv);
        }
    }

    /**
     * Format date to readable string
     */
    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    }

    /**
     * Show loading state
     */
    showLoading() {
        const contentSection = document.querySelector('.trip-content-section');
        if (contentSection) {
            contentSection.innerHTML = `
                <div class="trip-loading">
                    <div class="spinner"></div>
                    <p>Loading trip details...</p>
                </div>
            `;
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const contentSection = document.querySelector('.trip-content-section');
        if (contentSection) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'trip-error-message';
            errorDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
                <button onclick="location.reload()">Retry</button>
            `;
            contentSection.prepend(errorDiv);
        }
    }

    /**
     * Initialize and populate all sections
     */
    async init() {
        try {
            // Don't show loading if templates already have content
            // this.showLoading();
            
            await this.fetchTripDetails();
            
            this.populateHero();
            this.populateContent();
            this.addStatusBanner();
            this.addPricingInfo();
            
            // Dispatch custom event when data is loaded
            document.dispatchEvent(new CustomEvent('tripDetailsLoaded', { 
                detail: { tripData: this.tripData } 
            }));
            
        } catch (error) {
            console.error('Failed to initialize trip details:', error);
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Get trip ID from URL or data attribute
    const pathParts = window.location.pathname.split('/');
    // const
    const tripId = pathParts[pathParts.indexOf('trips') + 1] || 
                   document.querySelector('[data-trip-id]')?.dataset.tripId;
    
    if (tripId) {
        const tripManager = new TripDetailsManager(tripId);
        tripManager.init();
        
        // Make it globally accessible if needed
        window.tripManager = tripManager;
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TripDetailsManager;
}