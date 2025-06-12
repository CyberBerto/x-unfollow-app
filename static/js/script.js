/**
 * X Unfollow Tool - Client-side JavaScript
 * Handles UI interactions, API calls, and real-time updates
 */

class XUnfollowApp {
    constructor() {
        this.csvUserList = [];
        this.selectedUsers = new Set();
        this.isProcessing = false;
        this.authAttempts = 0;
        this.rateLimits = {
            unfollow: { remaining: 50, reset: 0, limit: 50 }
        };
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadRateLimits();
        this.checkAuthStatus();
        
        // Check for URL parameters (error messages from OAuth)
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        const errorDescription = urlParams.get('error_description');
        if (error) {
            this.showLoginError(error, errorDescription);
            // Clean URL after showing error
            const cleanUrl = window.location.pathname;
            window.history.replaceState({}, document.title, cleanUrl);
        }
    }
    
    bindEvents() {
        // Single unfollow form
        const singleForm = document.getElementById('single-unfollow-form');
        if (singleForm) {
            singleForm.addEventListener('submit', (e) => this.handleSingleUnfollow(e));
        }
        
        // CSV file input
        const csvInput = document.getElementById('csv-file-input');
        if (csvInput) {
            csvInput.addEventListener('change', (e) => this.handleCSVUpload(e));
        }
        
        // Select all/none buttons
        const selectAllBtn = document.getElementById('select-all-btn');
        const selectNoneBtn = document.getElementById('select-none-btn');
        const clearCSVBtn = document.getElementById('clear-csv-btn');
        if (selectAllBtn) selectAllBtn.addEventListener('click', () => this.selectAll());
        if (selectNoneBtn) selectNoneBtn.addEventListener('click', () => this.selectNone());
        if (clearCSVBtn) clearCSVBtn.addEventListener('click', () => this.clearCSVList());
        
        // Batch unfollow buttons
        const smallBatchBtn = document.getElementById('small-batch-btn');
        const fullBatchBtn = document.getElementById('full-batch-btn');
        if (smallBatchBtn) smallBatchBtn.addEventListener('click', () => this.handleBatchUnfollow('small'));
        if (fullBatchBtn) fullBatchBtn.addEventListener('click', () => this.handleBatchUnfollow('full'));
        
        // Track auth attempts
        document.addEventListener('click', (e) => {
            if (e.target.closest('a[href="/login"]')) {
                this.authAttempts++;
                this.updateAuthAttemptsDisplay();
            }
        });
    }
    
    async checkAuthStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            if (data.authenticated) {
                document.getElementById('username-display').textContent = data.username || 'User';
                if (data.rate_limits) {
                    this.updateRateLimitDisplay(data.rate_limits);
                }
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
        }
    }
    
    async loadRateLimits() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            if (data.rate_limits) {
                this.rateLimits = data.rate_limits;
                this.updateRateLimitDisplay(data.rate_limits);
            }
        } catch (error) {
            console.error('Error loading rate limits:', error);
        }
    }
    
    updateRateLimitDisplay(rateLimits) {
        const unfollowEl = document.getElementById('unfollow-rate-limit');
        
        if (unfollowEl && rateLimits.unfollow) {
            const limit = rateLimits.unfollow.limit || 50;
            unfollowEl.textContent = `${rateLimits.unfollow.remaining}/${limit}`;
            unfollowEl.className = `badge ${rateLimits.unfollow.remaining > 10 ? 'bg-success' : 'bg-warning'}`;
        }
        
        this.updateAuthAttemptsDisplay();
    }
    
    updateAuthAttemptsDisplay() {
        const authEl = document.getElementById('auth-attempts');
        if (authEl) {
            authEl.textContent = this.authAttempts;
            authEl.className = `badge ${this.authAttempts < 5 ? 'bg-info' : 'bg-warning'}`;
        }
    }
    
    async handleSingleUnfollow(event) {
        event.preventDefault();
        
        if (this.isProcessing) return;
        
        const usernameInput = document.getElementById('username-input');
        const target = usernameInput.value.trim();
        
        if (!target) {
            this.showStatus('warning', 'Please enter a username or user ID');
            return;
        }
        
        this.isProcessing = true;
        this.setButtonState('single-unfollow-btn', true, 'Unfollowing...');
        this.showStatus('info', `Attempting to unfollow @${target}...`);
        
        try {
            const response = await fetch('/unfollow/single', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ target })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showStatus('success', data.message);
                usernameInput.value = '';
                this.loadRateLimits(); // Update rate limits
            } else {
                this.showStatus('error', data.error || 'Unfollow failed');
            }
        } catch (error) {
            console.error('Single unfollow error:', error);
            this.showStatus('error', 'Network error occurred');
        } finally {
            this.isProcessing = false;
            this.setButtonState('single-unfollow-btn', false, '<i class=\"fas fa-user-minus me-2\"></i>Unfollow User');
        }
    }
    
    async handleCSVUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        this.showStatus('info', 'Processing CSV file...');
        
        try {
            const text = await file.text();
            const usernames = this.parseCSV(text);
            
            if (usernames.length === 0) {
                this.showStatus('warning', 'No valid usernames found in CSV file');
                return;
            }
            
            this.csvUserList = usernames.map((username, index) => ({
                id: `csv_${index}`,
                username: username.trim(),
                source: 'csv'
            }));
            
            this.renderCSVList();
            this.showStatus('success', `Loaded ${this.csvUserList.length} usernames from CSV`);
            
        } catch (error) {
            console.error('CSV parsing error:', error);
            this.showStatus('error', 'Failed to read CSV file');
        }
    }
    
    parseCSV(text) {
        // Simple CSV parsing - supports comma-separated or line-separated usernames
        const usernames = [];
        const lines = text.split(/[\n\r]+/);
        
        lines.forEach(line => {
            line = line.trim();
            if (!line) return;
            
            // Check if line contains commas (CSV format)
            if (line.includes(',')) {
                const parts = line.split(',');
                parts.forEach(part => {
                    const username = part.trim().replace(/[@"']/g, '');
                    if (username && this.isValidUsername(username)) {
                        usernames.push(username);
                    }
                });
            } else {
                // Single username per line
                const username = line.replace(/[@"']/g, '');
                if (username && this.isValidUsername(username)) {
                    usernames.push(username);
                }
            }
        });
        
        return [...new Set(usernames)]; // Remove duplicates
    }
    
    isValidUsername(username) {
        // Basic username validation
        return /^[a-zA-Z0-9_]{1,15}$/.test(username);
    }
    
    renderCSVList() {
        const listEl = document.getElementById('csv-list');
        const containerEl = document.getElementById('csv-list-container');
        const emptyEl = document.getElementById('csv-empty');
        
        if (!listEl) return;
        
        listEl.innerHTML = '';
        
        this.csvUserList.forEach(user => {
            const itemEl = document.createElement('div');
            itemEl.className = 'csv-item d-flex align-items-center p-2 border-bottom';
            itemEl.innerHTML = `
                <input type="checkbox" class="form-check-input me-2" 
                       data-username="${user.username}" id="csv_${user.username}">
                <label class="form-check-label flex-grow-1" for="csv_${user.username}">
                    @${user.username}
                </label>
            `;
            
            // Add click handler for selection
            const checkbox = itemEl.querySelector('.form-check-input');
            checkbox.addEventListener('change', () => this.toggleCSVUserSelection(user.username, checkbox.checked));
            
            listEl.appendChild(itemEl);
        });
        
        // Show/hide appropriate containers
        if (this.csvUserList.length > 0) {
            emptyEl.classList.add('d-none');
            containerEl.classList.remove('d-none');
        } else {
            emptyEl.classList.remove('d-none');
            containerEl.classList.add('d-none');
        }
        
        this.selectedUsers.clear();
        this.updateSelectedCount();
    }
    
    clearCSVList() {
        this.csvUserList = [];
        this.selectedUsers.clear();
        this.renderCSVList();
        document.getElementById('csv-file-input').value = '';
        this.showStatus('info', 'CSV list cleared');
    }
    
    toggleCSVUserSelection(username, selected) {
        if (selected) {
            this.selectedUsers.add(username);
        } else {
            this.selectedUsers.delete(username);
        }
        
        this.updateSelectedCount();
    }
    
    updateSelectedCount() {
        const countEl = document.getElementById('selected-count');
        if (countEl) {
            countEl.textContent = this.selectedUsers.size;
        }
    }
    
    selectAll() {
        const checkboxes = document.querySelectorAll('#csv-list .form-check-input');
        checkboxes.forEach(checkbox => {
            if (!checkbox.checked) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change'));
            }
        });
    }
    
    selectNone() {
        const checkboxes = document.querySelectorAll('#csv-list .form-check-input');
        checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                checkbox.checked = false;
                checkbox.dispatchEvent(new Event('change'));
            }
        });
    }
    
    async handleBatchUnfollow(type) {
        if (this.isProcessing) return;
        
        const selectedUsernames = [...this.selectedUsers];
        const maxUsers = type === 'small' ? 10 : 50;
        const buttonId = type === 'small' ? 'small-batch-btn' : 'full-batch-btn';
        const delay = type === 'small' ? 1 : 18;
        
        if (selectedUsernames.length === 0) {
            this.showStatus('warning', 'Please select at least one account to unfollow');
            return;
        }
        
        if (selectedUsernames.length > maxUsers) {
            this.showStatus('warning', `Maximum ${maxUsers} accounts allowed for ${type} batch`);
            return;
        }
        
        // Confirm batch operation
        const confirmMessage = `Are you sure you want to unfollow ${selectedUsernames.length} accounts?\\n\\n` +
                              `This will take approximately ${Math.round(selectedUsernames.length * delay / 60)} minutes to complete.`;
        
        if (!confirm(confirmMessage)) return;
        
        this.isProcessing = true;
        const originalButtonText = document.getElementById(buttonId).innerHTML;
        this.setButtonState(buttonId, true, 'Processing...');
        
        // Show progress
        this.showProgress(0, selectedUsernames.length);
        this.showStatus('info', `Starting ${type} batch unfollow of ${selectedUsernames.length} accounts...`);
        
        try {
            const endpoint = type === 'small' ? '/unfollow/small-batch' : '/unfollow/full-batch';
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ usernames: selectedUsernames })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const successCount = data.results ? data.results.filter(r => r.success).length : 0;
                this.showStatus(
                    data.success ? 'success' : 'warning', 
                    `Batch unfollow completed: ${successCount}/${selectedUsernames.length} successful`
                );
                
                // Clear selections and reload rate limits
                this.selectNone();
                this.loadRateLimits();
            } else {
                this.showStatus('error', data.error || 'Batch unfollow failed');
            }
        } catch (error) {
            console.error('Batch unfollow error:', error);
            this.showStatus('error', 'Network error occurred during batch unfollow');
        } finally {
            this.isProcessing = false;
            this.setButtonState(buttonId, false, originalButtonText);
            this.hideProgress();
        }
    }
    
    async refreshToken() {
        try {
            const response = await fetch('/refresh-token', { method: 'POST' });
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showStatus('success', 'Authentication token refreshed successfully');
                this.loadRateLimits();
            } else {
                this.showStatus('error', data.message || 'Token refresh failed');
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            this.showStatus('error', 'Failed to refresh token');
        }
    }
    
    showLoginError(error, errorDescription) {
        const container = document.getElementById('login-error-container');
        const messageEl = document.getElementById('login-error-message');
        const descriptionEl = document.getElementById('login-error-description');
        
        if (!container || !messageEl || !descriptionEl) return;
        
        // Format error message
        const errorMessages = {
            'callback_failed': 'OAuth callback failed',
            'no_code': 'No authorization code received',
            'unauthorized_client': 'Client authorization failed',
            'invalid_client': 'Invalid client credentials',
            'access_denied': 'User denied access'
        };
        
        messageEl.textContent = errorMessages[error] || error;
        descriptionEl.textContent = errorDescription || 'Check your X Developer Portal configuration';
        
        // Show error container
        container.classList.remove('d-none');
    }
    
    showStatus(type, message, duration = 5000) {
        const container = document.getElementById('status-container');
        const alert = document.getElementById('status-alert');
        const icon = document.getElementById('status-icon');
        const messageEl = document.getElementById('status-message');
        
        if (!container || !alert || !icon || !messageEl) return;
        
        // Set alert type
        alert.className = `alert alert-${type === 'error' ? 'danger' : type}`;
        
        // Set icon
        const iconClass = {
            success: 'fas fa-check-circle status-success',
            error: 'fas fa-exclamation-circle status-error',
            warning: 'fas fa-exclamation-triangle status-warning',
            info: 'fas fa-info-circle status-info'
        }[type] || 'fas fa-info-circle status-info';
        
        icon.innerHTML = `<i class="${iconClass}"></i>`;
        messageEl.textContent = message;
        
        // Show container
        container.classList.remove('d-none');
        container.classList.add('fade-in');
        
        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => {
                container.classList.add('d-none');
            }, duration);
        }
    }
    
    showProgress(current, total) {
        const progressContainer = document.getElementById('status-progress');
        const progressBar = document.getElementById('status-progress-bar');
        const progressText = document.getElementById('status-progress-text');
        
        if (!progressContainer || !progressBar || !progressText) return;
        
        const percentage = Math.round((current / total) * 100);
        
        progressContainer.classList.remove('d-none');
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `${current}/${total} (${percentage}%)`;
    }
    
    hideProgress() {
        const progressContainer = document.getElementById('status-progress');
        if (progressContainer) {
            progressContainer.classList.add('d-none');
        }
    }
    
    setButtonState(buttonId, disabled, text = null) {
        const button = document.getElementById(buttonId);
        if (!button) return;
        
        button.disabled = disabled;
        if (text) {
            button.innerHTML = text;
        }
        
        if (disabled) {
            button.classList.add('disabled');
        } else {
            button.classList.remove('disabled');
        }
    }
    
    showModal(title, content, showSpinner = false) {
        const modal = document.getElementById('loadingModal');
        const titleEl = document.getElementById('loading-text');
        const contentEl = document.getElementById('loading-detail');
        
        if (modal && titleEl && contentEl) {
            titleEl.textContent = title;
            contentEl.textContent = content;
            
            const spinner = modal.querySelector('.spinner-border');
            if (spinner) {
                spinner.style.display = showSpinner ? 'block' : 'none';
            }
            
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
        }
    }
    
    hideModal() {
        const modal = document.getElementById('loadingModal');
        if (modal) {
            const bootstrapModal = bootstrap.Modal.getInstance(modal);
            if (bootstrapModal) {
                bootstrapModal.hide();
            }
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.xUnfollowApp = new XUnfollowApp();
});

// Handle authentication errors and redirects
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('error')) {
        // Clean URL after showing error
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }
});

// Utility functions
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}