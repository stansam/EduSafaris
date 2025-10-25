let revenueData = {
    labels: [],
    datasets: [{
        label: 'Revenue',
        data: [],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true
    }]
};

let revenueChart = null;
let isChartInitialized = false;

function updateRevenueChart() {
    const monthlyRevenue = [
        { month: 'May', revenue: 45000 },
        { month: 'Jun', revenue: 52000 },
        { month: 'Jul', revenue: 48000 },
        { month: 'Aug', revenue: 61000 },
        { month: 'Sep', revenue: 55000 },
        { month: 'Oct', revenue: 67000 }
    ];

    // Clear and repopulate data
    revenueData.labels = [];
    revenueData.datasets[0].data = [];

    monthlyRevenue.forEach(item => {
        revenueData.labels.push(item.month);
        revenueData.datasets[0].data.push(item.revenue);
    });

    if (revenueChart) {
        revenueChart.update();
        return;
    }

    initializeChart();
}

function initializeChart() {
    const ctx = document.getElementById('safari-revenue-chart');
    if (!ctx || isChartInitialized) return;

    revenueChart = new Chart(ctx, {
        type: 'line',
        data: revenueData,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
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

    isChartInitialized = true;
}
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updateRevenueChart);
} else {
    updateRevenueChart();
}

