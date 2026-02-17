/**
 * AI Usage Dashboard - Modern JavaScript
 */

// Global state
let charts = {};
let currentPeriod = 'daily';
let selectedProvider = null;
let currentScreen = 'welcome';

// Provider icons mapping
const PROVIDER_ICONS = {
    openai: '🧠',
    claude: '💬',
    gemini: '✨',
    minimax: '⚡',
    zai: '🎯'
};

const PROVIDER_NAMES = {
    openai: 'OpenAI',
    claude: 'Claude',
    gemini: 'Gemini',
    minimax: 'Mini Max',
    zai: 'Z.ai'
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    checkStorageStatus();
});

// Check storage status
async function checkStorageStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.initialized) {
            showUnlockScreen();
        } else {
            showWelcomeScreen();
        }
    } catch (error) {
        console.error('Error checking status:', error);
        showToast('Error connecting to server', 'error');
    }
}

// Screen navigation
function showWelcomeScreen() {
    hideAllScreens();
    document.getElementById('welcome-screen').classList.remove('hidden');
    currentScreen = 'welcome';
}

function showUnlockScreen() {
    hideAllScreens();
    document.getElementById('unlock-screen').classList.remove('hidden');
    currentScreen = 'unlock';
}

function showDashboard() {
    hideAllScreens();
    document.getElementById('dashboard-screen').classList.remove('hidden');
    currentScreen = 'dashboard';
    loadDashboard();
}

function hideAllScreens() {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.add('hidden');
    });
}

// Setup storage
async function setupStorage() {
    const password = document.getElementById('master-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    if (!password) {
        showToast('Please enter a password', 'warning');
        return;
    }
    
    if (password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    if (password.length < 4) {
        showToast('Password must be at least 4 characters', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/initialize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Setup complete!', 'success');
            showDashboard();
        } else {
            showToast(data.error || 'Setup failed', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Unlock storage
async function unlockStorage() {
    const password = document.getElementById('unlock-password').value;
    
    if (!password) {
        showToast('Please enter your password', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/initialize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Welcome back!', 'success');
            document.getElementById('unlock-password').value = '';
            showDashboard();
        } else {
            const errorEl = document.getElementById('unlock-error');
            errorEl.textContent = 'Incorrect password';
            errorEl.classList.remove('hidden');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Load dashboard
async function loadDashboard() {
    showLoading();
    
    try {
        const response = await fetch(`/api/usage?period=${currentPeriod}`);
        const data = await response.json();
        
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }
        
        updateSummaryCards(data);
        updateCharts(data);
        updateProviderCards(data.providers);
        updateLastUpdateTime();
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showToast('Failed to load dashboard', 'error');
    } finally {
        hideLoading();
    }
}

// Update summary cards
function updateSummaryCards(data) {
    let totalTokens = 0;
    let totalRequests = 0;
    let totalCost = 0;
    let activeCount = 0;
    
    Object.values(data.providers).forEach(provider => {
        if (provider.status === 'success' && provider.data) {
            totalTokens += provider.data.total_tokens || 0;
            totalRequests += provider.data.total_requests || 0;
            totalCost += provider.data.total_cost || 0;
            activeCount++;
        }
    });
    
    document.getElementById('total-tokens').textContent = formatNumber(totalTokens);
    document.getElementById('total-requests').textContent = formatNumber(totalRequests);
    document.getElementById('total-cost').textContent = '$' + totalCost.toFixed(2);
    document.getElementById('active-providers').textContent = activeCount;
}

// Update charts
function updateCharts(data) {
    const providers = Object.entries(data.providers);
    
    const labels = [];
    const tokensData = [];
    const costData = [];
    const colors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];
    
    providers.forEach(([name, provider], index) => {
        if (provider.status === 'success' && provider.data) {
            labels.push(PROVIDER_NAMES[name] || name);
            tokensData.push(provider.data.total_tokens || 0);
            costData.push(provider.data.total_cost || 0);
        }
    });
    
    // Pie chart
    if (charts.pie) {
        charts.pie.destroy();
    }
    
    const pieCtx = document.getElementById('usage-pie-chart').getContext('2d');
    charts.pie = new Chart(pieCtx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: tokensData,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#a1a1aa',
                        padding: 20,
                        font: { size: 12 }
                    }
                }
            }
        }
    });
    
    // Bar chart
    if (charts.bar) {
        charts.bar.destroy();
    }
    
    const barCtx = document.getElementById('cost-bar-chart').getContext('2d');
    charts.bar = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Cost ($)',
                data: costData,
                backgroundColor: colors.slice(0, labels.length),
                borderRadius: 8,
                barThickness: 40
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#a1a1aa' }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: '#27272a' },
                    ticks: {
                        color: '#a1a1aa',
                        callback: value => '$' + value
                    }
                }
            }
        }
    });
}

// Update provider cards
function updateProviderCards(providers) {
    const container = document.getElementById('providers-grid');
    const emptyState = document.getElementById('empty-state');
    
    const providerEntries = Object.entries(providers);
    const hasProviders = providerEntries.length > 0;
    
    if (!hasProviders) {
        container.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }
    
    container.classList.remove('hidden');
    emptyState.classList.add('hidden');
    
    container.innerHTML = '';
    
    providerEntries.forEach(([name, provider], index) => {
        const card = createProviderCard(name, provider);
        container.appendChild(card);
    });
}

function createProviderCard(name, provider) {
    const card = document.createElement('div');
    card.className = 'provider-card';
    
    const status = provider.status === 'success' ? 'active' : 
                   provider.status === 'error' ? 'error' : 'inactive';
    
    const tokens = provider.data?.total_tokens || 0;
    const requests = provider.data?.total_requests || 0;
    const cost = provider.data?.total_cost || 0;
    const rateLimits = provider.rate_limits || {};
    const dailyLimit = rateLimits.requests_per_day || 1000;
    const progressPercent = Math.min((requests / dailyLimit) * 100, 100);
    
    const progressClass = progressPercent > 90 ? 'high' : 
                        progressPercent > 50 ? 'medium' : 'low';
    
    card.innerHTML = `
        <div class="provider-card-header">
            <div class="provider-info">
                <span class="provider-icon-large">${PROVIDER_ICONS[name] || '🔌'}</span>
                <div>
                    <div class="provider-name">${PROVIDER_NAMES[name] || name}</div>
                    <div class="provider-model">${rateLimits.requests_per_minute || 'N/A'} req/min</div>
                </div>
            </div>
            <span class="status-badge status-${status}">${status}</span>
        </div>
        
        <div class="provider-stats">
            <div class="provider-stat">
                <div class="provider-stat-value">${formatNumber(tokens)}</div>
                <div class="provider-stat-label">Tokens</div>
            </div>
            <div class="provider-stat">
                <div class="provider-stat-value">${formatNumber(requests)}</div>
                <div class="provider-stat-label">Requests</div>
            </div>
            <div class="provider-stat">
                <div class="provider-stat-value">$${cost.toFixed(4)}</div>
                <div class="provider-stat-label">Cost</div>
            </div>
            <div class="provider-stat">
                <div class="provider-stat-value">${formatNumber(dailyLimit)}</div>
                <div class="provider-stat-label">Limit</div>
            </div>
        </div>
        
        <div class="progress-container">
            <div class="progress-label">
                <span>Daily Limit</span>
                <span>${progressPercent.toFixed(0)}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill ${progressClass}" style="width: ${progressPercent}%"></div>
            </div>
        </div>
        
        <div class="provider-actions">
            <button class="btn-secondary" onclick="testProvider('${name}')">Test</button>
            <button class="btn-secondary" onclick="removeProvider('${name}')">Remove</button>
        </div>
        
        ${provider.error ? `<p class="error-text" style="margin-top: 8px; font-size: 0.8rem;">${provider.error}</p>` : ''}
        ${provider.data?.note ? `<p style="margin-top: 8px; font-size: 0.75rem; color: var(--text-tertiary);">${provider.data.note}</p>` : ''}
    `;
    
    return card;
}

// Change period
function changePeriod(period) {
    currentPeriod = period;
    
    document.querySelectorAll('.period-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.period === period);
    });
    
    loadDashboard();
}

// Update last update time
function updateLastUpdateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    document.getElementById('last-update-time').textContent = `Last updated: ${timeStr}`;
}

// Refresh all
async function refreshAll() {
    showToast('Refreshing...', 'success');
    await loadDashboard();
    showToast('Data refreshed', 'success');
}

// Settings
function openSettings() {
    loadApiKeysList();
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
}

// Add provider
function openAddProvider() {
    closeSettings();
    selectedProvider = null;
    document.getElementById('api-key-form').classList.add('hidden');
    document.querySelectorAll('.provider-select-card').forEach(card => {
        card.classList.remove('selected');
    });
    document.getElementById('add-provider-modal').classList.remove('hidden');
}

function closeAddProvider() {
    document.getElementById('add-provider-modal').classList.add('hidden');
    document.getElementById('api-key-input').value = '';
}

function selectProvider(provider) {
    selectedProvider = provider;
    
    document.querySelectorAll('.provider-select-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.provider === provider);
    });
    
    document.getElementById('selected-provider-name').textContent = PROVIDER_NAMES[provider] || provider;
    document.getElementById('api-key-form').classList.remove('hidden');
    document.getElementById('api-key-input').focus();
}

async function saveApiKey() {
    const apiKey = document.getElementById('api-key-input').value;
    
    if (!apiKey) {
        showToast('Please enter an API key', 'warning');
        return;
    }
    
    if (!selectedProvider) {
        showToast('Please select a provider', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`/api/keys/${selectedProvider}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`${PROVIDER_NAMES[selectedProvider]} API key saved`, 'success');
            closeAddProvider();
            loadDashboard();
        } else {
            showToast(data.error || 'Failed to save API key', 'error');
        }
    } catch (error) {
        showToast('Error saving API key', 'error');
    } finally {
        hideLoading();
    }
}

// Load API keys list
async function loadApiKeysList() {
    try {
        const response = await fetch('/api/keys');
        const data = await response.json();
        
        const container = document.getElementById('api-keys-list');
        
        if (data.count === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary);">No API keys configured</p>';
            return;
        }
        
        container.innerHTML = data.providers.map(provider => `
            <div class="api-key-item">
                <div class="api-key-item-info">
                    <span class="provider-icon-large">${PROVIDER_ICONS[provider] || '🔌'}</span>
                    <span class="api-key-item-name">${PROVIDER_NAMES[provider] || provider}</span>
                </div>
                <span class="api-key-item-status">✓ Configured</span>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading keys:', error);
    }
}

// Test provider
async function testProvider(provider) {
    showLoading();
    
    try {
        const response = await fetch(`/api/test/${provider}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`${PROVIDER_NAMES[provider] || provider} connected successfully!`, 'success');
        } else {
            showToast(`${provider} failed: ${data.error}`, 'error');
        }
    } catch (error) {
        showToast('Error testing connection', 'error');
    } finally {
        hideLoading();
    }
}

// Remove provider
async function removeProvider(provider) {
    if (!confirm(`Remove ${PROVIDER_NAMES[provider] || provider}?`)) {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`/api/keys/${provider}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`${PROVIDER_NAMES[provider] || provider} removed`, 'success');
            loadDashboard();
        }
    } catch (error) {
        showToast('Error removing provider', 'error');
    } finally {
        hideLoading();
    }
}

// Show/hide loading
function showLoading() {
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format numbers
function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

// Handle Enter key for password fields
document.getElementById('master-password')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') setupStorage();
});

document.getElementById('confirm-password')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') setupStorage();
});

document.getElementById('unlock-password')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') unlockStorage();
});

document.getElementById('api-key-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') saveApiKey();
});

// Auto-refresh every 5 minutes
setInterval(() => {
    if (currentScreen === 'dashboard') {
        loadDashboard();
    }
}, 300000);
