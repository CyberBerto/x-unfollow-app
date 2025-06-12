# X Unfollow Web App

A Flask-based web application for safely unfollowing X (formerly Twitter) accounts using the X API v2. This app implements OAuth 2.0 authentication and respects X's rate limits to prevent account restrictions.

## Features

- **OAuth 2.0 Authentication**: Secure login with X without managing developer tokens manually
- **Single Unfollow**: Unfollow individual accounts by username or user ID
- **Small Batch Unfollow**: Unfollow up to 10 accounts with 1-second delays
- **Full Batch Unfollow**: Unfollow up to 50 accounts with 18-second delays (rate limit compliant)
- **Real-time Progress**: Live updates during batch operations
- **Rate Limit Monitoring**: Visual display of current rate limit status
- **Responsive Design**: Works on desktop and mobile browsers

## Prerequisites

1. **Python 3.9+** installed on your system
2. **X Developer Account** and API access
3. **X API App** created in the X Developer Portal

## Setup Instructions

### 1. Get X API Credentials

1. Visit [X Developer Portal](https://developer.x.com)
2. Create a new app or use an existing one
3. Navigate to your app's settings
4. Copy your **Client ID** and **Client Secret**
5. Set the callback URL to: `http://localhost:5000/callback`
6. Ensure your app has the following permissions:
   - Read Tweets
   - Read Users
   - Read Following
   - Write Following

### 2. Clone and Setup the Project

```bash
# Create project directory
mkdir x-unfollow-app
cd x-unfollow-app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Credentials

1. Open `config.py`
2. Replace the placeholder values:
   ```python
   CLIENT_ID = "your_actual_client_id_here"
   CLIENT_SECRET = "your_actual_client_secret_here"
   ```

### 4. Run the Application

```bash
python app.py
```

The app will start on `http://localhost:5000`

## Usage

### Authentication
1. Open `http://localhost:5000` in your browser
2. Click "Login with X"
3. Authorize the app on X's login page
4. You'll be redirected back to the app

### Single Unfollow
1. Enter a username (without @) or user ID in the text field
2. Click "Unfollow User"

### Batch Unfollow
1. Click "Load Following List" to fetch accounts you're following
2. Select accounts using checkboxes
3. Choose batch size:
   - **Small Batch**: Up to 10 accounts (1-second delays)
   - **Full Batch**: Up to 50 accounts (18-second delays)

## Rate Limits and Compliance

This app strictly adheres to X API v2 rate limits:

- **Following List**: 15 requests per 15 minutes (max 1,500 accounts)
- **Unfollows**: 50 requests per 15 minutes
- **User Lookups**: 300 requests per 15 minutes

**Important Notes:**
- X platform limits: 400 follow/unfollow actions per day
- Aggressive unfollowing may result in account restrictions
- Full batch operations take ~15 minutes for 50 accounts
- The app automatically handles rate limit errors and retries

## File Structure

```
x-unfollow-app/
├── app.py                 # Main Flask application
├── api.py                 # X API client and OAuth logic
├── config.py              # Configuration and credentials
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main web interface
└── static/
    ├── css/
    │   └── style.css     # Custom styling
    └── js/
        └── script.js     # Client-side JavaScript
```

## Security Features

- Secure token storage using `keyring`
- CSRF protection for forms
- Input sanitization to prevent injection attacks
- Automatic token refresh (every 2 hours)
- No hardcoded credentials in source code

## Troubleshooting

### Common Issues

**"Invalid client_id" error:**
- Verify your Client ID is correct in `config.py`
- Ensure your app is approved and has the right permissions

**"Callback URL mismatch" error:**
- Set callback URL to `http://localhost:5000/callback` in X Developer Portal
- Ensure you're accessing the app via `localhost`, not `127.0.0.1`

**Rate limit errors:**
- Wait for the rate limit window to reset (15 minutes)
- Check the rate limit status display in the app

**Token expired errors:**
- The app should automatically refresh tokens
- If persistent, log out and log back in

### Logs

Check `app.log` for detailed error messages and API call logs.

## Development

### Running in Debug Mode

The app runs in debug mode by default for development. To disable:

```python
# In app.py, change the last line to:
app.run(debug=False, host='0.0.0.0', port=5000)
```

### Testing

Test with a small number of accounts first:
1. Follow 2-3 test accounts
2. Test single unfollow
3. Test small batch with 2-3 accounts
4. Verify rate limits are respected

## Production Deployment

For production deployment:

1. Set `DEBUG_MODE = False` in `config.py`
2. Use a proper WSGI server (e.g., Gunicorn)
3. Enable HTTPS
4. Use environment variables for credentials
5. Set up proper logging

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Limitations

- Free/Basic X API tiers have limited monthly usage
- Cannot unfollow more than 50 accounts per 15 minutes
- Requires manual OAuth flow for each user
- Desktop-focused UI (mobile responsive but not optimized)

## License

This project is for educational purposes. Ensure compliance with X's Terms of Service and Developer Agreement when using their API.

## Support

For issues:
1. Check the troubleshooting section above
2. Review `app.log` for error messages
3. Verify your X API app configuration
4. Ensure you have the required API access level

## Alternative Solutions

If this app doesn't meet your needs:
- [Circleboom](https://circleboom.com): Commercial unfollow tool
- [Unfollower Stats](https://unfollowerstats.com): Web-based analytics
- Manual unfollowing via X web interface