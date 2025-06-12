"""
Configuration settings for X Unfollow Web App.
Contains API credentials, URLs, and constants.
"""

# X API Credentials - Set via environment variables for production
import os

CLIENT_ID = os.getenv("X_CLIENT_ID", "your_actual_client_id_here")
CLIENT_SECRET = os.getenv("X_CLIENT_SECRET", "your_actual_client_secret_here")

# TODO: Replace the placeholder values above with your actual X API credentials
# Or set environment variables: export X_CLIENT_ID="your_client_id"

# OAuth Configuration - Update for production domain
CALLBACK_URL = os.getenv("CALLBACK_URL", "http://localhost:5001/callback")
# For production: CALLBACK_URL = "https://yourdomain.com/callback"

# X API v2 Base URL
API_BASE_URL = "https://api.x.com/2"

# Rate Limits (per 15-minute window)
RATE_LIMITS = {
    'following_list': 15,      # GET /users/:id/following
    'unfollow': 50,            # DELETE /users/:source_user_id/following/:target_user_id
    'user_lookup': 300         # GET /users/by/username/:username
}

# Batch Processing Settings
SMALL_BATCH_MAX = 10          # Maximum users for small batch unfollow
FULL_BATCH_MAX = 50           # Maximum users for full batch unfollow
SMALL_BATCH_DELAY = 1         # Seconds between small batch requests
FULL_BATCH_DELAY = 18         # Seconds between full batch requests (15min/50 = 18s)

# Application Settings
SECRET_KEY_LENGTH = 32        # Length for Flask secret key generation
SESSION_TIMEOUT = 7200        # Session timeout in seconds (2 hours - matches X token expiry)
DEVELOPMENT_MODE = True       # Enable extended session for testing

# Database Configuration (for multi-user support)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///users.db")

# User Management Settings
MAX_USERS_PER_DAY = 100       # Daily user registration limit
USER_RATE_LIMIT = {
    'unfollows_per_hour': 50,     # Per user unfollow limit
    'requests_per_minute': 10     # General API request limit per user
}

# Ad Configuration (for future implementation)
AD_CONFIG = {
    'enabled': os.getenv("ADS_ENABLED", "false").lower() == "true",
    'ad_frequency': 5,            # Show ad every N operations
    'ad_provider': 'google'       # google, custom, etc.
}

# Logging Configuration
LOG_FILE = "app.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Security Settings
CSRF_ENABLED = True
SECURE_HEADERS = True

# X API Scopes Required
OAUTH_SCOPES = [
    "tweet.read",
    "users.read", 
    "follows.read",
    "follows.write"
]

# Error Messages
ERROR_MESSAGES = {
    'not_authenticated': 'User not authenticated. Please log in.',
    'invalid_user': 'User not found or invalid username/ID.',
    'rate_limited': 'Rate limit reached. Please wait before trying again.',
    'api_error': 'X API error occurred. Please try again later.',
    'token_expired': 'Authentication token expired. Please log in again.',
    'batch_too_large': 'Too many users selected for batch operation.',
    'no_users_selected': 'No users selected for operation.',
    'oauth_failed': 'OAuth authentication failed. Please try again.'
}

# Success Messages
SUCCESS_MESSAGES = {
    'login_success': 'Successfully logged in to X.',
    'logout_success': 'Successfully logged out.',
    'unfollow_success': 'Successfully unfollowed user.',
    'batch_complete': 'Batch unfollow operation completed.',
    'token_refreshed': 'Authentication token refreshed successfully.'
}

# UI Configuration
UI_CONFIG = {
    'app_title': 'X Unfollow Tool',
    'app_description': 'Safely unfollow X accounts with rate limit compliance',
    'max_following_display': 1000,  # Maximum following list items to display
    'progress_update_interval': 1000,  # Milliseconds between progress updates
    'status_display_timeout': 5000     # Milliseconds to show status messages
}

# Development Settings
DEBUG_MODE = True
DEV_SERVER_HOST = '0.0.0.0'
DEV_SERVER_PORT = 5000

# Production Settings (for deployment)
PROD_SETTINGS = {
    'debug': False,
    'host': '0.0.0.0',
    'port': 5000,
    'ssl_context': None,  # Set to SSL context for HTTPS
    'threaded': True
}
