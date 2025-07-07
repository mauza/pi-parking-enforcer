// Dashboard JavaScript for Pi Parking Enforcer

class ParkingDashboard {
    constructor() {
        this.socket = null;
        this.updateInterval = null;
        this.isMonitoring = false;
        
        this.initializeSocket();
        this.bindEvents();
        this.loadInitialData();
        this.startAutoRefresh();
    }
    
    initializeSocket() {
        // Initialize Socket.IO connection
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateStatusIndicator('connected');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateStatusIndicator('disconnected');
        });
        
        this.socket.on('status_update', (data) => {
            this.updateDashboard(data);
        });
    }
    
    bindEvents() {
        // Control buttons
        document.getElementById('startBtn').addEventListener('click', () => {
            this.startMonitoring();
        });
        
        document.getElementById('stopBtn').addEventListener('click', () => {
            this.stopMonitoring();
        });
        
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });
        
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.openSettings();
        });
        
        // Settings modal
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });
    }
    
    async loadInitialData() {
        try {
            await this.loadStatus();
            await this.loadActiveSessions();
            await this.loadParkingStats();
            await this.loadOccupancyChart();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading data', 'error');
        }
    }
    
    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.error) {
                this.updateStatusIndicator('error');
                return;
            }
            
            this.updateDashboard(data);
        } catch (error) {
            console.error('Error loading status:', error);
            this.updateStatusIndicator('error');
        }
    }
    
    async loadActiveSessions() {
        try {
            const response = await fetch('/api/active-sessions');
            const sessions = await response.json();
            this.updateActiveSessions(sessions);
        } catch (error) {
            console.error('Error loading active sessions:', error);
        }
    }
    
    async loadParkingStats() {
        try {
            const response = await fetch('/api/parking-stats');
            const stats = await response.json();
            this.updateStatistics(stats);
        } catch (error) {
            console.error('Error loading parking stats:', error);
        }
    }
    
    async loadOccupancyChart() {
        try {
            const response = await fetch('/api/occupancy-chart');
            const data = await response.json();
            
            if (data.chart_data) {
                document.getElementById('occupancyChart').src = 
                    'data:image/png;base64,' + data.chart_data;
            }
        } catch (error) {
            console.error('Error loading occupancy chart:', error);
        }
    }
    
    async startMonitoring() {
        try {
            const response = await fetch('/api/start-monitoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.isMonitoring = true;
                this.updateControlButtons();
                this.showNotification('Monitoring started successfully', 'success');
                this.updateStatusIndicator('monitoring');
            } else {
                this.showNotification('Failed to start monitoring: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('Error starting monitoring:', error);
            this.showNotification('Error starting monitoring', 'error');
        }
    }
    
    async stopMonitoring() {
        try {
            const response = await fetch('/api/stop-monitoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.isMonitoring = false;
                this.updateControlButtons();
                this.showNotification('Monitoring stopped successfully', 'success');
                this.updateStatusIndicator('stopped');
            } else {
                this.showNotification('Failed to stop monitoring: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('Error stopping monitoring:', error);
            this.showNotification('Error stopping monitoring', 'error');
        }
    }
    
    async refreshData() {
        this.showNotification('Refreshing data...', 'info');
        await this.loadInitialData();
        this.showNotification('Data refreshed successfully', 'success');
    }
    
    updateDashboard(data) {
        this.updateStatistics(data.stats || {});
        this.updateStatusIndicator(data.is_running ? 'monitoring' : 'stopped');
        this.isMonitoring = data.is_running;
        this.updateControlButtons();
    }
    
    updateStatistics(stats) {
        document.getElementById('totalSpots').textContent = stats.total_spots || '-';
        document.getElementById('occupiedSpots').textContent = stats.occupied_spots || '-';
        document.getElementById('occupancyRate').textContent = 
            stats.occupancy_rate ? stats.occupancy_rate + '%' : '-';
        document.getElementById('avgDuration').textContent = 
            stats.avg_duration_minutes ? Math.round(stats.avg_duration_minutes) + ' min' : '-';
    }
    
    updateActiveSessions(sessions) {
        const container = document.getElementById('activeSessionsList');
        
        if (sessions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-parking"></i>
                    <p>No active parking sessions</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = sessions.map(session => {
            const alertClass = session.duration_hours >= 5 ? 'alert-danger' : 
                             session.duration_hours >= 3 ? 'alert-warning' : '';
            
            return `
                <div class="session-item ${alertClass}">
                    <div class="session-header">
                        <span class="session-spot">${session.spot_name}</span>
                        <span class="session-duration">${session.duration_hours}h</span>
                    </div>
                    <div class="session-details">
                        <div><strong>Car ID:</strong> ${session.car_identifier || 'Unknown'}</div>
                        <div><strong>Started:</strong> ${this.formatTime(session.start_time)}</div>
                        <div><strong>Confidence:</strong> ${(session.confidence_score * 100).toFixed(1)}%</div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateControlButtons() {
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        if (this.isMonitoring) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    }
    
    updateStatusIndicator(status) {
        const indicator = document.getElementById('status-indicator');
        const icon = indicator.querySelector('i');
        
        switch (status) {
            case 'connected':
                icon.className = 'fas fa-circle text-success';
                indicator.innerHTML = '<i class="fas fa-circle text-success"></i> Connected';
                break;
            case 'monitoring':
                icon.className = 'fas fa-circle text-success';
                indicator.innerHTML = '<i class="fas fa-circle text-success"></i> Monitoring';
                break;
            case 'stopped':
                icon.className = 'fas fa-circle text-warning';
                indicator.innerHTML = '<i class="fas fa-circle text-warning"></i> Stopped';
                break;
            case 'disconnected':
                icon.className = 'fas fa-circle text-danger';
                indicator.innerHTML = '<i class="fas fa-circle text-danger"></i> Disconnected';
                break;
            case 'error':
                icon.className = 'fas fa-circle text-danger';
                indicator.innerHTML = '<i class="fas fa-circle text-danger"></i> Error';
                break;
            default:
                icon.className = 'fas fa-circle text-warning';
                indicator.innerHTML = '<i class="fas fa-circle text-warning"></i> Initializing...';
        }
    }
    
    openSettings() {
        // Load current settings into modal
        document.getElementById('cameraIndex').value = '0';
        document.getElementById('detectionInterval').value = '5';
        document.getElementById('alertThreshold').value = '5';
        document.getElementById('confidenceThreshold').value = '0.5';
        
        const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
        modal.show();
    }
    
    async saveSettings() {
        // In a real implementation, you would send these settings to the server
        this.showNotification('Settings saved successfully', 'success');
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
        modal.hide();
    }
    
    startAutoRefresh() {
        // Refresh data every 30 seconds
        this.updateInterval = setInterval(() => {
            if (this.isMonitoring) {
                this.loadActiveSessions();
                this.loadParkingStats();
            }
        }, 30000);
    }
    
    formatTime(timeString) {
        const date = new Date(timeString);
        return date.toLocaleTimeString();
    }
    
    showNotification(message, type = 'info') {
        // Create toast notification
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new ParkingDashboard();
}); 