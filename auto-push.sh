#!/bin/bash

# Auto-Push Script for Atlas Code Development
# Automatically commits and pushes every 5 minutes during development

echo "🔄 Starting Atlas Code Auto-Push (5-minute intervals)..."
echo "⚠️  This will run indefinitely - press Ctrl+C to stop"
echo "📍 Working directory: $(pwd)"
echo "📍 Git branch: $(git branch --show-current 2>/dev/null || echo 'not a git repo')"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Function to perform auto-push
auto_push() {
    echo "🕐 $(date '+%H:%M:%S') - Checking for changes..."
    
    # Check if there are any changes
    if [ -z "$(git status --porcelain)" ]; then
        echo "✅ No changes to commit"
        return 0
    fi
    
    # Show what we're committing
    echo "📝 Changes detected:"
    git status --short
    
    # Add all changes
    git add -A
    
    # Commit with timestamp
    commit_msg="auto: 5-min backup - $(date '+%Y-%m-%d %H:%M')"
    git commit -m "$commit_msg

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    # Push to remote
    echo "🌐 Pushing to remote..."
    if git push; then
        echo "✅ Auto-push successful!"
    else
        echo "❌ Push failed - continuing anyway"
    fi
    
    echo ""
}

# Initial push to make sure we're synced
echo "🚀 Initial sync..."
auto_push

# Main loop - check every 5 minutes (300 seconds)
echo "⏰ Starting 5-minute auto-push loop..."
echo "   Use Ctrl+C to stop"
echo ""

while true; do
    sleep 300  # 5 minutes
    auto_push
done