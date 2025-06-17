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
        this.rateLimits = {
            unfollow: { remaining: 'unknown', reset: 0, limit: 'unknown' },
            unfollow_hourly: { remaining: 'unknown', reset: 0, limit: 'unknown' },
            unfollow_daily: { remaining: 'unknown', reset: 0, limit: 'unknown' }
        };
        
        this.init();
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
        }
    }
    
    init() {
        this.bindEvents();
        this.loadRateLimits();
        this.checkAuthStatus();
        this.loadSlowBatchOperations();
        this.loadCSVListFromStorage();
        
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
        
        // Realistic batch buttons
        const testBatchBtn = document.getElementById('test-batch-btn');
        const regularBatchBtn = document.getElementById('regular-batch-btn');
        if (testBatchBtn) testBatchBtn.addEventListener('click', () => this.handleRealisticBatch('test'));
        if (regularBatchBtn) regularBatchBtn.addEventListener('click', () => this.handleRealisticBatch('regular'));
        
        // Debug text extraction button
        const extractBtn = document.getElementById('extract-usernames-btn');
        if (extractBtn) extractBtn.addEventListener('click', () => this.handleExtractUsernames());
        
        // Kept for backward compatibility with existing operations
        const slowBatch15minBtn = document.getElementById('slow-batch-15min-btn');
        if (slowBatch15minBtn) slowBatch15minBtn.addEventListener('click', () => this.handleSlowBatch(15));
        
        // Refresh operations button
        const refreshOpsBtn = document.getElementById('refresh-operations-btn');
        if (refreshOpsBtn) refreshOpsBtn.addEventListener('click', () => this.loadSlowBatchOperations());
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
        const unfollowHourEl = document.getElementById('unfollow-rate-limit-hour');
        const unfollowDayEl = document.getElementById('unfollow-rate-limit-day');
        
        // Update hourly rate limits from persistent tracking data
        if (unfollowHourEl && rateLimits.unfollow_hourly) {
            const remaining = rateLimits.unfollow_hourly.remaining;
            const limit = rateLimits.unfollow_hourly.limit;
            
            if (remaining === 'unknown' || limit === 'unknown') {
                unfollowHourEl.textContent = 'Loading...';
                unfollowHourEl.className = 'badge bg-secondary';
            } else {
                unfollowHourEl.textContent = `${remaining}/${limit}`;
                unfollowHourEl.className = `badge ${remaining > 2 ? 'bg-success' : remaining > 0 ? 'bg-warning' : 'bg-danger'}`;
            }
        }
        
        // Update daily rate limits from persistent tracking data  
        if (unfollowDayEl && rateLimits.unfollow_daily) {
            const remaining = rateLimits.unfollow_daily.remaining;
            const limit = rateLimits.unfollow_daily.limit;
            
            if (remaining === 'unknown' || limit === 'unknown') {
                unfollowDayEl.textContent = 'Loading...';
                unfollowDayEl.className = 'badge bg-secondary';
            } else {
                unfollowDayEl.textContent = `${remaining}/${limit}`;
                unfollowDayEl.className = `badge ${remaining > 10 ? 'bg-success' : remaining > 0 ? 'bg-warning' : 'bg-danger'}`;
            }
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
                this.removeUsernameFromList(target); // Remove from list if present
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
    
    handleExtractUsernames() {
        console.log('🔍 handleExtractUsernames called!'); // Debug - check if function is called
        
        const textInput = document.getElementById('debug-text-input');
        const extractedCountEl = document.getElementById('extracted-count');
        const extractedNumberEl = document.getElementById('extracted-number');
        
        console.log('Elements found:', { textInput: !!textInput, extractedCountEl: !!extractedCountEl, extractedNumberEl: !!extractedNumberEl }); // Debug
        
        if (!textInput) {
            console.error('debug-text-input element not found!');
            return;
        }
        
        const text = textInput.value.trim();
        if (!text) {
            this.showStatus('warning', 'Please paste some text from X following page');
            return;
        }
        
        this.showStatus('info', 'Extracting usernames from pasted text...');
        
        try {
            const usernames = this.extractUsernamesFromText(text);
            console.log('Extracted usernames:', usernames); // Debug logging
            
            if (usernames.length === 0) {
                this.showStatus('warning', 'No valid @usernames found in the text');
                if (extractedCountEl) extractedCountEl.classList.add('d-none');
                return;
            }
            
            // Add extracted usernames to CSV list
            const newUsers = usernames.map((username, index) => ({
                id: `extract_${Date.now()}_${index}`,
                username: username,
                source: 'extracted'
            }));
            
            console.log('New users to add:', newUsers); // Debug
            
            // Merge with existing CSV list, avoiding duplicates
            const existingUsernames = new Set(this.csvUserList.map(u => u.username));
            const uniqueNewUsers = newUsers.filter(u => !existingUsernames.has(u.username));
            
            console.log('Unique new users after dedup:', uniqueNewUsers); // Debug
            console.log('CSV list before:', this.csvUserList.length); // Debug
            
            this.csvUserList = [...this.csvUserList, ...uniqueNewUsers];
            
            console.log('CSV list after:', this.csvUserList.length); // Debug
            
            this.renderCSVList();
            this.saveCSVListToStorage();
            
            // Update extracted count display
            if (extractedCountEl && extractedNumberEl) {
                extractedNumberEl.textContent = usernames.length;
                extractedCountEl.classList.remove('d-none');
            }
            
            this.showStatus('success', `Extracted ${usernames.length} usernames (${uniqueNewUsers.length} new)`);
            textInput.value = ''; // Clear the input
            
        } catch (error) {
            console.error('Username extraction error:', error);
            this.showStatus('error', 'Failed to extract usernames from text');
        }
    }
    
    extractUsernamesFromText(text) {
        const usernames = [];
        
        console.log('Input text:', text); // Debug logging
        
        // Simple parsing - treat each line as a potential username
        const lines = text.split(/[\n\r]+/);
        console.log('Split into lines:', lines); // Debug logging
        
        lines.forEach((line, index) => {
            line = line.trim();
            if (!line) return;
            
            // Remove @ symbol if present and clean the username
            const username = line.replace(/^@/, '').trim();
            console.log(`Line ${index}: "${line}" -> username: "${username}"`); // Debug logging
            
            // Validate and add username
            if (username && this.isValidUsername(username)) {
                usernames.push(username);
                console.log(`Added valid username: ${username}`); // Debug logging
            } else {
                console.log(`Invalid username rejected: "${username}"`); // Debug logging
            }
        });
        
        // Remove duplicates
        const uniqueUsernames = [...new Set(usernames)];
        console.log('Unique usernames:', uniqueUsernames); // Debug logging
        
        // Remove logged-in user from the list
        const loggedInUsername = this.getLoggedInUsername();
        if (loggedInUsername) {
            const filtered = uniqueUsernames.filter(username => username.toLowerCase() !== loggedInUsername.toLowerCase());
            console.log(`Filtered out logged-in user (${loggedInUsername}):`, filtered); // Debug logging
            return filtered;
        }
        
        return uniqueUsernames;
    }
    
    getLoggedInUsername() {
        const usernameDisplay = document.getElementById('username-display');
        return usernameDisplay ? usernameDisplay.textContent.trim() : null;
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
    
    async handleRealisticBatch(type) {
        if (this.isProcessing) return;
        
        const selectedUsernames = [...this.selectedUsers];
        const maxUsers = type === 'test' ? 5 : 1000; // Test: 5 users, Regular: unlimited
        const buttonId = type === 'test' ? 'test-batch-btn' : 'regular-batch-btn';
        
        if (selectedUsernames.length === 0) {
            this.showStatus('warning', 'Please select at least one account to unfollow');
            return;
        }
        
        if (selectedUsernames.length > maxUsers) {
            this.showStatus('warning', `Maximum ${maxUsers} accounts allowed for ${type} batch`);
            return;
        }
        
        // Calculate estimated duration (15 minutes per unfollow)
        const estimatedHours = Math.round(selectedUsernames.length * 15 / 60 * 10) / 10;
        const batchName = type === 'test' ? 'Test Batch' : 'Regular Batch';
        
        const confirmMessage = `Start ${batchName} for ${selectedUsernames.length} accounts?\n\n` +
                              `• 1 unfollow every 15 minutes\n` +
                              `• Estimated duration: ${estimatedHours} hours\n` +
                              `• Respects free API tier limits\n` +
                              `• You can monitor progress and cancel if needed\n\n` +
                              `This will run in the background. Continue?`;
        
        if (!confirm(confirmMessage)) return;
        
        this.isProcessing = true;
        this.setButtonState(buttonId, true, 'Starting...');
        
        try {
            const response = await fetch('/unfollow/slow-batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    usernames: selectedUsernames, 
                    interval_minutes: 15,
                    batch_type: type
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showStatus('success', `Started ${batchName} for ${selectedUsernames.length} users (${data.estimated_duration_hours} hours)`);
                this.selectNone(); // Clear selections
                this.loadSlowBatchOperations(); // Refresh operations list
            } else {
                this.showStatus('error', data.error || `Failed to start ${batchName}`);
            }
            
        } catch (error) {
            console.error('Realistic batch error:', error);
            this.showStatus('error', 'Network error occurred');
        } finally {
            this.isProcessing = false;
            const originalText = type === 'test' ? 
                '<i class="fas fa-flask me-2"></i>Test Batch<br><small class="d-block">1-5 users • 15 min intervals</small>' :
                '<i class="fas fa-users-slash me-2"></i>Regular Batch<br><small class="d-block">Unlimited users • 15 min intervals</small>';
            this.setButtonState(buttonId, false, originalText);
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
        
        // Calculate estimated duration
        const estimatedHours = Math.round(selectedUsernames.length * intervalMinutes / 60 * 10) / 10;
        
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
                data.successful_unfollows.forEach(username => {
                    this.removeUsernameFromList(username);
                });
            }
            
            // Smart refresh timing based on operation progress
            if (data.active_count > 0) {
                let refreshInterval = this.calculateRefreshInterval(data.operations);
                setTimeout(() => this.loadSlowBatchOperations(), refreshInterval);
            }
            
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
    
    calculateRefreshInterval(operations) {
        // Smart refresh timing: frequent after first unfollow, then match unfollow intervals
        for (const operation of operations) {
            if (operation.status === 'running') {
                // If this is a new operation (completed_count 0 or 1), refresh more frequently
                if (operation.completed_count <= 1) {
                    return 60000; // 1 minute for new operations
                }
                // For ongoing operations, refresh every 15 minutes (match unfollow intervals)
                return 900000; // 15 minutes
            }
        }
        // Default for non-running operations
        return 60000; // 1 minute
    }
    
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
                        <div class="small text-muted">
                            Started: ${operation.start_time || 'Not started'}
                        </div>
                        <div class="small text-muted">
                            Last activity: ${operation.last_activity || 'Unknown'}
                        </div>
                        ${operation.estimated_completion ? `<div class="small text-muted">Est. completion: ${operation.estimated_completion}</div>` : ''}
                    </div>
                    <div class="ms-3">
                        <button type="button" class="btn btn-outline-info btn-sm me-2" 
                                onclick="window.xUnfollowApp.showOperationDetails('${operation.operation_id}')">
                            <i class="fas fa-info-circle"></i> Details
                        </button>
                        ${operation.status === 'running' || operation.status === 'starting' ? 
                            `<button type="button" class="btn btn-outline-danger btn-sm" 
                                     onclick="window.xUnfollowApp.cancelOperation('${operation.operation_id}')">
                                <i class="fas fa-stop"></i> Cancel
                             </button>` : ''}
                    </div>
                </div>
                <div class="progress mt-2" style="height: 8px;">
                    <div class="progress-bar ${operation.status === 'completed' ? 'bg-success' : operation.status === 'error' ? 'bg-danger' : 'bg-info'}" 
                         style="width: ${(operation.completed_count / operation.total_count) * 100}%"></div>
                </div>
            `;
            
            list.appendChild(operationEl);
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