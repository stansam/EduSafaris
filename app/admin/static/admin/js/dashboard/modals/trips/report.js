(function() {
    'use strict';

    const ReportModal = {
        currentTripId: null,
        currentReport: null,

        init() {
            this.attachEventListeners();
        },

        attachEventListeners() {
            // Close buttons
            document.getElementById('edusafariReportCloseBtn')?.addEventListener('click', () => this.close());
            document.getElementById('edusafariReportCloseFooterBtn')?.addEventListener('click', () => this.close());
            
            // Overlay click to close
            document.querySelector('#edusafariReportModal .edusafari-modal-overlay')?.addEventListener('click', () => this.close());

            // Generate button
            document.getElementById('edusafariReportGenerateBtn')?.addEventListener('click', () => this.generateReport());

            // Download button
            document.getElementById('edusafariReportDownloadBtn')?.addEventListener('click', () => this.downloadReport());

            // ESC key to close
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen()) {
                    this.close();
                }
            });
        },

        open(tripId) {
            this.currentTripId = tripId;
            const modal = document.getElementById('edusafariReportModal');
            if (!modal) return;

            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';

            // Reset form and display
            document.getElementById('edusafariReportForm').style.display = 'block';
            document.getElementById('edusafariReportDisplay').style.display = 'none';
            document.getElementById('edusafariReportDownloadBtn').style.display = 'none';
            
            // Reset checkboxes to checked
            document.getElementById('edusafariReportParticipants').checked = true;
            document.getElementById('edusafariReportFinancials').checked = true;
            document.getElementById('edusafariReportActivity').checked = true;
        },

        close() {
            const modal = document.getElementById('edusafariReportModal');
            if (!modal) return;

            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            this.currentTripId = null;
            this.currentReport = null;
        },

        isOpen() {
            const modal = document.getElementById('edusafariReportModal');
            return modal && modal.style.display === 'block';
        },

        async generateReport() {
            if (!this.currentTripId) return;

            // Get form options
            const format = document.getElementById('edusafariReportFormat').value;
            const includeParticipants = document.getElementById('edusafariReportParticipants').checked;
            const includeFinancials = document.getElementById('edusafariReportFinancials').checked;
            const includeActivity = document.getElementById('edusafariReportActivity').checked;

            // Show loading
            const loading = document.getElementById('edusafariReportLoading');
            const formSection = document.getElementById('edusafariReportForm');
            const displaySection = document.getElementById('edusafariReportDisplay');
            
            loading.style.display = 'block';
            formSection.style.display = 'none';
            displaySection.style.display = 'none';

            try {
                // Build query params
                const params = new URLSearchParams({
                    format: format,
                    include_participants: includeParticipants,
                    include_financials: includeFinancials,
                    include_activity: includeActivity
                });

                const response = await fetch(`/api/admin/trips/${this.currentTripId}/report?${params}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include'
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    this.currentReport = data.data;
                    this.displayReport(data.data, format);
                    
                    // Hide loading, show display
                    loading.style.display = 'none';
                    displaySection.style.display = 'block';
                    document.getElementById('edusafariReportDownloadBtn').style.display = 'inline-flex';

                    if (window.EdusafariTrips) {
                        window.EdusafariTrips.showToast('success', 'Success', 'Report generated successfully');
                    }
                } else {
                    throw new Error(data.error || 'Failed to generate report');
                }
            } catch (error) {
                console.error('Error generating report:', error);
                
                if (window.EdusafariTrips) {
                    window.EdusafariTrips.showToast('error', 'Error', 'Failed to generate report: ' + error.message);
                }

                // Show form again
                loading.style.display = 'none';
                formSection.style.display = 'block';
            }
        },

        displayReport(reportData, format) {
            const displayEl = document.getElementById('edusafariReportJson');
            
            if (format === 'summary') {
                // Display formatted summary
                displayEl.innerHTML = this.formatSummaryReport(reportData);
                displayEl.style.whiteSpace = 'normal';
            } else {
                // Display JSON with syntax highlighting
                displayEl.textContent = JSON.stringify(reportData, null, 2);
                displayEl.style.whiteSpace = 'pre';
            }
        },

        formatSummaryReport(data) {
            const trip = data.trip || {};
            const regSummary = data.registration_summary || {};
            const paymentBreakdown = data.payment_breakdown || {};
            const keyMetrics = data.key_metrics || {};
            const timeline = data.timeline || {};

            let html = `
                <div class="edusafari-report-summary">
                    <div class="edusafari-report-header">
                        <h2>${this.escapeHtml(trip.title || 'Trip Report')}</h2>
                        <p class="edusafari-report-date">Generated: ${new Date().toLocaleString()}</p>
                    </div>

                    <div class="edusafari-report-section">
                        <h3><i class="fas fa-info-circle"></i> Trip Information</h3>
                        <table class="edusafari-report-table">
                            <tr>
                                <td><strong>Destination:</strong></td>
                                <td>${this.escapeHtml(trip.destination || 'N/A')}</td>
                            </tr>
                            <tr>
                                <td><strong>Status:</strong></td>
                                <td><span class="edusafari-status-badge edusafari-status-${trip.status}">${this.formatStatus(trip.status)}</span></td>
                            </tr>
                            <tr>
                                <td><strong>Duration:</strong></td>
                                <td>${trip.duration_days || 0} days</td>
                            </tr>
                            <tr>
                                <td><strong>Price per Student:</strong></td>
                                <td>KES ${parseFloat(trip.price_per_student || 0).toLocaleString()}</td>
                            </tr>
                            <tr>
                                <td><strong>Capacity:</strong></td>
                                <td>${trip.current_participants || 0} / ${trip.max_participants || 0}</td>
                            </tr>
                        </table>
                    </div>

                    <div class="edusafari-report-section">
                        <h3><i class="fas fa-users"></i> Registration Summary</h3>
                        <div class="edusafari-report-stats">
                            <div class="edusafari-report-stat edusafari-stat-success">
                                <span class="edusafari-report-stat-value">${regSummary.confirmed || 0}</span>
                                <span class="edusafari-report-stat-label">Confirmed</span>
                            </div>
                            <div class="edusafari-report-stat edusafari-stat-warning">
                                <span class="edusafari-report-stat-value">${regSummary.pending || 0}</span>
                                <span class="edusafari-report-stat-label">Pending</span>
                            </div>
                            <div class="edusafari-report-stat edusafari-stat-info">
                                <span class="edusafari-report-stat-value">${regSummary.waitlisted || 0}</span>
                                <span class="edusafari-report-stat-label">Waitlisted</span>
                            </div>
                            <div class="edusafari-report-stat edusafari-stat-danger">
                                <span class="edusafari-report-stat-value">${regSummary.cancelled || 0}</span>
                                <span class="edusafari-report-stat-label">Cancelled</span>
                            </div>
                        </div>
                    </div>

                    <div class="edusafari-report-section">
                        <h3><i class="fas fa-credit-card"></i> Payment Breakdown</h3>
                        <table class="edusafari-report-table">
                            <tr>
                                <td><strong>Fully Paid:</strong></td>
                                <td>${paymentBreakdown.fully_paid || 0} registrations</td>
                            </tr>
                            <tr>
                                <td><strong>Partially Paid:</strong></td>
                                <td>${paymentBreakdown.partially_paid || 0} registrations</td>
                            </tr>
                            <tr>
                                <td><strong>Unpaid:</strong></td>
                                <td>${paymentBreakdown.unpaid || 0} registrations</td>
                            </tr>
                        </table>
                    </div>

                    <div class="edusafari-report-section">
                        <h3><i class="fas fa-chart-line"></i> Key Metrics</h3>
                        <table class="edusafari-report-table">
                            <tr>
                                <td><strong>Capacity Utilization:</strong></td>
                                <td>${parseFloat(keyMetrics.capacity_utilization || 0).toFixed(2)}%</td>
                            </tr>
                            <tr>
                                <td><strong>Registration Conversion:</strong></td>
                                <td>${parseFloat(keyMetrics.registration_conversion || 0).toFixed(2)}%</td>
                            </tr>
                            <tr>
                                <td><strong>Documentation Completion:</strong></td>
                                <td>${parseFloat(keyMetrics.documentation_completion || 0).toFixed(2)}%</td>
                            </tr>
                            <tr>
                                <td><strong>Payment Completion:</strong></td>
                                <td>${parseFloat(keyMetrics.payment_completion || 0).toFixed(2)}%</td>
                            </tr>
                        </table>
                    </div>

                    <div class="edusafari-report-section">
                        <h3><i class="fas fa-calendar-check"></i> Timeline</h3>
                        <table class="edusafari-report-table">
                            <tr>
                                <td><strong>Created:</strong></td>
                                <td>${timeline.created ? new Date(timeline.created).toLocaleDateString() : 'N/A'}</td>
                            </tr>
                            <tr>
                                <td><strong>Registration Opens:</strong></td>
                                <td>${timeline.registration_opens ? new Date(timeline.registration_opens).toLocaleDateString() : 'N/A'}</td>
                            </tr>
                            <tr>
                                <td><strong>Registration Deadline:</strong></td>
                                <td>${timeline.registration_deadline ? new Date(timeline.registration_deadline).toLocaleDateString() : 'N/A'}</td>
                            </tr>
                            <tr>
                                <td><strong>Trip Starts:</strong></td>
                                <td>${timeline.trip_starts ? new Date(timeline.trip_starts).toLocaleDateString() : 'N/A'}</td>
                            </tr>
                            <tr>
                                <td><strong>Trip Ends:</strong></td>
                                <td>${timeline.trip_ends ? new Date(timeline.trip_ends).toLocaleDateString() : 'N/A'}</td>
                            </tr>
                            <tr>
                                <td><strong>Days Until Trip:</strong></td>
                                <td>${timeline.days_until_trip !== null ? timeline.days_until_trip + ' days' : 'N/A'}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            `;

            return html;
        },

        downloadReport() {
            if (!this.currentReport) return;

            const format = document.getElementById('edusafariReportFormat').value;
            const trip = this.currentReport.trip || {};
            const tripTitle = (trip.title || 'trip-report').replace(/[^a-z0-9]/gi, '-').toLowerCase();
            const timestamp = new Date().toISOString().split('T')[0];
            
            let filename, content, mimeType;

            if (format === 'summary') {
                // Download as HTML
                filename = `${tripTitle}-report-${timestamp}.html`;
                mimeType = 'text/html';
                
                content = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trip Report - ${this.escapeHtml(trip.title || 'Report')}</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
        .edusafari-report-header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #2c3e50; padding-bottom: 20px; }
        .edusafari-report-header h2 { margin: 0; color: #2c3e50; }
        .edusafari-report-date { color: #7f8c8d; margin: 5px 0 0 0; }
        .edusafari-report-section { margin-bottom: 30px; }
        .edusafari-report-section h3 { color: #3498db; border-bottom: 1px solid #ecf0f1; padding-bottom: 10px; }
        .edusafari-report-table { width: 100%; border-collapse: collapse; }
        .edusafari-report-table td { padding: 10px; border-bottom: 1px solid #ecf0f1; }
        .edusafari-report-table td:first-child { width: 40%; }
        .edusafari-report-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }
        .edusafari-report-stat { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .edusafari-report-stat-value { display: block; font-size: 32px; font-weight: bold; margin-bottom: 5px; }
        .edusafari-report-stat-label { display: block; color: #7f8c8d; font-size: 14px; }
        .edusafari-stat-success .edusafari-report-stat-value { color: #27ae60; }
        .edusafari-stat-warning .edusafari-report-stat-value { color: #f39c12; }
        .edusafari-stat-info .edusafari-report-stat-value { color: #3498db; }
        .edusafari-stat-danger .edusafari-report-stat-value { color: #e74c3c; }
        .edusafari-status-badge { padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        @media print { body { padding: 0; } }
    </style>
</head>
<body>
    ${this.formatSummaryReport(this.currentReport)}
</body>
</html>
                `;
            } else {
                // Download as JSON
                filename = `${tripTitle}-report-${timestamp}.json`;
                mimeType = 'application/json';
                content = JSON.stringify(this.currentReport, null, 2);
            }

            // Create blob and download
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            if (window.EdusafariTrips) {
                window.EdusafariTrips.showToast('success', 'Success', 'Report downloaded successfully');
            }
        },

        formatStatus(status) {
            const statusMap = {
                'draft': 'Draft',
                'published': 'Published',
                'registration_open': 'Registration Open',
                'registration_closed': 'Registration Closed',
                'full': 'Full',
                'in_progress': 'In Progress',
                'completed': 'Completed',
                'cancelled': 'Cancelled'
            };
            return statusMap[status] || status;
        },

        escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ReportModal.init());
    } else {
        ReportModal.init();
    }

    // Export to global scope
    window.EdusafariReportModal = ReportModal;

})();