/**
 * Maintenance 4.0 Dashboard - JavaScript Application
 */

const API_BASE = '/api/v1';

// ============================
// State Management
// ============================

const state = {
    sites: [],
    alerts: [],
    workorders: [],
    currentPage: 'overview'
};

// ============================
// Utility Functions
// ============================

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function updateCurrentTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        return null;
    }
}

async function patchAPI(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Patch Error (${endpoint}):`, error);
        return null;
    }
}

// ============================
// API Status Check
// ============================

async function checkAPIStatus() {
    try {
        const response = await fetch('/health');
        const statusDot = document.getElementById('api-status');
        const statusText = document.getElementById('api-status-text');
        
        if (response.ok) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Connecté';
        } else {
            throw new Error('API not responding');
        }
    } catch (error) {
        const statusDot = document.getElementById('api-status');
        const statusText = document.getElementById('api-status-text');
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Déconnecté';
    }
}

// ============================
// Data Loading Functions
// ============================

async function loadSites() {
    const sites = await fetchAPI('/sites');
    if (sites) {
        state.sites = sites;
        renderSites();
        document.getElementById('kpi-sites').textContent = sites.length;
        
        // Count total assets
        let totalAssets = 0;
        for (const site of sites) {
            const assets = await fetchAPI(`/sites/${site.id}/assets`);
            if (assets) totalAssets += assets.length;
        }
        document.getElementById('kpi-assets').textContent = totalAssets;
    }
}

async function loadAlerts() {
    const alerts = await fetchAPI('/alerts');
    if (alerts) {
        state.alerts = alerts;
        renderAlerts();
        
        const openAlerts = alerts.filter(a => a.status === 'open');
        document.getElementById('kpi-alerts').textContent = openAlerts.length;
        document.getElementById('alerts-badge').textContent = openAlerts.length;
    }
}

async function loadWorkOrders() {
    const workorders = await fetchAPI('/workorders');
    if (workorders) {
        state.workorders = workorders;
        renderWorkOrders();
        
        const activeWO = workorders.filter(w => w.status === 'open' || w.status === 'in_progress');
        document.getElementById('kpi-workorders').textContent = activeWO.length;
    }
}

// ============================
// Render Functions
// ============================

function renderSites() {
    const sitesListEl = document.getElementById('sites-list');
    const allSitesEl = document.getElementById('all-sites');
    
    if (state.sites.length === 0) {
        const emptyHtml = `
            <div class="empty-state">
                <i class="fas fa-building"></i>
                <p>Aucun site trouvé</p>
            </div>
        `;
        sitesListEl.innerHTML = emptyHtml;
        allSitesEl.innerHTML = emptyHtml;
        return;
    }
    
    const html = state.sites.map(site => `
        <div class="site-card" onclick="showSiteDetails(${site.id})">
            <div class="site-code">${site.code}</div>
            <div class="site-name">${site.name}</div>
            <div class="site-stats">
                <span class="stat-danger">
                    <i class="fas fa-exclamation-circle"></i>
                    ${site.high_alerts || 0} critiques
                </span>
                <span class="stat-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    ${site.medium_alerts || 0} moyennes
                </span>
            </div>
        </div>
    `).join('');
    
    sitesListEl.innerHTML = html;
    allSitesEl.innerHTML = html;
}

function renderAlerts() {
    // Recent alerts (overview)
    const recentEl = document.getElementById('recent-alerts');
    const openAlerts = state.alerts.filter(a => a.status === 'open').slice(0, 5);
    
    if (openAlerts.length === 0) {
        recentEl.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-check-circle"></i>
                <p>Aucune alerte ouverte</p>
            </div>
        `;
    } else {
        recentEl.innerHTML = openAlerts.map(alert => `
            <div class="alert-item">
                <div class="alert-severity ${alert.severity.toLowerCase()}">
                    <i class="fas fa-exclamation"></i>
                </div>
                <div class="alert-content">
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-meta">
                        <i class="fas fa-clock"></i> ${formatDate(alert.triggered_at)}
                        ${alert.asset_code ? `<span style="margin-left: 12px;"><i class="fas fa-cog"></i> ${alert.asset_code}</span>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    // Alerts table
    renderAlertsTable();
}

function renderAlertsTable() {
    const tbody = document.getElementById('alerts-table-body');
    const statusFilter = document.getElementById('alert-status-filter').value;
    const severityFilter = document.getElementById('alert-severity-filter').value;
    
    let filteredAlerts = state.alerts;
    if (statusFilter) filteredAlerts = filteredAlerts.filter(a => a.status === statusFilter);
    if (severityFilter) filteredAlerts = filteredAlerts.filter(a => a.severity === severityFilter);
    
    if (filteredAlerts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>Aucune alerte trouvée</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = filteredAlerts.map(alert => `
        <tr>
            <td>#${alert.id}</td>
            <td><span class="severity-badge ${alert.severity.toLowerCase()}">${getSeverityLabel(alert.severity)}</span></td>
            <td>${alert.asset_code || '-'}</td>
            <td>${alert.message}</td>
            <td>${formatDate(alert.triggered_at)}</td>
            <td><span class="status-badge ${alert.status}">${getStatusLabel(alert.status)}</span></td>
            <td>
                ${alert.status === 'open' ? 
                    `<button class="action-btn primary" onclick="acknowledgeAlert(${alert.id})">Acquitter</button>` : 
                    ''
                }
                ${alert.status === 'ack' ? 
                    `<button class="action-btn secondary" onclick="closeAlert(${alert.id})">Fermer</button>` : 
                    ''
                }
            </td>
        </tr>
    `).join('');
}

function renderWorkOrders() {
    const tbody = document.getElementById('workorders-table-body');
    const statusFilter = document.getElementById('wo-status-filter').value;
    
    let filteredWO = state.workorders;
    if (statusFilter) filteredWO = filteredWO.filter(w => w.status === statusFilter);
    
    if (filteredWO.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    <i class="fas fa-clipboard-check"></i>
                    <p>Aucun ordre de travail trouvé</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = filteredWO.map(wo => `
        <tr>
            <td>#${wo.id}</td>
            <td><span class="priority-badge ${wo.priority.toLowerCase()}">${getPriorityLabel(wo.priority)}</span></td>
            <td>#${wo.alert_id}</td>
            <td>${wo.assigned_to || '<em>Non assigné</em>'}</td>
            <td>${formatDate(wo.created_at)}</td>
            <td><span class="status-badge ${wo.status}">${getWOStatusLabel(wo.status)}</span></td>
            <td>
                ${wo.status === 'open' ? 
                    `<button class="action-btn primary" onclick="startWorkOrder(${wo.id})">Démarrer</button>` : 
                    ''
                }
                ${wo.status === 'in_progress' ? 
                    `<button class="action-btn secondary" onclick="completeWorkOrder(${wo.id})">Terminer</button>` : 
                    ''
                }
            </td>
        </tr>
    `).join('');
}

// ============================
// Label Helpers
// ============================

function getSeverityLabel(severity) {
    const labels = { HIGH: 'Critique', MEDIUM: 'Moyenne', LOW: 'Faible' };
    return labels[severity] || severity;
}

function getStatusLabel(status) {
    const labels = { open: 'Ouverte', ack: 'Acquittée', closed: 'Fermée' };
    return labels[status] || status;
}

function getWOStatusLabel(status) {
    const labels = { open: 'Ouvert', in_progress: 'En cours', done: 'Terminé', cancelled: 'Annulé' };
    return labels[status] || status;
}

function getPriorityLabel(priority) {
    const labels = { HIGH: 'Haute', MEDIUM: 'Moyenne', LOW: 'Basse' };
    return labels[priority] || priority;
}

// ============================
// Actions
// ============================

async function acknowledgeAlert(id) {
    const result = await patchAPI(`/alerts/${id}`, { status: 'ack' });
    if (result) {
        await loadAlerts();
    }
}

async function closeAlert(id) {
    const result = await patchAPI(`/alerts/${id}`, { status: 'closed' });
    if (result) {
        await loadAlerts();
    }
}

async function startWorkOrder(id) {
    const result = await patchAPI(`/workorders/${id}`, { status: 'in_progress' });
    if (result) {
        await loadWorkOrders();
    }
}

async function completeWorkOrder(id) {
    const result = await patchAPI(`/workorders/${id}`, { status: 'done' });
    if (result) {
        await loadWorkOrders();
    }
}

async function showSiteDetails(siteId) {
    const site = state.sites.find(s => s.id === siteId);
    if (!site) return;
    
    const assets = await fetchAPI(`/sites/${siteId}/assets`);
    
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modal = document.getElementById('detail-modal');
    
    modalTitle.textContent = site.name;
    
    if (!assets || assets.length === 0) {
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-cogs"></i>
                <p>Aucun équipement trouvé pour ce site</p>
            </div>
        `;
    } else {
        modalBody.innerHTML = `
            <div style="margin-bottom: 16px;">
                <strong>Code:</strong> ${site.code}<br>
                <strong>Adresse:</strong> ${site.address || '-'}
            </div>
            <h4 style="margin-bottom: 12px;">Équipements (${assets.length})</h4>
            <div class="sites-grid">
                ${assets.map(asset => `
                    <div class="site-card" style="cursor: default;">
                        <div class="site-code">${asset.type}</div>
                        <div class="site-name">${asset.code}</div>
                        <div class="site-stats">
                            <span class="${asset.status === 'OK' ? 'stat-success' : asset.status === 'WARNING' ? 'stat-warning' : 'stat-danger'}">
                                <i class="fas fa-circle"></i>
                                ${asset.status}
                            </span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    modal.classList.add('active');
}

// ============================
// Navigation
// ============================

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            
            // Update nav active state
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Update page visibility
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(`${page}-page`).classList.add('active');
            
            // Update header title
            const titles = {
                overview: 'Vue Globale',
                sites: 'Sites',
                alerts: 'Alertes',
                workorders: 'Ordres de Travail'
            };
            document.getElementById('page-title').textContent = titles[page];
            
            state.currentPage = page;
        });
    });
}

function setupModal() {
    const modal = document.getElementById('detail-modal');
    const closeBtn = document.getElementById('modal-close');
    
    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}

function setupFilters() {
    document.getElementById('alert-status-filter').addEventListener('change', renderAlertsTable);
    document.getElementById('alert-severity-filter').addEventListener('change', renderAlertsTable);
    document.getElementById('wo-status-filter').addEventListener('change', renderWorkOrders);
}

// ============================
// Initialization
// ============================

async function init() {
    // Setup UI
    setupNavigation();
    setupModal();
    setupFilters();
    
    // Start clock
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // Check API status
    await checkAPIStatus();
    setInterval(checkAPIStatus, 30000);
    
    // Load initial data
    await Promise.all([
        loadSites(),
        loadAlerts(),
        loadWorkOrders()
    ]);
    
    // Auto-refresh data every 30 seconds
    setInterval(async () => {
        await loadAlerts();
        await loadWorkOrders();
    }, 30000);
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
