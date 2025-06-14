#!/bin/bash

# Git History Cleanup Script
# This removes sensitive data from git history

echo "🚨 WARNING: This will rewrite git history!"
echo "Make sure you've regenerated your X API credentials first."
echo ""
read -p "Have you regenerated your API credentials? (y/N): " confirm

if [[ $confirm != [yY] ]]; then
    echo "❌ Please regenerate your API credentials first, then run this script."
    exit 1
fi

echo "🧹 Cleaning git history..."

# Remove sensitive data from git history using git filter-branch
# This removes the old config.py with exposed credentials
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config.py || true' \
  --prune-empty --tag-name-filter cat -- --all

# Clean up refs
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin

# Expire reflog and garbage collect
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "✅ Git history cleaned!"
echo ""
echo "Next steps:"
echo "1. Force push to update remote: git push --force-with-lease origin main"
echo "2. Verify credentials are not in history: git log --oneline | head -10"
echo "3. Update your .env file with new regenerated credentials"