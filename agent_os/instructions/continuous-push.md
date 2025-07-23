# Continuous Push Instructions

## Immediate Actions
When working on Atlas Code, always follow these steps:

### 1. Start of Development Session
```bash
git status
git pull origin main  # or current branch
```

### 2. During Development (Every 5 minutes)
```bash
git add -A
git commit -m "feat: describe what you just implemented"
git push
```

### 3. End of Development Session
```bash
git add -A
git commit -m "feat: end of session - summarize all changes"
git push
```

## Automated Push Reminders
Set up these development habits:

### Quick Push Script
Create `quick-push.sh`:
```bash
#!/bin/bash
echo "🚀 Quick pushing changes..."
git add -A
git commit -m "feat: incremental progress - $(date)"
git push
echo "✅ Changes pushed to GitHub"
```

### IDE Integration
- Set up auto-save every 2 minutes
- Configure git hooks for automatic staging
- Use IDE extensions for git status visibility
- Consider git auto-push extensions for 5-minute intervals

## Emergency Backup
If system crashes or unexpected issues:
```bash
# Emergency commit everything
git add -A
git commit -m "emergency: backup all work"
git push --force-with-lease
```

## Branch Management
- Always work on feature branches
- Push feature branches immediately after creation
- Regular sync with main branch
- Use descriptive branch names: `feature/model-router`, `fix/budget-calculation`

## Integration with Atlas Code
Atlas Code development should include:
1. Test changes locally
2. Commit with test results
3. Push immediately
4. Document any issues found
5. Continue development cycle

## GitHub Actions (Future)
Consider setting up:
- Automatic testing on push
- Code quality checks
- Deployment automation
- Notification systems for failed pushes