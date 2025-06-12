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
            'unfollow': {'remaining': 50, 'reset': 0, 'limit': 50}, 
            'user_lookup': {'remaining': 300, 'reset': 0, 'limit': 300}
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
                # Update remaining count with validation
                if remaining:
                    remaining_count = int(remaining)
                    expected_limit = self.rate_limits[endpoint]['limit']
                    # Only update if the value makes sense for this endpoint
                    if remaining_count <= expected_limit:
                        self.rate_limits[endpoint]['remaining'] = remaining_count
                        logging.info(f"Updated {endpoint} rate limit: {remaining_count}/{expected_limit} remaining")
                
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
    
    def get_rate_limit_status(self):
        """
        Get current rate limit status.
        
        Returns:
            dict: Rate limit information
        """
        return {
            'following': {
                'remaining': self.rate_limits['following']['remaining'],
                'limit': self.rate_limits['following']['limit'],
                'reset_time': self.rate_limits['following']['reset']
            },
            'unfollow': {
                'remaining': self.rate_limits['unfollow']['remaining'],
                'limit': self.rate_limits['unfollow']['limit'],
                'reset_time': self.rate_limits['unfollow']['reset']
            },
            'user_lookup': {
                'remaining': self.rate_limits['user_lookup']['remaining'],
                'limit': self.rate_limits['user_lookup']['limit'],
                'reset_time': self.rate_limits['user_lookup']['reset']
            }
        }