#!/bin/bash

# Quick Push Script for Atlas Code Development
# Provides continuous integration workflow with 5-minute intervals

echo "🚀 Atlas Code Quick Push..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Get current branch
branch=$(git branch --show-current)
echo "📍 Current branch: $branch"

# Check git status
status=$(git status --porcelain)
if [ -z "$status" ]; then
    echo "✅ No changes to commit"
    exit 0
fi

# Show what we're about to commit
echo "📝 Changes to commit:"
git status --short

# Add all changes
git add -A

# Get commit message from argument or use default
if [ $# -eq 0 ]; then
    commit_msg="feat: incremental progress - $(date '+%Y-%m-%d %H:%M')"
else
    commit_msg="$*"
fi

# Commit with message
echo "💾 Committing: $commit_msg"
git commit -m "$commit_msg

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
echo "🌐 Pushing to origin/$branch..."
if git push; then
    echo "✅ Successfully pushed to GitHub!"
    echo "🔗 View at: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')"
else
    echo "❌ Push failed - check network connection or branch permissions"
    exit 1
fi

# Show final status
echo "📊 Repository status:"
git log --oneline -1
echo "🎯 Ready for continuous development!"