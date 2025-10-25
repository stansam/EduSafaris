const revenueChartCtx = document.getElementById('safari-revenue-chart').getContext('2d');

const revenueData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
        label: 'Revenue',
        data: [11000, 15500, 18200, 22000, 27500, 35000],
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointBackgroundColor: '#22c55e',
        pointBorderColor: 'white',
        pointBorderWidth: 2,
    }]
};

const revenueChart = new Chart(revenueChartCtx, {
    type: 'line',
    data: revenueData,
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
                max: 36000,
                ticks: {
                    stepSize: 9000,
                    callback: function(value) {
                        return '$' + value.toLocaleString();
                    },
                    color: '#999',
                    font: {
                        size: 12
                    }
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                    drawBorder: false
                }
            },
            x: {
                grid: {
                    display: false,
                    drawBorder: false
                },
                ticks: {
                    color: '#999',
                    font: {
                        size: 12
                    }
                }
            }
        }
    }
});

// Tab Switching
document.querySelectorAll('.safari-tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.safari-tab-btn').forEach(b => b.classList.remove('safari-tab-active'));
        this.classList.add('safari-tab-active');
    });
});

// Interactive Metric Cards
const metricCards = document.querySelectorAll('.safari-metric-card');
metricCards.forEach(card => {
    card.addEventListener('click', function() {
        this.style.transform = 'scale(1.02)';
        setTimeout(() => {
            this.style.transform = '';
        }, 200);
    });
});

// Handle Create Trip
function handleCreateTrip() {
    alert('Create Trip modal would open here');
    console.log('Create Trip clicked');
}

// Simulate Real-time Updates
function updateMetrics() {
    const activeTrips = Math.floor(Math.random() * 5) + 2;
    const inProgress = Math.floor(Math.random() * 3) + 1;
    const pending = Math.floor(Math.random() * 8) + 3;
    const emergencies = Math.floor(Math.random() * 2);
    
    document.getElementById('active-trips-value').textContent = activeTrips;
    document.getElementById('in-progress-value').textContent = inProgress;
    document.getElementById('pending-value').textContent = pending;
    document.getElementById('emergencies-value').textContent = emergencies;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Safari Dashboard initialized');
});