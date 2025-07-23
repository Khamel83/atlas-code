# Git Workflow Standards

## Continuous Integration Approach
Atlas Code follows a continuous integration workflow with frequent pushes to maintain progress visibility and backup.

## Push Strategy
- **Push Early, Push Often**: Commit and push changes at least every 30 minutes of active development
- **Feature Branches**: Work on feature branches, push frequently to track progress
- **Atomic Commits**: Each commit should represent a single logical change
- **Descriptive Messages**: Use clear, descriptive commit messages following conventional commits

## Commit Message Format
```
<type>: <description>

[optional body]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

## Auto-Push Commands
For development efficiency, consider setting up these aliases:

```bash
# Quick commit and push
alias qcp="git add -A && git commit -m 'feat: work in progress' && git push"

# Status and push
alias gsp="git status && git add -A && git commit -m 'feat: incremental progress' && git push"
```

## Branch Protection
- Main branch should be protected
- All changes go through feature branches
- Regular merging from main to keep branches current

## Backup Strategy
- GitHub serves as primary backup
- Local commits every 15-30 minutes during active coding
- Push to remote at least every hour during development sessions
- End-of-day push mandatory

## Development Flow
1. Create feature branch from main
2. Work in small increments (15-30 min)
3. Commit locally with descriptive messages
4. Push to GitHub regularly
5. Create PR when feature complete
6. Merge to main after review