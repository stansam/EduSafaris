/**
 * EduSafaris Featured Trips Manager
 * Handles fetching and displaying featured trips from the API
 */

class FeaturedTripsManager {
    constructor(options = {}) {
        this.apiBaseUrl = options.apiBaseUrl || '/api/trips';
        this.containerSelector = options.containerSelector || '.edusafaris-trips-grid';
        this.limit = options.limit || 6;
        this.retryAttempts = options.retryAttempts || 3;
        this.retryDelay = options.retryDelay || 1000;
        this.cache = null;
        this.cacheExpiry = null;
        this.cacheDuration = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Initialize and load featured trips
     */
    async init() {
        try {
            await this.loadFeaturedTrips();
        } catch (error) {
            console.error('Failed to initialize featured trips:', error);
            this.showError();
        }
    }

    /**
     * Fetch featured trips from API with retry logic
     */
    async fetchFeaturedTrips(attempt = 1) {
        // Check cache first
        if (this.cache && this.cacheExpiry && Date.now() < this.cacheExpiry) {
            return this.cache;
        }

        try {
            const url = new URL(`${this.apiBaseUrl}/featured`, window.location.origin);
            url.searchParams.append('limit', this.limit);

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Failed to fetch trips');
            }

            // Cache the result
            this.cache = result;
            this.cacheExpiry = Date.now() + this.cacheDuration;

            return result;

        } catch (error) {
            console.error(`Attempt ${attempt} failed:`, error);

            // Retry logic
            if (attempt < this.retryAttempts) {
                await this.delay(this.retryDelay * attempt);
                return this.fetchFeaturedTrips(attempt + 1);
            }

            throw error;
        }
    }

    /**
     * Load and display featured trips
     */
    async loadFeaturedTrips() {
        const container = document.querySelector(this.containerSelector);
        
        if (!container) {
            console.error('Featured trips container not found');
            return;
        }

        // Show loading state
        this.showLoading(container);

        try {
            const result = await this.fetchFeaturedTrips();

            // If no trips from API, keep sample data (for testing)
            if (!result.data || result.data.length === 0) {
                console.info('No featured trips available, keeping sample data');
                // this.hideLoading(container);
                this.restoreOriginalContent(container);
                return;
            }

            // Clear container and render trips
            container.innerHTML = '';
            result.data.forEach(trip => {
                const tripCard = this.createTripCard(trip);
                container.appendChild(tripCard);
            });

            this.hideLoading(container);

            // Initialize event listeners
            this.initializeEventListeners();

        } catch (error) {
            console.error('Error loading featured trips:', error);
            // this.hideLoading(container);
            this.restoreOriginalContent(container);
            // Keep sample data on error for graceful degradation
        }
    }

    /**
     * Create trip card HTML element
     */
    createTripCard(trip) {
        const card = document.createElement('div');
        card.className = 'edusafaris-trip-card';
        card.setAttribute('data-trip-id', trip.id);

        // Build category badge
        const categoryBadge = trip.category ? 
            `<div class="edusafaris-trip-category">${this.capitalizeFirst(trip.category)}</div>` : '';

        // Build rating badge
        const ratingBadge = trip.rating ? `
            <div class="edusafaris-trip-rating">
                <i class="fas fa-star edusafaris-star-icon"></i>
                <span>${trip.rating.toFixed(1)}</span>
            </div>
        ` : '';

        // Build status badges
        let statusBadge = '';
        if (!trip.registration_open) {
            statusBadge = '<div class="edusafaris-trip-status-badge closed">Registration Closed</div>';
        } else if (trip.is_filling_fast) {
            statusBadge = '<div class="edusafaris-trip-status-badge filling">Filling Fast!</div>';
        } else if (trip.available_spots <= 0) {
            statusBadge = '<div class="edusafaris-trip-status-badge full">Fully Booked</div>';
        }

        card.innerHTML = `
            <div class="edusafaris-trip-image-container">
                <img src="${this.escapeHtml(trip.image_url)}" 
                     alt="${this.escapeHtml(trip.title)}" 
                     class="edusafaris-trip-image"
                     loading="lazy"
                     onerror="this.src='https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800&h=500&fit=crop'">
                ${categoryBadge}
                ${ratingBadge}
                ${statusBadge}
            </div>
            <div class="edusafaris-trip-content">
                <h3 class="edusafaris-trip-title">${this.escapeHtml(trip.title)}</h3>
                <div class="edusafaris-trip-location">
                    <i class="fas fa-map-marker-alt edusafaris-location-icon"></i>
                    <span>${this.escapeHtml(trip.destination)}</span>
                </div>
                <p class="edusafaris-trip-description">
                    ${this.escapeHtml(this.truncateText(trip.description, 120))}
                </p>
                <div class="edusafaris-trip-details">
                    <div class="edusafaris-detail-item">
                        <i class="far fa-clock edusafaris-detail-icon"></i>
                        <span>${this.escapeHtml(trip.duration_text)}</span>
                    </div>
                    <div class="edusafaris-detail-item">
                        <i class="fas fa-users edusafaris-detail-icon"></i>
                        <span>${this.escapeHtml(trip.participant_range)}</span>
                    </div>
                </div>
                <div class="edusafaris-trip-footer">
                    <div class="edusafaris-trip-price-container">
                        <span class="edusafaris-trip-price-label">Starting from</span>
                        <span class="edusafaris-trip-price">${this.escapeHtml(trip.price_formatted)}</span>
                    </div>
                    <button class="edusafaris-view-details-btn" data-trip-id="${trip.id}">
                        View Details
                    </button>
                </div>
            </div>
        `;

        return card;
    }

    restoreOriginalContent(container) {
        const originalContent = container.getAttribute('data-original-content');
        if (originalContent) {
            container.innerHTML = originalContent;
            container.style.minHeight = '';
            container.style.display = '';
            container.style.justifyContent = '';
            container.style.alignItems = '';
            console.info('Restored original sample trips.');
        }
    }

    /**
     * Initialize event listeners for trip cards
     */
    initializeEventListeners() {
        const detailButtons = document.querySelectorAll('.edusafaris-view-details-btn');
        
        detailButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tripId = e.target.getAttribute('data-trip-id');
                this.handleViewDetails(tripId);
            });
        });
    }

    /**
     * Handle view details button click
     */
    handleViewDetails(tripId) {
        if (window.viewTripDetails && typeof window.viewTripDetails === 'function') {
            window.viewTripDetails(tripId);
        } else {
            // Default behavior - navigate to trip details page
            window.location.href = `/trips/${tripId}`;
        }
    }

    /**
     * Show loading state
     */
    showLoading(container) {
        const loader = document.createElement('div');
        loader.className = 'edusafaris-trips-loading';
        loader.innerHTML = `
            <div class="edusafaris-spinner"></div>
            <p>Loading featured trips...</p>
        `;
        container.style.minHeight = '300px';
        container.style.display = 'flex';
        container.style.justifyContent = 'center';
        container.style.alignItems = 'center';
        
        // Store original content for restoration
        if (!container.hasAttribute('data-original-content')) {
            container.setAttribute('data-original-content', container.innerHTML);
        }
        
        container.innerHTML = '';
        container.appendChild(loader);
    }

    /**
     * Hide loading state
     */
    hideLoading(container) {
        container.style.minHeight = '';
        container.style.display = '';
        container.style.justifyContent = '';
        container.style.alignItems = '';
        
        const loader = container.querySelector('.edusafaris-trips-loading');
        if (loader) {
            loader.remove();
        }
    }

    /**
     * Show error message
     */
    showError() {
        const container = document.querySelector(this.containerSelector);
        if (!container) return;

        // Restore original content if available (sample data)
        const originalContent = container.getAttribute('data-original-content');
        if (originalContent) {
            container.innerHTML = originalContent;
            console.info('Restored sample data due to API error');
        }
    }

    /**
     * Refresh trips data
     */
    async refresh() {
        this.cache = null;
        this.cacheExpiry = null;
        await this.loadFeaturedTrips();
    }

    /**
     * Utility: Delay function for retry logic
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Utility: Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Utility: Truncate text
     */
    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength).trim() + '...';
    }

    /**
     * Utility: Capitalize first letter
     */
    capitalizeFirst(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

/**
 * Initialize featured trips when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the manager
    const featuredTripsManager = new FeaturedTripsManager({
        apiBaseUrl: '/api/trips',
        limit: 6
    });

    // Make it globally accessible if needed
    window.featuredTripsManager = featuredTripsManager;

    // Load featured trips
    featuredTripsManager.init();

    // Optional: Auto-refresh every 5 minutes
    // setInterval(() => featuredTripsManager.refresh(), 5 * 60 * 1000);
});

