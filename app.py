"""
Flask web application for unfollowing X accounts via X API v2.
Implements OAuth 2.0 authentication and batch unfollowing functionality.
"""

import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import time
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
        
        if success:
            logging.info(f"Successfully unfollowed user {target} (ID: {target_id})")
            return jsonify({'success': True, 'message': f'Successfully unfollowed {target}'})
        else:
            return jsonify({'error': 'Unfollow failed'}), 400
            
    except Exception as e:
        logging.error(f"Single unfollow error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/unfollow/small-batch', methods=['POST'])
def unfollow_small_batch():
    """Unfollow up to 10 users with 1-second delays."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        usernames = data.get('usernames', [])
        
        if not usernames:
            return jsonify({'error': 'No users selected'}), 400
        
        if len(usernames) > 10:
            return jsonify({'error': 'Maximum 10 users allowed for small batch'}), 400
        
        results = []
        success_count = 0
        
        for i, username in enumerate(usernames):
            try:
                # Resolve username to ID
                target_id = x_client.resolve_username_to_id(username) if not username.isdigit() else username
                
                if not target_id:
                    results.append({'username': username, 'success': False, 'error': 'User not found'})
                    continue
                
                success = x_client.unfollow_user(session['user_id'], target_id)
                if success:
                    success_count += 1
                    results.append({'username': username, 'success': True})
                    logging.info(f"Small batch: unfollowed user {username} ({i+1}/{len(usernames)})")
                else:
                    results.append({'username': username, 'success': False, 'error': 'Unfollow failed'})
                
                # 1-second delay between requests (except for the last one)
                if i < len(usernames) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Error unfollowing user {username}: {str(e)}")
                results.append({'username': username, 'success': False, 'error': str(e)})
        
        return jsonify({
            'success': success_count > 0,
            'message': f'Successfully unfollowed {success_count}/{len(usernames)} users',
            'results': results
        })
        
    except Exception as e:
        logging.error(f"Small batch unfollow error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/unfollow/full-batch', methods=['POST'])
def unfollow_full_batch():
    """Unfollow up to 50 users with 18-second delays for rate limit compliance."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        usernames = data.get('usernames', [])
        
        if not usernames:
            return jsonify({'error': 'No users selected'}), 400
        
        if len(usernames) > 50:
            return jsonify({'error': 'Maximum 50 users allowed for full batch'}), 400
        
        results = []
        success_count = 0
        
        for i, username in enumerate(usernames):
            try:
                # Resolve username to ID
                target_id = x_client.resolve_username_to_id(username) if not username.isdigit() else username
                
                if not target_id:
                    results.append({'username': username, 'success': False, 'error': 'User not found'})
                    continue
                
                success = x_client.unfollow_user(session['user_id'], target_id)
                if success:
                    success_count += 1
                    results.append({'username': username, 'success': True})
                    logging.info(f"Full batch: unfollowed user {username} ({i+1}/{len(usernames)})")
                else:
                    results.append({'username': username, 'success': False, 'error': 'Unfollow failed'})
                
                # 18-second delay between requests for rate limit compliance (except for the last one)
                if i < len(usernames) - 1:
                    logging.info(f"Waiting 18 seconds before next unfollow ({i+2}/{len(usernames)})")
                    time.sleep(18)
                    
            except Exception as e:
                logging.error(f"Error unfollowing user {username}: {str(e)}")
                results.append({'username': username, 'success': False, 'error': str(e)})
        
        return jsonify({
            'success': success_count > 0,
            'message': f'Successfully unfollowed {success_count}/{len(usernames)} users',
            'results': results
        })
        
    except Exception as e:
        logging.error(f"Full batch unfollow error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    """Get current authentication and rate limit status."""
    try:
        authenticated = 'user_id' in session
        rate_limits = x_client.get_rate_limit_status() if authenticated else None
        
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
        
        # Test a simple API call to check permissions
        test_response = x_client._make_api_request('GET', '/users/me', api_endpoint_type='user_lookup')
        
        return jsonify({
            'user_info_success': user_info is not None,
            'api_test_status': test_response.status_code,
            'api_response': test_response.text if test_response.status_code != 200 else 'OK',
            'client_id': CLIENT_ID,
            'scopes': 'tweet.read users.read follows.read follows.write'
        })
    except Exception as e:
        logging.error(f"Debug API error: {str(e)}")
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