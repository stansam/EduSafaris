(function() {
    'use strict';

    const StatsModal = {
        currentPeriod: 'month',
        chartInstances: {},

        init() {
            this.attachEventListeners();
        },

        attachEventListeners() {
            // Close buttons
            document.getElementById('edusafariStatsCloseBtn')?.addEventListener('click', () => this.close());
            document.getElementById('edusafariStatsCloseFooterBtn')?.addEventListener('click', () => this.close());
            
            // Overlay click to close
            document.querySelector('#edusafariStatsModal .edusafari-modal-overlay')?.addEventListener('click', () => this.close());

            // Period buttons
            document.querySelectorAll('#edusafariStatsModal .edusafari-period-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const period = e.target.dataset.period;
                    this.changePeriod(period);
                });
            });

            // ESC key to close
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen()) {
                    this.close();
                }
            });
        },

        async open() {
            const modal = document.getElementById('edusafariStatsModal');
            if (!modal) return;

            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';

            // Load default period stats
            await this.loadStatistics(this.currentPeriod);
        },

        close() {
            const modal = document.getElementById('edusafariStatsModal');
            if (!modal) return;

            modal.style.display = 'none';
            document.body.style.overflow = 'auto';

            // Destroy chart instances
            this.destroyCharts();
        },

        isOpen() {
            const modal = document.getElementById('edusafariStatsModal');
            return modal && modal.style.display === 'block';
        },

        async changePeriod(period) {
            this.currentPeriod = period;

            // Update active button
            document.querySelectorAll('#edusafariStatsModal .edusafari-period-btn').forEach(btn => {
                if (btn.dataset.period === period) {
                    btn.classList.add('edusafari-period-active');
                } else {
                    btn.classList.remove('edusafari-period-active');
                }
            });

            // Reload statistics
            await this.loadStatistics(period);
        },

        async loadStatistics(period) {
            // Show loading
            document.getElementById('edusafariStatsLoading').style.display = 'block';
            document.getElementById('edusafariStatsContent').style.display = 'none';

            try {
                const response = await fetch(`/api/admin/trips/statistics?period=${period}`, {
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
                    this.renderStatistics(data.data);
                    
                    // Show content
                    document.getElementById('edusafariStatsLoading').style.display = 'none';
                    document.getElementById('edusafariStatsContent').style.display = 'block';
                } else {
                    throw new Error(data.error || 'Failed to load statistics');
                }
            } catch (error) {
                console.error('Error loading statistics:', error);
                
                if (window.EdusafariTrips) {
                    window.EdusafariTrips.showToast('error', 'Error', 'Failed to load statistics: ' + error.message);
                }

                this.close();
            }
        },

        renderStatistics(data) {
            const overview = data.overview || {};
            const breakdowns = data.breakdowns || {};
            const trends = data.trends || {};

            // Render overview stats
            document.getElementById('edusafariStatsTotalTrips').textContent = overview.total_trips || 0;
            document.getElementById('edusafariStatsTotalParticipants').textContent = overview.total_participants || 0;
            document.getElementById('edusafariStatsTotalRevenue').textContent = 
                `KES ${parseFloat(overview.total_revenue || 0).toLocaleString()}`;
            document.getElementById('edusafariStatsCapacity').textContent = 
                `${parseFloat(overview.capacity_utilization || 0).toFixed(1)}%`;

            // Render charts
            this.renderCharts(breakdowns, trends);

            // Render top destinations
            this.renderTopDestinations(breakdowns.top_destinations || []);
        },

        renderCharts(breakdowns, trends) {
            // Destroy existing charts
            this.destroyCharts();

            // Check if Chart.js is available
            if (typeof Chart === 'undefined') {
                console.warn('Chart.js not loaded. Charts will not be displayed.');
                this.renderChartsPlaceholder();
                return;
            }

            // Category Chart
            this.renderCategoryChart(breakdowns.by_category || {});

            // Status Chart
            this.renderStatusChart(breakdowns.by_status || {});
        },

        renderCategoryChart(categoryData) {
            const canvas = document.getElementById('edusafariCategoryChart');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            
            const labels = Object.keys(categoryData);
            const data = Object.values(categoryData);

            const colors = [
                '#3498db', '#27ae60', '#f39c12', '#e74c3c', 
                '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
            ];

            this.chartInstances.category = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels.map(l => this.capitalize(l)),
                    datasets: [{
                        data: data,
                        backgroundColor: colors.slice(0, labels.length),
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 15,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        },

        renderStatusChart(statusData) {
            const canvas = document.getElementById('edusafariStatusChart');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            
            const labels = Object.keys(statusData);
            const data = Object.values(statusData);

            const statusColors = {
                'draft': '#95a5a6',
                'published': '#27ae60',
                'registration_open': '#3498db',
                'registration_closed': '#f39c12',
                'full': '#e74c3c',
                'in_progress': '#9b59b6',
                'completed': '#1abc9c',
                'cancelled': '#c0392b'
            };

            const colors = labels.map(status => statusColors[status] || '#7f8c8d');

            this.chartInstances.status = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels.map(l => this.formatStatus(l)),
                    datasets: [{
                        label: 'Number of Trips',
                        data: data,
                        backgroundColor: colors,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
        },

        renderChartsPlaceholder() {
            // Show message if Chart.js is not available
            const categoryChart = document.getElementById('edusafariCategoryChart');
            const statusChart = document.getElementById('edusafariStatusChart');

            if (categoryChart) {
                categoryChart.parentElement.innerHTML = `
                    <div style="padding: 40px; text-align: center; color: #7f8c8d;">
                        <i class="fas fa-chart-pie" style="font-size: 48px; margin-bottom: 15px;"></i>
                        <p>Chart.js library not loaded. Install Chart.js to view charts.</p>
                    </div>
                `;
            }

            if (statusChart) {
                statusChart.parentElement.innerHTML = `
                    <div style="padding: 40px; text-align: center; color: #7f8c8d;">
                        <i class="fas fa-chart-bar" style="font-size: 48px; margin-bottom: 15px;"></i>
                        <p>Chart.js library not loaded. Install Chart.js to view charts.</p>
                    </div>
                `;
            }
        },

        renderTopDestinations(destinations) {
            const container = document.getElementById('edusafariTopDestinationsContent');
            if (!container) return;

            if (destinations.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 20px;">No destination data available</p>';
                return;
            }

            const maxCount = Math.max(...destinations.map(d => d.count));

            container.innerHTML = destinations.map((dest, index) => {
                const percentage = (dest.count / maxCount) * 100;
                
                return `
                    <div class="edusafari-destination-item">
                        <div class="edusafari-destination-rank">#${index + 1}</div>
                        <div class="edusafari-destination-info">
                            <div class="edusafari-destination-header">
                                <span class="edusafari-destination-name">${this.escapeHtml(dest.destination)}</span>
                                <span class="edusafari-destination-count">${dest.count} trips</span>
                            </div>
                            <div class="edusafari-destination-bar">
                                <div class="edusafari-destination-fill" style="width: ${percentage}%"></div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        },

        destroyCharts() {
            // Destroy all chart instances
            Object.keys(this.chartInstances).forEach(key => {
                if (this.chartInstances[key]) {
                    this.chartInstances[key].destroy();
                    delete this.chartInstances[key];
                }
            });
        },

        capitalize(str) {
            return str.charAt(0).toUpperCase() + str.slice(1);
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
            return statusMap[status] || this.capitalize(status);
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
        document.addEventListener('DOMContentLoaded', () => StatsModal.init());
    } else {
        StatsModal.init();
    }

    // Export to global scope
    window.EdusafariStatsModal = StatsModal;

})();