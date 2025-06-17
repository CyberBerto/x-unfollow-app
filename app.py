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

# Global batch queue management
batch_queue = []  # Queue of pending batch operations
MAX_TOTAL_BATCHES = 3  # Maximum total batches (running + queued)

def get_active_batch_count(user_id):
    """Get count of active batches for a user (running + queued)."""
    active_count = 0
    
    # Count running/starting operations
    for operation in slow_batch_operations.values():
        if (operation['user_id'] == user_id and 
            operation['status'] in ['starting', 'running', 'waiting_for_rate_limit_reset']):
            active_count += 1
    
    # Count queued operations for this user
    for queued_op in batch_queue:
        if queued_op['user_id'] == user_id:
            active_count += 1
    
    return active_count

def get_running_batch(user_id):
    """Get the currently running batch for a user, if any."""
    for operation in slow_batch_operations.values():
        if (operation['user_id'] == user_id and 
            operation['status'] in ['running', 'waiting_for_rate_limit_reset']):
            return operation
    return None

def start_next_queued_batch():
    """Start the next batch in queue if no batch is currently running."""
    global batch_queue
    
    if not batch_queue:
        return
    
    # Check if any batch is currently running (across all users)
    for operation in slow_batch_operations.values():
        if operation['status'] in ['running', 'waiting_for_rate_limit_reset']:
            return  # A batch is already running, don't start another
    
    # Start the next queued batch
    next_batch = batch_queue.pop(0)
    logging.info(f"Starting queued batch {next_batch['operation_id']} for user {next_batch['user_id']}")
    
    # Start the batch thread
    thread = threading.Thread(
        target=slow_batch_worker,
        args=(next_batch['operation_id'], next_batch['user_id'], 
              next_batch['usernames'], next_batch['interval_minutes']),
        daemon=True
    )
    thread.start()

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
            
        # Try to start next queued batch after cleanup
        start_next_queued_batch()
            
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

def classify_unfollow_error(error_message, success):
    """
    Layer 2: Classify unfollow errors for intelligent wait timing.
    Enhanced to handle structured error information from X API client.
    
    Args:
        error_message (str): Error message from unfollow attempt
        success (bool): Whether unfollow was successful
        
    Returns:
        tuple: (error_type, wait_seconds)
    """
    if success:
        return "success", 15 * 60  # Normal 15-min wait
    
    # Check for enhanced error information from API client
    if hasattr(x_client, 'last_api_error') and x_client.last_api_error:
        error_info = x_client.last_api_error
        error_type = error_info.get('type', 'unknown')
        error_code = error_info.get('code', 0)
        http_status = error_info.get('http_status', 0)
        
        # Rate limit errors - wait longer
        if error_type == 'rate_limit' or http_status == 429:
            return "rate_limit", 15 * 60  # 15-minute wait
        
        # Authentication errors - require re-login
        if error_type == 'auth_error' or http_status == 401:
            return "auth_error", 15 * 60  # 15-minute wait
        
        # Permission errors - permanent issue
        if error_type == 'permission_error' or http_status == 403:
            return "permission_error", 15 * 60  # 15-minute wait
        
        # Server errors - retry later
        if error_type == 'server_error' or 500 <= http_status < 600:
            return "server_error", 15 * 60  # 15-minute wait
        
        # X API specific error codes (from JSON in 200 response)
        if error_type == 'api_error':
            # User-specific errors that don't consume quota (fast retry)
            USER_SPECIFIC_CODES = [17, 50, 63]  # User not found, suspended, doesn't exist
            if error_code in USER_SPECIFIC_CODES:
                return "user_specific", 5  # 5-second wait
        
        # Check error message for known patterns
        if error_info.get('message'):
            error_msg_lower = error_info['message'].lower()
            if any(pattern in error_msg_lower for pattern in [
                "not following", "user not found", "account suspended", "does not exist"
            ]):
                return "user_specific", 5  # 5-second wait
    
    # Default: Conservative wait for any unclassified errors
    return "unknown", 15 * 60  # Conservative 15-minute wait

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
                session['username'] = 'Rate Limited'
                session['display_name'] = 'Rate Limited (will update shortly)'
                logging.info("Authentication successful, user info rate limited - will retry later")
            else:
                # For non-rate-limit errors, still allow login but log the issue
                session.permanent = True
                session['user_id'] = 'authenticated'
                session['username'] = 'Loading...'
                session['display_name'] = 'Loading user info...'
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

@app.route('/debug/clear-batches', methods=['POST'])
def clear_all_batches():
    """Debug endpoint to clear all batch operations."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        global slow_batch_operations, batch_queue
        
        # Count operations before clearing
        total_operations = len(slow_batch_operations)
        user_operations = len([op for op in slow_batch_operations.values() if op['user_id'] == session['user_id']])
        
        # Clear all operations for this user
        operations_to_remove = []
        for op_id, operation in slow_batch_operations.items():
            if operation['user_id'] == session['user_id']:
                operations_to_remove.append(op_id)
        
        for op_id in operations_to_remove:
            del slow_batch_operations[op_id]
        
        # Clear queue entries for this user
        batch_queue = [q for q in batch_queue if q['user_id'] != session['user_id']]
        
        logging.info(f"Debug: Cleared {len(operations_to_remove)} batch operations for user {session['user_id']}")
        
        return jsonify({
            'success': True,
            'message': f'Cleared {len(operations_to_remove)} batch operations',
            'cleared_operations': len(operations_to_remove),
            'remaining_total': len(slow_batch_operations)
        })
        
    except Exception as e:
        logging.error(f"Error clearing batches: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/rate-limits', methods=['GET'])
def get_rate_limits():
    """Get current rate limit status for UI updates."""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
            
        # Get cached rate limits without making API calls
        rate_limits = x_client.get_rate_limit_status(refresh_from_api=False)
        
        return jsonify({
            'rate_limits': rate_limits,
            'timestamp': int(time.time())
        })
        
    except Exception as e:
        logging.error(f"Rate limits check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/retry-user-info', methods=['POST'])
def retry_user_info():
    """Retry getting user info when it failed during login."""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
            
        # Only retry if we're in a placeholder state
        current_username = session.get('username', '')
        if current_username not in ['User', 'Loading...', 'Rate Limited']:
            return jsonify({'success': True, 'message': 'User info already available'})
            
        # Try to get user info again
        user_info = x_client.get_user_info()
        if user_info:
            session['username'] = user_info.get('username', 'Unknown')
            session['display_name'] = user_info.get('name', session['username'])
            logging.info(f"User info retry successful: @{session['username']}")
            return jsonify({'success': True, 'message': 'User info updated'})
        else:
            return jsonify({'success': False, 'message': 'User info still unavailable'})
            
    except Exception as e:
        logging.error(f"User info retry error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Debug API endpoint removed - not needed for production batch processing

# Core batch processing functions below - all debug/single features removed

def slow_batch_worker(operation_id, user_id, usernames, interval_minutes=15):
    """Layer 1: Clean basic batch worker - simple, predictable processing."""
    operation = None
    try:
        # Verify operation exists
        if operation_id not in slow_batch_operations:
            logging.error(f"Operation {operation_id} not found in batch operations")
            return
            
        operation = slow_batch_operations[operation_id]
        operation['status'] = 'running'
        operation['start_time'] = time.time()
        
        logging.info(f"Starting batch {operation_id} for {len(usernames)} users")
        
        # Layer 1: Simple sequential processing
        for i, username in enumerate(usernames):
            # Check for cancellation
            if operation['status'] == 'cancelled':
                break
                
            # Update current progress
            operation['current_username'] = username
            operation['current_index'] = i
            operation['completed_count'] = i + 1
            operation['last_update'] = time.time()
            
            # Layer 1: Basic unfollow attempt
            success = False
            error_msg = None
            
            try:
                # Resolve username to ID (if needed)
                target_id = username if username.isdigit() else x_client.resolve_username_to_id(username)
                
                if target_id:
                    # Layer 2 Simplified: Direct unfollow with smart error classification
                    # Note: Following pre-check removed due to X API permission requirements
                    logging.info(f"🔄 Layer 2: Attempting unfollow for @{username}")
                    success = x_client.unfollow_user(user_id, target_id)
                    
                    if success:
                        track_unfollow_attempt(True)
                        logging.info(f"✅ Unfollowed @{username} ({i+1}/{len(usernames)})")
                    else:
                        track_unfollow_attempt(False)
                        error_msg = "Not following this account"
                        logging.info(f"ℹ️ Cannot unfollow @{username} - not following")
                else:
                    error_msg = "User not found"
                    logging.warning(f"⚠️ User @{username} not found")
                    
            except Exception as e:
                error_msg = str(e)
                track_unfollow_attempt(False)
                logging.error(f"❌ Error unfollowing @{username}: {error_msg}")
            
            # Layer 1: Simple result tracking
            if success:
                operation['results'].append({'username': username, 'success': True})
                operation['success_count'] += 1
                operation['successful_usernames'] = operation.get('successful_usernames', [])
                operation['successful_usernames'].append(username)
            else:
                operation['results'].append({'username': username, 'success': False, 'error': error_msg or 'Unfollow failed'})
                operation['failed_count'] += 1
            
            # Layer 1: Simple completion notification
            operation['completed_count'] = i + 1  # Ensure completed count is updated
            operation['last_completion_time'] = time.time()
            operation['completion_pending'] = True
            logging.info(f"UNFOLLOW_COMPLETED: {operation_id} - {i+1}/{len(usernames)} processed")
            
            # Layer 2: Smart wait based on error classification (except for last user)
            if i < len(usernames) - 1 and operation['status'] != 'cancelled':
                # Debug: Log classification inputs (can be removed after Layer 2 verification)
                logging.info(f"🔍 Layer 2 Classification: success={success}, error_msg='{error_msg}', username=@{username}")
                error_type, classified_wait = classify_unfollow_error(error_msg, success)
                operation['next_unfollow_time'] = time.time() + classified_wait
                
                if classified_wait == 5:
                    logging.info(f"⚡ {error_type.upper()} error - waiting 5 seconds before next unfollow...")
                else:
                    wait_minutes = classified_wait // 60
                    logging.info(f"⏳ {error_type.upper()} - waiting {wait_minutes} minutes before next unfollow...")
                
                # Wait in 1-second increments to allow cancellation
                for second in range(classified_wait):
                    if operation['status'] == 'cancelled':
                        break
                    time.sleep(1)
                    
                    # Layer 2: Progress updates during fast waits (5 seconds) for responsive UI
                    if classified_wait == 5:
                        operation['last_completion_time'] = time.time()
                        operation['completion_pending'] = True
        
        # Layer 1: Simple completion handling
        if operation['status'] == 'cancelled':
            operation['end_time'] = time.time()
            logging.info(f"Batch {operation_id} cancelled at user {i+1}/{len(usernames)}")
        else:
            operation['status'] = 'completed'
            operation['end_time'] = time.time()
            logging.info(f"✅ Batch {operation_id} completed: {operation['success_count']} successful, {operation['failed_count']} failed")
        
        # Start next queued batch
        start_next_queued_batch()
        
    except Exception as e:
        # Layer 1: Simple error handling
        logging.critical(f"Critical error in batch {operation_id}: {str(e)}")
        
        if operation is not None:
            operation['status'] = 'error'
            operation['error'] = str(e)
            operation['end_time'] = time.time()
        
        # Try to start next batch
        start_next_queued_batch()

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
        
        # Check batch limits
        active_batch_count = get_active_batch_count(session['user_id'])
        if active_batch_count >= MAX_TOTAL_BATCHES:
            return jsonify({'error': f'Maximum {MAX_TOTAL_BATCHES} batches allowed (running + queued). Complete or cancel existing batches first.'}), 400
        
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
        
        # Check if a batch is currently running (across all users)
        running_batch = None
        for operation in slow_batch_operations.values():
            if operation['status'] in ['running', 'waiting_for_rate_limit_reset']:
                running_batch = operation
                break
        
        # Initialize operation tracking
        slow_batch_operations[operation_id] = {
            'id': operation_id,
            'user_id': session['user_id'],
            'username': session.get('username', 'Unknown'),
            'status': 'queued' if running_batch else 'starting',
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
            'estimated_completion': time.time() + ((len(usernames) - 1) * interval_minutes * 60),
            'queue_position': len(batch_queue) + 1 if running_batch else 0,
            # Simplified - no complex timing tracking for now
        }
        
        if running_batch:
            # Add to queue
            batch_queue.append({
                'operation_id': operation_id,
                'user_id': session['user_id'],
                'usernames': usernames,
                'interval_minutes': interval_minutes
            })
            
            queue_position = len(batch_queue)
            estimated_wait_time = 0
            
            # Calculate estimated wait time based on running batch
            if running_batch['total_count'] > running_batch['completed_count']:
                remaining_unfollows = running_batch['total_count'] - running_batch['completed_count']
                estimated_wait_time = remaining_unfollows * interval_minutes
            
            logging.info(f"Queued batch {operation_id} at position {queue_position}. Current batch: {running_batch['id']}")
            
            return jsonify({
                'success': True,
                'operation_id': operation_id,
                'queued': True,
                'queue_position': queue_position,
                'message': f'Batch queued at position {queue_position}. Will start when current batch completes.',
                'estimated_wait_hours': round(estimated_wait_time / 60, 1),
                'current_running_batch': running_batch['id']
            })
        else:
            # Start immediately
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
        
        # Start next queued batch after cancellation
        start_next_queued_batch()
        
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
                    'estimated_completion': datetime.fromtimestamp(operation['estimated_completion']).strftime('%Y-%m-%d %H:%M:%S') if operation.get('estimated_completion') else None,
                    'queue_position': operation.get('queue_position', 0)
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
            'active_count': len([op for op in user_operations if op['status'] in ['starting', 'running', 'queued']]),
            'queue_length': len(batch_queue),
            'successful_unfollows': successful_unfollows,
            'completion_notifications': completion_notifications
        })
        
    except Exception as e:
        logging.error(f"List slow batch operations error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug/test-following-permissions')
def test_following_permissions():
    """Test following status check with main app's authentication."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    scott_id = "931286316"  # ScottPresler's ID
    
    results = {
        'user_info': {
            'your_user_id': user_id,
            'target_user_id': scott_id,
            'target_username': 'ScottPresler'
        },
        'tests': []
    }
    
    # Test 1: Direct following relationship check with detailed error info
    try:
        logging.info(f"🧪 Testing direct following check: {user_id} → {scott_id}")
        
        # Make direct API call to get detailed response
        response = x_client._make_api_request('GET', f'/users/{user_id}/following/{scott_id}', api_endpoint_type='user_lookup')
        
        test_result = {
            'test': 'Direct Following Relationship Check',
            'endpoint': f'/users/{user_id}/following/{scott_id}',
            'http_status': response.status_code,
            'raw_response': response.text,
            'notes': 'Layer 2 pre-check endpoint'
        }
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'following' in data['data']:
                following_status = data['data']['following']
                test_result.update({
                    'result': following_status,
                    'status': 'success',
                    'parsed_data': data
                })
            else:
                test_result.update({
                    'result': None,
                    'status': 'unexpected_format',
                    'parsed_data': data
                })
        elif response.status_code == 403:
            test_result.update({
                'result': None,
                'status': 'permission_denied',
                'solution': 'Need Elevated Access in X Developer Portal'
            })
        else:
            test_result.update({
                'result': None,
                'status': 'api_error',
                'error_details': f"HTTP {response.status_code}"
            })
            
        results['tests'].append(test_result)
        
    except Exception as e:
        results['tests'].append({
            'test': 'Direct Following Relationship Check',
            'endpoint': f'/users/{user_id}/following/{scott_id}',
            'result': None,
            'status': 'exception',
            'error': str(e),
            'notes': 'Layer 2 pre-check failed with exception'
        })
    
    # Test 2: Get user info to verify authentication works
    try:
        logging.info(f"🧪 Testing user info endpoint")
        response = x_client._make_api_request('GET', '/users/me', api_endpoint_type='user_lookup')
        
        if response.status_code == 200:
            data = response.json()
            results['tests'].append({
                'test': 'User Info Check',
                'endpoint': '/users/me',
                'result': {
                    'username': data['data']['username'],
                    'id': data['data']['id']
                },
                'status': 'success',
                'notes': 'Basic authentication working'
            })
        else:
            results['tests'].append({
                'test': 'User Info Check',
                'endpoint': '/users/me',
                'result': None,
                'status': 'failed',
                'error': f"Status {response.status_code}: {response.text}",
                'notes': 'Basic authentication failed'
            })
            
    except Exception as e:
        results['tests'].append({
            'test': 'User Info Check',
            'endpoint': '/users/me',
            'result': None,
            'status': 'error',
            'error': str(e),
            'notes': 'Authentication error'
        })
    
    # Test 3: Try getting your own following list (might work with basic permissions)
    try:
        logging.info(f"🧪 Testing following list endpoint")
        response = x_client._make_api_request('GET', f'/users/{user_id}/following?max_results=10', api_endpoint_type='user_lookup')
        
        test_result = {
            'test': 'Following List Check (Alternative)',
            'endpoint': f'/users/{user_id}/following?max_results=10',
            'http_status': response.status_code,
            'raw_response': response.text[:500] + '...' if len(response.text) > 500 else response.text,
            'notes': 'Alternative method - check if Scott is in your following list'
        }
        
        if response.status_code == 200:
            data = response.json()
            following_users = data.get('data', [])
            scott_in_list = any(user.get('id') == scott_id for user in following_users)
            
            test_result.update({
                'result': scott_in_list,
                'status': 'success',
                'following_count': len(following_users),
                'scott_found': scott_in_list,
                'note': 'Limited to first 10 users for testing'
            })
        else:
            test_result.update({
                'result': None,
                'status': 'failed' if response.status_code == 403 else 'api_error'
            })
            
        results['tests'].append(test_result)
        
    except Exception as e:
        results['tests'].append({
            'test': 'Following List Check (Alternative)',
            'endpoint': f'/users/{user_id}/following?max_results=10',
            'result': None,
            'status': 'exception',
            'error': str(e),
            'notes': 'Alternative method failed'
        })
    
    # Test 4: Try getting target user profile (might show relationship info)
    try:
        logging.info(f"🧪 Testing target user profile")
        response = x_client._make_api_request('GET', f'/users/{scott_id}?user.fields=public_metrics', api_endpoint_type='user_lookup')
        
        test_result = {
            'test': 'Target User Profile Check',
            'endpoint': f'/users/{scott_id}',
            'http_status': response.status_code,
            'notes': 'Check if user profile contains relationship indicators'
        }
        
        if response.status_code == 200:
            data = response.json()
            test_result.update({
                'result': data.get('data', {}),
                'status': 'success',
                'username': data.get('data', {}).get('username'),
                'note': 'Basic profile info - no relationship data with basic permissions'
            })
        else:
            test_result.update({
                'result': None,
                'status': 'failed',
                'raw_response': response.text
            })
            
        results['tests'].append(test_result)
        
    except Exception as e:
        results['tests'].append({
            'test': 'Target User Profile Check',
            'endpoint': f'/users/{scott_id}',
            'result': None,
            'status': 'exception',
            'error': str(e),
            'notes': 'Profile check failed'
        })
    
    # Summary and recommendations based on all tests
    following_test = next((t for t in results['tests'] if 'Following Relationship' in t['test']), None)
    following_list_test = next((t for t in results['tests'] if 'Following List' in t['test']), None)
    
    recommendations = []
    
    # Check direct following relationship result
    if following_test:
        if following_test.get('status') == 'success':
            recommendations.append('✅ Direct following check works - Layer 2 pre-check ready!')
        elif following_test.get('status') == 'permission_denied':
            recommendations.append('🔐 Direct following check requires Elevated Access')
        elif following_test.get('http_status') == 403:
            recommendations.append('🔐 HTTP 403: Need elevated permissions for following relationships')
    
    # Check alternative following list result  
    if following_list_test:
        if following_list_test.get('status') == 'success':
            recommendations.append('✅ Following list works - Can use alternative method (limited to recent follows)')
        elif following_list_test.get('http_status') == 403:
            recommendations.append('❌ Following list also requires elevated permissions')
        else:
            recommendations.append('⚠️ Following list method failed')
    
    # Overall recommendation
    if any('✅' in rec for rec in recommendations):
        results['recommendation'] = 'Layer 2 following pre-check possible with current setup!'
        results['next_steps'] = ['Implement working method in batch processing', 'Test with real batch']
    elif any('🔐' in rec for rec in recommendations):
        results['recommendation'] = 'Apply for Elevated Access in X Developer Portal for full Layer 2 functionality'
        results['next_steps'] = [
            'Go to https://developer.twitter.com/en/portal/dashboard',
            'Apply for Elevated Access',
            'Explain use case: "Building unfollow tool for account management"',
            'Wait 1-2 days for approval'
        ]
    else:
        results['recommendation'] = 'Simplify Layer 2 - Remove pre-check, keep smart timing benefits'
        results['next_steps'] = [
            'Remove following status pre-check from batch worker',
            'Keep Layer 2 smart timing (5s for errors, 15min for success)',
            'Still get 60%+ time savings for error-heavy batches',
            'Accept some false positives for simplicity'
        ]
    
    results['detailed_analysis'] = recommendations
    
    return jsonify(results)

@app.route('/debug/<path:endpoint>')
def debug_info(endpoint):
    """Info about debug functionality moved to separate test file."""
    if endpoint == 'test-following-permissions':
        return test_following_permissions()
    
    return jsonify({
        'message': 'Debug functionality moved to standalone test file',
        'debug_file': 'debug_tests.py',
        'available_functions': [
            'test_layer2_classification()',
            'performance_simulation()',
        ],
        'usage': 'Run: python debug_tests.py',
        'description': 'Tests Layer 2 logic without API calls or web server',
        'live_test': 'GET /debug/test-following-permissions (requires authentication)'
    })

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