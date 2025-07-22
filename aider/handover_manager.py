import json
import os
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
import git

from .analytics import Analytics
from .history import ChatSummary
from .handover_schema import HandoverStateValidator


@dataclass
class HandoverState:
    """Complete session state for LLM handover"""
    
    # Core session metadata
    session_id: str
    timestamp: str
    atlas_version: str
    git_branch: str
    git_commit: str
    working_directory: str
    
    # Model configuration
    main_model: Dict[str, Any]
    editor_model: Optional[Dict[str, Any]]
    weak_model: Optional[Dict[str, Any]]
    model_settings: Dict[str, Any]
    
    # File context
    active_files: List[str]
    read_only_files: List[str]
    repository_map: Dict[str, Any]
    git_status: Dict[str, Any]
    
    # Session context
    chat_history_summary: str
    conversation_context: Dict[str, Any]
    user_preferences: Dict[str, Any]
    environment_variables: Dict[str, str]
    
    # Operational state
    current_coder_type: str
    edit_format: str
    pending_operations: List[Dict[str, Any]]
    analytics_data: Dict[str, Any]
    
    # Performance metrics
    session_duration: float
    token_usage: Dict[str, int]
    success_metrics: Dict[str, Any]
    
    # Handover metadata
    handover_reason: str
    handover_trigger: str
    validation_checksum: str
    file_hashes: Optional[Dict[str, str]] = None


class HandoverManager:
    """Manages systematic LLM handover process"""
    
    def __init__(self, io=None, analytics=None):
        self.io = io
        self.analytics = analytics
        self.session_start_time = time.time()
        self.handover_state_file = ".aider.handover.state.json"
        self.handover_history_file = ".aider.handover.history.jsonl"
        self.validator = HandoverStateValidator()
        
    def capture_current_state(self, coder=None, reason="manual", trigger="user_request") -> HandoverState:
        """Capture complete current session state"""
        
        try:
            # Core session metadata
            session_id = self._generate_session_id()
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Git information
            git_info = self._get_git_info()
            
            # Model configuration
            model_config = self._capture_model_configuration(coder)
            
            # File context
            file_context = self._capture_file_context(coder)
            
            # Session context
            session_context = self._capture_session_context(coder)
            
            # Performance metrics
            performance_metrics = self._capture_performance_metrics()
            
            # Create handover state
            state = HandoverState(
                session_id=session_id,
                timestamp=timestamp,
                atlas_version=self._get_atlas_version(),
                git_branch=git_info.get("branch", "unknown"),
                git_commit=git_info.get("commit", "unknown"),
                working_directory=os.getcwd(),
                
                main_model=model_config.get("main", {}),
                editor_model=model_config.get("editor"),
                weak_model=model_config.get("weak"),
                model_settings=model_config.get("settings", {}),
                
                active_files=file_context.get("active", []),
                read_only_files=file_context.get("read_only", []),
                repository_map=file_context.get("repo_map", {}),
                git_status=file_context.get("git_status", {}),
                
                chat_history_summary=session_context.get("history_summary", ""),
                conversation_context=session_context.get("conversation", {}),
                user_preferences=session_context.get("preferences", {}),
                environment_variables=session_context.get("env_vars", {}),
                
                current_coder_type=session_context.get("coder_type", "unknown"),
                edit_format=session_context.get("edit_format", "unknown"),
                pending_operations=session_context.get("pending_ops", []),
                analytics_data=session_context.get("analytics", {}),
                
                session_duration=performance_metrics.get("duration", 0),
                token_usage=performance_metrics.get("tokens", {}),
                success_metrics=performance_metrics.get("success", {}),
                
                handover_reason=reason,
                handover_trigger=trigger,
                validation_checksum="",
                file_hashes={f: self._calculate_file_hash(f) for f in file_context.get("active", []) + file_context.get("read_only", [])}
            )
            
            # Calculate validation checksum
            state.validation_checksum = self._calculate_state_checksum(state)
            
            return state
            
        except Exception as e:
            if self.io:
                self.io.tool_error(f"Failed to capture handover state: {e}")
            raise
    
    def save_handover_state(self, state: HandoverState) -> str:
        """Save handover state to persistent storage with validation"""
        
        try:
            # Convert to dict for validation
            state_data = asdict(state)
            
            # Validate state before saving
            validation_result = self.validator.validate_state(state_data)
            
            if not validation_result["is_valid"]:
                error_msg = f"Invalid handover state: {validation_result['errors']}"
                if self.io:
                    self.io.tool_error(error_msg)
                raise ValueError(error_msg)
            
            # Log warnings if any
            if validation_result["warnings"] and self.io:
                for warning in validation_result["warnings"]:
                    self.io.tool_warning(f"Handover state warning: {warning}")
            
            # Save current state
            with open(self.handover_state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            # Append to history
            history_entry = {
                "timestamp": state.timestamp,
                "session_id": state.session_id,
                "reason": state.handover_reason,
                "trigger": state.handover_trigger,
                "validation_checksum": state.validation_checksum,
                "validation_status": "valid" if validation_result["is_valid"] else "invalid",
                "warnings_count": len(validation_result["warnings"])
            }
            
            with open(self.handover_history_file, 'a') as f:
                f.write(json.dumps(history_entry) + '\n')
            
            if self.io:
                self.io.tool_output(f"Handover state saved and validated: {self.handover_state_file}")
                if validation_result["warnings"]:
                    self.io.tool_output(f"Saved with {len(validation_result['warnings'])} warnings")
            
            return self.handover_state_file
            
        except Exception as e:
            if self.io:
                self.io.tool_error(f"Failed to save handover state: {e}")
            raise
    
    def load_handover_state(self, state_file: Optional[str] = None) -> Optional[HandoverState]:
        """Load handover state from persistent storage with validation"""
        
        state_file = state_file or self.handover_state_file
        
        try:
            if not os.path.exists(state_file):
                if self.io:
                    self.io.tool_output(f"No handover state file found: {state_file}")
                return None
            
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            # Schema validation
            validation_result = self.validator.validate_state(state_data)
            
            if not validation_result["is_valid"]:
                if self.io:
                    self.io.tool_error(f"Handover state schema validation failed: {validation_result['errors']}")
                return None
            
            # Log warnings
            if validation_result["warnings"] and self.io:
                for warning in validation_result["warnings"]:
                    self.io.tool_warning(f"Handover state warning: {warning}")
            
            # Create state object
            state = HandoverState(**state_data)
            
            # Validate checksum
            if not self._validate_state_checksum(state):
                if self.io:
                    self.io.tool_error("Handover state validation failed - checksum mismatch")
                return None
            
            if self.io:
                self.io.tool_output(f"Handover state loaded and validated: {state_file}")
                if validation_result["warnings"]:
                    self.io.tool_output(f"Loaded with {len(validation_result['warnings'])} warnings")
            
            return state
            
        except Exception as e:
            if self.io:
                self.io.tool_error(f"Failed to load handover state: {e}")
            return None
    
    def validate_handover_readiness(self, state: HandoverState) -> Dict[str, Any]:
        """Validate that handover state is complete and ready for transfer"""
        
        # Use schema validator for comprehensive validation
        state_data = asdict(state)
        schema_validation = self.validator.validate_state(state_data)
        
        validation_results = {
            "is_valid": schema_validation["is_valid"],
            "warnings": schema_validation["warnings"].copy(),
            "errors": schema_validation["errors"].copy(),
            "completeness_score": 0.0,
            "readiness_checks": {}
        }
        
        # Additional readiness-specific checks
        readiness_checks = self._perform_readiness_checks(state)
        validation_results["readiness_checks"] = readiness_checks
        
        # Merge readiness warnings and errors
        validation_results["warnings"].extend(readiness_checks.get("warnings", []))
        validation_results["errors"].extend(readiness_checks.get("errors", []))
        
        # Update overall validity
        if readiness_checks.get("errors"):
            validation_results["is_valid"] = False
        
        # Calculate completeness score
        total_fields = len(asdict(state))
        non_empty_fields = sum(1 for v in asdict(state).values() if v)
        validation_results["completeness_score"] = non_empty_fields / total_fields
        
        # Add readiness score
        validation_results["readiness_score"] = self._calculate_readiness_score(state, readiness_checks)
        
        return validation_results
    
    def _perform_readiness_checks(self, state: HandoverState) -> Dict[str, Any]:
        """Perform handover readiness-specific validation checks"""
        
        checks = {
            "warnings": [],
            "errors": [],
            "file_accessibility": {"accessible": 0, "total": 0, "missing": []},
            "git_consistency": {"status": "unknown"},
            "model_availability": {"status": "unknown"},
            "session_coherence": {"status": "unknown"}
        }
        
        # File accessibility check
        all_files = state.active_files + state.read_only_files
        checks["file_accessibility"]["total"] = len(all_files)
        
        for file_path in all_files:
            if os.path.exists(file_path):
                checks["file_accessibility"]["accessible"] += 1
            else:
                checks["file_accessibility"]["missing"].append(file_path)
        
        if checks["file_accessibility"]["missing"]:
            checks["warnings"].append(f"Missing files: {len(checks['file_accessibility']['missing'])} files not accessible")
        
        # Git consistency check
        try:
            current_git_info = self._get_git_info()
            if (current_git_info.get("branch") != state.git_branch or 
                current_git_info.get("commit") != state.git_commit):
                checks["warnings"].append("Git state has changed since handover capture")
                checks["git_consistency"]["status"] = "changed"
            else:
                checks["git_consistency"]["status"] = "consistent"
        except Exception:
            checks["warnings"].append("Unable to verify git consistency")
            checks["git_consistency"]["status"] = "error"
        
        # Model configuration validation
        if not state.main_model.get("name"):
            checks["errors"].append("Main model configuration is incomplete")
            checks["model_availability"]["status"] = "error"
        else:
            checks["model_availability"]["status"] = "configured"
        
        # Session coherence check
        if state.session_duration < 0:
            checks["errors"].append("Invalid session duration")
        
        if not state.session_id or len(state.session_id) != 12:
            checks["errors"].append("Invalid session ID format")
        
        if state.current_coder_type == "unknown" or state.edit_format == "unknown":
            checks["warnings"].append("Coder configuration may be incomplete")
            checks["session_coherence"]["status"] = "incomplete"
        else:
            checks["session_coherence"]["status"] = "complete"
        
        return checks
    
    def _calculate_readiness_score(self, state: HandoverState, checks: Dict[str, Any]) -> float:
        """Calculate overall readiness score (0.0 to 1.0)"""
        
        score = 1.0
        
        # Deduct for errors (critical issues)
        error_count = len(checks.get("errors", []))
        score -= (error_count * 0.2)  # Each error reduces score by 20%
        
        # Deduct for warnings (minor issues)
        warning_count = len(checks.get("warnings", []))
        score -= (warning_count * 0.05)  # Each warning reduces score by 5%
        
        # File accessibility factor
        file_check = checks.get("file_accessibility", {})
        if file_check["total"] > 0:
            file_score = file_check["accessible"] / file_check["total"]
            score *= (0.7 + 0.3 * file_score)  # Files contribute 30% to score
        
        # Git consistency factor
        git_status = checks.get("git_consistency", {}).get("status", "unknown")
        if git_status == "changed":
            score *= 0.9  # 10% penalty for git changes
        elif git_status == "error":
            score *= 0.8  # 20% penalty for git errors
        
        # Model availability factor
        model_status = checks.get("model_availability", {}).get("status", "unknown")
        if model_status == "error":
            score *= 0.5  # 50% penalty for model errors
        
        # Session coherence factor
        session_status = checks.get("session_coherence", {}).get("status", "unknown")
        if session_status == "incomplete":
            score *= 0.9  # 10% penalty for incomplete session info
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def generate_handover_document(self, state: HandoverState) -> str:
        """Generate comprehensive handover document"""
        
        doc_template = f"""# LLM Session Handover
        
**Session ID:** {state.session_id}
**Timestamp:** {state.timestamp}
**Handover Reason:** {state.handover_reason}
**Trigger:** {state.handover_trigger}

## Project Context
**Working Directory:** `{state.working_directory}`
**Git Branch:** `{state.git_branch}`
**Git Commit:** `{state.git_commit}`
**Atlas Version:** `{state.atlas_version}`

## Model Configuration
**Main Model:** {state.main_model.get('name', 'unknown')}
**Editor Model:** {state.editor_model.get('name', 'none') if state.editor_model else 'none'}
**Weak Model:** {state.weak_model.get('name', 'none') if state.weak_model else 'none'}
**Current Coder Type:** {state.current_coder_type}
**Edit Format:** {state.edit_format}

## File Context
**Active Files ({len(state.active_files)}):**
{self._format_file_list(state.active_files)}

**Read-Only Files ({len(state.read_only_files)}):**
{self._format_file_list(state.read_only_files)}

## Session Summary
{state.chat_history_summary}

## Performance Metrics
**Session Duration:** {state.session_duration:.1f} seconds
**Token Usage:** {state.token_usage}
**Success Metrics:** {state.success_metrics}

## Pending Operations
{self._format_pending_operations(state.pending_operations)}

## Next Steps
Based on the current session state and handover reason, the following actions are recommended:

1. Validate model configuration and connectivity
2. Restore file context and verify accessibility
3. Review conversation history and user preferences
4. Continue with pending operations if applicable

**Validation Checksum:** `{state.validation_checksum}`
"""
        
        return doc_template.strip()
    
    def _generate_session_id(self) -> str:
        """Generate unique session identifier"""
        timestamp = str(time.time())
        content = f"{timestamp}-{os.getcwd()}-{os.getpid()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_git_info(self) -> Dict[str, str]:
        """Get current git repository information"""
        try:
            repo = git.Repo(search_parent_directories=True)
            return {
                "branch": repo.active_branch.name,
                "commit": repo.head.commit.hexsha[:8],
                "is_dirty": repo.is_dirty()
            }
        except Exception:
            return {"branch": "unknown", "commit": "unknown", "is_dirty": False}
    
    def _get_atlas_version(self) -> str:
        """Get atlas-code version"""
        try:
            from . import __version__
            return __version__
        except ImportError:
            return "unknown"
    
    def _capture_model_configuration(self, coder) -> Dict[str, Any]:
        """Capture current model configuration"""
        if not coder:
            return {"main": {}, "editor": None, "weak": None, "settings": {}}
        
        return {
            "main": {
                "name": getattr(coder.main_model, 'name', 'unknown'),
                "max_tokens": getattr(coder.main_model, 'max_tokens', 0),
                "info": getattr(coder.main_model, 'info', {})
            },
            "editor": {
                "name": getattr(coder.editor_model, 'name', 'unknown'),
                "max_tokens": getattr(coder.editor_model, 'max_tokens', 0)
            } if getattr(coder, 'editor_model', None) else None,
            "weak": {
                "name": getattr(coder.weak_model, 'name', 'unknown'),
                "max_tokens": getattr(coder.weak_model, 'max_tokens', 0)
            } if getattr(coder, 'weak_model', None) else None,
            "settings": getattr(coder, 'model_settings', {})
        }
    
    def _capture_file_context(self, coder) -> Dict[str, Any]:
        """Capture current file context"""
        if not coder:
            return {"active": [], "read_only": [], "repo_map": {}, "git_status": {}}
        
        return {
            "active": list(getattr(coder, 'abs_fnames', [])),
            "read_only": list(getattr(coder, 'abs_read_only_fnames', [])),
            "repo_map": getattr(coder, 'repo_map', {}),
            "git_status": self._get_git_status()
        }
    
    def _capture_session_context(self, coder) -> Dict[str, Any]:
        """Capture session context and preferences"""
        context = {
            "history_summary": "",
            "conversation": {},
            "preferences": {},
            "env_vars": {},
            "coder_type": "unknown",
            "edit_format": "unknown",
            "pending_ops": [],
            "analytics": {}
        }
        
        if coder:
            context.update({
                "coder_type": type(coder).__name__,
                "edit_format": getattr(coder, 'edit_format', 'unknown'),
                "conversation": {
                    "total_cost": getattr(coder, 'total_cost', 0),
                    "num_exhausted_context_windows": getattr(coder, 'num_exhausted_context_windows', 0)
                }
            })
            
            # Capture chat history summary
            if hasattr(coder, 'chat_completion_call_hashes'):
                try:
                    chat_summary = ChatSummary(
                        getattr(coder, 'chat_completion_call_hashes', []),
                        max_tokens=1000
                    )
                    context["history_summary"] = chat_summary.summarize()
                except Exception:
                    context["history_summary"] = "Failed to generate chat summary"
        
        # Capture environment variables (non-sensitive)
        safe_env_vars = {}
        for key, value in os.environ.items():
            if key.isupper() and key.replace('_', '').isalnum():
                if not any(sensitive in key.lower() for sensitive in ['key', 'secret', 'token', 'password']):
                    safe_env_vars[key] = value
        context["env_vars"] = safe_env_vars
        
        return context
    
    def _capture_performance_metrics(self) -> Dict[str, Any]:
        """Capture session performance metrics"""
        return {
            "duration": time.time() - self.session_start_time,
            "tokens": {},  # Will be populated from model usage
            "success": {}  # Will be populated from analytics
        }
    
    def _get_git_status(self) -> Dict[str, Any]:
        """Get detailed git status"""
        try:
            repo = git.Repo(search_parent_directories=True)
            return {
                "untracked": [item.a_path for item in repo.index.diff(None)],
                "modified": [item.a_path for item in repo.index.diff("HEAD")],
                "staged": [item.a_path for item in repo.index.diff("HEAD", cached=True)]
            }
        except Exception:
            return {"untracked": [], "modified": [], "staged": []}
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA256 hash of a file"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(4096)  # Read in 4KB chunks
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None

    def _calculate_state_checksum(self, state: HandoverState) -> str:
        """Calculate validation checksum for state, including file hashes"""
        # Create copy without checksum field
        state_dict = asdict(state)
        state_dict.pop('validation_checksum', None)

        # Use file hashes from the state object directly
        state_dict["file_hashes"] = state.file_hashes
        
        state_json = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()[:16]
    
    def _validate_state_checksum(self, state: HandoverState) -> bool:
        """Validate state checksum and file hashes"""
        # Recalculate checksum based on current file contents
        expected_checksum = self._calculate_state_checksum(state)
        
        # Compare with stored checksum
        if expected_checksum != state.validation_checksum:
            if self.io:
                self.io.tool_error("Handover state validation failed - checksum mismatch.")
                self.io.tool_error(f"Expected: {expected_checksum}, Got: {state.validation_checksum}")
            return False

        # Verify individual file hashes against current file system state
        for fpath, stored_hash in state.file_hashes.items():
            current_hash = self._calculate_file_hash(fpath)
            if stored_hash != current_hash:
                if self.io:
                    self.io.tool_error(f"File integrity check failed for {fpath}. Hash mismatch.")
                    self.io.tool_error(f"Stored: {stored_hash}, Current: {current_hash}")
                return False
        
        return True
    
    def _format_file_list(self, files: List[str]) -> str:
        """Format file list for documentation"""
        if not files:
            return "  (none)"
        return "\n".join(f"  - {file}" for file in files)
    
    def _format_pending_operations(self, operations: List[Dict[str, Any]]) -> str:
        """Format pending operations for documentation"""
        if not operations:
            return "No pending operations."
        
        formatted = []
        for i, op in enumerate(operations, 1):
            formatted.append(f"{i}. {op.get('description', 'Unknown operation')}")
        
        return "\n".join(formatted)
    
    def trigger_github_integration(self, 
                                 handover_state_file: str,
                                 production_report: Dict[str, Any] = None,
                                 reason: str = "handover",
                                 auto_push: bool = True) -> Dict[str, Any]:
        """Trigger GitHub integration for handover process"""
        
        try:
            from .github_integration import GitHubHandoverIntegration
            
            github = GitHubHandoverIntegration(io=self.io, project_root=os.getcwd())
            
            # Check if this is a GitHub repository
            repo_info = github.get_github_repository_info()
            
            if not repo_info["has_remote"]:
                if self.io:
                    self.io.tool_warning("No remote repository configured - skipping GitHub integration")
                return {"success": False, "reason": "no_remote"}
            
            if not repo_info["is_github"]:
                if self.io:
                    self.io.tool_output(f"Non-GitHub remote detected: {repo_info['remote_url']}")
                    self.io.tool_output("Proceeding with git integration only")
            
            # Process handover with GitHub integration
            result = github.process_handover_with_github(
                handover_state_file=handover_state_file,
                production_report=production_report,
                reason=reason,
                auto_push=auto_push,
                create_branch=True  # Always create handover branch
            )
            
            if result.success:
                if self.io:
                    self.io.tool_output("🎉 GitHub integration completed successfully")
                    self.io.tool_output(f"📁 Artifacts uploaded: {len(result.artifacts_uploaded)}")
                    
                    if result.remote_urls:
                        self.io.tool_output("🔗 Remote URLs:")
                        for url in result.remote_urls:
                            self.io.tool_output(f"   {url}")
                
                # Set up GitHub Actions workflow if this is a GitHub repo
                if repo_info["is_github"] and repo_info["has_github_directory"]:
                    github.setup_github_actions_workflow()
                
                return {
                    "success": True,
                    "artifacts": len(result.artifacts_uploaded),
                    "remote_urls": result.remote_urls,
                    "operations": result.operations_performed
                }
            else:
                if self.io:
                    self.io.tool_error("GitHub integration failed")
                    for error in result.errors:
                        self.io.tool_error(f"  - {error}")
                
                return {
                    "success": False,
                    "errors": result.errors,
                    "warnings": result.warnings
                }
                
        except ImportError:
            if self.io:
                self.io.tool_warning("GitHub integration not available")
            return {"success": False, "reason": "import_error"}
        except Exception as e:
            if self.io:
                self.io.tool_error(f"GitHub integration error: {e}")
            return {"success": False, "reason": str(e)}

    def perform_production_validation(self, coder):
        """Perform production readiness validation and return results."""
        try:
            from .production_validator import ProductionReadinessValidator
            validator = ProductionReadinessValidator(io=self.io, root_path=coder.root)
            return validator.validate_project(coder=coder)
        except ImportError:
            if self.io:
                self.io.tool_warning("Production validation not available. Install aider-chat[production] to enable.")
            return None
        except Exception as e:
            if self.io:
                self.io.tool_error(f"Error during production validation: {e}")
            return None