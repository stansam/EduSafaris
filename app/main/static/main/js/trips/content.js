class TripManager {
    constructor() {
        this.trips = [];
        this.filteredTrips = [];
        this.currentPage = 1;
        this.perPage = 12;
        this.totalPages = 1;
        this.isLoading = false;
        this.filters = {
            search: '',
            category: 'all',
            duration: 'all',
            minPrice: null,
            maxPrice: null,
            gradeLevel: 'all',
            sortBy: 'popular'
        };
        
        this.init();
    }
    
    init() {
        this.bindSortingEvents();
        this.loadTrips();
    }
    
    bindSortingEvents() {
        const sortBtn = document.getElementById('sortBtn');
        const sortMenu = document.getElementById('sortMenu');
        const sortItems = sortMenu.querySelectorAll('.dropdown-item');
        
        sortBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isActive = sortBtn.classList.contains('active');
            sortBtn.classList.toggle('active');
            sortMenu.classList.toggle('show');
        });
        
        sortItems.forEach(item => {
            item.addEventListener('click', () => {
                sortItems.forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
                
                const sortText = document.getElementById('sortText');
                sortText.textContent = item.textContent;
                
                this.filters.sortBy = item.dataset.value;
                this.currentPage = 1;
                this.loadTrips();
                
                sortBtn.classList.remove('active');
                sortMenu.classList.remove('show');
            });
        });
        
        document.addEventListener('click', () => {
            sortBtn.classList.remove('active');
            sortMenu.classList.remove('show');
        });
    }
    
    async loadTrips() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const queryParams = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                sort_by: this.filters.sortBy,
                status: 'active'
            });
            
            // Add filters if they're set
            if (this.filters.search) {
                queryParams.append('search', this.filters.search);
            }
            if (this.filters.category && this.filters.category !== 'all') {
                queryParams.append('category', this.filters.category);
            }
            if (this.filters.duration && this.filters.duration !== 'all') {
                queryParams.append('duration', this.filters.duration);
            }
            if (this.filters.minPrice !== null) {
                queryParams.append('min_price', this.filters.minPrice);
            }
            if (this.filters.maxPrice !== null) {
                queryParams.append('max_price', this.filters.maxPrice);
            }
            if (this.filters.gradeLevel && this.filters.gradeLevel !== 'all') {
                queryParams.append('grade_level', this.filters.gradeLevel);
            }
            
            const response = await fetch(`/api/trips?${queryParams.toString()}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.trips = data.trips;
                this.filteredTrips = data.trips;
                this.totalPages = data.pagination.pages;
                this.updateResultsCount(data.pagination.total);
                this.renderTrips();
                this.renderPagination(data.pagination);
            } else {
                throw new Error(data.error || 'Failed to load trips');
            }
            
        } catch (error) {
            console.error('Error loading trips:', error);
            this.showError('Failed to load trips. Please try again.');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    renderTrips() {
        const tripsGrid = document.getElementById('tripsGrid');
        
        if (!this.filteredTrips || this.filteredTrips.length === 0) {
            tripsGrid.innerHTML = this.getEmptyState();
            return;
        }
        
        tripsGrid.innerHTML = this.filteredTrips.map(trip => this.createTripCard(trip)).join('');
        
        // Bind click events to "View Details" buttons
        this.bindTripCardEvents();
    }
    
    createTripCard(trip) {
        const categoryIcon = this.getCategoryIcon();
        const locationIcon = this.getLocationIcon();
        const clockIcon = this.getClockIcon();
        const usersIcon = this.getUsersIcon();
        
        return `
            <div class="trip-card" data-trip-id="${trip.id}">
                <div class="trip-image">
                    <img src="${trip.image_url || this.getDefaultImage(trip.category)}" 
                         alt="${trip.title}"
                         onerror="this.src='https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?w=800'">
                    <div class="trip-category">
                        ${categoryIcon}
                        ${this.formatCategory(trip.category)}
                    </div>
                    <div class="trip-rating">
                        <span class="star-icon">★</span> ${trip.rating || '4.8'}
                    </div>
                </div>
                <div class="trip-content">
                    <h3 class="trip-title">${this.escapeHtml(trip.title)}</h3>
                    <div class="trip-location">
                        ${locationIcon}
                        ${this.escapeHtml(trip.destination)}
                    </div>
                    <p class="trip-description">
                        ${this.escapeHtml(this.truncateText(trip.description, 120))}
                    </p>
                    <div class="trip-details">
                        <div class="trip-detail-item">
                            ${clockIcon}
                            ${trip.duration_days} Day${trip.duration_days !== 1 ? 's' : ''}
                        </div>
                        <div class="trip-detail-item">
                            ${usersIcon}
                            ${trip.min_participants || 10}-${trip.max_participants} Students
                        </div>
                    </div>
                    <div class="trip-footer">
                        <div class="trip-price">
                            <span class="price-label">Starting from</span>
                            <span class="price-amount">$${this.formatPrice(trip.price_per_student)}/student</span>
                        </div>
                        <button class="view-details-btn" data-trip-id="${trip.id}">View Details</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindTripCardEvents() {
        const viewDetailsButtons = document.querySelectorAll('.view-details-btn');
        viewDetailsButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tripId = e.target.dataset.tripId;
                this.viewTripDetails(tripId);
            });
        });
    }
    
    async viewTripDetails(tripId) {
        // Navigate to trip details page or open modal
        window.location.href = `/trip/${tripId}`;
    }
    
    renderPagination(pagination) {
        // You can implement pagination UI here if needed
        // For now, we'll skip it, but you can add it later
        console.log('Pagination:', pagination);
    }
    
    updateResultsCount(total) {
        const resultsCount = document.querySelector('.results-count');
        if (resultsCount) {
            const tripText = total === 1 ? 'trip' : 'trips';
            resultsCount.textContent = `${total} ${tripText} found`;
        }
    }
    
    showLoading() {
        const tripsGrid = document.getElementById('tripsGrid');
        tripsGrid.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Loading trips...</p>
            </div>
        `;
    }
    
    hideLoading() {
        // Loading state is replaced by content
    }
    
    showError(message) {
        const tripsGrid = document.getElementById('tripsGrid');
        tripsGrid.innerHTML = `
            <div class="error-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <h3>Oops! Something went wrong</h3>
                <p>${message}</p>
                <button class="retry-btn" onclick="tripManager.loadTrips()">Try Again</button>
            </div>
        `;
    }
    
    getEmptyState() {
        return `
            <div class="empty-state">
                <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <h3>No trips found</h3>
                <p>Try adjusting your filters to see more results</p>
                <button class="clear-filters-btn" onclick="tripManager.clearFilters()">Clear Filters</button>
            </div>
        `;
    }
    
    clearFilters() {
        this.filters = {
            search: '',
            category: 'all',
            duration: 'all',
            minPrice: null,
            maxPrice: null,
            gradeLevel: 'all',
            sortBy: 'popular'
        };
        this.currentPage = 1;
        
        // Reset UI
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.value = '';
        
        // Reset dropdowns
        document.querySelectorAll('.dropdown-item').forEach(item => {
            item.classList.remove('selected');
            if (item.dataset.value === 'all' || item.dataset.value === 'popular') {
                item.classList.add('selected');
            }
        });
        
        // Reset dropdown texts
        const categoryText = document.getElementById('categoryText');
        const durationText = document.getElementById('durationText');
        if (categoryText) categoryText.textContent = 'Category';
        if (durationText) durationText.textContent = 'Duration';
        
        this.loadTrips();
    }
    
    // Utility methods
    formatCategory(category) {
        if (!category) return 'General';
        return category.charAt(0).toUpperCase() + category.slice(1);
    }
    
    formatPrice(price) {
        return parseFloat(price).toLocaleString('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }
    
    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength).trim() + '...';
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getDefaultImage(category) {
        const imageMap = {
            'wildlife': 'https://images.unsplash.com/photo-1564760055775-d63b17a55c44?w=800',
            'nature': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800',
            'adventure': 'https://images.unsplash.com/photo-1591825729269-caeb344f6df2?w=800',
            'marine': 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800',
            'history': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800',
        };
        return imageMap[category?.toLowerCase()] || 'https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?w=800';
    }
    
    // SVG Icons
    getCategoryIcon() {
        return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        </svg>`;
    }
    
    getLocationIcon() {
        return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
            <circle cx="12" cy="10" r="3"/>
        </svg>`;
    }
    
    getClockIcon() {
        return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
        </svg>`;
    }
    
    getUsersIcon() {
        return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>`;
    }
}

// Initialize trip manager
let tripManager;
document.addEventListener('DOMContentLoaded', () => {
    tripManager = new TripManager();
    window.tripManager = tripManager;
    tripManager.init()
});