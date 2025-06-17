# Security Guidelines

## Environment Variables Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual credentials:**
   ```bash
   # X API Credentials from https://developer.twitter.com/en/portal/dashboard
   X_CLIENT_ID=your_actual_client_id
   X_CLIENT_SECRET=your_actual_client_secret
   
   # OAuth Configuration
   CALLBACK_URL=http://localhost:5001/callback
   
   # Flask Secret Key (generate a random one for production)
   FLASK_SECRET_KEY=your_secure_random_key
   ```

3. **Install python-dotenv:**
   ```bash
   pip install python-dotenv
   ```

## Important Security Notes

- **Never commit `.env` files** - they are already in `.gitignore`
- **Regenerate your X API credentials** if they were previously exposed
- **Use different credentials for production and development**
- **Keep your `.env` file private** and never share it

## If You Accidentally Exposed Credentials

1. **Immediately regenerate your X API credentials** in the X Developer Portal
2. **Update your `.env` file** with the new credentials
3. **Remove the exposed credentials from git history:**
   ```bash
   # If you've already committed exposed credentials, remove them from history
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch config.py' \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push to update remote (use with caution)
   git push origin --force --all
   ```

## Git History Cleanup

If credentials were already committed, follow these steps:

1. **Change your credentials immediately** in the X Developer Portal
2. **Use BFG Repo-Cleaner** (recommended) or git filter-branch to remove sensitive data:
   ```bash
   # Using BFG (safer option)
   brew install bfg  # On macOS
   bfg --delete-files config.py
   git reflog expire --expire=now --all && git gc --prune=now --aggressive
   ```

3. **Force push to overwrite remote history:**
   ```bash
   git push --force-with-lease origin main
   ```

## Production Deployment

For production deployment:
- Use secure environment variable management (AWS Secrets Manager, Azure Key Vault, etc.)
- Enable HTTPS/SSL
- Use strong, unique secret keys
- Regular credential rotation
- Monitor access logs

## Verification

To verify your setup is secure:
1. Check that `.env` is in `.gitignore`
2. Confirm credentials are loaded: `python -c "from config import CLIENT_ID; print('✅ Loaded' if CLIENT_ID else '❌ Missing')"`
3. Verify no credentials in git: `git log --oneline | head -10`