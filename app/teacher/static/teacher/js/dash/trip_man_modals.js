// Configuration
const TRIP_API_CONFIG = {
    baseUrl: '/api/trip', 
    userId: TEACHER_DASHBOARD_CONFIG.teacherUserId 
};

// Global state
let tripCurrentEditId = null;
let tripItineraryCounters = { create: 0, edit: 0 };

// Utility functions
function tripShowAlert(modalType, message, type = 'error', details = null) {
    const alertDiv = document.getElementById(`trip${modalType}Alert`);
    alertDiv.className = `trip-alert trip-alert-${type} show`;
    
    let html = `<div class="trip-alert-title">${type === 'error' ? '❌ Error' : '✅ Success'}</div>`;
    html += `<div>${message}</div>`;
    
    if (details && Array.isArray(details)) {
        html += '<ul class="trip-alert-list">';
        details.forEach(detail => {
            html += `<li>${detail}</li>`;
        });
        html += '</ul>';
    }
    
    alertDiv.innerHTML = html;
    alertDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    if (type === 'success') {
        setTimeout(() => {
            alertDiv.classList.remove('show');
        }, 5000);
    }
}

function tripHideAlert(modalType) {
    const alertDiv = document.getElementById(`trip${modalType}Alert`);
    alertDiv.classList.remove('show');
}

function tripSetLoading(modalType, isLoading) {
    const submitBtn = document.getElementById(`trip${modalType}SubmitBtn`);
    const form = document.getElementById(`trip${modalType}Form`);
    
    if (isLoading) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="trip-loading-spinner"></span> Processing...';
        form.querySelectorAll('input, select, textarea, button').forEach(el => {
            if (el !== submitBtn) el.disabled = true;
        });
    } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = modalType === 'Create' ? 'Create Trip' : 'Update Trip';
        form.querySelectorAll('input, select, textarea, button').forEach(el => {
            el.disabled = false;
        });
    }
}

// Modal control functions
function tripOpenCreateModal() {
    document.getElementById('tripCreateModal').classList.add('active');
    document.body.style.overflow = 'hidden';
    tripResetCreateForm();
}

function tripCloseCreateModal() {
    document.getElementById('tripCreateModal').classList.remove('active');
    document.body.style.overflow = '';
    tripHideAlert('Create');
}

function tripOpenEditModal(tripId) {
    tripCurrentEditId = tripId;
    document.getElementById('tripEditModal').classList.add('active');
    document.body.style.overflow = 'hidden';
    tripLoadTripData(tripId);
}

function tripCloseEditModal() {
    document.getElementById('tripEditModal').classList.remove('active');
    document.body.style.overflow = '';
    tripHideAlert('Edit');
    tripCurrentEditId = null;
}

// Close modals on overlay click
document.getElementById('tripCreateModal').addEventListener('click', function(e) {
    if (e.target === this) tripCloseCreateModal();
});

document.getElementById('tripEditModal').addEventListener('click', function(e) {
    if (e.target === this) tripCloseEditModal();
});

// Itinerary management
function tripAddItineraryDay(modalType) {
    const counter = ++tripItineraryCounters[modalType];
    const container = document.getElementById(`trip${modalType === 'create' ? 'Create' : 'Edit'}ItineraryDays`);
    
    const dayDiv = document.createElement('div');
    dayDiv.className = 'trip-itinerary-day';
    dayDiv.id = `trip${modalType}ItineraryDay${counter}`;
    dayDiv.innerHTML = `
        <div class="trip-itinerary-day-header">
            <span class="trip-itinerary-day-title">Day ${counter}</span>
            <button type="button" class="trip-btn trip-btn-small trip-btn-danger" onclick="tripRemoveItineraryDay('${modalType}', ${counter})"> Remove</button>
        </div>
        <div class="trip-form-group">
            <label class="trip-form-label">Day Title</label>
            <input type="text" class="trip-form-input" 
                    id="trip${modalType}DayTitle${counter}" 
                    placeholder="e.g., Museum Visit">
        </div>
        <div class="trip-form-group">
            <label class="trip-form-label">Activities</label>
            <textarea class="trip-form-textarea" 
                        id="trip${modalType}DayActivities${counter}" 
                        placeholder="Describe the day's activities..."
                        style="min-height: 80px;"></textarea>
        </div>
    `;
    
    container.appendChild(dayDiv);
}

function tripRemoveItineraryDay(modalType, dayNumber) {
    const dayDiv = document.getElementById(`trip${modalType}ItineraryDay${dayNumber}`);
    if (dayDiv) {
        dayDiv.remove();
        tripReindexItinerary(modalType);
    }
}

function tripReindexItinerary(modalType) {
  const container = document.getElementById(`trip${modalType === 'create' ? 'Create' : 'Edit'}ItineraryDays`);
  const days = container.querySelectorAll('.trip-itinerary-day');

  days.forEach((day, index) => {
    day.querySelector('.trip-itinerary-day-title').textContent = `Day ${index + 1}`;
  });

  tripItineraryCounters[modalType] = days.length;
}

function tripCollectItineraryData(modalType) {
    const prefix = modalType === 'create' ? 'Create' : 'Edit';
    const container = document.getElementById(`trip${prefix}ItineraryDays`);
    const days = container.querySelectorAll('.trip-itinerary-day');
    
    if (days.length === 0) return null;
    
    // const itinerary = [];
    // days.forEach((day, index) => {
    //     const dayId = day.id.match(/\d+$/)?.[0];
    //     const title = document.getElementById(`trip${modalType}DayTitle${dayId}`)?.value || '';
    //     const activities = document.getElementById(`trip${modalType}DayActivities${dayId}`)?.value || '';
        
    //     if (title || activities) {
    //         // itinerary.push({
    //         //     day: index + 1,
    //         //     title: title,
    //         //     activities: activities
    //         // });
    //         itinerary[`day_${index + 1}`] = activities || title;
    //     }
    // });

    const itinerary = {};  // Changed from array to object
    days.forEach((day, index) => {
        const dayId = day.id.match(/\d+$/)?.[0];
        const title = document.getElementById(`trip${modalType}DayTitle${dayId}`)?.value || '';
        const activities = document.getElementById(`trip${modalType}DayActivities${dayId}`)?.value || '';
        
        if (title || activities) {
            // Store as object with day_N keys
            itinerary[`day_${index + 1}`] = {
                title: title,
                activities: activities
            };
        }
    });
    
    return Object.keys(itinerary).length > 0 ? itinerary : null;
}

function tripResetCreateForm() {
    document.getElementById('tripCreateForm').reset();
    document.getElementById('tripCreateItineraryDays').innerHTML = '';
    tripItineraryCounters.create = 0;
    tripHideAlert('Create');
}

// Load trip data for editing
async function tripLoadTripData(tripId) {
    try {
        tripSetLoading('Edit', true);
        
        // For demo purposes, using mock data
        // Replace with actual API call: const response = await fetch(`${TRIP_API_CONFIG.baseUrl}/${tripId}`);
        const response = await fetch(`api/trips/${tripId}`);
        const data = await response.json();
        const mockTripData = data.trip;
        // const mockTripData = {
        //     id: 1,
        //     title: "Summer Science Camp",
        //     destination: "National Science Center",
        //     description: "An exciting week exploring science and technology",
        //     category: "science",
        //     grade_level: "6-8",
        //     start_date: "2025-07-15",
        //     end_date: "2025-07-19",
        //     registration_deadline: "2025-06-30",
        //     price_per_student: 299.99,
        //     max_participants: 30,
        //     min_participants: 10,
        //     current_participants: 15,
        //     medical_info_required: true,
        //     consent_required: true,
        //     status: "active",
        //     itinerary: [
        //         { day: 1, title: "Physics Lab", activities: "Explore fundamental physics concepts" },
        //         { day: 2, title: "Chemistry Workshop", activities: "Hands-on chemistry experiments" }
        //     ]
        // };
        
        // Populate form fields
        document.getElementById('tripEditTitle').value = mockTripData.title || '';
        document.getElementById('tripEditDestination').value = mockTripData.destination || '';
        document.getElementById('tripEditDescription').value = mockTripData.description || '';
        document.getElementById('tripEditCategory').value = mockTripData.category || '';
        document.getElementById('tripEditGradeLevel').value = mockTripData.grade_level || '';
        document.getElementById('tripEditStartDate').value = mockTripData.start_date || '';
        document.getElementById('tripEditEndDate').value = mockTripData.end_date || '';
        document.getElementById('tripEditRegDeadline').value = mockTripData.registration_deadline || '';
        document.getElementById('tripEditPrice').value = mockTripData.price_per_student || '';
        document.getElementById('tripEditMaxParticipants').value = mockTripData.max_participants || '';
        document.getElementById('tripEditMinParticipants').value = mockTripData.min_participants || '';
        document.getElementById('tripEditMedicalInfo').checked = mockTripData.medical_info_required || false;
        document.getElementById('tripEditConsent').checked = mockTripData.consent_required || false;
        document.getElementById('tripEditStatus').value = mockTripData.status || 'draft';
        
        // Show current participants info
        if (mockTripData.current_participants !== undefined) {
            document.getElementById('tripEditCurrentParticipants').textContent = 
                `Current participants: ${mockTripData.current_participants}`;
        }
        
        // Load itinerary
        document.getElementById('tripEditItineraryDays').innerHTML = '';
        tripItineraryCounters.edit = 0;
        
        // if (mockTripData.itinerary && Array.isArray(mockTripData.itinerary)) {
        //     mockTripData.itinerary.forEach(day => {
        //         tripAddItineraryDay('edit');
        //         const counter = tripItineraryCounters.edit;
        //         document.getElementById(`tripeditDayTitle${counter}`).value = day.title || '';
        //         document.getElementById(`tripeditDayActivities${counter}`).value = day.activities || '';
        //     });
        // }
        // if (mockTripData.itinerary && typeof mockTripData.itinerary === 'object') {
        //     Object.entries(mockTripData.itinerary).forEach(([dayKey, activities]) => {
        //         tripAddItineraryDay('edit');
        //         const counter = tripItineraryCounters.edit;

        //         document.getElementById(`tripeditDayTitle${counter}`).value = dayKey.replace('_', ' ') || '';
        //         document.getElementById(`tripeditDayActivities${counter}`).value = activities || '';
        //     });
        // }
        if (mockTripData.itinerary && typeof mockTripData.itinerary === 'object') {
            Object.entries(mockTripData.itinerary).forEach(([dayKey, dayData]) => {
                tripAddItineraryDay('edit');
                const counter = tripItineraryCounters.edit;
                
                // Handle both formats: string or object
                if (typeof dayData === 'string') {
                    document.getElementById(`tripeditDayTitle${counter}`).value = dayKey.replace('_', ' ') || '';
                    document.getElementById(`tripeditDayActivities${counter}`).value = dayData || '';
                } else if (typeof dayData === 'object') {
                    document.getElementById(`tripeditDayTitle${counter}`).value = dayData.title || '';
                    document.getElementById(`tripeditDayActivities${counter}`).value = dayData.activities || '';
                }
            });
        }
        
        tripSetLoading('Edit', false);
        
    } catch (error) {
        console.error('Error loading trip data:', error);
        tripShowAlert('Edit', 'Failed to load trip data. Please try again.', 'error');
        tripSetLoading('Edit', false);
    }
}

// Handle create form submission
async function tripHandleCreateSubmit(event) {
    event.preventDefault();
    tripHideAlert('Create');
    
    try {
        tripSetLoading('Create', true);
        
        // Collect form data
        const formData = {
            title: document.getElementById('tripCreateTitle').value.trim(),
            destination: document.getElementById('tripCreateDestination').value.trim(),
            description: document.getElementById('tripCreateDescription').value.trim() || null,
            category: document.getElementById('tripCreateCategory').value.trim() || null,
            grade_level: document.getElementById('tripCreateGradeLevel').value.trim() || null,
            start_date: document.getElementById('tripCreateStartDate').value,
            end_date: document.getElementById('tripCreateEndDate').value,
            registration_deadline: document.getElementById('tripCreateRegDeadline').value || null,
            price_per_student: parseFloat(document.getElementById('tripCreatePrice').value),
            max_participants: parseInt(document.getElementById('tripCreateMaxParticipants').value),
            min_participants: parseInt(document.getElementById('tripCreateMinParticipants').value) || 0,
            medical_info_required: document.getElementById('tripCreateMedicalInfo').checked,
            consent_required: document.getElementById('tripCreateConsent').checked,
            status: document.getElementById('tripCreateStatus').value,
            itinerary: tripCollectItineraryData('create'),
            destination_country: document.getElementById('tripCreateDestinationCountry')?.value.trim() || null,
            meeting_point: document.getElementById('tripCreateMeetingPoint')?.value.trim() || null,
            registration_start_date: document.getElementById('tripCreateRegStartDate')?.value || null,
            transportation_included: document.getElementById('tripCreateTransportation')?.checked ?? true,
            meals_included: document.getElementById('tripCreateMeals')?.checked ?? true,
            accommodation_included: document.getElementById('tripCreateAccommodation')?.checked ?? false,
        };
        
        // Make API call
        const response = await fetch(`${TRIP_API_CONFIG.baseUrl}/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': TRIP_API_CONFIG.userId
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            tripShowAlert('Create', 'Trip created successfully!', 'success');
            setTimeout(() => {
                tripCloseCreateModal();
                // Optionally redirect or refresh trip list
                // window.location.href = '/trips';
            }, 2000);
        } else {
            tripShowAlert('Create', 
                result.error || 'Failed to create trip', 
                'error', 
                result.details
            );
        }
        
    } catch (error) {
        console.error('Error creating trip:', error);
        tripShowAlert('Create', 'Network error. Please check your connection and try again.', 'error');
    } finally {
        tripSetLoading('Create', false);
    }
}

// Handle edit form submission
async function tripHandleEditSubmit(event) {
    event.preventDefault();
    tripHideAlert('Edit');
    
    if (!tripCurrentEditId) {
        tripShowAlert('Edit', 'No trip selected for editing', 'error');
        return;
    }
    
    try {
        tripSetLoading('Edit', true);
        
        // Collect form data
        const formData = {
            title: document.getElementById('tripEditTitle').value.trim(),
            destination: document.getElementById('tripEditDestination').value.trim(),
            description: document.getElementById('tripEditDescription').value.trim() || null,
            category: document.getElementById('tripEditCategory').value.trim() || null,
            grade_level: document.getElementById('tripEditGradeLevel').value.trim() || null,
            start_date: document.getElementById('tripEditStartDate').value,
            end_date: document.getElementById('tripEditEndDate').value,
            registration_deadline: document.getElementById('tripEditRegDeadline').value || null,
            price_per_student: parseFloat(document.getElementById('tripEditPrice').value),
            max_participants: parseInt(document.getElementById('tripEditMaxParticipants').value),
            min_participants: parseInt(document.getElementById('tripEditMinParticipants').value) || 0,
            medical_info_required: document.getElementById('tripEditMedicalInfo').checked,
            consent_required: document.getElementById('tripEditConsent').checked,
            status: document.getElementById('tripEditStatus').value,
            itinerary: tripCollectItineraryData('edit')
        };
        
        // Make API call
        const response = await fetch(`${TRIP_API_CONFIG.baseUrl}/edit/${tripCurrentEditId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': TRIP_API_CONFIG.userId
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            tripShowAlert('Edit', 'Trip updated successfully!', 'success');
            setTimeout(() => {
                tripCloseEditModal();
                // Optionally refresh trip list or redirect
                // window.location.reload();
            }, 2000);
        } else {
            tripShowAlert('Edit', 
                result.error || 'Failed to update trip', 
                'error', 
                result.details
            );
        }
        
    } catch (error) {
        console.error('Error updating trip:', error);
        tripShowAlert('Edit', 'Network error. Please check your connection and try again.', 'error');
    } finally {
        tripSetLoading('Edit', false);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (document.getElementById('tripCreateModal').classList.contains('active')) {
            tripCloseCreateModal();
        }
        if (document.getElementById('tripEditModal').classList.contains('active')) {
            tripCloseEditModal();
        }
    }
});
    