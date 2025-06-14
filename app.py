"""
Flask web application for unfollowing X accounts via X API v2.
Implements OAuth 2.0 authentication and batch unfollowing functionality.
"""

import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import time
import threading
import json
from datetime import datetime, timedelta
from api import XAPIClient
from config import CLIENT_ID, CLIENT_SECRET, CALLBACK_URL, SESSION_TIMEOUT, DEVELOPMENT_MODE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
# Use a fixed secret key for development to maintain sessions across restarts
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-for-testing-only-change-in-production')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Configure session for development
if DEVELOPMENT_MODE:
    app.permanent_session_lifetime = SESSION_TIMEOUT
    app.config['SESSION_PERMANENT'] = True

# Initialize X API client
x_client = XAPIClient(CLIENT_ID, CLIENT_SECRET, CALLBACK_URL)

# Global variable to track slow batch operations
slow_batch_operations = {}

def cleanup_old_operations():
    """Clean up old completed/cancelled/error operations to prevent memory buildup."""
    try:
        current_time = time.time()
        cutoff_time = current_time - (24 * 60 * 60)  # 24 hours ago
        
        operations_to_remove = []
        for op_id, operation in slow_batch_operations.items():
            # Keep active operations
            if operation['status'] in ['starting', 'running', 'waiting_for_rate_limit_reset']:
                continue
                
            # Remove old completed/cancelled/error operations
            end_time = operation.get('end_time', operation.get('start_time', current_time))
            if end_time < cutoff_time:
                operations_to_remove.append(op_id)
        
        # Remove old operations
        for op_id in operations_to_remove:
            del slow_batch_operations[op_id]
            
        if operations_to_remove:
            logging.info(f"Cleaned up {len(operations_to_remove)} old batch operations")
            
    except Exception as e:
        logging.error(f"Error during operation cleanup: {str(e)}")

# Persistent unfollow tracking
UNFOLLOW_LOG_FILE = 'unfollow_tracking.json'

def load_unfollow_log():
    """Load persistent unfollow tracking log."""
    try:
        if os.path.exists(UNFOLLOW_LOG_FILE):
            with open(UNFOLLOW_LOG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Error loading unfollow log: {str(e)}")
    
    return {'attempts': []}

def save_unfollow_log(log_data):
    """Save persistent unfollow tracking log."""
    try:
        with open(UNFOLLOW_LOG_FILE, 'w') as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving unfollow log: {str(e)}")

def clean_old_entries(log_data):
    """Remove entries older than 24 hours."""
    current_time = time.time()
    cutoff_time = current_time - (24 * 60 * 60)  # 24 hours ago
    
    log_data['attempts'] = [
        attempt for attempt in log_data['attempts'] 
        if attempt['timestamp'] > cutoff_time
    ]
    return log_data

def track_unfollow_attempt(success):
    """Track an unfollow attempt with persistent storage."""
    try:
        log_data = load_unfollow_log()
        
        # Clean old entries (older than 24 hours)
        log_data = clean_old_entries(log_data)
        
        # Add new attempt
        attempt = {
            'timestamp': time.time(),
            'success': success,
            'date': datetime.now().isoformat()
        }
        log_data['attempts'].append(attempt)
        
        # Save back to file
        save_unfollow_log(log_data)
        
        # Log current stats
        current_time = time.time()
        hour_ago = current_time - 3600
        day_ago = current_time - (24 * 60 * 60)
        
        hourly_successful = len([a for a in log_data['attempts'] if a['timestamp'] > hour_ago and a['success']])
        daily_successful = len([a for a in log_data['attempts'] if a['timestamp'] > day_ago and a['success']])
        
        logging.info(f"Unfollow tracking: {hourly_successful} successful in last hour, {daily_successful} successful in last 24h")
        
    except Exception as e:
        logging.error(f"Error tracking unfollow attempt: {str(e)}")

def get_unfollow_stats():
    """Get current unfollow statistics."""
    try:
        log_data = load_unfollow_log()
        log_data = clean_old_entries(log_data)
        
        current_time = time.time()
        hour_ago = current_time - 3600
        day_ago = current_time - (24 * 60 * 60)
        
        hourly_successful = len([a for a in log_data['attempts'] if a['timestamp'] > hour_ago and a['success']])
        daily_successful = len([a for a in log_data['attempts'] if a['timestamp'] > day_ago and a['success']])
        
        return {
            'hourly_successful': hourly_successful,
            'daily_successful': daily_successful,
            'hourly_limit': 4,  # Conservative free tier estimate
            'daily_limit': 50   # Conservative free tier estimate
        }
    except Exception as e:
        logging.error(f"Error getting unfollow stats: {str(e)}")
        return {'hourly_successful': 0, 'daily_successful': 0, 'hourly_limit': 4, 'daily_limit': 50}

@app.route('/')
def index():
    """Main page with login check and unfollow interface."""
    if 'user_id' not in session:
        return render_template('index.html', authenticated=False)
    return render_template('index.html', authenticated=True, user_id=session['user_id'])

@app.route('/login')
def login():
    """Initiate OAuth 2.0 login with X."""
    try:
        auth_url = x_client.get_authorization_url()
        logging.info("Redirecting to X authorization page")
        return redirect(auth_url)
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/callback')
def callback():
    """Handle OAuth callback from X."""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            error_description = request.args.get('error_description', 'Unknown OAuth error')
            logging.error(f"OAuth error: {error} - {error_description}")
            return redirect(url_for('index') + f'?error={error}&error_description={error_description}')
        
        if not code:
            logging.error("No authorization code received")
            return redirect(url_for('index') + '?error=no_code&error_description=No authorization code received from X')
        
        # Exchange code for tokens and get user info in one transaction
        tokens = x_client.exchange_code_for_tokens(code, state)
        
        # Get user info as part of login - this should work most of the time
        try:
            user_info = x_client.get_user_info()
            if user_info:
                session.permanent = True
                session['user_id'] = user_info['id']
                session['username'] = user_info.get('username', 'Unknown')
                session['display_name'] = user_info.get('name', session['username'])
                logging.info(f"User authenticated: @{session['username']} (ID: {session['user_id']})")
            else:
                # Authentication succeeded but user info failed - still allow login
                session.permanent = True
                session['user_id'] = 'authenticated'
                session['username'] = 'User'
                session['display_name'] = 'User'
                logging.info("Authentication successful, but user info unavailable")
        except Exception as user_info_error:
            # Rate limit or other error getting user info - still allow login since auth worked
            if "Rate limit exceeded" in str(user_info_error):
                session.permanent = True
                session['user_id'] = 'authenticated'
                session['username'] = 'User'
                session['display_name'] = 'User'
                logging.info("Authentication successful, user info rate limited")
            else:
                # For non-rate-limit errors, still allow login but log the issue
                session.permanent = True
                session['user_id'] = 'authenticated'
                session['username'] = 'User'
                session['display_name'] = 'User'
                logging.warning(f"Authentication successful, but user info failed: {str(user_info_error)}")
        
        return redirect(url_for('index'))
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Callback error: {error_msg}")
        # Extract specific error info for better user feedback
        if "unauthorized_client" in error_msg:
            error_description = "OAuth configuration error. Check your X Developer Portal app settings."
        elif "invalid_client" in error_msg:
            error_description = "Invalid client credentials. Verify your Client ID and Secret."
        elif "Token exchange failed" in error_msg:
            error_description = "Failed to exchange authorization code for tokens. Check app configuration."
        else:
            error_description = error_msg
        return redirect(url_for('index') + f'?error=callback_failed&error_description={error_description}')

# Login status endpoint removed - was causing unnecessary API calls

@app.route('/logout')
def logout():
    """Log out user and clear session."""
    session.clear()
    x_client.clear_tokens()
    logging.info("User logged out")
    return redirect(url_for('index'))

@app.route('/refresh-token', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token."""
    try:
        success = x_client.refresh_access_token()
        if success:
            return jsonify({'success': True, 'message': 'Token refreshed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Token refresh failed'}), 401
    except Exception as e:
        logging.error(f"Token refresh error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Removed bloated features - focusing on core batch functionality only

# Single unfollow endpoint removed - focusing on batch operations only

# Local rate limit checking removed - handled within batch worker

# Simplified to single batch processing approach (15-minute intervals only)

@app.route('/status')
def status():
    """Get current authentication and rate limit status (simplified)."""
    try:
        authenticated = 'user_id' in session
        
        if authenticated:
            # Return cached rate limits only - no API calls to avoid waste
            rate_limits = x_client.get_rate_limit_status(refresh_from_api=False)
            
            return jsonify({
                'authenticated': True,
                'user_id': session.get('user_id'),
                'username': session.get('username'),
                'display_name': session.get('display_name'),
                'rate_limits': rate_limits
            })
        else:
            return jsonify({'authenticated': False})
            
    except Exception as e:
        logging.error(f"Status check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Debug API endpoint removed - not needed for production batch processing

# Core batch processing functions below - all debug/single features removed

def slow_batch_worker(operation_id, user_id, usernames, interval_minutes=15):
    """Background worker for slow batch unfollowing (configurable interval)."""
    operation = None
    try:
        # Initialize operation with error recovery
        if operation_id not in slow_batch_operations:
            logging.error(f"Operation {operation_id} not found in batch operations")
            return
            
        operation = slow_batch_operations[operation_id]
        operation['status'] = 'running'
        operation['start_time'] = time.time()
        operation['error_count'] = 0
        operation['consecutive_errors'] = 0
        operation['last_error'] = None
        
        # No pre-check - we'll handle rate limits on first actual unfollow attempt
        
        for i, username in enumerate(usernames):
            if operation['status'] == 'cancelled':
                break
                
            operation['current_username'] = username
            operation['current_index'] = i
            
            try:
                # Network connectivity check for critical errors
                if operation['consecutive_errors'] >= 5:
                    logging.warning(f"Batch {operation_id}: Too many consecutive errors, adding recovery delay")
                    time.sleep(30)  # 30-second recovery delay
                    operation['consecutive_errors'] = 0
                    operation['notes'] = operation.get('notes', [])
                    operation['notes'].append(f"Recovery delay applied after {operation['consecutive_errors']} consecutive errors")
                
                # Resolve username to ID with enhanced error handling
                target_id = None
                try:
                    target_id = x_client.resolve_username_to_id(username) if not username.isdigit() else username
                except Exception as resolve_error:
                    resolve_error_msg = str(resolve_error)
                    logging.error(f"Username resolution failed for {username}: {resolve_error_msg}")
                    
                    # Handle specific resolve errors
                    if "Rate limit" in resolve_error_msg:
                        operation['results'].append({'username': username, 'success': False, 'error': 'Rate limited during username resolution'})
                    elif "Network" in resolve_error_msg or "Connection" in resolve_error_msg:
                        operation['results'].append({'username': username, 'success': False, 'error': 'Network error during username resolution'})
                        operation['consecutive_errors'] += 1
                    else:
                        operation['results'].append({'username': username, 'success': False, 'error': f'Username resolution error: {resolve_error_msg}'})
                    
                    operation['failed_count'] += 1
                    operation['error_count'] += 1
                    continue
                
                if not target_id:
                    operation['results'].append({'username': username, 'success': False, 'error': 'User not found'})
                    operation['failed_count'] += 1
                    continue
                
                # Attempt unfollow with intelligent rate limit handling
                success = False
                retry_attempted = False
                error_msg = None
                
                try:
                    success = x_client.unfollow_user(user_id, target_id)
                    operation['current_rate_limits'] = x_client.get_rate_limit_status()
                    
                    if success:
                        track_unfollow_attempt(True)
                        logging.info(f"Unfollow successful for {username} ({i+1}/{len(usernames)})")
                    else:
                        track_unfollow_attempt(False)
                        error_msg = "Unfollow returned False"
                        
                except Exception as e:
                    error_msg = str(e)
                    operation['error_count'] += 1
                    operation['last_error'] = error_msg
                    
                    # Categorize error types for better handling
                    if "Network" in error_msg or "Connection" in error_msg or "timeout" in error_msg.lower():
                        operation['consecutive_errors'] += 1
                        logging.error(f"Network error unfollowing {username}: {error_msg}")
                    elif "unauthorized" in error_msg.lower() or "forbidden" in error_msg.lower():
                        logging.error(f"Authorization error unfollowing {username}: {error_msg}")
                        # Critical auth error - may need to abort batch
                        if "token" in error_msg.lower():
                            operation['notes'] = operation.get('notes', [])
                            operation['notes'].append(f"Critical auth error detected: {error_msg}")
                    else:
                        logging.error(f"Unfollow attempt failed for {username}: {error_msg}")
                    
                    # Enhanced rate limit handling - retry for any user if rate limited
                    if "Rate limit exceeded" in error_msg and not retry_attempted:
                        operation_note = f"Rate limit hit on user {i+1}/{len(usernames)} ({username})"
                        if i == 0:
                            operation_note += " - First unfollow retry to ensure smooth batch"
                        
                        logging.info(f"Rate limit exceeded for {username}. Implementing smart retry...")
                        operation['notes'] = operation.get('notes', [])
                        operation['notes'].append(operation_note)
                        operation['status'] = 'waiting_for_rate_limit_reset'
                        operation['rate_limit_retry_count'] = operation.get('rate_limit_retry_count', 0) + 1
                        
                        # Get rate limit reset time with enhanced retry logic
                        try:
                            rate_status = x_client.get_rate_limit_status()
                            reset_time = rate_status['unfollow']['reset_time']
                            current_time = time.time()
                            
                            # Progressive wait buffer - longer buffer for multiple rate limit hits
                            retry_count = operation.get('rate_limit_retry_count', 1)
                            base_buffer = 10
                            progressive_buffer = min(base_buffer * retry_count, 60)  # Max 60 second buffer
                            wait_seconds = max(0, reset_time - current_time + progressive_buffer)
                            
                            # Adaptive wait time based on batch context
                            if wait_seconds > 0:
                                # For sustained 15-minute operations, be more conservative
                                if len(usernames) > 50:  # Large batch
                                    wait_seconds += 30  # Extra 30 seconds for large batches
                                
                                operation['rate_limit_wait_until'] = reset_time + progressive_buffer
                                operation['adaptive_wait_seconds'] = wait_seconds
                                logging.info(f"Suspending batch for {int(wait_seconds)} seconds (progressive buffer: {progressive_buffer}s)...")
                                
                                # Update operation status with wait time
                                operation['waiting_for_reset'] = True
                                operation['reset_wait_seconds'] = wait_seconds
                                operation['current_username'] = f"{username} (waiting for rate limit reset)"
                                
                                # Enhanced wait with adaptive checking interval
                                wait_start = time.time()
                                check_interval = 5 if wait_seconds <= 300 else 10  # 10s intervals for long waits
                                
                                while time.time() - wait_start < wait_seconds:
                                    if operation['status'] == 'cancelled':
                                        break
                                    
                                    # Adaptive sleep interval based on remaining time
                                    remaining_wait = wait_seconds - (time.time() - wait_start)
                                    sleep_time = min(check_interval, max(1, remaining_wait))
                                    time.sleep(sleep_time)
                                    
                                    operation['reset_wait_seconds'] = max(0, remaining_wait)
                                    
                                    # Log progress for long waits (every 60 seconds)
                                    elapsed = time.time() - wait_start
                                    if elapsed > 0 and int(elapsed) % 60 == 0 and remaining_wait > 60:
                                        logging.info(f"Rate limit wait progress: {int(remaining_wait)}s remaining")
                                
                                if operation['status'] != 'cancelled':
                                    operation['status'] = 'running'
                                    operation['waiting_for_reset'] = False
                                    retry_attempted = True
                                    
                                    # Retry with enhanced validation and fallback
                                    logging.info(f"Rate limit reset. Retrying unfollow for {username} (attempt {retry_count})...")
                                    
                                    # Pre-retry validation
                                    try:
                                        # Quick rate limit check before retry
                                        pre_retry_status = x_client.get_rate_limit_status()
                                        if pre_retry_status['unfollow']['remaining'] == 0:
                                            logging.warning(f"Rate limit still active after wait, extending wait time...")
                                            time.sleep(60)  # Extra minute wait
                                    except Exception as pre_check_error:
                                        logging.warning(f"Pre-retry check failed: {str(pre_check_error)}")
                                    
                                    # Actual retry attempt
                                    try:
                                        success = x_client.unfollow_user(user_id, target_id)
                                        operation['current_rate_limits'] = x_client.get_rate_limit_status()
                                        if success:
                                            track_unfollow_attempt(True)
                                            error_msg = None  # Clear error since retry succeeded
                                            operation['consecutive_errors'] = 0  # Reset consecutive errors
                                            logging.info(f"Retry successful for {username} - batch will continue smoothly")
                                            operation['notes'].append(f"Rate limit retry #{retry_count} successful for {username}")
                                        else:
                                            track_unfollow_attempt(False)
                                            error_msg = "Retry unfollow returned False"
                                            logging.warning(f"Retry returned False for {username} despite rate limit reset")
                                    except Exception as retry_error:
                                        error_msg = str(retry_error)
                                        operation['error_count'] += 1
                                        if "Network" in str(retry_error) or "Connection" in str(retry_error):
                                            operation['consecutive_errors'] += 1
                                        
                                        # Enhanced retry error handling
                                        if "Rate limit" in str(retry_error):
                                            logging.error(f"Rate limit still active after wait for {username}: {error_msg}")
                                            operation['notes'].append(f"Rate limit retry failed - limit still active")
                                        else:
                                            logging.error(f"Retry also failed for {username}: {error_msg}")
                                        
                                        track_unfollow_attempt(False)
                        except Exception as rate_error:
                            rate_error_msg = str(rate_error)
                            operation['error_count'] += 1
                            logging.error(f"Error during rate limit handling: {rate_error_msg}")
                            
                            # Fallback rate limit handling when API status fails
                            if "Network" in rate_error_msg or "Connection" in rate_error_msg:
                                operation['consecutive_errors'] += 1
                                operation['notes'] = operation.get('notes', [])
                                operation['notes'].append(f"Rate limit handling failed due to network error: {rate_error_msg}")
                                
                                # Fallback: Use conservative 15-minute wait when status API fails
                                fallback_wait = 15 * 60  # 15 minutes
                                logging.info(f"Using fallback 15-minute wait due to rate limit API failure")
                                operation['status'] = 'waiting_for_rate_limit_reset'
                                operation['waiting_for_reset'] = True
                                operation['reset_wait_seconds'] = fallback_wait
                                operation['current_username'] = f"{username} (fallback rate limit wait)"
                                
                                # Fallback wait with cancellation support
                                fallback_start = time.time()
                                while time.time() - fallback_start < fallback_wait:
                                    if operation['status'] == 'cancelled':
                                        break
                                    time.sleep(10)  # 10-second intervals for fallback
                                    operation['reset_wait_seconds'] = max(0, fallback_wait - (time.time() - fallback_start))
                                
                                if operation['status'] != 'cancelled':
                                    operation['status'] = 'running'
                                    operation['waiting_for_reset'] = False
                                    operation['notes'].append(f"Fallback wait completed, resuming batch")
                            else:
                                # Non-network error in rate limit handling
                                operation['notes'] = operation.get('notes', [])
                                operation['notes'].append(f"Rate limit handling error: {rate_error_msg}")
                    
                    # Track failed attempt if not already tracked
                    if not success and not retry_attempted:
                        track_unfollow_attempt(False)
                        
                        # Check if we should pause batch due to repeated failures
                        if operation['consecutive_errors'] >= 3 and "Rate limit" not in error_msg:
                            logging.warning(f"Multiple consecutive errors ({operation['consecutive_errors']}) - adding stability pause")
                            operation['notes'] = operation.get('notes', [])
                            operation['notes'].append(f"Stability pause after {operation['consecutive_errors']} consecutive errors")
                            time.sleep(60)  # 1-minute stability pause
                
                if success:
                    operation['results'].append({'username': username, 'success': True})
                    operation['success_count'] += 1
                    operation['successful_usernames'] = operation.get('successful_usernames', [])
                    operation['successful_usernames'].append(username)
                    operation['consecutive_errors'] = 0  # Reset consecutive error count on success
                    logging.info(f"Slow batch {operation_id}: unfollowed @{username} ({i+1}/{len(usernames)})")
                else:
                    failure_reason = error_msg or 'Unfollow failed'
                    operation['results'].append({'username': username, 'success': False, 'error': failure_reason})
                    operation['failed_count'] += 1
                
            except Exception as e:
                error_msg = str(e)
                operation['error_count'] += 1
                operation['last_error'] = error_msg
                
                # Categorize the outer exception for better debugging
                if "Network" in error_msg or "Connection" in error_msg or "timeout" in error_msg.lower():
                    operation['consecutive_errors'] += 1
                    logging.error(f"Network error in batch {operation_id} for @{username}: {error_msg}")
                elif "Memory" in error_msg or "memory" in error_msg.lower():
                    logging.critical(f"Memory error in batch {operation_id} for @{username}: {error_msg}")
                    operation['notes'] = operation.get('notes', [])
                    operation['notes'].append(f"Memory error detected: {error_msg}")
                else:
                    logging.error(f"Slow batch {operation_id}: error unfollowing @{username}: {error_msg}")
                
                operation['results'].append({'username': username, 'success': False, 'error': error_msg})
                operation['failed_count'] += 1
            
            # Update progress with real-time timestamp
            operation['completed_count'] = i + 1
            operation['last_update'] = time.time()
            operation['last_activity'] = datetime.now().strftime('%H:%M:%S')
            
            # Log unfollow completion for frontend detection
            logging.info(f"UNFOLLOW_COMPLETED: {operation_id} - User {i+1}/{len(usernames)} - {operation['completed_count']} total completed")
            
            # Add timestamp and trigger notification
            operation['last_completion_time'] = time.time()
            operation['completion_pending'] = True  # Flag for frontend to detect
            
            # Long-running operation stability checks
            elapsed_hours = (time.time() - operation['start_time']) / 3600
            if elapsed_hours > 12:  # After 12 hours of operation
                # Periodic memory and stability logging
                if (i + 1) % 50 == 0:  # Every 50 users
                    logging.info(f"Long-running batch {operation_id}: {elapsed_hours:.1f}h elapsed, {operation['success_count']}/{i+1} successful")
                    
                # Trim old result entries to prevent excessive memory usage
                if len(operation['results']) > 1000:  # Keep last 1000 results
                    operation['results'] = operation['results'][-1000:]
                    operation['notes'] = operation.get('notes', [])
                    operation['notes'].append(f"Trimmed old results at user {i+1} for memory management")
            
            # Wait specified interval before next unfollow (except for the last one)
            if i < len(usernames) - 1 and operation['status'] != 'cancelled':
                wait_seconds = interval_minutes * 60
                operation['next_unfollow_time'] = time.time() + wait_seconds
                
                # Wait in small increments to allow for cancellation
                for wait_interval in range(wait_seconds):
                    if operation['status'] == 'cancelled':
                        break
                    time.sleep(1)
        
        # Mark as completed or handle cancellation cleanup
        if operation['status'] == 'cancelled':
            # Clean cancellation handling
            operation['end_time'] = time.time()
            operation['cancelled_at_user'] = operation.get('current_index', 0)
            operation['notes'] = operation.get('notes', [])
            operation['notes'].append(f"Operation cancelled at user {operation['cancelled_at_user'] + 1}/{len(usernames)}")
            logging.info(f"Slow batch {operation_id} cancelled: {operation['success_count']} successful, {operation['failed_count']} failed before cancellation")
        else:
            operation['status'] = 'completed'
            operation['end_time'] = time.time()
            logging.info(f"Slow batch {operation_id} completed: {operation['success_count']} successful, {operation['failed_count']} failed, {operation['error_count']} total errors")
        
    except Exception as e:
        critical_error = str(e)
        logging.critical(f"Critical error in slow batch worker for {operation_id}: {critical_error}")
        
        # Ensure operation object exists before updating it
        if operation is not None:
            operation['status'] = 'error'
            operation['error'] = critical_error
            operation['end_time'] = time.time()
            operation['notes'] = operation.get('notes', [])
            operation['notes'].append(f"Critical worker error: {critical_error}")
        else:
            # Operation object doesn't exist - log and try to create minimal error state
            logging.critical(f"Operation {operation_id} not accessible for error reporting")
            if operation_id in slow_batch_operations:
                slow_batch_operations[operation_id]['status'] = 'error'
                slow_batch_operations[operation_id]['error'] = f"Critical worker error: {critical_error}"

@app.route('/unfollow/slow-batch', methods=['POST'])
def unfollow_slow_batch():
    """Start a slow batch unfollow operation (configurable interval)."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Clean up old operations before starting new one
        cleanup_old_operations()
        
        data = request.get_json()
        usernames = data.get('usernames', [])
        interval_minutes = data.get('interval_minutes', 15)  # Default to 15 minutes
        batch_type = data.get('batch_type', 'regular')  # 'test' or 'regular'
        
        if not usernames:
            return jsonify({'error': 'No users selected'}), 400
        
        # Enforce limits based on batch type
        if batch_type == 'test' and len(usernames) > 5:
            return jsonify({'error': 'Maximum 5 users allowed for test batch'}), 400
        elif batch_type == 'regular' and len(usernames) > 1000:
            return jsonify({'error': 'Maximum 1000 users allowed for regular batch'}), 400
            
        # Only allow 15-minute intervals for free API tier
        if interval_minutes != 15:
            return jsonify({'error': 'Only 15-minute intervals supported for free API tier'}), 400
        
        # Create operation ID
        operation_id = f"{batch_type}_batch_{interval_minutes}min_{int(time.time())}_{session['user_id']}"
        
        # Initialize operation tracking
        slow_batch_operations[operation_id] = {
            'id': operation_id,
            'user_id': session['user_id'],
            'username': session.get('username', 'Unknown'),
            'status': 'starting',
            'interval_minutes': interval_minutes,
            'total_count': len(usernames),
            'completed_count': 0,
            'success_count': 0,
            'failed_count': 0,
            'current_username': None,
            'current_index': 0,
            'usernames': usernames,
            'results': [],
            'start_time': None,
            'end_time': None,
            'last_update': time.time(),
            'next_unfollow_time': None,
            'estimated_completion': time.time() + ((len(usernames) - 1) * interval_minutes * 60)
        }
        
        # Start background thread
        thread = threading.Thread(
            target=slow_batch_worker, 
            args=(operation_id, session['user_id'], usernames, interval_minutes),
            daemon=True
        )
        thread.start()
        
        logging.info(f"Started {interval_minutes}-minute slow batch operation {operation_id} for {len(usernames)} users")
        
        return jsonify({
            'success': True,
            'operation_id': operation_id,
            'message': f'Started slow batch unfollow for {len(usernames)} users ({interval_minutes}min intervals)',
            'estimated_duration_hours': round((len(usernames) - 1) * interval_minutes / 60, 1)
        })
        
    except Exception as e:
        logging.error(f"Slow batch unfollow error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/unfollow/slow-batch/<operation_id>/status')
def slow_batch_status(operation_id):
    """Get status of a slow batch operation."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        if operation_id not in slow_batch_operations:
            return jsonify({'error': 'Operation not found'}), 404
        
        operation = slow_batch_operations[operation_id]
        
        # Check if user owns this operation
        if operation['user_id'] != session['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        current_time = time.time()
        progress_percentage = (operation['completed_count'] / operation['total_count']) * 100 if operation['total_count'] > 0 else 0
        
        # Calculate time estimates
        time_elapsed = (current_time - operation['start_time']) if operation['start_time'] else 0
        time_remaining = max(0, operation['next_unfollow_time'] - current_time) if operation['next_unfollow_time'] else 0
        
        # Check for rate limit wait status
        rate_limit_info = {}
        if operation.get('waiting_for_reset'):
            rate_limit_info = {
                'waiting_for_reset': True,
                'reset_wait_seconds': operation.get('reset_wait_seconds', 0),
                'wait_until': operation.get('rate_limit_wait_until', 0)
            }
        
        return jsonify({
            'operation_id': operation_id,
            'status': operation['status'],
            'progress': {
                'completed': operation['completed_count'],
                'total': operation['total_count'],
                'percentage': round(progress_percentage, 1),
                'successful': operation['success_count'],
                'failed': operation['failed_count']
            },
            'current': {
                'username': operation['current_username'],
                'index': operation['current_index']
            },
            'timing': {
                'elapsed_minutes': round(time_elapsed / 60, 1),
                'next_unfollow_in_minutes': round(time_remaining / 60, 1),
                'estimated_completion': datetime.fromtimestamp(operation['estimated_completion']).strftime('%Y-%m-%d %H:%M:%S') if operation.get('estimated_completion') else None,
                'last_activity': operation.get('last_activity', 'Unknown')
            },
            'rate_limits': operation.get('current_rate_limits', {}),
            'rate_limit_wait': rate_limit_info,
            'last_update': operation['last_update'],
            'notes': operation.get('notes', [])
        })
        
    except Exception as e:
        logging.error(f"Slow batch status error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/unfollow/slow-batch/<operation_id>/cancel', methods=['POST'])
def cancel_slow_batch(operation_id):
    """Cancel a slow batch operation."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        if operation_id not in slow_batch_operations:
            return jsonify({'error': 'Operation not found'}), 404
        
        operation = slow_batch_operations[operation_id]
        
        # Check if user owns this operation
        if operation['user_id'] != session['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Enhanced cancellation with cleanup
        previous_status = operation['status']
        operation['status'] = 'cancelled'
        operation['end_time'] = time.time()
        operation['cancellation_reason'] = 'user_requested'
        operation['cancelled_from_status'] = previous_status
        
        # Add cancellation context to notes
        operation['notes'] = operation.get('notes', [])
        current_user = operation.get('current_username', 'unknown')
        current_index = operation.get('current_index', 0)
        operation['notes'].append(f"User cancelled operation at user: {current_user} ({current_index + 1}/{operation['total_count']})")
        
        # Log detailed cancellation info
        elapsed_time = operation['end_time'] - operation.get('start_time', operation['end_time'])
        logging.info(f"Cancelled slow batch operation {operation_id} after {elapsed_time:.1f}s (was: {previous_status})")
        
        return jsonify({
            'success': True,
            'message': 'Slow batch operation cancelled',
            'cancellation_details': {
                'cancelled_at_user': current_user,
                'cancelled_at_index': current_index + 1,
                'total_users': operation['total_count'],
                'elapsed_time_seconds': elapsed_time,
                'previous_status': previous_status
            },
            'final_stats': {
                'completed': operation['completed_count'],
                'successful': operation['success_count'],
                'failed': operation['failed_count'],
                'error_count': operation.get('error_count', 0)
            }
        })
        
    except Exception as e:
        logging.error(f"Cancel slow batch error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Removed SSE endpoint - using direct completion flags instead

@app.route('/unfollow/slow-batch/list')
def list_slow_batch_operations():
    """List all slow batch operations for the current user."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user_operations = []
        for op_id, operation in slow_batch_operations.items():
            if operation['user_id'] == session['user_id']:
                user_operations.append({
                    'operation_id': op_id,
                    'status': operation['status'],
                    'total_count': operation['total_count'],
                    'completed_count': operation['completed_count'],
                    'success_count': operation['success_count'],
                    'start_time': datetime.fromtimestamp(operation['start_time']).strftime('%Y-%m-%d %H:%M:%S') if operation['start_time'] else None,
                    'estimated_completion': datetime.fromtimestamp(operation['estimated_completion']).strftime('%Y-%m-%d %H:%M:%S') if operation.get('estimated_completion') else None
                })
        
        # Collect all successful unfollows from user's operations
        successful_unfollows = []
        completion_notifications = []
        
        for operation in slow_batch_operations.values():
            if operation['user_id'] == session['user_id']:
                successful_unfollows.extend(operation.get('successful_usernames', []))
                
                # Check for pending completion notifications
                if operation.get('completion_pending'):
                    completion_notifications.append({
                        'operation_id': operation['id'],
                        'completed_count': operation['completed_count'],
                        'total_count': operation['total_count'],
                        'timestamp': operation['last_completion_time']
                    })
                    # Clear the flag after sending
                    operation['completion_pending'] = False
        
        return jsonify({
            'operations': user_operations,
            'active_count': len([op for op in user_operations if op['status'] in ['starting', 'running']]),
            'successful_unfollows': successful_unfollows,
            'completion_notifications': completion_notifications
        })
        
    except Exception as e:
        logging.error(f"List slow batch operations error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logging.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logging.info("Starting X Unfollow Flask App")
    app.run(debug=True, host='127.0.0.1', port=5001)