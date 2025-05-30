// AEON Weapon AI System - Main JavaScript Application

// Global variables
let systemHealthData = {};
let statisticsChart = null;
let currentGeneration = null;

// API Base URL
const API_BASE = window.location.origin;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    console.log('🔫 AEON Weapon AI System - Initializing...');
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize charts if on dashboard
    if (document.getElementById('stats-chart')) {
        initializeStatisticsChart();
    }
    
    // Check system health
    checkSystemHealth();
    
    console.log('✅ Application initialized');
}

function setupEventListeners() {
    // Weapon generation form
    const generateForm = document.getElementById('weapon-generation-form');
    if (generateForm) {
        generateForm.addEventListener('submit', handleWeaponGeneration);
    }
    
    // Auto-refresh system health every 30 seconds
    setInterval(checkSystemHealth, 30000);
    
    // Handle notification clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('alert')) {
            e.target.style.display = 'none';
        }
    });
}

// System Health Functions
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();
        
        systemHealthData = data;
        updateHealthDisplay(data);
        
        return data;
    } catch (error) {
        console.error('Health check failed:', error);
        updateHealthDisplay({ 
            status: 'error', 
            models_loaded: false, 
            gpu_available: false 
        });
        return null;
    }
}

function updateHealthDisplay(health) {
    // Update system status
    const statusElement = document.getElementById('system-status');
    if (statusElement) {
        statusElement.textContent = health.status === 'healthy' ? 'Healthy' : 'Offline';
        statusElement.parentElement.parentElement.className = 
            `card ${health.status === 'healthy' ? 'bg-success' : 'bg-danger'} text-white`;
    }
    
    // Update GPU status
    const gpuElement = document.getElementById('gpu-status');
    if (gpuElement) {
        gpuElement.textContent = health.gpu_available ? 
            `Available (${health.gpu_count || 1})` : 'Not Available';
        gpuElement.parentElement.parentElement.className = 
            `card ${health.gpu_available ? 'bg-info' : 'bg-warning'} text-white`;
    }
    
    // Update models status
    const modelsElement = document.getElementById('models-status');
    if (modelsElement) {
        modelsElement.textContent = health.models_loaded ? 'Loaded' : 'Not Loaded';
        modelsElement.parentElement.parentElement.className = 
            `card ${health.models_loaded ? 'bg-warning' : 'bg-danger'} text-white`;
    }
    
    // Update total weapons count
    const totalElement = document.getElementById('total-weapons');
    if (totalElement && health.stats) {
        totalElement.textContent = health.stats.total_generated || 0;
    }
}

// Weapon Generation Functions
async function handleWeaponGeneration(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const player1Personality = formData.get('player1-personality') || document.getElementById('player1-personality').value;
    const player2Personality = formData.get('player2-personality') || document.getElementById('player2-personality').value;
    const arenaTheme = formData.get('arena-theme') || document.getElementById('arena-theme').value;
    
    // Validate inputs
    if (!player1Personality || !player2Personality) {
        showError('Please select personalities for both players');
        return;
    }
    
    try {
        // Start generation process
        await generateWeapons(player1Personality, player2Personality, arenaTheme);
    } catch (error) {
        console.error('Weapon generation error:', error);
        showError('Failed to generate weapons: ' + error.message);
    }
}

async function generateWeapons(player1Personality, player2Personality, arenaTheme) {
    const generateBtn = document.getElementById('generate-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    try {
        // Disable form and show progress
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        progressContainer.style.display = 'block';
        
        // Step 1: Generate weapon scenarios
        updateProgress(20, 'Generating weapon scenarios...');
        
        const scenarioResponse = await fetch(`${API_BASE}/api/weapons/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player1_personality: player1Personality,
                player2_personality: player2Personality,
                arena_theme: arenaTheme
            })
        });
        
        if (!scenarioResponse.ok) {
            throw new Error(`Scenario generation failed: ${scenarioResponse.statusText}`);
        }
        
        const scenarioData = await scenarioResponse.json();
        const weapons = scenarioData.weapons;
        
        updateProgress(50, 'Creating 3D models...');
        
        // Step 2: Generate 3D models
        const modelResponse = await fetch(`${API_BASE}/api/weapons/batch-create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weapons: weapons })
        });
        
        if (!modelResponse.ok) {
            throw new Error(`3D model generation failed: ${modelResponse.statusText}`);
        }
        
        const modelData = await modelResponse.json();
        
        updateProgress(100, 'Generation complete!');
        
        // Show success
        setTimeout(() => {
            showWeaponGenerationSuccess(weapons, modelData);
            resetGenerationForm();
        }, 1000);
        
    } catch (error) {
        console.error('Generation error:', error);
        showError('Generation failed: ' + error.message);
        resetGenerationForm();
    }
}

function updateProgress(percentage, text) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
    }
    
    if (progressText) {
        progressText.textContent = text;
    }
}

function resetGenerationForm() {
    const generateBtn = document.getElementById('generate-btn');
    const progressContainer = document.getElementById('progress-container');
    
    if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Weapons';
    }
    
    if (progressContainer) {
        setTimeout(() => {
            progressContainer.style.display = 'none';
            updateProgress(0, 'Initializing...');
        }, 2000);
    }
}

function showWeaponGenerationSuccess(weapons, modelData) {
    const modalBody = document.getElementById('success-modal-body');
    
    if (modalBody) {
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="fas fa-check-circle text-success"></i> Generation Summary</h6>
                    <ul class="list-unstyled">
                        <li><strong>Total Weapons:</strong> ${weapons.length}</li>
                        <li><strong>Successful Models:</strong> ${modelData.summary.successful}/${modelData.summary.total}</li>
                        <li><strong>Generation Time:</strong> ${modelData.summary.total_time?.toFixed(2) || 'N/A'}s</li>
                        <li><strong>Arena Theme:</strong> ${weapons[0]?.arena_theme || 'Unknown'}</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-users text-info"></i> Player Info</h6>
                    <ul class="list-unstyled">
                        <li><strong>Player 1:</strong> ${weapons[0]?.personality || 'Unknown'}</li>
                        <li><strong>Player 2:</strong> ${weapons[2]?.personality || 'Unknown'}</li>
                    </ul>
                </div>
            </div>
            
            <hr>
            
            <h6><i class="fas fa-sword text-primary"></i> Generated Weapons</h6>
            <div class="row">
                ${weapons.map((weapon, index) => `
                    <div class="col-md-6 mb-3">
                        <div class="card ${modelData.results[index]?.status === 'completed' ? 'border-success' : 'border-warning'}">
                            <div class="card-body">
                                <h6 class="card-title">${weapon.weaponName}</h6>
                                <p class="card-text small">${weapon.description.substring(0, 100)}...</p>
                                <div class="d-flex justify-content-between">
                                    <span class="badge bg-danger">DMG: ${weapon.damage}</span>
                                    <span class="badge bg-success">SPD: ${weapon.speed}</span>
                                    <span class="badge bg-primary">P${weapon.player}</span>
                                </div>
                                <div class="mt-2">
                                    ${modelData.results[index]?.status === 'completed' ? 
                                        '<span class="badge bg-success"><i class="fas fa-check"></i> Model Ready</span>' :
                                        '<span class="badge bg-warning"><i class="fas fa-exclamation"></i> Model Failed</span>'
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('successModal'));
    modal.show();
    
    // Refresh statistics and recent weapons
    setTimeout(() => {
        loadStatistics();
        loadRecentWeapons();
    }, 1000);
}

// Statistics Functions
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/api/weapons/stats`);
        const data = await response.json();
        
        updateStatisticsDisplay(data);
        updateStatisticsChart(data);
        
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

function updateStatisticsDisplay(data) {
    const stats = data.generation_stats || {};
    
    // Update success rate
    const successRateElement = document.getElementById('success-rate');
    if (successRateElement) {
        const rate = stats.total_generated > 0 ? 
            Math.round((stats.successful_generations / stats.total_generated) * 100) : 0;
        successRateElement.textContent = rate + '%';
    }
    
    // Update average time
    const avgTimeElement = document.getElementById('avg-time');
    if (avgTimeElement) {
        const avgTime = stats.average_time || 0;
        avgTimeElement.textContent = avgTime.toFixed(1) + 's';
    }
}

function initializeStatisticsChart() {
    const ctx = document.getElementById('stats-chart');
    if (!ctx) return;
    
    statisticsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Aggressive Warrior', 'Strategic Mage', 'Defensive Guardian', 'Agile Assassin', 'Elemental Mage'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    '#ef4444',  // Red for aggressive
                    '#3b82f6',  // Blue for strategic
                    '#f59e0b',  // Yellow for defensive
                    '#8b5cf6',  // Purple for agile
                    '#10b981'   // Green for elemental
                ],
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
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function updateStatisticsChart(data) {
    if (!statisticsChart) return;
    
    const personalityCounts = data.generation_stats?.personality_counts || {};
    
    const chartData = [
        personalityCounts['aggressive_warrior'] || 0,
        personalityCounts['strategic_mage'] || 0,
        personalityCounts['defensive_guardian'] || 0,
        personalityCounts['agile_assassin'] || 0,
        personalityCounts['elemental_mage'] || 0
    ];
    
    statisticsChart.data.datasets[0].data = chartData;
    statisticsChart.update();
}

// Recent Weapons Functions
async function loadRecentWeapons() {
    try {
        const response = await fetch(`${API_BASE}/api/weapons/list`);
        const data = await response.json();
        
        displayRecentWeapons(data.weapons || []);
        
    } catch (error) {
        console.error('Failed to load recent weapons:', error);
    }
}

function displayRecentWeapons(weapons) {
    const container = document.getElementById('recent-weapons');
    if (!container) return;
    
    if (weapons.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-sword fa-3x mb-3"></i>
                <p>No weapons generated yet. Create some weapons to see them here!</p>
            </div>
        `;
        return;
    }
    
    // Show only the 6 most recent weapons
    const recentWeapons = weapons.slice(0, 6);
    
    container.innerHTML = `
        <div class="row">
            ${recentWeapons.map(weapon => `
                <div class="col-lg-2 col-md-3 col-sm-4 col-6 mb-3">
                    <div class="card weapon-item h-100">
                        <div class="card-body text-center p-3">
                            <i class="fas fa-sword fa-2x text-primary mb-2"></i>
                            <h6 class="card-title small text-truncate" title="${weapon.filename}">
                                ${weapon.filename.replace('.obj', '').replace('weapon_', '').replace(/\d+_\d+/, '')}
                            </h6>
                            <small class="text-muted">
                                ${formatFileSize(weapon.size)}<br>
                                ${formatDate(weapon.created_at)}
                            </small>
                        </div>
                        <div class="card-footer bg-transparent p-2">
                            <div class="btn-group w-100" role="group">
                                <button class="btn btn-outline-primary btn-sm" 
                                        onclick="window.location.href='/gallery'" title="View">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-outline-success btn-sm" 
                                        onclick="downloadSingleWeapon('${weapon.filename}')" title="Download">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// API Testing Functions
async function testHealthAPI() {
    const responseElement = document.getElementById('api-response');
    
    try {
        responseElement.textContent = 'Testing health API...';
        
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();
        
        responseElement.textContent = JSON.stringify(data, null, 2);
        
        if (data.status === 'healthy') {
            showSuccess('Health API test successful');
        } else {
            showWarning('Health API responded but system not healthy');
        }
        
    } catch (error) {
        responseElement.textContent = `Error: ${error.message}`;
        showError('Health API test failed');
    }
}

async function testGenerationAPI() {
    const responseElement = document.getElementById('api-response');
    
    try {
        responseElement.textContent = 'Testing generation API...';
        
        const response = await fetch(`${API_BASE}/api/weapons/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player1_personality: 'aggressive_warrior',
                player2_personality: 'strategic_mage',
                arena_theme: 'volcanic'
            })
        });
        
        const data = await response.json();
        
        responseElement.textContent = JSON.stringify(data, null, 2);
        
        if (response.ok) {
            showSuccess('Generation API test successful');
        } else {
            showError('Generation API test failed');
        }
        
    } catch (error) {
        responseElement.textContent = `Error: ${error.message}`;
        showError('Generation API test failed');
    }
}

// Download Functions
function downloadBatch() {
    window.location.href = `${API_BASE}/download/batch`;
}

function downloadSingleWeapon(filename) {
    window.location.href = `${API_BASE}/download/weapon/${filename}`;
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

// Notification Functions
function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'danger');
}

function showWarning(message) {
    showNotification(message, 'warning');
}

function showInfo(message) {
    showNotification(message, 'info');
}

function showNotification(message, type = 'info') {
    const container = document.querySelector('.container');
    if (!container) return;
    
    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" id="${alertId}" role="alert">
            <strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    container.insertAdjacentHTML('afterbegin', alertHTML);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// Export functions for global use
window.checkSystemHealth = checkSystemHealth;
window.loadStatistics = loadStatistics;
window.loadRecentWeapons = loadRecentWeapons;
window.testHealthAPI = testHealthAPI;
window.testGenerationAPI = testGenerationAPI;
window.downloadBatch = downloadBatch;
window.downloadSingleWeapon = downloadSingleWeapon;
window.showSuccess = showSuccess;
window.showError = showError;
window.showWarning = showWarning;
window.showInfo = showInfo;

console.log('🚀 AEON Weapon AI System - JavaScript loaded');