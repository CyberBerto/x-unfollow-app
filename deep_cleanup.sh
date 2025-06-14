#!/bin/bash

# Enhanced Git History Cleanup Script
# This removes specific sensitive tokens from git history

echo "🚨 WARNING: This will rewrite git history completely!"
echo "This will remove exposed client tokens from the first commit."
echo ""
read -p "Are you sure you want to proceed? (y/N): " confirm

if [[ $confirm != [yY] ]]; then
    echo "❌ Cleanup cancelled."
    exit 1
fi

echo "🧹 Deep cleaning git history..."

# Use git filter-repo to remove sensitive patterns
# This will replace the actual token values with placeholders
git filter-branch --force --tree-filter '
    if [ -f config.py ]; then
        sed -i.bak "s/OV9rN2RLNWk2Mk9lWC05SlY1VFQ6MTpjaQ/your_actual_client_id_here/g" config.py
        sed -i.bak "s/VMN7Xoi8HtzKYZ7xxLY32_LloDYc0qlfM1FMobTLor95qNwgiG/your_actual_client_secret_here/g" config.py
        rm -f config.py.bak
    fi
' --prune-empty --tag-name-filter cat -- --all

# Clean up refs
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin

# Expire reflog and garbage collect
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "✅ Deep cleanup complete!"
echo ""
echo "Next steps:"
echo "1. Force push to update remote: git push --force-with-lease origin main"
echo "2. Verify tokens are removed: git log --all -p | grep -E 'OV9rN2RLNWk2|VMN7Xoi8'"