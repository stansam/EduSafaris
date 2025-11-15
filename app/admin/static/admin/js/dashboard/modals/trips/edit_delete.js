(function() {
    'use strict';

    const EditTripModal = {
        currentTripId: null,

        init() {
            this.attachEventListeners();
        },

        attachEventListeners() {
            document.getElementById('edusafariEditTripCloseBtn')?.addEventListener('click', () => this.close());
            document.getElementById('edusafariEditCancelFormBtn')?.addEventListener('click', () => this.close());
            document.getElementById('edusafariEditSaveBtn')?.addEventListener('click', () => this.saveTrip());
            document.getElementById('edusafariEditDeleteBtn')?.addEventListener('click', () => this.deleteTrip());
            document.getElementById('edusafariEditCancelBtn')?.addEventListener('click', () => this.cancelTrip());
            document.getElementById('edusafariEditFeatureToggleBtn')?.addEventListener('click', () => this.toggleFeature());
            document.getElementById('edusafariEditApproveBtn')?.addEventListener('click', () => this.approveTrip());
        },

        async open(tripId) {
            this.currentTripId = tripId;
            document.getElementById('edusafariEditTripModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
            
            await this.loadTripData(tripId);
        },

        close() {
            document.getElementById('edusafariEditTripModal').style.display = 'none';
            document.body.style.overflow = 'auto';
        },

        async loadTripData(tripId) {
            // Show loading
            document.getElementById('edusafariEditTripLoading').style.display = 'block';
            document.getElementById('edusafariEditTripForm').style.display = 'none';

            try {
                const response = await fetch(`/api/admin/trips/${tripId}`);
                const data = await response.json();

                if (data.success) {
                    this.populateForm(data.data.trip);
                    document.getElementById('edusafariEditTripLoading').style.display = 'none';
                    document.getElementById('edusafariEditTripForm').style.display = 'block';
                }
            } catch (error) {
                console.error('Error:', error);
                this.close();
            }
        },

        populateForm(trip) {
            // Populate all form fields
            document.getElementById('edusafariEditTitle').value = trip.title || '';
            document.getElementById('edusafariEditDescription').value = trip.description || '';
            document.getElementById('edusafariEditDestination').value = trip.destination || '';
            // ... populate other fields
            document.getElementById('edusafariEditFeatured').checked = trip.featured || false;
            document.getElementById('edusafariEditPublished').checked = trip.is_published || false;
        },

        async saveTrip() {
            const formData = this.getFormData();
            
            try {
                const response = await fetch(`/api/admin/trips/${this.currentTripId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (data.success) {
                    window.EdusafariTrips?.showToast('success', 'Success', 'Trip updated successfully');
                    window.EdusafariTrips?.reload();
                    this.close();
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                window.EdusafariTrips?.showToast('error', 'Error', error.message);
            }
        },

        getFormData() {
            const form = document.getElementById('edusafariEditTripForm');
            const formData = {};
            
            // Collect all form inputs
            form.querySelectorAll('input, select, textarea').forEach(input => {
                if (input.type === 'checkbox') {
                    formData[input.name] = input.checked;
                } else if (input.name) {
                    formData[input.name] = input.value;
                }
            });
            
            return formData;
        },

        async deleteTrip() {
            if (!confirm('Delete this trip? This cannot be undone.')) return;

            try {
                const response = await fetch(`/api/admin/trips/${this.currentTripId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });

                const data = await response.json();

                if (data.success) {
                    window.EdusafariTrips?.showToast('success', 'Success', 'Trip deleted');
                    window.EdusafariTrips?.reload();
                    this.close();
                }
            } catch (error) {
                window.EdusafariTrips?.showToast('error', 'Error', error.message);
            }
        },

        async cancelTrip() {
            const reason = prompt('Enter cancellation reason:');
            if (!reason) return;

            try {
                const response = await fetch(`/api/admin/trips/${this.currentTripId}/status`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ status: 'cancelled', reason })
                });

                const data = await response.json();
                if (data.success) {
                    window.EdusafariTrips?.showToast('success', 'Success', 'Trip cancelled');
                    window.EdusafariTrips?.reload();
                    this.close();
                }
            } catch (error) {
                window.EdusafariTrips?.showToast('error', 'Error', error.message);
            }
        },

        async toggleFeature() {
            const currentlyFeatured = document.getElementById('edusafariEditFeatured').checked;
            
            try {
                const response = await fetch(`/api/admin/trips/${this.currentTripId}/feature`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ featured: !currentlyFeatured })
                });

                const data = await response.json();
                if (data.success) {
                    document.getElementById('edusafariEditFeatured').checked = !currentlyFeatured;
                    window.EdusafariTrips?.showToast('success', 'Success', 
                        `Trip ${!currentlyFeatured ? 'featured' : 'unfeatured'}`);
                    window.EdusafariTrips?.reload();
                }
            } catch (error) {
                window.EdusafariTrips?.showToast('error', 'Error', error.message);
            }
        },

        async approveTrip() {
            try {
                const response = await fetch(`/api/admin/trips/${this.currentTripId}/status`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ status: 'published' })
                });

                const data = await response.json();
                if (data.success) {
                    window.EdusafariTrips?.showToast('success', 'Success', 'Trip approved');
                    window.EdusafariTrips?.reload();
                    this.close();
                }
            } catch (error) {
                window.EdusafariTrips?.showToast('error', 'Error', error.message);
            }
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => EditTripModal.init());
    } else {
        EditTripModal.init();
    }

    window.EdusafariEditTripModal = EditTripModal;
})();