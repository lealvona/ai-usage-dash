/**
 * AI Usage Dashboard - JavaScript
 */

// Global state
let charts = {};
let currentPeriod = 'daily';
let autoRefreshInterval = null;

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // Check if already initialized
    checkStatus();
    
    // Setup auto-refresh
    setupAutoRefresh();
});

// Check application status
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.initialized) {
            showMainApp();
            loadDashboard();
            loadProviders();
        } else {
            showPasswordModal();
        }
    } catch (error) {
        console.error('Error checking status:', error);
        showNotification('Error connecting to server', 'error');
    }
}

// Initialize storage with password
async function initializeStorage() {
    const password = document.getElementById('master-password').value;
    const errorDiv = document.getElementById('password-error');
    
    if (!password) {
        errorDiv.textContent = 'Please enter a password';
        return;
    }
    
    try {
        const response = await fetch('/api/initialize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            hidePasswordModal();
            showMainApp();
            loadDashboard();
            loadProviders();
            showNotification('Welcome to AI Usage Dashboard!', 'success');
        } else {
            errorDiv.textContent = data.error || 'Failed to initialize';
        }
    } catch (error) {
        errorDiv.textContent = 'Error: ' + error.message;
    }
}

// Show/hide modals
function showPasswordModal() {
    document.getElementById('password-modal').classList.remove('hidden');
}

function hidePasswordModal() {
    document.getElementById('password-modal').classList.add('hidden');
}

function showMainApp() {
    document.getElementById('main-app').classList.remove('hidden');
}

function showSettings() {
    loadApiKeysList();
    document.getElementById('settings-modal').classList.remove('hidden');
}

function hideSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
}

// Tab switching
function switchTab(tabName) {
    // Update nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    document.getElementById(`${tabName}-tab`).classList.remove('hidden');
    
    // Load data for tab
    if (tabName === 'dashboard') {
        loadDashboard();
    } else if (tabName === 'providers') {
        loadProviders();
    }
}

// Period selection
function changePeriod(period) {
    currentPeriod = period;
    
    // Update buttons
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-period="${period}"]`).classList.add('active');
    
    loadDashboard();
}

// Load dashboard data
async function loadDashboard() {
    showLoading();
    
    try {
        const response = await fetch(`/api/usage?period=${currentPeriod}`);
        const data = await response.json();
        
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        
        updateSummaryCards(data);
        updateCharts(data);
        updateProviderCards(data.providers);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
    } finally {
        hideLoading();
    }
}

// Update summary cards
function updateSummaryCards(data) {
    let totalTokens = 0;
    let totalRequests = 0;
    let totalCost = 0;
    
    Object.values(data.providers).forEach(provider => {
        if (provider.status === 'success' && provider.data) {
            totalTokens += provider.data.total_tokens || 0;
            totalRequests += provider.data.total_requests || 0;
            totalCost += provider.data.total_cost || 0;
        }
    });
    
    document.getElementById('total-tokens').textContent = formatNumber(totalTokens);
    document.getElementById('total-requests').textContent = formatNumber(totalRequests);
    document.getElementById('total-cost').textContent = '$' + totalCost.toFixed(2);
    document.getElementById('active-providers').textContent = Object.keys(data.providers).length;
}

// Update charts
function updateCharts(data) {
    const providers = Object.entries(data.providers);
    
    // Pie chart data
    const pieLabels = [];
    const pieData = [];
    const pieColors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];
    
    providers.forEach(([name, provider], index) => {
        if (provider.status === 'success' && provider.data) {
            pieLabels.push(name.charAt(0).toUpperCase() + name.slice(1));
            pieData.push(provider.data.total_tokens || 0);
        }
    });
    
    // Update or create pie chart
    if (charts.pie) {
        charts.pie.data.labels = pieLabels;
        charts.pie.data.datasets[0].data = pieData;
        charts.pie.update();
    } else {
        const pieCtx = document.getElementById('usage-pie-chart').getContext('2d');
        charts.pie = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: pieLabels,
                datasets: [{
                    data: pieData,
                    backgroundColor: pieColors.slice(0, pieLabels.length),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Bar chart data
    const barLabels = [];
    const barData = [];
    
    providers.forEach(([name, provider]) => {
        if (provider.status === 'success' && provider.data) {
            barLabels.push(name.charAt(0).toUpperCase() + name.slice(1));
            barData.push(provider.data.total_cost || 0);
        }
    });
    
    // Update or create bar chart
    if (charts.bar) {
        charts.bar.data.labels = barLabels;
        charts.bar.data.datasets[0].data = barData;
        charts.bar.update();
    } else {
        const barCtx = document.getElementById('cost-bar-chart').getContext('2d');
        charts.bar = new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: barLabels,
                datasets: [{
                    label: 'Cost ($)',
                    data: barData,
                    backgroundColor: pieColors.slice(0, barLabels.length),
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => '$' + value
                        }
                    }
                }
            }
        });
    }
}

// Update provider cards
function updateProviderCards(providers) {
    const container = document.getElementById('provider-cards');
    container.innerHTML = '';
    
    Object.entries(providers).forEach(([name, provider]) => {
        const card = document.createElement('div');
        card.className = 'provider-card';
        
        const status = provider.status === 'success' ? 'active' : 
                      provider.status === 'error' ? 'error' : 'inactive';
        
        const tokens = provider.data?.total_tokens || 0;
        const requests = provider.data?.total_requests || 0;
        const cost = provider.data?.total_cost || 0;
        
        // Calculate progress percentage
        const rateLimits = provider.rate_limits || {};
        const dailyLimit = rateLimits.requests_per_day || 1000;
        const progressPercent = Math.min((requests / dailyLimit) * 100, 100);
        
        const progressClass = progressPercent > 90 ? 'critical' : 
                            progressPercent > 70 ? 'warning' : 'ok';
        
        card.innerHTML = `
            <div class="provider-header">
                <span class="provider-name">${name.charAt(0).toUpperCase() + name.slice(1)}</span>
                <span class="provider-status status-${status}">${status}</span>
            </div>
            <div class="provider-stats">
                <div class="stat-item">
                    <div class="stat-label">Tokens</div>
                    <div class="stat-value">${formatNumber(tokens)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Requests</div>
                    <div class="stat-value">${formatNumber(requests)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Cost</div>
                    <div class="stat-value">$${cost.toFixed(4)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Rate Limit</div>
                    <div class="stat-value">${formatNumber(dailyLimit)}</div>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill ${progressClass}" style="width: ${progressPercent}%"></div>
            </div>
            ${provider.data?.note ? `<p class="stat-label" style="margin-top: 0.5rem; font-style: italic;">${provider.data.note}</p>` : ''}
            ${provider.error ? `<p class="error-message">${provider.error}</p>` : ''}
        `;
        
        container.appendChild(card);
    });
}

// Load providers list
async function loadProviders() {
    try {
        const response = await fetch('/api/providers');
        const data = await response.json();
        
        const container = document.getElementById('providers-grid');
        container.innerHTML = '';
        
        data.providers.forEach(provider => {
            const card = document.createElement('div');
            card.className = 'provider-config-card';
            
            card.innerHTML = `
                <div class="provider-config-header">
                    <h3>${provider.display_name}</h3>
                    <span class="key-status ${provider.has_key ? 'configured' : 'not-configured'}">
                        ${provider.has_key ? '✓ Configured' : '○ Not configured'}
                    </span>
                </div>
                <p class="stat-label">Status: ${provider.status}</p>
                <div class="provider-actions">
                    ${provider.has_key ? `
                        <button onclick="testProvider('${provider.name}')" class="btn-secondary">Test</button>
                        <button onclick="removeApiKey('${provider.name}')" class="btn-danger">Remove</button>
                    ` : `
                        <button onclick="showAddKeyForProvider('${provider.name}')" class="btn-primary">Add Key</button>
                    `}
                </div>
            `;
            
            container.appendChild(card);
        });
        
    } catch (error) {
        console.error('Error loading providers:', error);
    }
}

// Load API keys list in settings
async function loadApiKeysList() {
    try {
        const response = await fetch('/api/keys');
        const data = await response.json();
        
        const container = document.getElementById('api-keys-list');
        
        if (data.count === 0) {
            container.innerHTML = '<p class="stat-label">No API keys configured</p>';
            return;
        }
        
        container.innerHTML = data.providers.map(provider => `
            <div class="provider-key-item">
                <span>${provider.charAt(0).toUpperCase() + provider.slice(1)}</span>
                <span class="key-status configured">✓ Configured</span>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading keys list:', error);
    }
}

// Add API key
async function addApiKey() {
    const provider = document.getElementById('provider-select').value;
    const apiKey = document.getElementById('new-api-key').value;
    
    if (!apiKey) {
        showNotification('Please enter an API key', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/keys/${provider}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`${provider} API key saved`, 'success');
            document.getElementById('new-api-key').value = '';
            loadProviders();
            loadDashboard();
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        showNotification('Error saving API key', 'error');
    }
}

// Remove API key
async function removeApiKey(provider) {
    if (!confirm(`Remove API key for ${provider}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/keys/${provider}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`${provider} API key removed`, 'success');
            loadProviders();
            loadDashboard();
        }
    } catch (error) {
        showNotification('Error removing API key', 'error');
    }
}

// Test provider connection
async function testProvider(provider) {
    showLoading();
    
    try {
        const response = await fetch(`/api/test/${provider}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`${provider} connection successful!`, 'success');
        } else {
            showNotification(`${provider} failed: ${data.error}`, 'error');
        }
    } catch (error) {
        showNotification('Error testing connection', 'error');
    } finally {
        hideLoading();
    }
}

// Show add key for specific provider
function showAddKeyForProvider(provider) {
    document.getElementById('provider-select').value = provider;
    showSettings();
}

// Refresh data
async function refreshData() {
    try {
        await fetch('/api/refresh', { method: 'POST' });
        loadDashboard();
        showNotification('Data refreshed', 'success');
    } catch (error) {
        showNotification('Error refreshing data', 'error');
    }
}

// Auto refresh setup
function setupAutoRefresh() {
    // Refresh every 5 minutes
    autoRefreshInterval = setInterval(() => {
        if (document.getElementById('main-app').classList.contains('hidden') === false) {
            loadDashboard();
        }
    }, 300000);
}

// Show/hide loading
function showLoading() {
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    const messageSpan = document.getElementById('notification-message');
    
    notification.className = `notification ${type}`;
    messageSpan.textContent = message;
    notification.classList.remove('hidden');
    
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}

// Format numbers
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Handle password modal enter key
document.getElementById('master-password').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        initializeStorage();
    }
});
