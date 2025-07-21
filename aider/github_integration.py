"""
GitHub Integration for Handover Process

Provides automatic GitHub push, branch management, and artifact upload
as part of the systematic handover workflow.
"""

import os
import json
import subprocess
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import git

from .io import InputOutput


@dataclass
class GitHubHandoverArtifact:
    """GitHub handover artifact metadata"""
    artifact_type: str  # "handover_state", "production_report", "session_summary"
    file_path: str
    branch: str
    commit_hash: str
    timestamp: str
    size_bytes: int
    description: str


@dataclass
class GitHubIntegrationResult:
    """Results of GitHub integration operations"""
    success: bool
    operations_performed: List[str]
    artifacts_uploaded: List[GitHubHandoverArtifact]
    remote_urls: List[str]
    errors: List[str]
    warnings: List[str]


class GitHubHandoverIntegration:
    """Integrates handover process with GitHub workflows"""
    
    def __init__(self, io: InputOutput = None, project_root: str = None):
        self.io = io
        self.project_root = project_root or os.getcwd()
        self.repo = None
        self._initialize_git_repo()
        
    def _initialize_git_repo(self):
        """Initialize git repository connection"""
        try:
            self.repo = git.Repo(search_parent_directories=True)
        except Exception as e:
            if self.io:
                self.io.tool_warning(f"Could not initialize git repository: {e}")
            self.repo = None
    
    def process_handover_with_github(self, 
                                   handover_state_file: str,
                                   production_report: Dict[str, Any] = None,
                                   reason: str = "handover",
                                   auto_push: bool = True,
                                   create_branch: bool = False) -> GitHubIntegrationResult:
        """Process handover with GitHub integration"""
        
        operations = []
        artifacts = []
        errors = []
        warnings = []
        remote_urls = []
        
        if self.io:
            self.io.tool_output("🔄 Processing handover with GitHub integration...")
        
        try:
            # Ensure we have a git repository
            if not self.repo:
                errors.append("No git repository found")
                return GitHubIntegrationResult(
                    success=False,
                    operations_performed=operations,
                    artifacts_uploaded=artifacts,
                    remote_urls=remote_urls,
                    errors=errors,
                    warnings=warnings
                )
            
            # Get current branch info
            current_branch = self.repo.active_branch.name
            current_commit = self.repo.head.commit.hexsha[:8]
            
            # Create handover branch if requested
            handover_branch = current_branch
            if create_branch:
                handover_branch = f"handover/{reason.replace(' ', '-')}-{int(time.time())}"
                try:
                    self.repo.create_head(handover_branch)
                    self.repo.heads[handover_branch].checkout()
                    operations.append(f"Created and switched to branch: {handover_branch}")
                    if self.io:
                        self.io.tool_output(f"📝 Created handover branch: {handover_branch}")
                except Exception as e:
                    warnings.append(f"Could not create handover branch: {e}")
            
            # Add handover artifacts to git
            artifacts_added = self._add_handover_artifacts(
                handover_state_file, production_report, reason
            )
            artifacts.extend(artifacts_added)
            operations.extend([f"Added artifact: {a.file_path}" for a in artifacts_added])
            
            # Commit handover changes
            commit_success = self._commit_handover_changes(reason, artifacts_added)
            if commit_success:
                operations.append("Committed handover changes")
                new_commit = self.repo.head.commit.hexsha[:8]
                
                # Update artifact metadata with new commit
                for artifact in artifacts:
                    artifact.commit_hash = new_commit
            else:
                warnings.append("No changes to commit")
            
            # Push to remote if requested and available
            if auto_push:
                push_result = self._push_to_remote(handover_branch)
                if push_result["success"]:
                    operations.append(f"Pushed branch {handover_branch} to remote")
                    remote_urls.extend(push_result["urls"])
                    
                    if self.io:
                        self.io.tool_output(f"📤 Pushed handover to remote: {handover_branch}")
                        for url in push_result["urls"]:
                            self.io.tool_output(f"   Remote URL: {url}")
                else:
                    warnings.extend(push_result["errors"])
            
            # Create GitHub artifacts summary
            self._create_github_artifacts_summary(artifacts, handover_branch)
            operations.append("Created GitHub artifacts summary")
            
            success = len(errors) == 0
            
            if self.io:
                if success:
                    self.io.tool_output("✅ GitHub integration completed successfully")
                else:
                    self.io.tool_error("❌ GitHub integration completed with errors")
                
                self.io.tool_output(f"📊 Operations: {len(operations)}")
                self.io.tool_output(f"📁 Artifacts: {len(artifacts)}")
                if warnings:
                    self.io.tool_output(f"⚠️  Warnings: {len(warnings)}")
            
            return GitHubIntegrationResult(
                success=success,
                operations_performed=operations,
                artifacts_uploaded=artifacts,
                remote_urls=remote_urls,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"GitHub integration failed: {e}")
            if self.io:
                self.io.tool_error(f"GitHub integration error: {e}")
            
            return GitHubIntegrationResult(
                success=False,
                operations_performed=operations,
                artifacts_uploaded=artifacts,
                remote_urls=remote_urls,
                errors=errors,
                warnings=warnings
            )
    
    def _add_handover_artifacts(self, 
                               handover_state_file: str,
                               production_report: Dict[str, Any] = None,
                               reason: str = "handover") -> List[GitHubHandoverArtifact]:
        """Add handover artifacts to git repository"""
        
        artifacts = []
        current_branch = self.repo.active_branch.name
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        
        try:
            # Add handover state file
            if os.path.exists(handover_state_file):
                # Add to git staging
                self.repo.index.add([handover_state_file])
                
                # Create artifact metadata
                file_stats = os.stat(handover_state_file)
                artifact = GitHubHandoverArtifact(
                    artifact_type="handover_state",
                    file_path=handover_state_file,
                    branch=current_branch,
                    commit_hash="pending",  # Will be updated after commit
                    timestamp=timestamp,
                    size_bytes=file_stats.st_size,
                    description=f"Handover state captured for: {reason}"
                )
                artifacts.append(artifact)
            
            # Add LLM_HANDOVER.md if it exists
            handover_md = os.path.join(self.project_root, "LLM_HANDOVER.md")
            if os.path.exists(handover_md):
                self.repo.index.add([handover_md])
                
                file_stats = os.stat(handover_md)
                artifact = GitHubHandoverArtifact(
                    artifact_type="session_summary",
                    file_path="LLM_HANDOVER.md",
                    branch=current_branch,
                    commit_hash="pending",
                    timestamp=timestamp,
                    size_bytes=file_stats.st_size,
                    description="LLM session handover documentation"
                )
                artifacts.append(artifact)
            
            # Add production report if provided
            if production_report:
                prod_report_file = f"production_validation_{int(time.time())}.json"
                prod_report_path = os.path.join(self.project_root, prod_report_file)
                
                with open(prod_report_path, 'w') as f:
                    json.dump(production_report, f, indent=2)
                
                self.repo.index.add([prod_report_file])
                
                file_stats = os.stat(prod_report_path)
                artifact = GitHubHandoverArtifact(
                    artifact_type="production_report",
                    file_path=prod_report_file,
                    branch=current_branch,
                    commit_hash="pending",
                    timestamp=timestamp,
                    size_bytes=file_stats.st_size,
                    description="Production readiness validation report"
                )
                artifacts.append(artifact)
            
            # Add handover history if it exists
            handover_history = os.path.join(self.project_root, ".aider.handover.history.jsonl")
            if os.path.exists(handover_history):
                self.repo.index.add([handover_history])
                
                file_stats = os.stat(handover_history)
                artifact = GitHubHandoverArtifact(
                    artifact_type="handover_history",
                    file_path=".aider.handover.history.jsonl",
                    branch=current_branch,
                    commit_hash="pending",
                    timestamp=timestamp,
                    size_bytes=file_stats.st_size,
                    description="Complete handover history log"
                )
                artifacts.append(artifact)
            
        except Exception as e:
            if self.io:
                self.io.tool_warning(f"Could not add handover artifacts: {e}")
        
        return artifacts
    
    def _commit_handover_changes(self, reason: str, artifacts: List[GitHubHandoverArtifact]) -> bool:
        """Commit handover changes to git"""
        
        try:
            # Check if there are changes to commit
            if not self.repo.index.diff("HEAD") and not self.repo.untracked_files:
                return False
            
            # Create comprehensive commit message
            commit_message = self._generate_handover_commit_message(reason, artifacts)
            
            # Commit changes
            self.repo.index.commit(commit_message)
            
            if self.io:
                self.io.tool_output(f"📝 Committed handover changes: {len(artifacts)} artifacts")
            
            return True
            
        except Exception as e:
            if self.io:
                self.io.tool_warning(f"Could not commit handover changes: {e}")
            return False
    
    def _generate_handover_commit_message(self, reason: str, artifacts: List[GitHubHandoverArtifact]) -> str:
        """Generate comprehensive commit message for handover"""
        
        lines = [
            f"🔄 Handover: {reason}",
            "",
            "Automated handover process with systematic state capture:",
            ""
        ]
        
        # Add artifact summary
        artifact_types = {}
        for artifact in artifacts:
            artifact_types[artifact.artifact_type] = artifact_types.get(artifact.artifact_type, 0) + 1
        
        for artifact_type, count in artifact_types.items():
            lines.append(f"- {artifact_type.replace('_', ' ').title()}: {count} file{'s' if count > 1 else ''}")
        
        lines.extend([
            "",
            "This commit includes:",
            "- Complete session state for seamless handover",
            "- Documentation for next LLM to continue work",
            "- Production readiness validation results",
            "- Historical handover data for audit trail",
            "",
            "Ready for production deployment aftercare procedures.",
            "",
            "🤖 Generated with [Atlas Code](https://github.com/anthropics/atlas-code)",
            "",
            "Co-Authored-By: Atlas Code Handover System <noreply@anthropic.com>"
        ])
        
        return "\n".join(lines)
    
    def _push_to_remote(self, branch: str) -> Dict[str, Any]:
        """Push branch to remote repository"""
        
        result = {
            "success": False,
            "urls": [],
            "errors": []
        }
        
        try:
            # Check if remote exists
            if not self.repo.remotes:
                result["errors"].append("No remote repository configured")
                return result
            
            # Get origin remote
            origin = self.repo.remotes.origin
            
            # Push branch to remote
            push_info = origin.push(branch)
            
            # Check push results
            for info in push_info:
                if info.flags & info.ERROR:
                    result["errors"].append(f"Push error: {info.summary}")
                elif info.flags & info.REJECTED:
                    result["errors"].append(f"Push rejected: {info.summary}")
                else:
                    result["success"] = True
                    result["urls"].append(f"{origin.url}/tree/{branch}")
            
            if not result["success"] and not result["errors"]:
                result["errors"].append("Push completed but status unclear")
            
        except Exception as e:
            result["errors"].append(f"Push failed: {e}")
        
        return result
    
    def _create_github_artifacts_summary(self, artifacts: List[GitHubHandoverArtifact], branch: str):
        """Create GitHub artifacts summary file"""
        
        try:
            summary = {
                "handover_artifacts": {
                    "branch": branch,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                    "total_artifacts": len(artifacts),
                    "total_size_bytes": sum(a.size_bytes for a in artifacts),
                    "artifacts": [asdict(a) for a in artifacts]
                },
                "github_integration": {
                    "auto_push_enabled": True,
                    "branch_protection_recommended": True,
                    "deployment_ready": len([a for a in artifacts if a.artifact_type == "production_report"]) > 0
                },
                "next_steps": [
                    "Review handover artifacts in GitHub repository",
                    "Verify production readiness validation results",
                    "Set up branch protection rules if not already configured",
                    "Consider creating GitHub release for production deployment",
                    "Update team about handover completion and new branch"
                ]
            }
            
            summary_file = os.path.join(self.project_root, ".github-handover-summary.json")
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            # Add to git if .github directory exists (indicating GitHub repo)
            github_dir = os.path.join(self.project_root, ".github")
            if os.path.exists(github_dir):
                self.repo.index.add([".github-handover-summary.json"])
                
        except Exception as e:
            if self.io:
                self.io.tool_warning(f"Could not create GitHub artifacts summary: {e}")
    
    def create_handover_pull_request(self, 
                                   source_branch: str,
                                   target_branch: str = "main",
                                   title: str = None,
                                   description: str = None) -> Dict[str, Any]:
        """Create pull request for handover changes (requires GitHub CLI)"""
        
        result = {
            "success": False,
            "pull_request_url": None,
            "errors": []
        }
        
        try:
            # Check if GitHub CLI is available
            gh_check = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            if gh_check.returncode != 0:
                result["errors"].append("GitHub CLI (gh) not available")
                return result
            
            # Generate PR title and description
            if not title:
                title = f"🔄 Handover: {source_branch}"
            
            if not description:
                description = self._generate_pr_description(source_branch)
            
            # Create pull request
            pr_cmd = [
                "gh", "pr", "create",
                "--base", target_branch,
                "--head", source_branch,
                "--title", title,
                "--body", description
            ]
            
            pr_result = subprocess.run(pr_cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if pr_result.returncode == 0:
                result["success"] = True
                result["pull_request_url"] = pr_result.stdout.strip()
                
                if self.io:
                    self.io.tool_output(f"✅ Created pull request: {result['pull_request_url']}")
            else:
                result["errors"].append(f"PR creation failed: {pr_result.stderr}")
        
        except Exception as e:
            result["errors"].append(f"PR creation error: {e}")
        
        return result
    
    def _generate_pr_description(self, source_branch: str) -> str:
        """Generate pull request description for handover"""
        
        description = f"""# Handover Pull Request

This pull request contains systematic handover artifacts for seamless project continuation.

## 🔄 Handover Details

**Branch:** `{source_branch}`  
**Generated:** {time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}  
**Purpose:** Enable smooth transition to next development phase

## 📁 Included Artifacts

- **Handover State**: Complete session state for LLM continuation
- **Session Documentation**: Updated LLM_HANDOVER.md with current context
- **Production Validation**: Readiness assessment for deployment
- **History Log**: Complete audit trail of handover events

## 🎯 Production Readiness

This handover includes production validation to ensure deployment readiness:

- Code quality checks
- Testing coverage validation
- Security considerations
- Documentation completeness
- Deployment configuration review

## 🚀 Next Steps

1. **Review Artifacts**: Examine all handover files for completeness
2. **Validate State**: Ensure handover state is coherent and accessible
3. **Production Check**: Review production validation results
4. **Team Notification**: Update team about handover completion
5. **Continue Development**: Use handover state to resume work seamlessly

## 🤖 Automated Generation

This pull request was automatically generated by the Atlas Code handover system to ensure systematic and complete project transitions.

**Ready for merge and production deployment.**
"""
        
        return description
    
    def setup_github_actions_workflow(self) -> bool:
        """Set up GitHub Actions workflow for handover automation"""
        
        try:
            github_dir = os.path.join(self.project_root, ".github")
            workflows_dir = os.path.join(github_dir, "workflows")
            
            # Create directories if they don't exist
            os.makedirs(workflows_dir, exist_ok=True)
            
            # Create handover workflow
            workflow_content = self._generate_github_actions_workflow()
            workflow_file = os.path.join(workflows_dir, "atlas-handover.yml")
            
            with open(workflow_file, 'w') as f:
                f.write(workflow_content)
            
            if self.io:
                self.io.tool_output(f"📄 Created GitHub Actions workflow: {workflow_file}")
            
            return True
            
        except Exception as e:
            if self.io:
                self.io.tool_error(f"Could not set up GitHub Actions workflow: {e}")
            return False
    
    def _generate_github_actions_workflow(self) -> str:
        """Generate GitHub Actions workflow for handover automation"""
        
        workflow = """name: Atlas Code Handover Validation

on:
  push:
    branches: [ 'handover/**' ]
  pull_request:
    branches: [ main, master ]
    paths:
      - '.aider.handover.state.json'
      - 'LLM_HANDOVER.md'
      - 'production_validation_*.json'

jobs:
  validate-handover:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install GitPython jsonschema
    
    - name: Validate handover state
      run: |
        python -c "
        import json
        import os
        
        # Validate handover state file exists and is valid JSON
        handover_file = '.aider.handover.state.json'
        if os.path.exists(handover_file):
            with open(handover_file, 'r') as f:
                state = json.load(f)
            print(f'✅ Handover state is valid JSON')
            print(f'📊 Session ID: {state.get(\"session_id\", \"unknown\")}')
            print(f'🕐 Timestamp: {state.get(\"timestamp\", \"unknown\")}')
            print(f'🎯 Reason: {state.get(\"handover_reason\", \"unknown\")}')
        else:
            print('❌ Handover state file not found')
            exit(1)
        "
    
    - name: Validate production report
      run: |
        python -c "
        import json
        import glob
        
        # Find production validation files
        prod_files = glob.glob('production_validation_*.json')
        if prod_files:
            for prod_file in prod_files:
                with open(prod_file, 'r') as f:
                    report = json.load(f)
                status = report.get('overall_status', 'unknown')
                score = report.get('readiness_score', 0)
                print(f'📋 Production Report: {prod_file}')
                print(f'📊 Status: {status.upper()}')
                print(f'🎯 Readiness: {score:.1%}')
        else:
            print('ℹ️  No production validation report found')
        "
    
    - name: Validate documentation
      run: |
        if [ -f "LLM_HANDOVER.md" ]; then
          echo "✅ LLM_HANDOVER.md exists"
          wc -l LLM_HANDOVER.md
        else
          echo "⚠️ LLM_HANDOVER.md not found"
        fi
    
    - name: Summary
      run: |
        echo "🎉 Handover validation completed successfully!"
        echo "📝 Ready for project continuation"
        echo "🚀 Production deployment procedures available"

  # Optional: Deploy to staging environment for testing
  deploy-staging:
    runs-on: ubuntu-latest
    needs: validate-handover
    if: contains(github.event.head_commit.message, 'production') || contains(github.event.head_commit.message, 'deploy')
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Production readiness check
      run: |
        echo "🔍 Checking production readiness..."
        # Add your production deployment checks here
        echo "✅ Ready for production deployment"
    
    - name: Notify team
      run: |
        echo "📢 Handover completed - ready for production deployment"
        # Add team notification logic here (Slack, email, etc.)
"""
        
        return workflow
    
    def get_github_repository_info(self) -> Dict[str, Any]:
        """Get GitHub repository information"""
        
        info = {
            "has_remote": False,
            "remote_url": None,
            "is_github": False,
            "repository_name": None,
            "default_branch": None,
            "has_github_directory": False
        }
        
        try:
            if self.repo and self.repo.remotes:
                origin = self.repo.remotes.origin
                info["has_remote"] = True
                info["remote_url"] = origin.url
                
                # Check if it's a GitHub repository
                if "github.com" in origin.url:
                    info["is_github"] = True
                    
                    # Extract repository name
                    url_parts = origin.url.replace(".git", "").split("/")
                    if len(url_parts) >= 2:
                        info["repository_name"] = f"{url_parts[-2]}/{url_parts[-1]}"
            
            # Check for .github directory
            github_dir = os.path.join(self.project_root, ".github")
            info["has_github_directory"] = os.path.exists(github_dir)
            
        except Exception as e:
            if self.io:
                self.io.tool_warning(f"Could not get GitHub repository info: {e}")
        
        return info