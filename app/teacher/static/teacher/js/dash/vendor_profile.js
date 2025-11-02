/**
 * Vendor Profile Modal JavaScript
 * Handles vendor profile display and navigation
 */

let currentVendorProfile = null;

/**
 * Open vendor profile modal
 */
function openVendorProfileModal(vendorId) {
    const modal = document.getElementById('vendorProfileModal');
    if (!modal) {
        console.error('Vendor profile modal not found');
        return;
    }

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    loadVendorProfile(vendorId);
    setupVendorProfileListeners();
}

/**
 * Close vendor profile modal
 */
function closeVendorProfileModal() {
    const modal = document.getElementById('vendorProfileModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        currentVendorProfile = null;
    }
}

/**
 * Setup event listeners
 */
// function setupVendorProfileListeners() {
//     // Close buttons
//     document.getElementById('btnCloseVendorProfile')?.addEventListener('click', closeVendorProfileModal);
//     document.getElementById('btnVpmClose')?.addEventListener('click', closeVendorProfileModal);

//     // Tab buttons
//     const tabButtons = document.querySelectorAll('.vpm-tab-btn');
//     tabButtons.forEach(btn => {
//         btn.addEventListener('click', () => {
//             const tabName = btn.dataset.tab;
//             switchVpmTab(tabName);
//         });
//     });

//     // Action buttons
//     document.getElementById('btnVpmRequestQuote')?.addEventListener('click', () => {
//         if (currentVendorProfile && typeof openRequestQuoteModal === 'function') {
//             closeVendorProfileModal();
//             openRequestQuoteModal(currentVendorProfile.id);
//         }
//     });

//     document.getElementById('btnVpmCreateBooking')?.addEventListener('click', () => {
//         if (currentVendorProfile && typeof openCreateBookingModal === 'function') {
//             closeVendorProfileModal();
//             openCreateBookingModal(currentVendorProfile.id);
//         }
//     });

//     // Close on overlay click
//     document.getElementById('vendorProfileModal')?.addEventListener('click', (e) => {
//         if (e.target.id === 'vendorProfileModal') {
//             closeVendorProfileModal();
//         }
//     });
// }

function setupVendorProfileListeners() {
    // Remove old listeners by cloning and replacing buttons
    const btnRequestQuote = document.getElementById('btnVpmRequestQuote');
    const btnCreateBooking = document.getElementById('btnVpmCreateBooking');
    
    if (btnRequestQuote) {
        const newBtnRequestQuote = btnRequestQuote.cloneNode(true);
        btnRequestQuote.parentNode.replaceChild(newBtnRequestQuote, btnRequestQuote);
        newBtnRequestQuote.addEventListener('click', handleRequestQuoteClick);
    }
    
    if (btnCreateBooking) {
        const newBtnCreateBooking = btnCreateBooking.cloneNode(true);
        btnCreateBooking.parentNode.replaceChild(newBtnCreateBooking, btnCreateBooking);
        newBtnCreateBooking.addEventListener('click', handleCreateBookingClick);
    }

    // Close buttons
    const btnClose = document.getElementById('btnCloseVendorProfile');
    const btnVpmClose = document.getElementById('btnVpmClose');
    
    if (btnClose) {
        const newBtnClose = btnClose.cloneNode(true);
        btnClose.parentNode.replaceChild(newBtnClose, btnClose);
        newBtnClose.addEventListener('click', closeVendorProfileModal);
    }
    
    if (btnVpmClose) {
        const newBtnVpmClose = btnVpmClose.cloneNode(true);
        btnVpmClose.parentNode.replaceChild(newBtnVpmClose, btnVpmClose);
        newBtnVpmClose.addEventListener('click', closeVendorProfileModal);
    }

    // Tab buttons
    const tabButtons = document.querySelectorAll('.vpm-tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchVpmTab(tabName);
        });
    });

    // Close on overlay click
    const modal = document.getElementById('vendorProfileModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'vendorProfileModal') {
                closeVendorProfileModal();
            }
        });
    }
}

/**
 * Handle request quote button click
 */
function handleRequestQuoteClick() {
    if (!currentVendorProfile) {
        console.error('No vendor profile loaded');
        return;
    }
    
    if (typeof openRequestQuoteModal === 'function') {
        // closeVendorProfileModal();

        openRequestQuoteModal(currentVendorProfile.id);
    } else {
        console.error('openRequestQuoteModal function not found');
    }
}

/**
 * Handle create booking button click
 */
function handleCreateBookingClick() {
    if (!currentVendorProfile) {
        console.error('No vendor profile loaded');
        return;
    }
    
    if (typeof openCreateBookingModal === 'function') {
        // closeVendorProfileModal();
        openCreateBookingModal(currentVendorProfile.id);
    } else {
        console.error('openCreateBookingModal function not found');
    }
}

/**
 * Switch between tabs
 */
function switchVpmTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.vpm-tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update tab panes
    document.querySelectorAll('.vpm-tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });

    const targetPane = document.getElementById(`vpm${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`);
    if (targetPane) {
        targetPane.classList.add('active');
    }
}

/**
 * Load vendor profile data
 */
async function loadVendorProfile(vendorId) {
    const loadingState = document.getElementById('vpmLoadingState');
    const content = document.getElementById('vpmContent');

    if (loadingState) loadingState.style.display = 'block';
    if (content) content.style.display = 'none';

    try {
        const response = await fetch(`/api/teacher/vendors/${vendorId}`);
        const data = await handleVpmApiResponse(response);

        if (data.success) {
            currentVendorProfile = data.data;
            displayVendorProfile(data.data);
            if (loadingState) loadingState.style.display = 'none';
            if (content) content.style.display = 'block';
        } else {
            showVpmError('Failed to load vendor profile');
        }
    } catch (error) {
        console.error('Error loading vendor profile:', error);
        showVpmError('An error occurred while loading the profile');
    }
}

/**
 * Display vendor profile data
 */
function displayVendorProfile(vendor) {
    // Set current vendor ID
    const vendorIdInput = document.getElementById('vpmVendorId');
    if (vendorIdInput) {
        vendorIdInput.value = vendor.id || '';
    }

    // Business name
    const businessName = document.getElementById('vpmBusinessName');
    if (businessName) {
        businessName.textContent = vendor.business_name || 'Unknown Vendor';
    }

    // Badges
    const verifiedBadge = document.getElementById('vpmVerifiedBadge');
    if (verifiedBadge && vendor.is_verified) {
        verifiedBadge.style.display = 'inline-flex';
    }

    const typeBadge = document.getElementById('vpmTypeBadge');
    if (typeBadge) {
        typeBadge.textContent = vendor.business_type || 'General';
    }

    // Rating
    updateVpmStars('vpmStars', vendor.average_rating || 0);
    updateVpmStars('vpmStarsLarge', vendor.average_rating || 0);
    
    const ratingText = document.getElementById('vpmRatingText');
    if (ratingText) {
        const reviewCount = vendor.total_reviews || 0;
        ratingText.textContent = `${(vendor.average_rating || 0).toFixed(1)} (${reviewCount} ${reviewCount === 1 ? 'review' : 'reviews'})`;
    }

    // Overview tab
    const description = document.getElementById('vpmDescription');
    if (description) {
        description.textContent = vendor.description || 'No description available';
    }

    document.getElementById('vpmOwnerName').textContent = vendor.owner_name || 'N/A';
    document.getElementById('vpmPhone').textContent = vendor.phone || 'N/A';
    document.getElementById('vpmEmail').textContent = vendor.email || 'N/A';
    
    const address = [vendor.address, vendor.city, vendor.state, vendor.postal_code]
        .filter(Boolean)
        .join(', ') || 'Not specified';
    document.getElementById('vpmAddress').textContent = address;

    document.getElementById('vpmRegNumber').textContent = vendor.registration_number || 'N/A';
    document.getElementById('vpmYearsInBusiness').textContent = vendor.years_in_business 
        ? `${vendor.years_in_business} years` 
        : 'N/A';
    document.getElementById('vpmServices').textContent = vendor.services_offered || 'N/A';

    // Reviews tab
    displayVpmReviews(vendor);

    // Documents tab
    if (vendor.documents) {
        displayVpmDocuments(vendor.documents);
    }

    // Statistics tab
    if (vendor.stats) {
        document.getElementById('vpmTotalBookings').textContent = vendor.stats.total_bookings || 0;
        document.getElementById('vpmPendingBookings').textContent = vendor.stats.pending_bookings || 0;
        document.getElementById('vpmConfirmedBookings').textContent = vendor.stats.confirmed_bookings || 0;
    }
}

/**
 * Display reviews
 */
function displayVpmReviews(vendor) {
    const overallRating = document.getElementById('vpmOverallRating');
    const totalReviews = document.getElementById('vpmTotalReviews');
    const reviewsList = document.getElementById('vpmReviewsList');
    const ratingBreakdown = document.getElementById('vpmRatingBreakdown');

    if (overallRating) {
        overallRating.textContent = (vendor.average_rating || 0).toFixed(1);
    }

    if (totalReviews) {
        const count = vendor.total_reviews || 0;
        totalReviews.textContent = `${count} ${count === 1 ? 'review' : 'reviews'}`;
    }

    // Rating breakdown
    if (ratingBreakdown && vendor.rating_breakdown) {
        ratingBreakdown.innerHTML = '';
        for (let i = 5; i >= 1; i--) {
            const count = vendor.rating_breakdown[i] || 0;
            const percentage = vendor.total_reviews > 0 
                ? (count / vendor.total_reviews) * 100 
                : 0;

            const row = document.createElement('div');
            row.className = 'vpm-rating-bar-row';
            row.innerHTML = `
                <span class="vpm-rating-bar-label">${i} stars</span>
                <div class="vpm-rating-bar-container">
                    <div class="vpm-rating-bar-fill" style="width: ${percentage}%"></div>
                </div>
                <span class="vpm-rating-bar-count">${count}</span>
            `;
            ratingBreakdown.appendChild(row);
        }
    }

    // Reviews list
    if (reviewsList) {
        reviewsList.innerHTML = '';

        if (!vendor.recent_reviews || vendor.recent_reviews.length === 0) {
            reviewsList.innerHTML = '<p style="text-align: center; color: #95a5a6; padding: 40px;">No reviews yet</p>';
            return;
        }

        const template = document.getElementById('vpmReviewTemplate');
        if (!template) return;

        vendor.recent_reviews.forEach(review => {
            const item = template.content.cloneNode(true);

            item.querySelector('.vpm-reviewer-name').textContent = review.reviewer_name || 'Anonymous';
            updateVpmStars(item.querySelector('.vpm-review-stars'), review.rating || 0);
            item.querySelector('.vpm-review-date').textContent = formatVpmDate(review.created_at);
            item.querySelector('.vpm-review-title').textContent = review.title || '';
            item.querySelector('.vpm-review-text').textContent = review.review_text || '';

            reviewsList.appendChild(item);
        });
    }
}

/**
 * Display documents
 */
function displayVpmDocuments(documents) {
    const documentsList = document.getElementById('vpmDocumentsList');
    if (!documentsList) return;

    if (!documents || documents.length === 0) {
        documentsList.innerHTML = '<p style="text-align: center; color: #95a5a6; padding: 40px;">No documents available</p>';
        return;
    }

    const template = document.getElementById('vpmDocumentTemplate');
    if (!template) return;

    documentsList.innerHTML = '';

    documents.forEach(doc => {
        const item = template.content.cloneNode(true);

        item.querySelector('.vpm-document-title').textContent = doc.title || 'Untitled';
        item.querySelector('.vpm-document-type').textContent = doc.document_type || 'Document';

        const badge = item.querySelector('.vpm-document-badge');
        if (doc.is_expired) {
            badge.textContent = 'Expired';
            badge.classList.add('expired');
        } else if (doc.is_verified) {
            badge.textContent = 'Verified';
            badge.classList.add('verified');
        } else {
            badge.textContent = 'Pending';
            badge.classList.add('pending');
        }

        const expiry = item.querySelector('.vpm-document-expiry');
        if (doc.expiry_date) {
            expiry.textContent = `Expires: ${formatVpmDate(doc.expiry_date)}`;
        }

        documentsList.appendChild(item);
    });
}

/**
 * Update star rating display
 */
function updateVpmStars(container, rating) {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    
    if (!container) return;

    const stars = container.querySelectorAll('i');
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;

    stars.forEach((star, index) => {
        star.className = 'fas fa-star';
        if (index >= fullStars) {
            star.className = 'far fa-star';
        }
        if (index === fullStars && hasHalfStar) {
            star.className = 'fas fa-star-half-alt';
        }
    });
}

/**
 * Format date string
 */
function formatVpmDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Handle API response
 */
async function handleVpmApiResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'An error occurred');
    }
    return await response.json();
}

/**
 * Show error message
 */
function showVpmError(message) {
    const loadingState = document.getElementById('vpmLoadingState');
    if (loadingState) {
        loadingState.innerHTML = `
            <i class="fas fa-exclamation-circle" style="font-size: 48px; color: #e74c3c; margin-bottom: 20px;"></i>
            <p style="color: #e74c3c; font-weight: 600;">${message}</p>
            <button onclick="closeVendorProfileModal()" style="margin-top: 20px; padding: 10px 20px; background: #3498db; color: #fff; border: none; border-radius: 6px; cursor: pointer;">Close</button>
        `;
    }
}