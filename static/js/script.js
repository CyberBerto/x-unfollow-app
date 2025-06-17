/**
 * X Unfollow Tool - Client-side JavaScript
 * Handles UI interactions, API calls, and real-time updates
 */

class XUnfollowApp {
    constructor() {
        this.csvUserList = [];
        this.selectedUsers = new Set();
        this.isProcessing = false;
        this.activeSlowBatchOperations = [];
        this.alertLog = [];
        this.rateLimits = {
            unfollow: { remaining: 'unknown', reset: 0, limit: 'unknown' },
            unfollow_hourly: { remaining: 'unknown', reset: 0, limit: 'unknown' },
            unfollow_daily: { remaining: 'unknown', reset: 0, limit: 'unknown' }
        };
        
        this.init();
    }
    
    
    updateOperationTimer(operationId, startTime) {
        // Update timer display for running operations
        const timerEl = document.getElementById(`timer-${operationId}`);
        if (!timerEl || !startTime) return;
        
        const updateTimer = () => {
            const now = new Date();
            const start = new Date(startTime);
            const elapsed = Math.floor((now - start) / 1000);
            
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;
            
            let timeString = '';
            if (hours > 0) {
                timeString = `${hours}h ${minutes}m ${seconds}s elapsed`;
            } else if (minutes > 0) {
                timeString = `${minutes}m ${seconds}s elapsed`;
            } else {
                timeString = `${seconds}s elapsed`;
            }
            
            timerEl.textContent = `Running: ${timeString}`;
        };
        
        // Update immediately and then every second
        updateTimer();
        const timerId = setInterval(updateTimer, 1000);
        
        // Store timer ID for cleanup
        if (!this.operationTimers) this.operationTimers = {};
        this.operationTimers[operationId] = timerId;
    }
    
    saveCSVListToStorage() {
        // Save CSV list to localStorage for persistence
        try {
            localStorage.setItem('csvUserList', JSON.stringify(this.csvUserList));
        } catch (error) {
            console.error('Error saving CSV list:', error);
        }
    }
    
    loadCSVListFromStorage() {
        // Load CSV list from localStorage
        try {
            const saved = localStorage.getItem('csvUserList');
            if (saved) {
                this.csvUserList = JSON.parse(saved);
                this.renderCSVList();
            }
        } catch (error) {
            console.error('Error loading CSV list:', error);
        }
    }
    
    removeUsernameFromList(username) {
        // Remove a username from the CSV list (after successful unfollow)
        const initialLength = this.csvUserList.length;
        this.csvUserList = this.csvUserList.filter(user => user.username !== username);
        
        if (this.csvUserList.length < initialLength) {
            this.selectedUsers.delete(username);
            this.renderCSVList();
            this.saveCSVListToStorage();
            console.log(`Removed ${username} from unfollow list`);
            return true; // Successfully removed
        }
        return false; // Username not found in list
    }
    
    init() {
        // UX Layer 1: Simple initialization flow
        this.bindEvents();
        this.checkAuthStatus();
        this.loadCSVListFromStorage();
        this.loadSlowBatchOperations();
        
        // UX Layer 1: Simple error handling for OAuth
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        if (error) {
            this.showLoginError(error, urlParams.get('error_description'));
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }
    
    bindEvents() {
        // Single unfollow form removed
        
        // CSV file input
        const csvInput = document.getElementById('csv-file-input');
        if (csvInput) {
            csvInput.addEventListener('change', (e) => this.handleCSVUpload(e));
        }
        
        // Alert log toggle button
        const toggleAlertLogBtn = document.getElementById('toggle-alert-log');
        if (toggleAlertLogBtn) {
            toggleAlertLogBtn.addEventListener('click', () => this.toggleAlertLog());
        }
        
        // Select all/none buttons
        const selectAllBtn = document.getElementById('select-all-btn');
        const selectNoneBtn = document.getElementById('select-none-btn');
        const clearCSVBtn = document.getElementById('clear-csv-btn');
        if (selectAllBtn) selectAllBtn.addEventListener('click', () => this.selectAll());
        if (selectNoneBtn) selectNoneBtn.addEventListener('click', () => this.selectNone());
        if (clearCSVBtn) clearCSVBtn.addEventListener('click', () => this.clearCSVList());
        
        // Batch button
        const regularBatchBtn = document.getElementById('regular-batch-btn');
        if (regularBatchBtn) regularBatchBtn.addEventListener('click', () => this.handleBatchUnfollow());
        
        // Extract usernames button removed
        
        // Kept for backward compatibility with existing operations
        const slowBatch15minBtn = document.getElementById('slow-batch-15min-btn');
        if (slowBatch15minBtn) slowBatch15minBtn.addEventListener('click', () => this.handleSlowBatch(15));
        
        // Refresh operations button
        const refreshOpsBtn = document.getElementById('refresh-operations-btn');
        if (refreshOpsBtn) refreshOpsBtn.addEventListener('click', () => this.manualRefresh());
        
        // Clear batches button
        const clearBatchesBtn = document.getElementById('clear-batches-btn');
        if (clearBatchesBtn) clearBatchesBtn.addEventListener('click', () => this.clearAllBatches());
    }
    
    // Login status checking removed - was causing unnecessary API calls
    
    async checkAuthStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            if (data.authenticated) {
                const userInfoSection = document.getElementById('user-info-section');
                const userInfoLoading = document.getElementById('user-info-loading');
                
                const displayName = data.username || 'User';
                const displayId = data.user_id || 'Loading...';
                const userDisplayName = data.display_name || displayName;
                
                // Check if we have real user data or just placeholders
                const hasRealData = displayName !== 'User' && displayName !== 'Loading...' && displayName !== 'Rate Limited' && displayId !== 'authenticated';
                
                if (hasRealData) {
                    // Show display name only
                    const displayNameEl = document.getElementById('display-name');
                    if (displayNameEl) {
                        displayNameEl.textContent = userDisplayName || displayName;
                    }
                    
                    if (userInfoSection) userInfoSection.classList.remove('d-none');
                    if (userInfoLoading) userInfoLoading.classList.add('d-none');
                } else {
                    // Show loading state with actual info if available
                    const displayNameEl = document.getElementById('display-name');
                    if (displayNameEl) {
                        displayNameEl.textContent = data.display_name || displayName;
                    }
                    
                    if (userInfoSection) userInfoSection.classList.remove('d-none');
                    if (userInfoLoading) userInfoLoading.classList.add('d-none');
                    
                    // Retry getting user info after a delay if it's still loading
                    if (displayName === 'Loading...' || displayName === 'Rate Limited') {
                        setTimeout(() => this.retryUserInfo(), 10000); // Retry after 10 seconds
                    }
                }
                
                if (data.rate_limits) {
                    this.updateRateLimitDisplay(data.rate_limits);
                }
                
                // Rate limit message handling simplified - removed complex UI updates
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
        }
    }
    
    async loadRateLimits() {
        // Only load initial rate limits on startup - don't make additional API calls
        // Rate limits will be updated after actual unfollow operations
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            if (data.rate_limits) {
                this.rateLimits = data.rate_limits;
                this.updateRateLimitDisplay(data.rate_limits);
            }
        } catch (error) {
            console.error('Error loading initial rate limits:', error);
        }
    }
    
    updateRateLimitDisplay(rateLimits) {
        const unfollowHourEl = document.getElementById('unfollow-rate-limit-hour');
        const unfollowDayEl = document.getElementById('unfollow-rate-limit-day');
        
        // Update hourly rate limits from persistent tracking data
        if (unfollowHourEl && rateLimits.unfollow_hourly) {
            const remaining = rateLimits.unfollow_hourly.remaining;
            const limit = rateLimits.unfollow_hourly.limit;
            const resetTime = rateLimits.unfollow_hourly.reset_time;
            
            if (remaining === 'unknown' || limit === 'unknown') {
                unfollowHourEl.textContent = 'No data';
                unfollowHourEl.className = 'badge bg-secondary';
            } else {
                const resetText = this.formatResetTime(resetTime);
                unfollowHourEl.textContent = `${remaining}/${limit}`;
                unfollowHourEl.title = `Resets ${resetText}`;
                unfollowHourEl.className = `badge ${remaining > 2 ? 'bg-success' : remaining > 0 ? 'bg-warning' : 'bg-danger'}`;
            }
        }
        
        // Update daily rate limits from persistent tracking data  
        if (unfollowDayEl && rateLimits.unfollow_daily) {
            const remaining = rateLimits.unfollow_daily.remaining;
            const limit = rateLimits.unfollow_daily.limit;
            const resetTime = rateLimits.unfollow_daily.reset_time;
            
            if (remaining === 'unknown' || limit === 'unknown') {
                unfollowDayEl.textContent = 'No data';
                unfollowDayEl.className = 'badge bg-secondary';
            } else {
                const resetText = this.formatResetTime(resetTime);
                unfollowDayEl.textContent = `${remaining}/${limit}`;
                unfollowDayEl.title = `Resets ${resetText}`;
                unfollowDayEl.className = `badge ${remaining > 10 ? 'bg-success' : remaining > 0 ? 'bg-warning' : 'bg-danger'}`;
            }
        }
    }

    formatResetTime(resetTimestamp) {
        if (!resetTimestamp) return 'unknown';
        
        const now = Math.floor(Date.now() / 1000);
        const timeDiff = resetTimestamp - now;
        
        if (timeDiff <= 0) {
            // Reset time has passed - trigger rate limit refresh
            this.checkAndResetExpiredRateLimits();
            return 'now';
        }
        
        const hours = Math.floor(timeDiff / 3600);
        const minutes = Math.floor((timeDiff % 3600) / 60);
        
        if (hours > 0) {
            return `in ${hours}h ${minutes}m`;
        } else {
            return `in ${minutes}m`;
        }
    }
    
    checkAndResetExpiredRateLimits() {
        const now = Math.floor(Date.now() / 1000);
        let needsUpdate = false;
        
        // Check if hourly reset time has passed
        if (this.rateLimits.unfollow_hourly.reset && 
            this.rateLimits.unfollow_hourly.reset <= now) {
            // Refresh rate limits from server
            this.fetchUpdatedRateLimits();
            needsUpdate = true;
        }
        
        // Check if daily reset time has passed  
        if (this.rateLimits.unfollow_daily.reset &&
            this.rateLimits.unfollow_daily.reset <= now) {
            // Refresh rate limits from server
            this.fetchUpdatedRateLimits();
            needsUpdate = true;
        }
        
        return needsUpdate;
    }
    
    fetchUpdatedRateLimits() {
        // Fetch fresh rate limit data from server
        fetch('/api/rate-limits')
            .then(response => response.json())
            .then(data => {
                if (data.rate_limits) {
                    this.rateLimits = { ...this.rateLimits, ...data.rate_limits };
                    this.updateRateLimitDisplay(this.rateLimits);
                }
            })
            .catch(error => {
                console.error('Error fetching updated rate limits:', error);
            });
    }
    
    retryUserInfo() {
        // Retry getting user info when it's in loading state
        fetch('/api/retry-user-info', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Refresh the page or update the display
                    this.checkAuthStatus();
                }
            })
            .catch(error => {
                console.error('Error retrying user info:', error);
            });
    }
    
    // Single unfollow removed - focusing on batch operations only
    
    // Extract usernames functionality removed - use CSV import instead
    
    getLoggedInUsername() {
        const usernameDisplay = document.getElementById('username-display');
        const username = usernameDisplay ? usernameDisplay.textContent.trim() : null;
        // If username is 'User' (placeholder), return null to skip filtering
        return (username && username !== 'User') ? username : null;
    }
    
    // Complex timer functions removed - were causing excessive API calls

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
            
            const newUsers = usernames.map((username, index) => ({
                id: `csv_${Date.now()}_${index}`,
                username: username.trim(),
                source: 'csv'
            }));
            
            // Merge with existing list, avoiding duplicates
            const existingUsernames = new Set(this.csvUserList.map(u => u.username));
            const uniqueNewUsers = newUsers.filter(u => !existingUsernames.has(u.username));
            
            this.csvUserList = [...this.csvUserList, ...uniqueNewUsers];
            this.renderCSVList();
            this.saveCSVListToStorage();
            this.showStatus('success', `Loaded ${uniqueNewUsers.length} new usernames from CSV (${this.csvUserList.length} total)`);
            
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
        // More permissive username validation for X usernames
        // Allow letters, numbers, underscores, 1-15 characters
        if (!username || username.length === 0 || username.length > 15) {
            return false;
        }
        // Basic pattern but more lenient
        return /^[a-zA-Z0-9_]+$/.test(username);
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
            console.log('Showing CSV list container'); // Debug for extract usernames
            if (emptyEl) emptyEl.classList.add('d-none');
            if (containerEl) containerEl.classList.remove('d-none');
        } else {
            console.log('Hiding CSV list container'); // Debug for extract usernames
            if (emptyEl) emptyEl.classList.remove('d-none');
            if (containerEl) containerEl.classList.add('d-none');
        }
        
        this.selectedUsers.clear();
        this.updateSelectedCount();
    }
    
    clearCSVList() {
        this.csvUserList = [];
        this.selectedUsers.clear();
        this.renderCSVList();
        document.getElementById('csv-file-input').value = '';
        this.saveCSVListToStorage();
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
    
    async handleBatchUnfollow() {
        // UX Layer 1: Simple batch start flow
        if (this.isProcessing) return;
        
        const selectedUsernames = [...this.selectedUsers];
        
        // UX Layer 1: Basic validation
        if (selectedUsernames.length === 0) {
            this.showStatus('warning', 'Please select at least one account to unfollow');
            return;
        }
        
        if (selectedUsernames.length > 1000) {
            this.showStatus('warning', 'Maximum 1000 accounts allowed per batch');
            return;
        }
        
        // UX Layer 1: Simple confirmation
        const estimatedHours = Math.round((selectedUsernames.length - 1) * 15 / 60 * 10) / 10;
        const confirmMessage = `Start batch unfollow for ${selectedUsernames.length} accounts?\n\n` +
                              `Estimated duration: ${estimatedHours} hours\n` +
                              `15-minute intervals between unfollows\n\n` +
                              `Continue?`;
        
        if (!confirm(confirmMessage)) return;
        
        // UX Layer 1: Simple processing state
        this.isProcessing = true;
        this.setButtonState('regular-batch-btn', true, 'Starting batch...');
        
        try {
            // UX Layer 1: Simple API call
            const response = await fetch('/unfollow/slow-batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    usernames: selectedUsernames, 
                    interval_minutes: 15,
                    batch_type: 'regular'
                })
            });
            
            const data = await response.json();
            
            // UX Layer 1: Simple response handling
            if (response.ok && data.success) {
                if (data.queued) {
                    this.showStatus('info', `Batch queued at position ${data.queue_position}`);
                } else {
                    this.showStatus('success', `Batch started for ${selectedUsernames.length} users`);
                }
                this.selectNone();
                this.loadSlowBatchOperations();
            } else {
                this.showStatus('error', data.error || 'Failed to start batch');
            }
            
        } catch (error) {
            console.error('Batch error:', error);
            this.showStatus('error', 'Network error occurred');
        } finally {
            // UX Layer 1: Reset button state
            this.isProcessing = false;
            this.setButtonState('regular-batch-btn', false, 
                '<i class="fas fa-users-slash me-2"></i>Start Batch Unfollow<br><small class="d-block">15 minute intervals</small>');
        }
    }
    
    async refreshToken() {
        try {
            const response = await fetch('/refresh-token', { method: 'POST' });
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showStatus('success', 'Authentication token refreshed successfully');
                this.checkAuthStatus(); // Check auth status after token refresh
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
    
    showStatus(type, message, duration = 10000) {
        // Update compact status in header
        const icon = document.getElementById('status-icon-compact');
        const messageEl = document.getElementById('status-message-compact');
        
        if (!icon || !messageEl) return;
        
        // Set icon and color
        const iconConfig = {
            success: { class: 'fas fa-check-circle text-success', color: 'text-success' },
            error: { class: 'fas fa-exclamation-circle text-danger', color: 'text-danger' },
            warning: { class: 'fas fa-exclamation-triangle text-warning', color: 'text-warning' },
            info: { class: 'fas fa-info-circle text-info', color: 'text-info' }
        }[type] || { class: 'fas fa-info-circle text-info', color: 'text-info' };
        
        icon.innerHTML = `<i class="${iconConfig.class}"></i>`;
        messageEl.textContent = message;
        messageEl.className = `small ${iconConfig.color}`;
        
        // Add to alert log
        this.addToAlertLog(type, message);
        
        // Auto-reset to "Ready" after duration
        if (duration > 0) {
            setTimeout(() => {
                icon.innerHTML = '<i class="fas fa-info-circle text-info"></i>';
                messageEl.textContent = 'Ready';
                messageEl.className = 'small';
            }, duration);
        }
    }
    
    addToAlertLog(type, message) {
        const timestamp = new Date();
        this.alertLog.unshift({
            type: type,
            message: message,
            timestamp: timestamp.toLocaleTimeString()
        });
        
        // Keep only last 50 alerts
        if (this.alertLog.length > 50) {
            this.alertLog = this.alertLog.slice(0, 50);
        }
        
        // Update alert log display if panel is visible
        const panel = document.getElementById('alert-log-panel');
        if (panel && !panel.classList.contains('d-none')) {
            this.updateAlertLogDisplay();
        }
    }
    
    updateAlertLogDisplay() {
        const logContent = document.getElementById('alert-log-content');
        if (!logContent) return;
        
        if (this.alertLog.length === 0) {
            logContent.innerHTML = '<div class="text-muted text-center">No alerts yet...</div>';
            return;
        }
        
        const logHtml = this.alertLog.map(alert => {
            const iconConfig = {
                success: 'fas fa-check-circle text-success',
                error: 'fas fa-exclamation-circle text-danger',
                warning: 'fas fa-exclamation-triangle text-warning',
                info: 'fas fa-info-circle text-info'
            }[alert.type] || 'fas fa-info-circle text-info';
            
            return `
                <div class="d-flex align-items-start mb-1">
                    <i class="${iconConfig} me-2 mt-1" style="font-size: 12px;"></i>
                    <div class="flex-grow-1">
                        <div class="text-truncate">${alert.message}</div>
                        <div class="text-muted" style="font-size: 10px;">${alert.timestamp}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        logContent.innerHTML = logHtml;
        
        // Auto-scroll to top (newest)
        logContent.scrollTop = 0;
    }
    
    toggleAlertLog() {
        const panel = document.getElementById('alert-log-panel');
        const button = document.getElementById('toggle-alert-log');
        
        if (!panel || !button) return;
        
        if (panel.classList.contains('d-none')) {
            panel.classList.remove('d-none');
            this.updateAlertLogDisplay();
            button.innerHTML = '<i class="fas fa-times"></i>';
            button.title = 'Hide Alert Log';
        } else {
            panel.classList.add('d-none');
            button.innerHTML = '<i class="fas fa-history"></i>';
            button.title = 'Toggle Alert Log';
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
    
    async handleSlowBatch(intervalMinutes) {
        if (this.isProcessing) return;
        
        const selectedUsernames = [...this.selectedUsers];
        
        if (selectedUsernames.length === 0) {
            this.showStatus('warning', 'Please select at least one account to unfollow');
            return;
        }
        
        if (selectedUsernames.length > 100) {
            this.showStatus('warning', 'Maximum 100 accounts allowed for slow batch');
            return;
        }
        
        // Simple estimation: use the interval time as base
        const estimatedHours = Math.round((selectedUsernames.length - 1) * intervalMinutes / 60 * 10) / 10;
        
        const confirmMessage = `Start slow batch unfollow for ${selectedUsernames.length} accounts?\n\n` +
                              `• 1 unfollow every ${intervalMinutes} minutes\n` +
                              `• Estimated duration: ${estimatedHours} hours\n` +
                              `• You can monitor progress and cancel if needed\n\n` +
                              `This will run in the background. Continue?`;
        
        if (!confirm(confirmMessage)) return;
        
        this.isProcessing = true;
        const buttonId = intervalMinutes === 5 ? 'slow-batch-5min-btn' : 'slow-batch-15min-btn';
        this.setButtonState(buttonId, true, 'Starting...');
        
        try {
            const response = await fetch('/unfollow/slow-batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ usernames: selectedUsernames, interval_minutes: intervalMinutes })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showStatus('success', `Started ${intervalMinutes}-minute slow batch operation for ${selectedUsernames.length} users (${data.estimated_duration_hours} hours)`);
                this.selectNone(); // Clear selections
                this.loadSlowBatchOperations(); // Refresh operations list
            } else {
                this.showStatus('error', data.error || 'Failed to start slow batch operation');
            }
            
        } catch (error) {
            console.error('Slow batch error:', error);
            this.showStatus('error', 'Network error occurred');
        } finally {
            this.isProcessing = false;
            const originalText = intervalMinutes === 5 ? 
                '<i class="fas fa-clock me-2"></i>Slow 5min<br><small class="d-block">Max 100 users</small>' :
                '<i class="fas fa-history me-2"></i>Slow 15min<br><small class="d-block">Max 100 users</small>';
            this.setButtonState(buttonId, false, originalText);
        }
    }
    
    async loadSlowBatchOperations() {
        try {
            const response = await fetch('/unfollow/slow-batch/list');
            if (!response.ok) return; // Not authenticated or error
            
            const data = await response.json();
            this.activeSlowBatchOperations = data.operations || [];
            this.renderSlowBatchOperations();
            
            // Remove successful unfollows from the CSV list
            if (data.successful_unfollows && data.successful_unfollows.length > 0) {
                let removedCount = 0;
                data.successful_unfollows.forEach(username => {
                    const wasRemoved = this.removeUsernameFromList(username);
                    if (wasRemoved) removedCount++;
                });
                
                if (removedCount > 0) {
                    console.log(`Auto-removed ${removedCount} successfully unfollowed users from CSV list`);
                }
            }
            
            // Check for completion notifications and trigger refresh
            if (data.completion_notifications && data.completion_notifications.length > 0) {
                for (const notification of data.completion_notifications) {
                    console.log(`Unfollow completion: ${notification.completed_count}/${notification.total_count} for ${notification.operation_id}`);
                }
                // Trigger refresh for rate limit updates
                setTimeout(() => this.refreshRateLimitsAndStatus(), 1000);
            }
            
            // Schedule smart checking for active operations only
            this.scheduleSmartCheck(data.operations);
            
            // Update rate limits if we got new data
            this.updateRateLimitsFromOperations(data.operations);
            
        } catch (error) {
            console.error('Error loading slow batch operations:', error);
        }
    }
    
    updateRateLimitsFromOperations(operations) {
        // Check if any operation has current rate limit data
        for (const operation of operations) {
            if (operation.status === 'running' && operation.rate_limits) {
                // Update our rate limits with the latest data
                this.rateLimits = operation.rate_limits;
                this.updateRateLimitDisplay(this.rateLimits);
                break; // Use the first active operation's rate limits
            }
        }
    }
    
    // Removed complex completion detection - using backend recent_completion flag instead

    async manualRefresh() {
        // Manual refresh with visual feedback
        const refreshBtn = document.getElementById('refresh-operations-btn');
        const originalText = refreshBtn.innerHTML;
        
        try {
            // Show loading state
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
            refreshBtn.disabled = true;
            
            // Refresh both rate limits and operations
            await this.refreshRateLimitsAndStatus();
            
            // Brief success feedback
            refreshBtn.innerHTML = '<i class="fas fa-check me-1"></i>Updated';
            setTimeout(() => {
                refreshBtn.innerHTML = originalText;
                refreshBtn.disabled = false;
            }, 1000);
            
        } catch (error) {
            console.error('Manual refresh error:', error);
            refreshBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error';
            setTimeout(() => {
                refreshBtn.innerHTML = originalText;
                refreshBtn.disabled = false;
            }, 2000);
        }
    }

    async refreshRateLimitsAndStatus() {
        // Refresh rate limits and status without excessive UI updates
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            if (data.rate_limits) {
                this.updateRateLimitDisplay(data.rate_limits);
            }
            
            // Also refresh operations list for latest data
            this.loadSlowBatchOperations();
            
        } catch (error) {
            console.error('Error refreshing rate limits:', error);
        }
    }

    checkInitialUnfollow() {
        // Check for the first unfollow completion after starting a batch
        // Wait a few seconds for the initial unfollow to process, then check once
        setTimeout(async () => {
            try {
                const response = await fetch('/unfollow/slow-batch/list');
                const data = await response.json();
                
                // Check if any operation shows a completion
                for (const operation of data.operations || []) {
                    if (operation.completed_count > 0) {
                        console.log(`Initial unfollow detected for ${operation.id}: ${operation.completed_count} completed`);
                        // Refresh to show updated rate limits
                        this.refreshRateLimitsAndStatus();
                        break;
                    }
                }
                
            } catch (error) {
                console.error('Error checking initial unfollow:', error);
            }
        }, 1000); // Wait 1 second for first unfollow to process
    }

    scheduleSmartCheck(operations) {
        // Clear any existing smart check timer
        if (this.smartCheckTimer) {
            clearTimeout(this.smartCheckTimer);
            this.smartCheckTimer = null;
        }
        
        // Only schedule if there are active operations
        const activeOperations = operations && operations.filter(op => op.status === 'running');
        if (!activeOperations || activeOperations.length === 0) {
            console.log('No active operations - smart checking disabled');
            return;
        }
        
        // Calculate when the NEXT unfollow should happen
        let nextCheckTime = this.calculateNextUnfollowTime(activeOperations);
        
        if (nextCheckTime) {
            this.smartCheckTimer = setTimeout(() => {
                console.log('Smart check: Looking for unfollow completions...');
                this.loadSlowBatchOperations(); // This will check for completion notifications
            }, nextCheckTime);
            
            console.log(`Smart check scheduled for ${(nextCheckTime/60000).toFixed(1)} minutes (next expected unfollow + 1min buffer)`);
        }
    }

    calculateNextUnfollowTime(activeOperations) {
        // Calculate when the next unfollow should happen based on batch progress
        for (const operation of activeOperations) {
            if (operation.start_time && operation.completed_count !== undefined) {
                // Parse start time (format: "2025-06-13 15:29:16")
                const startTime = new Date(operation.start_time).getTime();
                const completedCount = operation.completed_count;
                const totalCount = operation.total_count;
                // If all unfollows are done, no need to check
                if (completedCount >= totalCount) {
                    continue;
                }
                
                // Simple timing calculation with small margin
                // Use the actual interval with small buffer for API timing
                const expectedUnfollowTime = startTime + (completedCount * operation.interval_minutes * 60 * 1000);
                const checkTime = expectedUnfollowTime + (60 * 1000); // +1 minute buffer
                
                // Calculate milliseconds from now
                const now = Date.now();
                const timeUntilCheck = checkTime - now;
                
                // Don't schedule if time has already passed or is too soon
                if (timeUntilCheck > 30000) { // At least 30 seconds in the future
                    return timeUntilCheck;
                }
            }
        }
        
        return null; // No valid check time found
    }

    // Removed SSE event stream - using direct completion notifications instead

    // Removed automatic timer refresh - now only refreshes on actual unfollow completions
    
    renderSlowBatchOperations() {
        const container = document.getElementById('slow-batch-operations-container');
        const list = document.getElementById('slow-batch-operations-list');
        
        if (!container || !list) return;
        
        if (this.activeSlowBatchOperations.length === 0) {
            container.style.display = 'none';
            return;
        }
        
        container.style.display = 'block';
        list.innerHTML = '';
        
        this.activeSlowBatchOperations.forEach(operation => {
            const operationEl = document.createElement('div');
            operationEl.className = 'border rounded p-3 mb-3';
            
            const statusColor = {
                'running': 'text-success',
                'starting': 'text-info',
                'queued': 'text-primary',
                'waiting_for_lookup_reset': 'text-warning',
                'completed': 'text-secondary',
                'cancelled': 'text-warning',
                'error': 'text-danger'
            }[operation.status] || 'text-muted';
            
            operationEl.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">
                            <span class="${statusColor}">
                                <i class="fas fa-circle me-1" style="font-size: 0.5rem;"></i>
                                ${operation.status.charAt(0).toUpperCase() + operation.status.slice(1)}
                            </span>
                            - ${operation.total_count} users
                        </h6>
                        <div class="small text-muted">
                            Progress: ${operation.completed_count}/${operation.total_count} 
                            (${operation.success_count} successful)
                        </div>
                        <div class="small text-muted" id="timer-${operation.operation_id}">
                            ${operation.status === 'queued' ? `Queue position: ${operation.queue_position || 'Unknown'}` : 
                              operation.status === 'waiting_for_lookup_reset' ? `Waiting for rate limit reset: ${operation.lookup_wait_minutes ? Math.ceil(operation.lookup_wait_minutes) + 'm remaining' : 'Processing...'}` :
                              `Started: ${operation.start_time || 'Not started'}`}
                        </div>
                        ${operation.estimated_completion ? `<div class="small text-muted">Est. completion: ${operation.estimated_completion}</div>` : ''}
                    </div>
                    <div class="ms-3">
                        <button type="button" class="btn btn-outline-info btn-sm me-2" 
                                onclick="window.xUnfollowApp.showOperationDetails('${operation.operation_id}')">
                            <i class="fas fa-info-circle"></i> Details
                        </button>
                        ${operation.status === 'running' || operation.status === 'starting' || operation.status === 'queued' || operation.status === 'waiting_for_lookup_reset' ? 
                            `<button type="button" class="btn btn-outline-danger btn-sm" 
                                     onclick="window.xUnfollowApp.cancelOperation('${operation.operation_id}')">
                                <i class="fas fa-stop"></i> Cancel
                             </button>` : ''}
                    </div>
                </div>
                <div class="progress mt-2" style="height: 8px;">
                    <div class="progress-bar ${operation.status === 'completed' ? 'bg-success' : operation.status === 'error' ? 'bg-danger' : operation.status === 'queued' || operation.status === 'waiting_for_lookup_reset' ? 'bg-warning' : 'bg-info'}" 
                         style="width: ${(operation.completed_count / operation.total_count) * 100}%"></div>
                </div>
            `;
            
            list.appendChild(operationEl);
            
            // Add timer functionality for active operations
            if (operation.status === 'running') {
                this.updateOperationTimer(operation.operation_id, operation.start_time);
            }
        });
    }
    
    async showOperationDetails(operationId) {
        try {
            const response = await fetch(`/unfollow/slow-batch/${operationId}/status`);
            const data = await response.json();
            
            if (response.ok) {
                const details = `
Operation ID: ${data.operation_id}
Status: ${data.status}

Progress:
• Completed: ${data.progress.completed}/${data.progress.total} (${data.progress.percentage}%)
• Successful: ${data.progress.successful}
• Failed: ${data.progress.failed}

Current:
• Processing: @${data.current.username || 'None'}

Timing:
• Elapsed: ${data.timing.elapsed_minutes} minutes
• Next unfollow in: ${data.timing.next_unfollow_in_minutes} minutes
• Estimated completion: ${data.timing.estimated_completion}
                `;
                
                alert(details);
            } else {
                this.showStatus('error', data.error || 'Failed to get operation details');
            }
        } catch (error) {
            console.error('Error getting operation details:', error);
            this.showStatus('error', 'Network error occurred');
        }
    }
    
    async cancelOperation(operationId) {
        if (!confirm('Are you sure you want to cancel this slow batch operation?')) return;
        
        try {
            const response = await fetch(`/unfollow/slow-batch/${operationId}/cancel`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showStatus('success', data.message);
                this.loadSlowBatchOperations(); // Refresh list
            } else {
                this.showStatus('error', data.error || 'Failed to cancel operation');
            }
        } catch (error) {
            console.error('Error cancelling operation:', error);
            this.showStatus('error', 'Network error occurred');
        }
    }
    
    async clearAllBatches() {
        if (!confirm('Are you sure you want to clear ALL batch operations? This will remove all active, queued, and completed batches.')) return;
        
        try {
            const response = await fetch('/debug/clear-batches', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showStatus('success', `Cleared ${data.cleared_operations} batch operations`);
                this.loadSlowBatchOperations(); // Refresh list
            } else {
                this.showStatus('error', data.error || 'Failed to clear batches');
            }
        } catch (error) {
            console.error('Error clearing batches:', error);
            this.showStatus('error', 'Network error occurred');
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 JavaScript loading...'); // Debug
    try {
        window.xUnfollowApp = new XUnfollowApp();
        console.log('✅ App initialized successfully'); // Debug
    } catch (error) {
        console.error('❌ App initialization failed:', error); // Debug
    }
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

// Complex rate limit message and timer functions removed - were causing API waste and UI complexity

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