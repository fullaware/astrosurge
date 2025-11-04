// Charts module

// Charts object - will be initialized on window
if (!window.charts) {
    window.charts = {};
}

// Setup charts
function setupCharts() {
    if (!window.dashboardData) return;

    // Mission Status Chart
    const missionCtx = document.getElementById('missionStatusChart');
    if (missionCtx) {
        window.charts.missionStatus = new Chart(missionCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: window.dashboardData.charts.mission_status.labels,
                datasets: [{
                    data: window.dashboardData.charts.mission_status.data,
                    backgroundColor: ['#ffaa00', '#00d4ff', '#4488ff', '#00ff88'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#ffffff'
                        }
                    }
                }
            }
        });
    }

    // Revenue Chart
    const revenueCtx = document.getElementById('revenueChart');
    if (revenueCtx) {
        window.charts.revenue = new Chart(revenueCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: window.dashboardData.charts.revenue_trend.labels,
                datasets: [{
                    label: 'Revenue (M$)',
                    data: window.dashboardData.charts.revenue_trend.data,
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }

    // Fleet Chart
    const fleetCtx = document.getElementById('fleetChart');
    if (fleetCtx) {
        window.charts.fleet = new Chart(fleetCtx.getContext('2d'), {
            type: 'pie',
            data: {
                labels: window.dashboardData.charts.fleet_utilization.labels,
                datasets: [{
                    data: window.dashboardData.charts.fleet_utilization.data,
                    backgroundColor: ['#00d4ff', '#888888', '#ffaa00'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#ffffff'
                        }
                    }
                }
            }
        });
    }

    // Commodity Chart
    const commodityCtx = document.getElementById('commodityChart');
    if (commodityCtx) {
        window.charts.commodity = new Chart(commodityCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: window.dashboardData.charts.commodity_prices.labels,
                datasets: [{
                    label: 'Price ($)',
                    data: window.dashboardData.charts.commodity_prices.data,
                    backgroundColor: '#00d4ff',
                    borderColor: '#00d4ff',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }
}

// Update charts
function updateCharts() {
    if (!window.dashboardData) return;

    // Update mission status chart
    if (window.charts.missionStatus) {
        window.charts.missionStatus.data.datasets[0].data = window.dashboardData.charts.mission_status.data;
        window.charts.missionStatus.update();
    }

    // Update revenue chart
    if (window.charts.revenue) {
        window.charts.revenue.data.datasets[0].data = window.dashboardData.charts.revenue_trend.data;
        window.charts.revenue.update();
    }

    // Update fleet chart
    if (window.charts.fleet) {
        window.charts.fleet.data.datasets[0].data = window.dashboardData.charts.fleet_utilization.data;
        window.charts.fleet.update();
    }

    // Update commodity chart
    if (window.charts.commodity) {
        window.charts.commodity.data.datasets[0].data = window.dashboardData.charts.commodity_prices.data;
        window.charts.commodity.update();
    }
}

