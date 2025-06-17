"""
X API v2 client with OAuth 2.0 authentication and rate limit handling.
Handles all API interactions including authentication, following list retrieval, and unfollowing.
"""

import requests
import logging
import time
import keyring
import json
from urllib.parse import urlencode, parse_qs
from requests_oauthlib import OAuth2Session
import secrets
import base64
import hashlib
from config import API_BASE_URL

class XAPIClient:
    """X API v2 client with OAuth 2.0 PKCE authentication."""
    
    def __init__(self, client_id, client_secret, redirect_uri):
        """
        Initialize X API client.
        
        Args:
            client_id (str): X API client ID
            client_secret (str): X API client secret
            redirect_uri (str): OAuth redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.api_base_url = API_BASE_URL
        self.session = requests.Session()
        
        # OAuth 2.0 PKCE parameters
        self.code_verifier = None
        self.state = None
        
        # Rate limit tracking - initialize with defaults
        self.rate_limits = {
            'following': {'remaining': 15, 'reset': 0, 'limit': 15},
            'unfollow': {'remaining': 'unknown', 'reset': 0, 'limit': 'unknown'}, 
            'user_lookup': {'remaining': 300, 'reset': 0, 'limit': 300},
            'unfollow_hourly': {'remaining': 'unknown', 'reset': 0, 'limit': 'unknown'},
            'unfollow_daily': {'remaining': 'unknown', 'reset': 0, 'limit': 'unknown'}
        }
        
        # Load stored tokens
        self._load_tokens()
    
    def _generate_pkce_pair(self):
        """Generate PKCE code verifier and challenge for OAuth 2.0."""
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        return code_challenge
    
    def get_authorization_url(self):
        """
        Generate OAuth 2.0 authorization URL for user authentication.
        
        Returns:
            str: Authorization URL for user to visit
        """
        try:
            self.state = secrets.token_urlsafe(32)
            code_challenge = self._generate_pkce_pair()
            
            params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': 'tweet.read users.read follows.read follows.write',
                'state': self.state,
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256'
            }
            
            auth_url = f"https://x.com/i/oauth2/authorize?{urlencode(params)}"
            logging.info("Generated OAuth authorization URL")
            return auth_url
            
        except Exception as e:
            logging.error(f"Error generating authorization URL: {str(e)}")
            raise
    
    def exchange_code_for_tokens(self, code, state):
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code (str): Authorization code from callback
            state (str): State parameter for CSRF protection
            
        Returns:
            dict: Token information
        """
        try:
            if state != self.state:
                raise ValueError("Invalid state parameter - possible CSRF attack")
            
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'code': code,
                'redirect_uri': self.redirect_uri,
                'code_verifier': self.code_verifier
            }
            
            # For Web App type, need to include Authorization header with client credentials
            import base64
            credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {credentials}'
            }
            
            response = requests.post(
                'https://api.x.com/2/oauth2/token',
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                tokens = response.json()
                self._store_tokens(tokens)
                logging.info("Successfully exchanged code for tokens")
                return tokens
            else:
                logging.error(f"Token exchange failed: {response.status_code} - {response.text}")
                raise Exception(f"Token exchange failed: {response.text}")
                
        except Exception as e:
            logging.error(f"Error exchanging code for tokens: {str(e)}")
            raise
    
    def refresh_access_token(self):
        """
        Refresh access token using refresh token.
        
        Returns:
            bool: True if refresh successful, False otherwise
        """
        try:
            refresh_token = keyring.get_password("x_unfollow_app", "refresh_token")
            if not refresh_token:
                logging.warning("No refresh token available - user needs to re-authenticate")
                return False
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id
            }
            
            # For Web App type, need to include Authorization header with client credentials
            import base64
            credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {credentials}'
            }
            
            response = requests.post(
                'https://api.x.com/2/oauth2/token',
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                tokens = response.json()
                self._store_tokens(tokens)
                logging.info("Successfully refreshed access token")
                return True
            else:
                logging.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error refreshing access token: {str(e)}")
            return False
    
    def _store_tokens(self, tokens):
        """Store access and refresh tokens securely using keyring."""
        try:
            access_token = tokens.get('access_token')
            keyring.set_password("x_unfollow_app", "access_token", access_token)
            if 'refresh_token' in tokens:
                keyring.set_password("x_unfollow_app", "refresh_token", tokens.get('refresh_token'))
            
            # Store token metadata
            token_info = {
                'expires_in': tokens.get('expires_in', 7200),
                'token_type': tokens.get('token_type', 'bearer'),
                'created_at': time.time()
            }
            keyring.set_password("x_unfollow_app", "token_info", json.dumps(token_info))
            
            # Update session headers immediately
            if access_token:
                self.session.headers.update({
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                })
                logging.info("Updated session headers with new access token")
            
        except Exception as e:
            logging.error(f"Error storing tokens: {str(e)}")
            raise
    
    def _load_tokens(self):
        """Load stored tokens from keyring."""
        try:
            access_token = keyring.get_password("x_unfollow_app", "access_token")
            if access_token:
                self.session.headers.update({
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                })
        except Exception as e:
            logging.error(f"Error loading tokens: {str(e)}")
    
    def clear_tokens(self):
        """Clear stored tokens from keyring."""
        try:
            keyring.delete_password("x_unfollow_app", "access_token")
            keyring.delete_password("x_unfollow_app", "refresh_token")
            keyring.delete_password("x_unfollow_app", "token_info")
            self.session.headers.pop('Authorization', None)
            logging.info("Cleared stored tokens")
        except Exception as e:
            logging.error(f"Error clearing tokens: {str(e)}")
    
    def _check_rate_limit(self, endpoint):
        """
        Check if we're within rate limits for an endpoint.
        
        Args:
            endpoint (str): API endpoint category ('following', 'unfollow', 'user_lookup')
            
        Returns:
            bool: True if within limits, False otherwise
        """
        if endpoint not in self.rate_limits:
            return True
        
        limit_info = self.rate_limits[endpoint]
        current_time = time.time()
        
        # If rate limit is unknown, allow the request (we'll learn from the API response)
        if limit_info['remaining'] == 'unknown' or limit_info['limit'] == 'unknown':
            logging.info(f"Rate limit unknown for {endpoint}, allowing request to learn from API response")
            return True
        
        # Reset counters if window has passed
        if current_time > limit_info['reset']:
            limit_info['remaining'] = limit_info['limit']
            limit_info['reset'] = current_time + 900  # 15 minutes
            logging.info(f"Rate limit window reset for {endpoint}: {limit_info['remaining']}/{limit_info['limit']}")
        
        # If rate limited, raise exception instead of waiting
        if limit_info['remaining'] <= 0:
            wait_time = limit_info['reset'] - current_time
            if wait_time > 0:
                raise Exception(f"Rate limit exceeded for {endpoint}. Please wait {int(wait_time // 60)} minutes before trying again.")
        
        return limit_info['remaining'] > 0
    
    def _update_rate_limit(self, response, endpoint):
        """Update rate limit counters from API response headers."""
        try:
            remaining = response.headers.get('x-rate-limit-remaining')
            reset = response.headers.get('x-rate-limit-reset')
            limit = response.headers.get('x-rate-limit-limit')
            
            if endpoint in self.rate_limits:
                # If this is the first time we're getting data for this endpoint, initialize from API response
                if self.rate_limits[endpoint]['remaining'] == 'unknown' or self.rate_limits[endpoint]['limit'] == 'unknown':
                    if remaining and limit:
                        remaining_count = int(remaining)
                        limit_count = int(limit)
                        current_time = time.time()
                        
                        # Initialize with API data, but adjust for the request we just made
                        if 200 <= response.status_code < 300:
                            # Successful request - API shows remaining AFTER this call
                            self.rate_limits[endpoint]['remaining'] = remaining_count
                        else:
                            # Failed request - API shows remaining BEFORE this call
                            self.rate_limits[endpoint]['remaining'] = remaining_count
                        
                        self.rate_limits[endpoint]['limit'] = limit_count
                        self.rate_limits[endpoint]['reset'] = int(reset) if reset else current_time + 900
                        
                        logging.info(f"Initialized {endpoint} rate limits from API: {remaining_count}/{limit_count}, reset: {self.rate_limits[endpoint]['reset']}, status: {response.status_code}")
                        return  # Don't continue with normal update logic since we just initialized
                
                # Normal rate limit update logic for known limits
                # Decrement local counter for successful API calls (status 200-299)
                if 200 <= response.status_code < 300:
                    if isinstance(self.rate_limits[endpoint]['remaining'], int) and self.rate_limits[endpoint]['remaining'] > 0:
                        self.rate_limits[endpoint]['remaining'] -= 1
                        logging.info(f"Decremented {endpoint} rate limit: {self.rate_limits[endpoint]['remaining']}/{self.rate_limits[endpoint]['limit']} remaining")
                
                # Update remaining count from headers if available and valid
                if remaining and isinstance(self.rate_limits[endpoint]['limit'], int):
                    remaining_count = int(remaining)
                    expected_limit = self.rate_limits[endpoint]['limit']
                    # Only update if the value makes sense for this endpoint
                    if remaining_count <= expected_limit:
                        # Only trust API headers in these cases:
                        # 1. API shows higher count than local (we missed some resets)
                        # 2. We got a 429 response (definitely rate limited)
                        # 3. API count is very close to our local count (±2 difference)
                        local_count = self.rate_limits[endpoint]['remaining']
                        if isinstance(local_count, int):
                            count_diff = abs(remaining_count - local_count)
                            
                            if (remaining_count > local_count or 
                                response.status_code == 429 or 
                                count_diff <= 2):
                                self.rate_limits[endpoint]['remaining'] = remaining_count
                                logging.info(f"Updated {endpoint} rate limit from API headers: {remaining_count}/{expected_limit} remaining")
                            else:
                                logging.info(f"Ignoring potentially incorrect API header: API={remaining_count}, Local={local_count} for {endpoint}")
                        else:
                            # Local count is unknown, trust API
                            self.rate_limits[endpoint]['remaining'] = remaining_count
                            logging.info(f"Updated {endpoint} rate limit from API headers: {remaining_count}/{expected_limit} remaining")
                
                # Update reset time
                if reset:
                    self.rate_limits[endpoint]['reset'] = int(reset)
                
                # Update limit if provided (helps with accuracy)
                if limit:
                    limit_count = int(limit)
                    if limit_count in [15, 50, 300]:  # Expected X API limits
                        self.rate_limits[endpoint]['limit'] = limit_count
                
        except (ValueError, Exception) as e:
            logging.error(f"Error updating rate limits: {str(e)}")
    
    def _make_api_request(self, method, endpoint, params=None, data=None, api_endpoint_type='general'):
        """
        Make authenticated API request with rate limit handling.
        
        Args:
            method (str): HTTP method
            endpoint (str): API endpoint
            params (dict): Query parameters
            data (dict): Request body data
            api_endpoint_type (str): Type for rate limiting
            
        Returns:
            requests.Response: API response
        """
        try:
            # Check rate limits (will raise exception if rate limited)
            self._check_rate_limit(api_endpoint_type)
            
            url = f"{self.api_base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Update rate limits from response headers
            self._update_rate_limit(response, api_endpoint_type)
            
            # Handle rate limit errors
            if response.status_code == 429:
                retry_after = int(response.headers.get('retry-after', 900))
                logging.warning(f"Rate limited for {api_endpoint_type}, would need to wait {retry_after} seconds")
                # Don't actually retry automatically to avoid hanging the UI
                # Let the user know they need to wait
                raise Exception(f"Rate limit exceeded. Please wait {retry_after // 60} minutes before trying again.")
            
            # Handle project requirement error  
            if response.status_code == 403:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                if 'client-not-enrolled' in str(error_data):
                    raise Exception("X API Project Setup Required: Your app must be attached to a Project in the X Developer Portal. Visit https://developer.twitter.com/en/portal/dashboard to create/attach a project.")
                else:
                    raise Exception(f"Access forbidden: {error_data.get('detail', 'Permission denied')}")
            
            # Handle token expiration
            if response.status_code == 401:
                logging.info("Access token expired, attempting refresh")
                if self.refresh_access_token():
                    return self._make_api_request(method, endpoint, params, data, api_endpoint_type)
                else:
                    raise Exception("Authentication failed - please re-login")
            
            return response
            
        except Exception as e:
            logging.error(f"API request error: {str(e)}")
            raise
    
    def get_user_info(self):
        """
        Get authenticated user's information.
        
        Returns:
            dict: User information
        """
        try:
            response = self._make_api_request('GET', '/users/me', api_endpoint_type='user_lookup')
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
            else:
                logging.error(f"Failed to get user info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error getting user info: {str(e)}")
            return None
    
    def resolve_username_to_id(self, username):
        """
        Convert username to user ID.
        
        Args:
            username (str): Username to resolve
            
        Returns:
            str: User ID or None if not found
        """
        try:
            # Remove @ symbol if present
            username = username.lstrip('@')
            
            response = self._make_api_request('GET', f'/users/by/username/{username}', api_endpoint_type='user_lookup')
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {})
                return user_data.get('id')
            else:
                logging.error(f"Failed to resolve username {username}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error resolving username {username}: {str(e)}")
            return None
    
    def get_following_list(self, user_id, max_results=100):
        """
        Get list of users that the specified user is following.
        
        Args:
            user_id (str): User ID to get following list for
            max_results (int): Maximum results per request (max 1000)
            
        Returns:
            list: List of following users
        """
        try:
            following = []
            pagination_token = None
            
            while len(following) < 1000:  # X API limit per 15-minute window
                params = {
                    'max_results': min(max_results, 1000 - len(following)),
                    'user.fields': 'id,name,username,profile_image_url'
                }
                
                if pagination_token:
                    params['pagination_token'] = pagination_token
                
                response = self._make_api_request('GET', f'/users/{user_id}/following', params=params, api_endpoint_type='following')
                
                if response.status_code == 200:
                    data = response.json()
                    users = data.get('data', [])
                    following.extend(users)
                    
                    # Check for next page
                    meta = data.get('meta', {})
                    pagination_token = meta.get('next_token')
                    
                    if not pagination_token:
                        break
                        
                    logging.info(f"Fetched {len(following)} following users so far")
                    
                else:
                    logging.error(f"Failed to get following list: {response.status_code} - {response.text}")
                    break
            
            logging.info(f"Retrieved {len(following)} following users for user {user_id}")
            return following
            
        except Exception as e:
            logging.error(f"Error getting following list: {str(e)}")
            return []
    
    def unfollow_user(self, source_user_id, target_user_id):
        """
        Unfollow a user.
        
        Args:
            source_user_id (str): ID of user doing the unfollowing
            target_user_id (str): ID of user to unfollow
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self._make_api_request('DELETE', f'/users/{source_user_id}/following/{target_user_id}', api_endpoint_type='unfollow')
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('data', {}).get('following', True) == False
                if success:
                    logging.info(f"Successfully unfollowed user {target_user_id}")
                return success
            else:
                logging.error(f"Failed to unfollow user {target_user_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error unfollowing user {target_user_id}: {str(e)}")
            return False
    
    def get_rate_limit_status(self, refresh_from_api=False):
        """
        Get current rate limit status.
        
        Args:
            refresh_from_api (bool): If True, fetch fresh rate limits from X API
        
        Returns:
            dict: Rate limit information
        """
        if refresh_from_api:
            self._refresh_rate_limits_from_api()
        
        # Calculate estimated hourly/daily limits for free tier using persistent tracking
        current_time = time.time()
        
        # Try to get actual counts from persistent tracking
        try:
            from app import get_unfollow_stats
            stats = get_unfollow_stats()
            
            # Use persistent tracking data for more accurate remaining counts
            estimated_hourly = stats['hourly_limit']
            estimated_daily = stats['daily_limit']
            hourly_remaining = max(0, estimated_hourly - stats['hourly_successful'])
            daily_remaining = max(0, estimated_daily - stats['daily_successful'])
            
        except (ImportError, Exception):
            # Fallback to estimates if tracking not available
            base_15min_limit = self.rate_limits['unfollow']['limit']
            if base_15min_limit != 'unknown' and isinstance(base_15min_limit, int):
                # Conservative estimates: assume rate limits apply across longer periods
                estimated_hourly = min(base_15min_limit * 4, 4)  # 4 windows per hour, but cap at 4 for free tier
                estimated_daily = min(base_15min_limit * 96, 50)  # 96 windows per day, but cap at 50 for free tier
                
                # Calculate remaining based on recent usage patterns
                hourly_remaining = estimated_hourly
                daily_remaining = estimated_daily
            else:
                # Use conservative free tier defaults when unknown
                estimated_hourly = 4
                estimated_daily = 50
                hourly_remaining = 'unknown'
                daily_remaining = 'unknown'
        
        return {
            'unfollow': {
                'remaining': self.rate_limits['unfollow']['remaining'],
                'limit': self.rate_limits['unfollow']['limit'],
                'reset_time': self.rate_limits['unfollow']['reset']
            },
            'unfollow_hourly': {
                'remaining': hourly_remaining,
                'limit': estimated_hourly,
                'reset_time': current_time + 3600  # Next hour
            },
            'unfollow_daily': {
                'remaining': daily_remaining,
                'limit': estimated_daily,
                'reset_time': current_time + 86400  # Next day
            },
            'user_lookup': {
                'remaining': self.rate_limits['user_lookup']['remaining'],
                'limit': self.rate_limits['user_lookup']['limit'],
                'reset_time': self.rate_limits['user_lookup']['reset']
            }
        }
    
    def _refresh_rate_limits_from_api(self):
        """Refresh rate limits by making actual API calls to get current headers."""
        try:
            logging.info("Refreshing rate limits from X API...")
            
            # Make a lightweight API call to get fresh rate limit headers
            # Use the user lookup endpoint as it's typically available and reliable
            response = self._make_api_request('GET', '/users/me', api_endpoint_type='user_lookup')
            
            if response and hasattr(response, 'headers'):
                self._update_rate_limit(response, 'user_lookup')
                
                # Get rate limit info from headers
                remaining = response.headers.get('x-rate-limit-remaining')
                limit = response.headers.get('x-rate-limit-limit')
                reset = response.headers.get('x-rate-limit-reset')
                
                if remaining and limit:
                    logging.info(f"Fresh rate limit from API headers - Remaining: {remaining}/{limit}, Reset: {reset}")
                    
                    # For unfollow limits, we need to estimate based on X API documentation
                    # X API v2 typically allows 50 unfollow requests per 15-minute window
                    current_time = time.time()
                    
                    # Check if we need to reset the unfollow window
                    if self.rate_limits['unfollow']['reset'] < current_time:
                        # Reset window has passed, refresh unfollow limits
                        self.rate_limits['unfollow']['remaining'] = 50
                        self.rate_limits['unfollow']['reset'] = current_time + (15 * 60)  # 15 minutes from now
                        logging.info("Reset unfollow rate limit window: 50/50 remaining")
                    
                    # Update other endpoints based on their specific limits
                    if int(limit) == 300:  # User lookup endpoint
                        self.rate_limits['user_lookup']['remaining'] = int(remaining)
                        self.rate_limits['user_lookup']['limit'] = int(limit)
                        if reset:
                            self.rate_limits['user_lookup']['reset'] = int(reset)
                    
                else:
                    logging.warning("No rate limit headers found in API response")
                    
            else:
                logging.warning("Could not get API response for rate limit refresh")
                
        except Exception as e:
            logging.error(f"Error refreshing rate limits from API: {str(e)}")
            # Log error and continue with current rate limits
            logging.warning("Could not refresh rate limits from API, using existing values")
    
    def discover_account_rate_limits(self):
        """
        Discover the actual rate limits for this account by making test API calls.
        This helps adapt to different account tiers and restrictions.
        """
        discovered_limits = {}
        
        try:
            logging.info("🔍 Discovering account rate limits...")
            
            # Test different endpoints to discover their limits
            test_endpoints = [
                ('user_lookup', 'GET', '/users/me'),
                ('unfollow', 'DELETE', '/users/{user_id}/following/{target_user_id}'),  # We'll simulate this
            ]
            
            for endpoint_name, method, path in test_endpoints:
                try:
                    if endpoint_name == 'user_lookup':
                        # Make actual user lookup call
                        response = self._make_api_request(method, path, api_endpoint_type=endpoint_name)
                        
                        if response and hasattr(response, 'headers'):
                            remaining = response.headers.get('x-rate-limit-remaining')
                            limit = response.headers.get('x-rate-limit-limit')
                            reset = response.headers.get('x-rate-limit-reset')
                            
                            if remaining and limit:
                                discovered_limits[endpoint_name] = {
                                    'remaining': int(remaining),
                                    'limit': int(limit),
                                    'reset': int(reset) if reset else 0,
                                    'window_minutes': 15  # X API standard
                                }
                                logging.info(f"✅ Discovered {endpoint_name}: {remaining}/{limit}")
                    
                    elif endpoint_name == 'unfollow':
                        # For unfollow, we can only discover limits when we actually unfollow
                        # Check if we have existing data from previous unfollows
                        if self.rate_limits[endpoint_name]['limit'] != 'unknown':
                            discovered_limits[endpoint_name] = {
                                'remaining': self.rate_limits[endpoint_name]['remaining'],
                                'limit': self.rate_limits[endpoint_name]['limit'],
                                'reset': self.rate_limits[endpoint_name]['reset'],
                                'window_minutes': 15
                            }
                            logging.info(f"✅ Using known {endpoint_name}: {discovered_limits[endpoint_name]['remaining']}/{discovered_limits[endpoint_name]['limit']}")
                        else:
                            logging.info(f"⏳ {endpoint_name} limits unknown - will be discovered on first unfollow")
                
                except Exception as e:
                    logging.error(f"❌ Error testing {endpoint_name}: {str(e)}")
            
            # Update our internal rate limits with discovered data
            for endpoint_name, limits in discovered_limits.items():
                if endpoint_name in self.rate_limits:
                    self.rate_limits[endpoint_name].update(limits)
            
            # Log summary
            logging.info("📋 Account Rate Limit Discovery Results:")
            for endpoint_name, limits in discovered_limits.items():
                logging.info(f"   {endpoint_name}: {limits['remaining']}/{limits['limit']} per {limits['window_minutes']} min")
            
            return discovered_limits
            
        except Exception as e:
            logging.error(f"Error discovering account rate limits: {str(e)}")
            return {}
    
    def get_adaptive_rate_limits(self):
        """
        Get rate limits that adapt to the account's actual restrictions.
        Discovers limits if unknown and provides recommendations.
        """
        # First, try to discover current limits
        discovered = self.discover_account_rate_limits()
        
        # Get current status
        current_status = self.get_rate_limit_status()
        
        # Build adaptive recommendations
        adaptive_limits = {}
        
        for endpoint in ['unfollow', 'user_lookup', 'following']:
            endpoint_limits = current_status.get(endpoint, {})
            remaining = endpoint_limits.get('remaining', 'unknown')
            limit = endpoint_limits.get('limit', 'unknown')
            reset_time = endpoint_limits.get('reset_time', 0)
            
            # Calculate time until reset
            current_time = time.time()
            time_until_reset = max(0, reset_time - current_time)
            
            # Determine optimal strategy based on limits
            if remaining != 'unknown' and limit != 'unknown':
                if limit <= 1:
                    strategy = "Very restrictive - use automated 15-minute intervals"
                    recommended_delay = 900  # 15 minutes
                elif limit <= 10:
                    strategy = "Restrictive - use 5-10 minute intervals"
                    recommended_delay = 300  # 5 minutes
                elif limit <= 50:
                    strategy = "Standard - use 18-second intervals for batches"
                    recommended_delay = 18  # 18 seconds
                else:
                    strategy = "High limit - can use faster intervals"
                    recommended_delay = 1  # 1 second
            else:
                strategy = "Unknown limits - test with single unfollows first"
                recommended_delay = 60  # 1 minute
            
            adaptive_limits[endpoint] = {
                'current_remaining': remaining,
                'current_limit': limit,
                'time_until_reset_minutes': int(time_until_reset / 60),
                'strategy': strategy,
                'recommended_delay_seconds': recommended_delay,
                'is_restrictive': limit != 'unknown' and limit <= 10
            }
        
        return adaptive_limits