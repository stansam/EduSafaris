const filterSection = document.getElementById('filterSection');
const navbar = document.querySelector('.edusafaris-nav');
const filterOffsetTop = filterSection.offsetTop;

window.addEventListener('scroll', () => {
    if (window.pageYOffset >= filterOffsetTop - navbar.offsetHeight) {
        filterSection.classList.add('sticky');
    } else {
        filterSection.classList.remove('sticky');
    }
});

// Dropdown functionality
const dropdowns = [
    {
        btn: document.getElementById('categoryBtn'),
        menu: document.getElementById('categoryMenu'),
        text: document.getElementById('categoryText')
    },
    {
        btn: document.getElementById('durationBtn'),
        menu: document.getElementById('durationMenu'),
        text: document.getElementById('durationText')
    }
];

dropdowns.forEach(dropdown => {
    dropdown.btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isActive = dropdown.btn.classList.contains('active');
        
        // Close all dropdowns
        dropdowns.forEach(d => {
            d.btn.classList.remove('active');
            d.menu.classList.remove('show');
        });

        // Toggle current dropdown
        if (!isActive) {
            dropdown.btn.classList.add('active');
            dropdown.menu.classList.add('show');
        }
    });

    // Handle item selection
    const items = dropdown.menu.querySelectorAll('.dropdown-item');
    items.forEach(item => {
        item.addEventListener('click', () => {
            // Remove selected class from all items
            items.forEach(i => i.classList.remove('selected'));
            // Add selected class to clicked item
            item.classList.add('selected');
            // Update button text
            dropdown.text.textContent = item.textContent;
            // Close dropdown
            dropdown.btn.classList.remove('active');
            dropdown.menu.classList.remove('show');

            if (window.tripManager) {
                window.tripManager.filters[dropdown.filterKey] = item.dataset.value;
                window.tripManager.currentPage = 1;
                window.tripManager.loadTrips();
            }
            
            // Update filter badge
            updateFilterBadge();
        });
    });
});

// Close dropdowns when clicking outside
document.addEventListener('click', () => {
    dropdowns.forEach(d => {
        d.btn.classList.remove('active');
        d.menu.classList.remove('show');
    });

    const advancedModal = document.getElementById('advancedFiltersModal');
    if (advancedModal && advancedModal.classList.contains('show')) {
        closeAdvancedFilters();
    }
});

// Search functionality
const searchInput = document.getElementById('searchInput');
let searchTimeout;

searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const searchTerm = e.target.value.trim();

    searchTimeout = setTimeout(() => {
        // const searchTerm = e.target.value.toLowerCase();
        // console.log('Searching for:', searchTerm);

        if (window.tripManager) {
            window.tripManager.filters.search = searchTerm;
            window.tripManager.currentPage = 1;
            window.tripManager.loadTrips();
        }

        updateFilterBadge();
    }, 300);
});

// Filter badge update
function updateFilterBadge() {
    const filterBadge = document.getElementById('filterBadge');
    let activeFilters = 0;

    // Check if search has value
    if (searchInput.value.trim()) activeFilters++;

    // Check if category is selected
    const categorySelected = document.querySelector('#categoryMenu .dropdown-item.selected');
    if (categorySelected && categorySelected.dataset.value !== 'all') activeFilters++;

    // Check if duration is selected
    const durationSelected = document.querySelector('#durationMenu .dropdown-item.selected');
    if (durationSelected && durationSelected.dataset.value !== 'all') activeFilters++;

    if (window.tripManager) {
        if (window.tripManager.filters.minPrice !== null) activeFilters++;
        if (window.tripManager.filters.maxPrice !== null) activeFilters++;
        if (window.tripManager.filters.gradeLevel && window.tripManager.filters.gradeLevel !== 'all') activeFilters++;
    }

    filterBadge.textContent = activeFilters;
    filterBadge.style.display = activeFilters > 0 ? 'flex' : 'none';
}

// Filter toggle 
const filterToggle = document.getElementById('filterToggle');
filterToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    openAdvancedFilters();
});

function openAdvancedFilters() {
    // Create modal if it doesn't exist
    let modal = document.getElementById('advancedFiltersModal');
    if (!modal) {
        modal = createAdvancedFiltersModal();
        document.body.appendChild(modal);
    }
    
    // Populate current values
    populateAdvancedFilters();
    
    // Show modal
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeAdvancedFilters() {
    const modal = document.getElementById('advancedFiltersModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function createAdvancedFiltersModal() {
    const modal = document.createElement('div');
    modal.id = 'advancedFiltersModal';
    modal.className = 'advanced-filters-modal';
    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeAdvancedFilters()"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h2>Advanced Filters</h2>
                <button class="modal-close" onclick="closeAdvancedFilters()">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
            
            <div class="modal-body">
                <!-- Price Range -->
                <div class="filter-group">
                    <label class="filter-label">Price Range (per student)</label>
                    <div class="price-range-inputs">
                        <div class="price-input-wrapper">
                            <span class="price-prefix">$</span>
                            <input type="number" id="minPrice" class="price-input" placeholder="Min" min="0">
                        </div>
                        <span class="price-separator">-</span>
                        <div class="price-input-wrapper">
                            <span class="price-prefix">$</span>
                            <input type="number" id="maxPrice" class="price-input" placeholder="Max" min="0">
                        </div>
                    </div>
                    <div class="price-range-slider">
                        <input type="range" id="minPriceSlider" class="range-slider" min="0" max="5000" step="100" value="0">
                        <input type="range" id="maxPriceSlider" class="range-slider" min="0" max="5000" step="100" value="5000">
                    </div>
                </div>
                
                <!-- Grade Level -->
                <div class="filter-group">
                    <label class="filter-label">Grade Level</label>
                    <div class="checkbox-group" id="gradeLevelGroup">
                        <label class="checkbox-label">
                            <input type="radio" name="gradeLevel" value="all" checked>
                            <span>All Grades</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="radio" name="gradeLevel" value="K-2">
                            <span>K-2</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="radio" name="gradeLevel" value="3-5">
                            <span>3-5</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="radio" name="gradeLevel" value="6-8">
                            <span>6-8</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="radio" name="gradeLevel" value="9-12">
                            <span>9-12</span>
                        </label>
                    </div>
                </div>
                
                <!-- Trip Status -->
                <div class="filter-group">
                    <label class="filter-label">Availability</label>
                    <div class="checkbox-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="availableOnly" checked>
                            <span>Show only available trips</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="upcomingOnly">
                            <span>Upcoming trips only</span>
                        </label>
                    </div>
                </div>
                
                <!-- Features -->
                <div class="filter-group">
                    <label class="filter-label">Features</label>
                    <div class="checkbox-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="featuredOnly">
                            <span>Featured trips</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="highRated">
                            <span>Highly rated (4.5+)</span>
                        </label>
                    </div>
                </div>
            </div>
            
            <div class="modal-footer">
                <button class="btn-secondary" onclick="resetAdvancedFilters()">Reset All</button>
                <button class="btn-primary" onclick="applyAdvancedFilters()">Apply Filters</button>
            </div>
        </div>
    `;
    
    // Add event listeners for price sliders
    setTimeout(() => {
        setupPriceSliders();
    }, 100);
    
    return modal;
}

function setupPriceSliders() {
    const minPriceInput = document.getElementById('minPrice');
    const maxPriceInput = document.getElementById('maxPrice');
    const minPriceSlider = document.getElementById('minPriceSlider');
    const maxPriceSlider = document.getElementById('maxPriceSlider');
    
    if (!minPriceInput || !maxPriceInput || !minPriceSlider || !maxPriceSlider) return;
    
    // Sync input with slider
    minPriceInput.addEventListener('input', (e) => {
        minPriceSlider.value = e.target.value || 0;
    });
    
    maxPriceInput.addEventListener('input', (e) => {
        maxPriceSlider.value = e.target.value || 5000;
    });
    
    minPriceSlider.addEventListener('input', (e) => {
        minPriceInput.value = e.target.value;
    });
    
    maxPriceSlider.addEventListener('input', (e) => {
        maxPriceInput.value = e.target.value;
    });
}

function populateAdvancedFilters() {
    if (!window.tripManager) return;
    
    const filters = window.tripManager.filters;
    
    // Set price values
    const minPriceInput = document.getElementById('minPrice');
    const maxPriceInput = document.getElementById('maxPrice');
    const minPriceSlider = document.getElementById('minPriceSlider');
    const maxPriceSlider = document.getElementById('maxPriceSlider');
    
    if (minPriceInput && filters.minPrice !== null) {
        minPriceInput.value = filters.minPrice;
        if (minPriceSlider) minPriceSlider.value = filters.minPrice;
    }
    
    if (maxPriceInput && filters.maxPrice !== null) {
        maxPriceInput.value = filters.maxPrice;
        if (maxPriceSlider) maxPriceSlider.value = filters.maxPrice;
    }
    
    // Set grade level
    if (filters.gradeLevel) {
        const gradeLevelRadio = document.querySelector(`input[name="gradeLevel"][value="${filters.gradeLevel}"]`);
        if (gradeLevelRadio) gradeLevelRadio.checked = true;
    }
}

function applyAdvancedFilters() {
    if (!window.tripManager) return;
    
    // Get price values
    const minPrice = document.getElementById('minPrice').value;
    const maxPrice = document.getElementById('maxPrice').value;
    
    window.tripManager.filters.minPrice = minPrice ? parseFloat(minPrice) : null;
    window.tripManager.filters.maxPrice = maxPrice ? parseFloat(maxPrice) : null;
    
    // Get grade level
    const gradeLevelChecked = document.querySelector('input[name="gradeLevel"]:checked');
    if (gradeLevelChecked) {
        window.tripManager.filters.gradeLevel = gradeLevelChecked.value;
    }
    
    // Reset to first page and reload
    window.tripManager.currentPage = 1;
    window.tripManager.loadTrips();
    
    // Update badge
    updateFilterBadge();
    
    // Close modal
    closeAdvancedFilters();
}

function resetAdvancedFilters() {
    if (!window.tripManager) return;
    
    // Reset filters in trip manager
    window.tripManager.filters.minPrice = null;
    window.tripManager.filters.maxPrice = null;
    window.tripManager.filters.gradeLevel = 'all';
    
    // Reset form fields
    document.getElementById('minPrice').value = '';
    document.getElementById('maxPrice').value = '';
    document.getElementById('minPriceSlider').value = 0;
    document.getElementById('maxPriceSlider').value = 5000;
    
    const allGradesRadio = document.querySelector('input[name="gradeLevel"][value="all"]');
    if (allGradesRadio) allGradesRadio.checked = true;
    
    // Uncheck all checkboxes
    document.querySelectorAll('.modal-body input[type="checkbox"]').forEach(cb => {
        if (cb.id === 'availableOnly') {
            cb.checked = true;
        } else {
            cb.checked = false;
        }
    });
    
    // Reload trips
    window.tripManager.currentPage = 1;
    window.tripManager.loadTrips();
    
    // Update badge
    updateFilterBadge();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateFilterBadge();
});