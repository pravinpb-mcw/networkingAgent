// App state
const state = {
    currentTab: 'dashboard',
    charts: {},
    systemStatus: 'unknown',
    timeRange: 24, // hours
    autoRefreshEnabled: true,
    refreshInterval: 5000, // 5 seconds (configurable)
    lastRefresh: null
};

// API Endpoints
const API = {
    status: '/status',
    risk: '/metrics/risk',
    nearest: '/metrics/nearest',
    history: '/analysis/history',
    start: '/system/start',
    stop: '/system/stop',
    timeseries: (type, hours) => `/metrics/timeseries/${type}?hours=${hours}`,
    webhook: '/settings/webhook',
    webhookTest: '/settings/webhook/test',
    scenariosAps: '/scenarios/aps',
    scenarioFailAp: '/scenarios/fail-ap',
    scenarioRecoverAp: '/scenarios/recover-ap'
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupClock();
    setupRefresh();
    setupButtons();
    setupScenarioControls();

    // Initial load
    refreshData();
    
    // Auto-refresh with configurable interval (default: 5 seconds)
    setInterval(() => {
        if (state.autoRefreshEnabled) {
            refreshData();
        }
    }, state.refreshInterval);
    
    // Update "last refresh" indicator
    setInterval(updateLastRefreshIndicator, 1000);
});

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-links li');
    const sections = document.querySelectorAll('.view-section');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(n => n.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));

            item.classList.add('active');
            const tabName = item.dataset.tab;
            document.getElementById(`view-${tabName}`).classList.add('active');
            state.currentTab = tabName;
            
            // Load APs when settings tab is opened
            if (tabName === 'settings') {
                loadAvailableAPs();
            }
        });
    });
}

function setupClock() {
    const updateTime = () => {
        const now = new Date();
        document.getElementById('system-clock').textContent = now.toLocaleTimeString();
    };
    setInterval(updateTime, 1000);
    updateTime();
}

function setupRefresh() {
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.addEventListener('click', () => {
        refreshBtn.querySelector('i').classList.add('fa-spin');
        refreshData().finally(() => {
            setTimeout(() => {
                refreshBtn.querySelector('i').classList.remove('fa-spin');
            }, 500);
        });
    });
}

function updateLastRefreshIndicator() {
    if (!state.lastRefresh) {
        state.lastRefresh = Date.now();
        return;
    }
    
    const now = Date.now();
    const elapsed = now - state.lastRefresh;
    const remaining = Math.max(0, state.refreshInterval - elapsed);
    const secondsRemaining = Math.ceil(remaining / 1000);
    
    const timerEl = document.getElementById('refresh-timer');
    if (timerEl) {
        timerEl.textContent = `${secondsRemaining}s`;
    }
    
    const indicatorEl = document.getElementById('auto-refresh-indicator');
    if (indicatorEl) {
        indicatorEl.title = `Auto-refresh every ${state.refreshInterval / 1000}s | Next in ${secondsRemaining}s`;
    }
}

function setupButtons() {
    const startBtn = document.getElementById('btn-start-agents');
    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            try {
                // visual feedback
                startBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Starting...';
                startBtn.disabled = true;

                const res = await fetch(API.start, { method: 'POST' });
                const data = await res.json();

                setTimeout(() => {
                    startBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start All Agents';
                    startBtn.disabled = false;
                    alert('Command sent. Please allow 10-20 seconds for system startup.');
                    refreshStatus();
                }, 3000);
            } catch (e) {
                console.error(e);
                alert('Failed to start system');
                startBtn.disabled = false;
            }
        });
    }

    const stopBtn = document.getElementById('btn-stop-agents');
    if (stopBtn) {
        stopBtn.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to stop the entire system?')) return;

            try {
                stopBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Stopping...';
                stopBtn.disabled = true;

                await fetch(API.stop, { method: 'POST' });

                setTimeout(() => {
                    stopBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop All';
                    stopBtn.disabled = false;
                    refreshStatus();
                }, 2000);
            } catch (e) {
                console.error('Stop failed', e);
                alert('Failed to stop system');
                stopBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop All';
                stopBtn.disabled = false;
            }
        });
    }

    // Individual Agent Controls
    setupAgentControls();

    // Time Range Selector
    const timeButtons = document.querySelectorAll('.time-selector button');
    timeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            timeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.timeRange = parseInt(btn.dataset.hours);
            loadMetrics(); // Reload with new time range
        });
    });

    // Webhook Test Button
    const webhookTestBtn = document.getElementById('btn-test-webhook');
    if (webhookTestBtn) {
        webhookTestBtn.addEventListener('click', async () => {
            try {
                webhookTestBtn.disabled = true;
                webhookTestBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending...';

                const res = await fetch(API.webhookTest, { method: 'POST' });
                const data = await res.json();

                if (res.ok) {
                    alert('✅ Test notification sent! Check your Teams channel.');
                } else {
                    alert(`❌ ${data.detail || 'Webhook test failed'}`);
                }
            } catch (e) {
                alert('❌ Error: ' + e.message);
            } finally {
                webhookTestBtn.disabled = false;
                webhookTestBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Test Notification';
            }
        });
    }
}

// Load available APs for scenario dropdowns
async function loadAvailableAPs() {
    try {
        const res = await fetch(API.scenariosAps);
        if (!res.ok) {
            console.error('Failed to fetch APs:', res.status);
            return;
        }
        
        const aps = await res.json();
        console.log('Loaded APs:', aps);

        const failSelect = document.getElementById('select-fail-ap');
        const recoverSelect = document.getElementById('select-recover-ap');

        if (!failSelect || !recoverSelect) {
            console.error('Dropdown elements not found');
            return;
        }

        // Clear existing options except the first placeholder
        failSelect.innerHTML = '<option value="">-- Select AP --</option>';
        recoverSelect.innerHTML = '<option value="">-- Select AP --</option>';

        // Add AP options
        aps.forEach(ap => {
            const option1 = document.createElement('option');
            option1.value = ap.serial;
            option1.textContent = `${ap.name} (${ap.serial})`;
            failSelect.appendChild(option1);

            const option2 = document.createElement('option');
            option2.value = ap.serial;
            option2.textContent = `${ap.name} (${ap.serial})`;
            recoverSelect.appendChild(option2);
        });
        
        console.log('APs loaded into dropdowns');
    } catch (e) {
        console.error('Failed to load APs:', e);
    }
}

async function setupScenarioControls() {
    // Load available APs initially
    await loadAvailableAPs();

    // Fail AP button
    const failBtn = document.getElementById('btn-fail-ap');
    if (failBtn) {
        failBtn.addEventListener('click', async () => {
            const select = document.getElementById('select-fail-ap');
            const apSerial = select.value;
            const statusDiv = document.getElementById('fail-ap-status');

            if (!apSerial) {
                statusDiv.textContent = '⚠️ Please select an AP';
                statusDiv.style.color = 'var(--warning)';
                return;
            }

            const apName = select.options[select.selectedIndex].text;

            if (!confirm(`Confirm: Simulate failure for ${apName}?\n\nThis will set critical failure metrics for this AP.`)) {
                return;
            }

            try {
                failBtn.disabled = true;
                failBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Applying...';
                statusDiv.textContent = 'Applying failure scenario...';
                statusDiv.style.color = 'var(--text-muted)';

                const res = await fetch(API.scenarioFailAp, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ap_serial: apSerial })
                });

                const data = await res.json();

                if (res.ok) {
                    statusDiv.textContent = `✅ ${data.message}`;
                    statusDiv.style.color = 'var(--success)';
                    alert(`Success! ${data.ap_name} failure scenario applied.\n\nAgents will detect the failure shortly.`);
                    // Refresh data to show updated metrics
                    setTimeout(refreshData, 2000);
                } else {
                    statusDiv.textContent = `❌ ${data.detail || 'Failed'}`;
                    statusDiv.style.color = 'var(--danger)';
                }
            } catch (e) {
                console.error(e);
                statusDiv.textContent = '❌ Error: ' + e.message;
                statusDiv.style.color = 'var(--danger)';
            } finally {
                failBtn.disabled = false;
                failBtn.innerHTML = '<i class="fa-solid fa-exclamation-circle"></i> Simulate Failure';
            }
        });
    }

    // Recover AP button
    const recoverBtn = document.getElementById('btn-recover-ap');
    if (recoverBtn) {
        recoverBtn.addEventListener('click', async () => {
            const select = document.getElementById('select-recover-ap');
            const apSerial = select.value;
            const statusDiv = document.getElementById('recover-ap-status');

            if (!apSerial) {
                statusDiv.textContent = '⚠️ Please select an AP';
                statusDiv.style.color = 'var(--warning)';
                return;
            }

            const apName = select.options[select.selectedIndex].text;

            if (!confirm(`Confirm: Restore ${apName} to healthy state?\n\nThis will set excellent healthy metrics for this AP.`)) {
                return;
            }

            try {
                recoverBtn.disabled = true;
                recoverBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Restoring...';
                statusDiv.textContent = 'Applying recovery scenario...';
                statusDiv.style.color = 'var(--text-muted)';

                const res = await fetch(API.scenarioRecoverAp, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ap_serial: apSerial })
                });

                const data = await res.json();

                if (res.ok) {
                    statusDiv.textContent = `✅ ${data.message}`;
                    statusDiv.style.color = 'var(--success)';
                    alert(`Success! ${data.ap_name} restored to healthy state.\n\nAgents will detect the recovery shortly.`);
                    // Refresh data to show updated metrics
                    setTimeout(refreshData, 2000);
                } else {
                    statusDiv.textContent = `❌ ${data.detail || 'Failed'}`;
                    statusDiv.style.color = 'var(--danger)';
                }
            } catch (e) {
                console.error(e);
                statusDiv.textContent = '❌ Error: ' + e.message;
                statusDiv.style.color = 'var(--danger)';
            } finally {
                recoverBtn.disabled = false;
                recoverBtn.innerHTML = '<i class="fa-solid fa-heart"></i> Restore to Healthy';
            }
        });
    }
}

async function refreshData() {
    state.lastRefresh = Date.now();
    
    await refreshStatus();

    // Always load metrics and chat regardless of system status
    await Promise.all([
        loadMetrics(),
        loadChat()
    ]);
}

async function refreshStatus() {
    try {
        const res = await fetch(API.status);
        const data = await res.json();

        // Logic: specific check for each
        updateBadge('status-agent1', data.agent1);
        updateBadge('status-agent2', data.agent2);
        updateBadge('status-agent3', data.agent3);

        // Count running agents
        const runningCount = [data.agent1, data.agent2, data.agent3].filter(s => s === 'running').length;
        const phoenixRunning = data.phoenix === 'running';
        const allRunning = runningCount === 3;

        // Update "All Agents" badge
        const allAgentsBadge = document.getElementById('status-all-agents');
        if (allAgentsBadge) {
            if (allRunning) {
                allAgentsBadge.textContent = '3/3 Running';
                allAgentsBadge.className = 'badge running';
            } else if (runningCount === 0) {
                allAgentsBadge.textContent = '0/3 Stopped';
                allAgentsBadge.className = 'badge stopped';
            } else {
                allAgentsBadge.textContent = `${runningCount}/3 Running`;
                allAgentsBadge.className = 'badge partial';
            }
        }

        // Update Phoenix status
        const phoenixBadge = document.getElementById('phoenix-status');
        if (phoenixBadge) {
            if (phoenixRunning) {
                phoenixBadge.textContent = 'Running';
                phoenixBadge.className = 'badge running';
            } else {
                phoenixBadge.textContent = 'Stopped';
                phoenixBadge.className = 'badge stopped';
            }
        }

        state.systemStatus = allRunning ? 'running' : (runningCount === 0 ? 'stopped' : 'partial');

        const statusEl = document.getElementById('metrics-system-status');
        if (allRunning && phoenixRunning) {
            statusEl.textContent = 'HEALTHY';
            statusEl.className = 'value text-success';
        } else if (state.systemStatus === 'stopped') {
            statusEl.textContent = 'OFFLINE';
            statusEl.className = 'value text-muted';
        } else {
            statusEl.textContent = 'DEGRADED';
            statusEl.className = 'value text-warning';
        }

        // Check webhook status
        try {
            const webhookRes = await fetch(API.webhook);
            const webhookData = await webhookRes.json();
            const webhookBadge = document.getElementById('webhook-status');
            if (webhookBadge) {
                if (webhookData.configured) {
                    webhookBadge.textContent = 'Configured';
                    webhookBadge.className = 'badge running';
                } else {
                    webhookBadge.textContent = 'Not Configured';
                    webhookBadge.className = 'badge stopped';
                }
            }
        } catch (e) {
            console.warn('Webhook status check failed', e);
        }

    } catch (e) {
        console.warn('Status check failed', e);
        state.systemStatus = 'stopped';
    }
}

function updateBadge(id, status) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = status.toUpperCase();
        el.className = `badge ${status}`;
    }
}

async function loadMetrics() {
    try {
        // Fetch current snapshot data
        const res = await fetch(API.risk);
        const data = await res.json();

        console.log('Risk data fetched:', data);

        const aps = Object.values(data);
        console.log('Total APs:', aps.length);
        
        if (aps.length === 0) {
            updateAPMetricsTable([]);
            return;
        }

        // Process current data
        let maxRisk = 0;
        const risks = [];
        const snrData = [];
        const latencyData = [];
        const jitterData = [];

        aps.forEach(ap => {
            const current = ap.current.risk_score;
            if (current > maxRisk) maxRisk = current;
            const name = ap.current.ap_name || ap.ap_serial.substring(0, 10);

            risks.push({ name, score: current });

            if (ap.current.metrics) {
                snrData.push({ name, value: ap.current.metrics.snr_db || 0 });
                latencyData.push({ name, value: ap.current.metrics.latency_ms || 0 });
                jitterData.push({ name, value: ap.current.metrics.jitter_ms || 0 });
            }
        });

        // Update AP Metrics Chart
        updateAPMetricsChart(aps);

        // Update KPIs
        document.getElementById('metrics-ap-count').textContent = aps.length;
        document.getElementById('metrics-max-risk').textContent = Math.round(maxRisk);

        const riskEl = document.getElementById('kpi-risk').querySelector('.value');
        riskEl.style.color = maxRisk > 50 ? 'var(--danger)' : (maxRisk > 25 ? 'var(--warning)' : 'var(--success)');

        // Update charts with current data
        updateCharts(risks, snrData, latencyData, jitterData);

    } catch (e) {
        console.error('Metrics load failed', e);
    }
}

function updateAPMetricsChart(aps) {
    console.log('=== updateAPMetricsChart START ===');
    console.log('Chart.js loaded?', typeof Chart !== 'undefined');
    
    const ctx = document.getElementById('apMetricsChart');
    
    console.log('Canvas element:', ctx);
    console.log('Canvas context available?', ctx ? ctx.getContext('2d') : 'NO');
    console.log('Number of APs:', aps.length);
    
    if (!ctx) {
        console.error('❌ apMetricsChart canvas element not found!');
        return;
    }
    
    if (aps.length === 0) {
        console.warn('⚠️ No APs to display');
        return;
    }
    
    // Prepare data
    const labels = [];
    const latencyData = [];
    const jitterData = [];
    const snrData = [];
    
    aps.forEach((ap, index) => {
        const current = ap.current;
        const metrics = current.metrics || {};
        const apName = current.ap_name || ap.ap_serial.substring(0, 12);
        
        console.log(`AP ${index + 1}: ${apName}`, metrics);
        
        labels.push(apName);
        latencyData.push(metrics.latency_ms || 0);
        jitterData.push(metrics.jitter_ms || 0);
        snrData.push(metrics.snr_db || 0);
    });
    
    console.log('Chart data prepared:', { labels, latencyData, jitterData, snrData });
    
    // Create or update chart
    if (!state.charts.apMetrics) {
        console.log('📊 Creating new AP Metrics chart...');
        state.charts.apMetrics = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Latency (ms)',
                        data: latencyData,
                        backgroundColor: 'rgba(0, 242, 255, 0.6)',
                        borderColor: 'rgba(0, 242, 255, 1)',
                        borderWidth: 1,
                        yAxisID: 'y',
                    },
                    {
                        label: 'Jitter (ms)',
                        data: jitterData,
                        backgroundColor: 'rgba(245, 158, 11, 0.6)',
                        borderColor: 'rgba(245, 158, 11, 1)',
                        borderWidth: 1,
                        yAxisID: 'y',
                    },
                    {
                        label: 'SNR (dB)',
                        data: snrData,
                        backgroundColor: 'rgba(0, 217, 126, 0.6)',
                        borderColor: 'rgba(0, 217, 126, 1)',
                        borderWidth: 1,
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#e2e8f0',
                            font: {
                                size: 12
                            },
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(13, 15, 23, 0.9)',
                        titleColor: '#00f2ff',
                        bodyColor: '#e2e8f0',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += context.parsed.y.toFixed(1);
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Latency & Jitter (ms)',
                            color: '#94a3b8'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'SNR (dB)',
                            color: '#94a3b8'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
        console.log('✅ AP Metrics chart created successfully');
    } else {
        console.log('🔄 Updating existing AP Metrics chart...');
        // Update existing chart
        state.charts.apMetrics.data.labels = labels;
        state.charts.apMetrics.data.datasets[0].data = latencyData;
        state.charts.apMetrics.data.datasets[1].data = jitterData;
        state.charts.apMetrics.data.datasets[2].data = snrData;
        state.charts.apMetrics.update();
        console.log('✅ AP Metrics chart updated');
    }
    console.log('=== updateAPMetricsChart END ===');
}

function updateAPMetricsTable(aps) {
    const tbody = document.getElementById('ap-metrics-body');
    
    console.log('updateAPMetricsTable called with', aps.length, 'APs');
    
    if (!tbody) {
        console.error('ap-metrics-body element not found!');
        return;
    }
    
    if (aps.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No AP data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    aps.forEach(ap => {
        const current = ap.current;
        const metrics = current.metrics || {};
        const riskScore = current.risk_score || 0;
        const apName = current.ap_name || ap.ap_serial;
        
        // Determine status
        let statusClass, statusText;
        if (riskScore >= 60) {
            statusClass = 'ap-status-critical';
            statusText = 'Critical';
        } else if (riskScore >= 25) {
            statusClass = 'ap-status-warning';
            statusText = 'Warning';
        } else {
            statusClass = 'ap-status-healthy';
            statusText = 'Healthy';
        }
        
        // Color code metrics
        const latency = metrics.latency_ms || 0;
        const jitter = metrics.jitter_ms || 0;
        const snr = metrics.snr_db || 0;
        const retrans = metrics.retrans_per_min || 0;
        
        const latencyClass = latency > 100 ? 'metric-critical' : (latency > 50 ? 'metric-warning' : 'metric-good');
        const jitterClass = jitter > 20 ? 'metric-critical' : (jitter > 10 ? 'metric-warning' : 'metric-good');
        const snrClass = snr < 15 ? 'metric-critical' : (snr < 25 ? 'metric-warning' : 'metric-good');
        const retransClass = retrans > 30 ? 'metric-critical' : (retrans > 15 ? 'metric-warning' : 'metric-good');
        
        const row = document.createElement('tr');
        row.title = `Serial: ${ap.ap_serial}\nRisk Score: ${riskScore.toFixed(1)}\nLast Updated: ${current.timestamp}`;
        row.innerHTML = `
            <td><strong>${apName}</strong></td>
            <td><span class="metric-value ${latencyClass}">${latency.toFixed(1)}</span></td>
            <td><span class="metric-value ${jitterClass}">${jitter.toFixed(1)}</span></td>
            <td><span class="metric-value ${snrClass}">${snr.toFixed(1)}</span></td>
            <td><span class="metric-value">${metrics.client_count || 0}</span></td>
            <td><span class="metric-value ${retransClass}">${retrans.toFixed(1)}</span></td>
            <td><span class="ap-status-badge ${statusClass}">${statusText}</span></td>
        `;
        
        tbody.appendChild(row);
    });
}

function updateCharts(risks, snrData, latencyData, jitterData) {
    console.log('Updating charts with risks:', risks);

    // 1. Top Chart - Line showing risk overview
    const ctxTrend = document.getElementById('trendChart');
    if (!state.charts.trend) {
        state.charts.trend = new Chart(ctxTrend, {
            type: 'line',
            data: {
                labels: risks.map(r => r.name),
                datasets: [{
                    label: 'Risk Score',
                    data: risks.map(r => r.score),
                    borderColor: '#00f2ff',
                    backgroundColor: '#00f2ff30',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.1)' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    } else {
        state.charts.trend.data.labels = risks.map(r => r.name);
        state.charts.trend.data.datasets[0].data = risks.map(r => r.score);
        state.charts.trend.update();
    }

    // 2. Line Chart - Current Risk Scores (Wave format)
    const ctxRisk = document.getElementById('riskChart');

    if (!state.charts.risk) {
        state.charts.risk = new Chart(ctxRisk, {
            type: 'line',
            data: {
                labels: risks.map(r => r.name),
                datasets: [{
                    label: 'Risk Score',
                    data: risks.map(r => r.score),
                    borderColor: 'rgba(0, 242, 255, 1)',
                    backgroundColor: 'rgba(0, 242, 255, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4, // Smooth curve
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: risks.map(r => {
                        if (r.score >= 60) return '#ef4444';
                        if (r.score >= 25) return '#f59e0b';
                        return '#00d97e';
                    }),
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: { 
                        beginAtZero: true, 
                        max: 100, 
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: { 
                        grid: { display: false }, 
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: { 
                    legend: { 
                        display: true,
                        labels: {
                            color: '#e2e8f0',
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(13, 15, 23, 0.9)',
                        titleColor: '#00f2ff',
                        bodyColor: '#e2e8f0',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12
                    }
                }
            }
        });
    } else {
        state.charts.risk.data.labels = risks.map(r => r.name);
        state.charts.risk.data.datasets[0].data = risks.map(r => r.score);
        state.charts.risk.data.datasets[0].pointBackgroundColor = risks.map(r => {
            if (r.score >= 60) return '#ef4444';
            if (r.score >= 25) return '#f59e0b';
            return '#00d97e';
        });
        state.charts.risk.update();
    }

    // 3. Pie Chart
    const ctxDist = document.getElementById('distributionChart');
    const safe = risks.filter(r => r.score < 30).length;
    const warn = risks.filter(r => r.score >= 30 && r.score < 60).length;
    const critical = risks.filter(r => r.score >= 60).length;

    if (!state.charts.dist) {
        state.charts.dist = new Chart(ctxDist, {
            type: 'doughnut',
            data: {
                labels: ['Stable', 'Warning', 'Critical'],
                datasets: [{
                    data: [safe, warn, critical],
                    backgroundColor: ['#00d97e', '#f59e0b', '#ef4444'],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#fff',
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 13 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#00f2ff',
                        bodyColor: '#fff'
                    }
                },
                cutout: '65%'
            }
        });
    } else {
        state.charts.dist.data.datasets[0].data = [safe, warn, critical];
        state.charts.dist.update();
    }
}

async function loadChat() {
    try {
        const res = await fetch(API.history);
        const data = await res.json();

        const container = document.getElementById('chat-feed-container');

        // Update "last checked" indicator every second
        let statusIndicator = document.getElementById('chat-status-indicator');
        if (!statusIndicator) {
            statusIndicator = document.createElement('div');
            statusIndicator.id = 'chat-status-indicator';
            statusIndicator.style.cssText = 'font-size: 11px; color: var(--text-secondary); padding: 4px 8px; text-align: right;';
            container.parentNode.insertBefore(statusIndicator, container);
        }
        statusIndicator.innerHTML = `<i class="fa-solid fa-sync fa-spin" style="color: var(--accent);"></i> Live • Last checked: ${new Date().toLocaleTimeString()} • ${data.length} entries`;

        // Update tab badge with latest analysis time
        const tabTime = document.getElementById('analysis-tab-time');
        const headerStatus = document.getElementById('analysis-last-update');
        if (data.length > 0) {
            const latestEntry = [...data].reverse()[0];
            const latestTime = new Date(latestEntry.timestamp);
            const timeAgo = Math.round((Date.now() - latestTime.getTime()) / 1000);
            const timeAgoStr = timeAgo < 60 ? `${timeAgo}s ago` : `${Math.round(timeAgo/60)}m ago`;
            
            if (tabTime) tabTime.textContent = `(${timeAgoStr})`;
            if (headerStatus) headerStatus.textContent = `Last update: ${latestTime.toLocaleTimeString()} (${timeAgoStr})`;
        }

        // If data hasn't changed, don't rebuild DOM (optimization)
        if (state.lastChatLength === data.length) return;
        
        // NEW DATA - Flash notification!
        const isNewData = state.lastChatLength !== undefined && state.lastChatLength < data.length;
        state.lastChatLength = data.length;

        container.innerHTML = '';

        // Reverse to show latest first
        const sortedData = [...data].reverse();

        // 1. Highlight the Latest Analysis (Top 1)
        if (sortedData.length > 0) {
            const latest = sortedData[0];
            const div = document.createElement('div');
            div.className = 'chat-entry latest-entry' + (isNewData ? ' new-entry-flash' : '');
            div.innerHTML = renderChatEntry(latest, true);
            container.appendChild(div);
            
            // Flash effect for new data
            if (isNewData) {
                div.style.animation = 'flashNew 1s ease-out';
                // Also flash the tab
                const analysisTab = document.querySelector('[data-tab="analysis"]');
                if (analysisTab) {
                    analysisTab.style.animation = 'flashNew 1s ease-out';
                    setTimeout(() => analysisTab.style.animation = '', 1000);
                }
            }
        }

        // 2. Show History (Collapsed by default)
        if (sortedData.length > 1) {
            const historyContainer = document.createElement('div');
            historyContainer.id = 'history-container';
            historyContainer.style.display = 'none'; // Hidden by default

            const divider = document.createElement('div');
            divider.className = 'history-divider';
            // Click to toggle
            divider.innerHTML = '<span style="cursor:pointer">Show History <i class="fa-solid fa-chevron-down"></i></span>';
            divider.onclick = () => {
                const isHidden = historyContainer.style.display === 'none';
                historyContainer.style.display = isHidden ? 'block' : 'none';
                divider.innerHTML = isHidden ?
                    '<span style="cursor:pointer">Hide History <i class="fa-solid fa-chevron-up"></i></span>' :
                    '<span style="cursor:pointer">Show History <i class="fa-solid fa-chevron-down"></i></span>';
            };

            container.appendChild(divider);

            // Render older items into history container
            sortedData.slice(1).forEach(entry => {
                const div = document.createElement('div');
                div.className = 'chat-entry';
                div.innerHTML = renderChatEntry(entry, false);
                historyContainer.appendChild(div);
            });

            container.appendChild(historyContainer);
        }

    } catch (e) {
        console.error("Chat load failed", e);
    }
}

function renderChatEntry(entry, isLatest) {
    const date = new Date(entry.timestamp);
    const timeStr = date.toLocaleTimeString();

    // Use Marked.js for proper rendering
    let content = marked.parse(entry.analysis);

    return `
        <div class="chat-entry-header">
            <span class="chat-agent">
                <i class="fa-solid fa-robot"></i> System Analysis #${entry.iteration}
                ${isLatest ? '<span class="status-tag pulse-tag">LIVE</span>' : ''}
            </span>
            <span class="chat-timestamp">${timeStr}</span>
        </div>
        <div class="chat-content markdown-body">${content}</div>
    `;
}

// Individual Agent Controls
function setupAgentControls() {
    console.log('🔧 Setting up individual agent controls...');
    const agents = [1, 2, 3];
    
    agents.forEach(num => {
        const startBtn = document.getElementById(`btn-start-agent${num}`);
        const stopBtn = document.getElementById(`btn-stop-agent${num}`);
        
        console.log(`Agent ${num} - Start button found:`, !!startBtn, `Stop button found:`, !!stopBtn);
        
        if (startBtn) {
            console.log(`✅ Attaching click handler to start-agent${num}`);
            startBtn.addEventListener('click', async () => {
                console.log(`🚀 Start Agent ${num} clicked!`);
                try {
                    startBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                    startBtn.disabled = true;
                    
                    console.log(`   Making request to: /system/start-agent/${num}`);
                    const res = await fetch(`/system/start-agent/${num}`, { method: 'POST' });
                    const data = await res.json();
                    
                    console.log(`   Response:`, data);
                    
                    if (res.ok) {
                        console.log(`   ✅ Agent ${num} started successfully`);
                        alert(`✅ Agent ${num} started!\n\nPID: ${data.pid}\n\nA new console window should have opened.`);
                    } else {
                        console.error(`   ❌ Failed:`, data);
                        alert(`❌ Failed to start Agent ${num}:\n\n${data.detail || 'Unknown error'}`);
                    }
                    
                    setTimeout(() => {
                        startBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start';
                        startBtn.disabled = false;
                        refreshStatus();
                    }, 2000);
                } catch (e) {
                    console.error(`❌ Start Agent ${num} failed:`, e);
                    alert(`❌ Error starting Agent ${num}:\n\n${e.message}\n\nCheck browser console for details.`);
                    startBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start';
                    startBtn.disabled = false;
                }
            });
        } else {
            console.error(`❌ Start button for Agent ${num} NOT FOUND in HTML!`);
        }
        
        if (stopBtn) {
            console.log(`✅ Attaching click handler to stop-agent${num}`);
            stopBtn.addEventListener('click', async () => {
                console.log(`🛑 Stop Agent ${num} clicked!`);
                try {
                    stopBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                    stopBtn.disabled = true;
                    
                    const res = await fetch(`/system/stop-agent/${num}`, { method: 'POST' });
                    const data = await res.json();
                    
                    if (res.ok) {
                        console.log(`Agent ${num} stopped:`, data);
                    } else {
                        alert(`Failed to stop Agent ${num}: ${data.detail || 'Unknown error'}`);
                    }
                    
                    setTimeout(() => {
                        stopBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop';
                        stopBtn.disabled = false;
                        refreshStatus();
                    }, 1500);
                } catch (e) {
                    console.error(`Stop Agent ${num} failed:`, e);
                    alert(`Failed to stop Agent ${num}`);
                    stopBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop';
                    stopBtn.disabled = false;
                }
            });
        }
    });
}
