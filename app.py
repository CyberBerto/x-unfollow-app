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
        
        # Exchange code for tokens
        tokens = x_client.exchange_code_for_tokens(code, state)
        
        # Get user info
        user_info = x_client.get_user_info()
        if user_info:
            session.permanent = True  # Make session persistent for development
            session['user_id'] = user_info['id']
            session['username'] = user_info.get('username', 'Unknown')
            logging.info(f"User authenticated: {session['username']} (ID: {session['user_id']})")
        
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

# Following list route removed - replaced with CSV import functionality

@app.route('/unfollow/single', methods=['POST'])
def unfollow_single():
    """Unfollow a single user by username or ID."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        target = data.get('target', '').strip()
        
        if not target:
            return jsonify({'error': 'Username or user ID required'}), 400
        
        # Resolve username to ID if necessary
        target_id = x_client.resolve_username_to_id(target) if not target.isdigit() else target
        
        if not target_id:
            return jsonify({'error': 'User not found'}), 404
        
        # Perform unfollow
        success = x_client.unfollow_user(session['user_id'], target_id)
        
        # Track the unfollow attempt
        track_unfollow_attempt(success)
        
        if success:
            logging.info(f"Successfully unfollowed user {target} (ID: {target_id})")
            return jsonify({'success': True, 'message': f'Successfully unfollowed {target}'})
        else:
            return jsonify({'error': 'Unfollow failed'}), 400
            
    except Exception as e:
        logging.error(f"Single unfollow error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def check_local_rate_limits_and_wait():
    """Check local rate limit tracking and wait if necessary."""
    try:
        # Get current rate limit status from local tracking (no API call)
        rate_status = x_client.get_rate_limit_status(refresh_from_api=False)
        unfollow_remaining = rate_status['unfollow']['remaining']
        reset_time = rate_status['unfollow']['reset_time']
        current_time = time.time()
        
        # If we know the limits and they're exhausted, wait for reset
        if unfollow_remaining != 'unknown' and unfollow_remaining <= 0:
            wait_seconds = max(0, reset_time - current_time)
            if wait_seconds > 0:
                logging.info(f"Local rate limit tracking shows exhaustion. Waiting {int(wait_seconds)} seconds for reset...")
                time.sleep(wait_seconds + 5)  # Add 5 second buffer
                return True  # Indicate we waited
        
        return False  # No wait needed
    except Exception as e:
        logging.error(f"Error checking local rate limits: {str(e)}")
        return False

# Old batch endpoints removed - replaced with realistic 15-minute interval batching

@app.route('/status')
def status():
    """Get current authentication and rate limit status."""
    try:
        authenticated = 'user_id' in session
        # Get fresh rate limits from X API for accurate display
        rate_limits = x_client.get_rate_limit_status(refresh_from_api=True) if authenticated else None
        
        return jsonify({
            'authenticated': authenticated,
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'rate_limits': rate_limits
        })
    except Exception as e:
        logging.error(f"Status check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug-api')
def debug_api():
    """Debug API access and permissions."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Test basic user info call
        user_info = x_client.get_user_info()
        
        # Test a simple API call to check permissions and get rate limit headers
        test_response = x_client._make_api_request('GET', '/users/me', api_endpoint_type='user_lookup')
        
        # Get current rate limit status with fresh data
        rate_limits = x_client.get_rate_limit_status(refresh_from_api=True)
        
        # Extract headers for debugging
        headers_info = {}
        if test_response and hasattr(test_response, 'headers'):
            headers_info = {
                'x-rate-limit-remaining': test_response.headers.get('x-rate-limit-remaining'),
                'x-rate-limit-limit': test_response.headers.get('x-rate-limit-limit'),
                'x-rate-limit-reset': test_response.headers.get('x-rate-limit-reset'),
                'x-rate-limit-resource': test_response.headers.get('x-rate-limit-resource')
            }
        
        return jsonify({
            'user_info_success': user_info is not None,
            'api_test_status': test_response.status_code if test_response else 'No Response',
            'api_response': test_response.text if test_response and test_response.status_code != 200 else 'OK',
            'rate_limit_headers': headers_info,
            'current_rate_limits': rate_limits,
            'client_id': CLIENT_ID,
            'scopes': 'tweet.read users.read follows.read follows.write'
        })
    except Exception as e:
        logging.error(f"Debug API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Debug routes removed - functionality integrated into main app flow

def slow_batch_worker(operation_id, user_id, usernames, interval_minutes=15):
    """Background worker for slow batch unfollowing (configurable interval)."""
    try:
        operation = slow_batch_operations[operation_id]
        operation['status'] = 'running'
        operation['start_time'] = time.time()
        
        # No pre-check - we'll handle rate limits on first actual unfollow attempt
        
        for i, username in enumerate(usernames):
            if operation['status'] == 'cancelled':
                break
                
            operation['current_username'] = username
            operation['current_index'] = i
            
            try:
                # Resolve username to ID
                target_id = x_client.resolve_username_to_id(username) if not username.isdigit() else username
                
                if not target_id:
                    operation['results'].append({'username': username, 'success': False, 'error': 'User not found'})
                    operation['failed_count'] += 1
                    continue
                
                # Attempt unfollow with rate limit handling for first attempt
                success = False
                retry_attempted = False
                error_msg = None
                
                try:
                    success = x_client.unfollow_user(user_id, target_id)
                    operation['current_rate_limits'] = x_client.get_rate_limit_status()
                    
                    if success:
                        track_unfollow_attempt(True)
                        logging.info(f"Unfollow successful for {username}")
                    else:
                        track_unfollow_attempt(False)
                        error_msg = "Unfollow returned False"
                        
                except Exception as e:
                    error_msg = str(e)
                    logging.error(f"Unfollow attempt failed: {error_msg}")
                    
                    # If this is the first unfollow and it failed due to rate limits, wait and retry
                    if i == 0 and "Rate limit exceeded" in error_msg and not retry_attempted:
                        logging.info(f"First unfollow failed due to rate limits. Waiting for reset...")
                        operation['notes'] = operation.get('notes', [])
                        operation['notes'].append('First unfollow delayed due to rate limits')
                        
                        # Get rate limit reset time and wait
                        try:
                            rate_status = x_client.get_rate_limit_status()
                            reset_time = rate_status['unfollow']['reset_time']
                            current_time = time.time()
                            wait_seconds = max(0, reset_time - current_time + 5)  # Add 5 second buffer
                            
                            if wait_seconds > 0:
                                logging.info(f"Waiting {int(wait_seconds)} seconds for rate limit reset...")
                                time.sleep(wait_seconds)
                                retry_attempted = True
                                
                                # Retry the unfollow
                                try:
                                    success = x_client.unfollow_user(user_id, target_id)
                                    operation['current_rate_limits'] = x_client.get_rate_limit_status()
                                    if success:
                                        track_unfollow_attempt(True)
                                        error_msg = None  # Clear error since retry succeeded
                                    else:
                                        track_unfollow_attempt(False)
                                        error_msg = "Retry unfollow returned False"
                                except Exception as retry_error:
                                    error_msg = str(retry_error)
                                    logging.error(f"Retry also failed: {error_msg}")
                                    track_unfollow_attempt(False)
                        except Exception as rate_error:
                            logging.error(f"Error during rate limit wait: {str(rate_error)}")
                    
                    # Track failed attempt if not already tracked
                    if not success and not retry_attempted:
                        track_unfollow_attempt(False)
                
                if success:
                    operation['results'].append({'username': username, 'success': True})
                    operation['success_count'] += 1
                    operation['successful_usernames'] = operation.get('successful_usernames', [])
                    operation['successful_usernames'].append(username)
                    logging.info(f"Slow batch {operation_id}: unfollowed @{username} ({i+1}/{len(usernames)})")
                else:
                    failure_reason = error_msg or 'Unfollow failed'
                    operation['results'].append({'username': username, 'success': False, 'error': failure_reason})
                    operation['failed_count'] += 1
                
            except Exception as e:
                error_msg = str(e)
                operation['results'].append({'username': username, 'success': False, 'error': error_msg})
                operation['failed_count'] += 1
                logging.error(f"Slow batch {operation_id}: error unfollowing @{username}: {error_msg}")
            
            # Update progress with real-time timestamp
            operation['completed_count'] = i + 1
            operation['last_update'] = time.time()
            operation['last_activity'] = datetime.now().strftime('%H:%M:%S')
            
            # Wait specified interval before next unfollow (except for the last one)
            if i < len(usernames) - 1 and operation['status'] != 'cancelled':
                wait_seconds = interval_minutes * 60
                operation['next_unfollow_time'] = time.time() + wait_seconds
                
                # Wait in small increments to allow for cancellation
                for wait_interval in range(wait_seconds):
                    if operation['status'] == 'cancelled':
                        break
                    time.sleep(1)
        
        # Mark as completed
        if operation['status'] != 'cancelled':
            operation['status'] = 'completed'
            operation['end_time'] = time.time()
            
        logging.info(f"Slow batch {operation_id} finished: {operation['success_count']} successful, {operation['failed_count']} failed")
        
    except Exception as e:
        logging.error(f"Slow batch worker error for {operation_id}: {str(e)}")
        operation['status'] = 'error'
        operation['error'] = str(e)

@app.route('/unfollow/slow-batch', methods=['POST'])
def unfollow_slow_batch():
    """Start a slow batch unfollow operation (configurable interval)."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
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
            'estimated_completion': time.time() + (len(usernames) * interval_minutes * 60)
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
            'estimated_duration_hours': round(len(usernames) * interval_minutes / 60, 1)
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
        
        operation['status'] = 'cancelled'
        operation['end_time'] = time.time()
        
        logging.info(f"Cancelled slow batch operation {operation_id}")
        
        return jsonify({
            'success': True,
            'message': 'Slow batch operation cancelled',
            'final_stats': {
                'completed': operation['completed_count'],
                'successful': operation['success_count'],
                'failed': operation['failed_count']
            }
        })
        
    except Exception as e:
        logging.error(f"Cancel slow batch error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        for operation in slow_batch_operations.values():
            if operation['user_id'] == session['user_id']:
                successful_unfollows.extend(operation.get('successful_usernames', []))
        
        return jsonify({
            'operations': user_operations,
            'active_count': len([op for op in user_operations if op['status'] in ['starting', 'running']]),
            'successful_unfollows': successful_unfollows
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