import json
import jsonschema
from jsonschema import validate, ValidationError
from typing import Dict, Any, List, Optional
from datetime import datetime


HANDOVER_STATE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Atlas Handover State",
    "description": "Complete session state for LLM handover in Atlas Code",
    "type": "object",
    "required": [
        "session_id",
        "timestamp", 
        "atlas_version",
        "git_branch",
        "git_commit",
        "working_directory",
        "main_model",
        "current_coder_type",
        "edit_format",
        "handover_reason",
        "handover_trigger",
        "validation_checksum"
    ],
    "properties": {
        "session_id": {
            "type": "string",
            "pattern": "^[a-f0-9]{12}$",
            "description": "Unique 12-character hex session identifier"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of handover creation"
        },
        "atlas_version": {
            "type": "string",
            "description": "Atlas code version string"
        },
        "git_branch": {
            "type": "string",
            "description": "Current git branch name"
        },
        "git_commit": {
            "type": "string",
            "description": "Current git commit hash"
        },
        "working_directory": {
            "type": "string",
            "description": "Absolute path to working directory"
        },
        "main_model": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Model name identifier"
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Maximum token limit for model"
                },
                "info": {
                    "type": "object",
                    "description": "Additional model metadata"
                }
            },
            "additionalProperties": True
        },
        "editor_model": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "max_tokens": {"type": "integer", "minimum": 0}
                    },
                    "additionalProperties": True
                }
            ],
            "description": "Editor model configuration or null"
        },
        "weak_model": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object", 
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "max_tokens": {"type": "integer", "minimum": 0}
                    },
                    "additionalProperties": True
                }
            ],
            "description": "Weak model configuration or null"
        },
        "model_settings": {
            "type": "object",
            "description": "Model-specific settings and configurations"
        },
        "active_files": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "Absolute path to active file"
            },
            "uniqueItems": True,
            "description": "List of currently active files in session"
        },
        "read_only_files": {
            "type": "array",
            "items": {
                "type": "string", 
                "description": "Absolute path to read-only file"
            },
            "uniqueItems": True,
            "description": "List of read-only files in session"
        },
        "repository_map": {
            "type": "object",
            "description": "Repository file mapping and metadata"
        },
        "git_status": {
            "type": "object",
            "properties": {
                "untracked": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of untracked files"
                },
                "modified": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of modified files"
                },
                "staged": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of staged files"
                }
            },
            "additionalProperties": True,
            "description": "Current git repository status"
        },
        "chat_history_summary": {
            "type": "string",
            "description": "Summarized conversation history"
        },
        "conversation_context": {
            "type": "object",
            "properties": {
                "total_cost": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Total session cost in USD"
                },
                "num_exhausted_context_windows": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Number of times context window was exhausted"
                }
            },
            "additionalProperties": True,
            "description": "Conversation context and statistics"
        },
        "user_preferences": {
            "type": "object",
            "description": "User preferences and settings"
        },
        "environment_variables": {
            "type": "object",
            "patternProperties": {
                "^[A-Z_][A-Z0-9_]*$": {
                    "type": "string"
                }
            },
            "additionalProperties": False,
            "description": "Safe environment variables (no secrets)"
        },
        "current_coder_type": {
            "type": "string",
            "enum": [
                "BaseCoder",
                "EditBlockCoder", 
                "WholeFileCoder",
                "ArchitectCoder",
                "AskCoder",
                "unknown"
            ],
            "description": "Current coder class type"
        },
        "edit_format": {
            "type": "string",
            "enum": [
                "diff",
                "whole", 
                "edit-block",
                "architect",
                "ask",
                "unknown"
            ],
            "description": "Current edit format preference"
        },
        "pending_operations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["description"],
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Human-readable operation description"
                    },
                    "type": {
                        "type": "string",
                        "description": "Operation type identifier"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Operation parameters"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Operation priority level"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Operation creation timestamp"
                    }
                },
                "additionalProperties": True
            },
            "description": "List of pending operations to complete"
        },
        "analytics_data": {
            "type": "object",
            "description": "Analytics and telemetry data"
        },
        "session_duration": {
            "type": "number",
            "minimum": 0,
            "description": "Session duration in seconds"
        },
        "token_usage": {
            "type": "object",
            "properties": {
                "input_tokens": {
                    "type": "integer",
                    "minimum": 0
                },
                "output_tokens": {
                    "type": "integer", 
                    "minimum": 0
                },
                "total_tokens": {
                    "type": "integer",
                    "minimum": 0
                }
            },
            "additionalProperties": True,
            "description": "Token usage statistics"
        },
        "success_metrics": {
            "type": "object",
            "properties": {
                "successful_operations": {
                    "type": "integer",
                    "minimum": 0
                },
                "failed_operations": {
                    "type": "integer",
                    "minimum": 0
                },
                "success_rate": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                }
            },
            "additionalProperties": True,
            "description": "Session success metrics"
        },
        "handover_reason": {
            "type": "string",
            "enum": [
                "manual",
                "session_completion", 
                "context_window_exhausted",
                "model_switch",
                "performance_degradation",
                "error_recovery",
                "user_request",
                "automated",
                "timeout",
                "other"
            ],
            "description": "Reason for handover initiation"
        },
        "handover_trigger": {
            "type": "string",
            "enum": [
                "user_request",
                "automated",
                "error_condition",
                "performance_threshold",
                "context_limit",
                "model_switch",
                "scheduled",
                "manual",
                "other"
            ],
            "description": "What triggered the handover"
        },
        "validation_checksum": {
            "type": "string",
            "pattern": "^[a-f0-9]{16}$",
            "description": "16-character hex validation checksum"
        }
    },
    "additionalProperties": False
}


class HandoverStateValidator:
    """Validates handover state against schema"""
    
    def __init__(self):
        self.schema = HANDOVER_STATE_SCHEMA
        
    def validate_state(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate handover state data against schema
        
        Returns:
            Dict with validation results including is_valid, errors, warnings
        """
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "schema_version": "1.0"
        }
        
        try:
            # Basic schema validation
            validate(instance=state_data, schema=self.schema)
            
            # Additional custom validations
            custom_validation = self._perform_custom_validations(state_data)
            validation_result["warnings"].extend(custom_validation.get("warnings", []))
            
            if custom_validation.get("errors"):
                validation_result["errors"].extend(custom_validation["errors"])
                validation_result["is_valid"] = False
                
        except ValidationError as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Schema validation failed: {e.message}")
            
            # Add path information for nested errors
            if e.absolute_path:
                path_str = ".".join(str(p) for p in e.absolute_path)
                validation_result["errors"].append(f"Error location: {path_str}")
                
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _perform_custom_validations(self, state_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Perform additional custom validations beyond schema"""
        
        custom_result = {
            "errors": [],
            "warnings": []
        }
        
        # Validate timestamp format
        try:
            timestamp = state_data.get("timestamp")
            if timestamp:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            custom_result["errors"].append("Invalid timestamp format")
        
        # Validate file paths existence (warnings only)
        active_files = state_data.get("active_files", [])
        read_only_files = state_data.get("read_only_files", [])
        
        for file_path in active_files + read_only_files:
            import os
            if not os.path.exists(file_path):
                custom_result["warnings"].append(f"File not accessible: {file_path}")
        
        # Validate git information consistency
        git_branch = state_data.get("git_branch")
        git_commit = state_data.get("git_commit")
        
        if git_branch == "unknown" or git_commit == "unknown":
            custom_result["warnings"].append("Git information not available")
        
        # Validate model configuration consistency
        main_model = state_data.get("main_model", {})
        if not main_model.get("name"):
            custom_result["errors"].append("Main model name is required")
        
        # Validate session metrics consistency
        session_duration = state_data.get("session_duration", 0)
        if session_duration < 0:
            custom_result["errors"].append("Session duration cannot be negative")
        
        token_usage = state_data.get("token_usage", {})
        if token_usage:
            input_tokens = token_usage.get("input_tokens", 0)
            output_tokens = token_usage.get("output_tokens", 0)
            total_tokens = token_usage.get("total_tokens", 0)
            
            if total_tokens > 0 and total_tokens != (input_tokens + output_tokens):
                custom_result["warnings"].append("Token usage totals may be inconsistent")
        
        return custom_result
    
    def validate_state_file(self, file_path: str) -> Dict[str, Any]:
        """Validate handover state from file"""
        
        try:
            with open(file_path, 'r') as f:
                state_data = json.load(f)
            
            return self.validate_state(state_data)
            
        except FileNotFoundError:
            return {
                "is_valid": False,
                "errors": [f"State file not found: {file_path}"],
                "warnings": [],
                "schema_version": "1.0"
            }
        except json.JSONDecodeError as e:
            return {
                "is_valid": False,
                "errors": [f"Invalid JSON in state file: {e}"],
                "warnings": [],
                "schema_version": "1.0"
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Error reading state file: {e}"],
                "warnings": [],
                "schema_version": "1.0"
            }
    
    def get_schema_documentation(self) -> str:
        """Generate human-readable schema documentation"""
        
        doc = """# Atlas Handover State Schema Documentation

## Overview
The handover state schema defines the complete structure for capturing and validating LLM session state in Atlas Code.

## Required Fields

### Core Session Metadata
- `session_id`: 12-character hex identifier (pattern: ^[a-f0-9]{12}$)
- `timestamp`: ISO 8601 date-time format
- `atlas_version`: Atlas code version string
- `git_branch`: Current git branch name
- `git_commit`: Current git commit hash
- `working_directory`: Absolute path to working directory

### Model Configuration
- `main_model`: Object with required 'name' field, optional 'max_tokens' and 'info'
- `current_coder_type`: Enum of valid coder types (BaseCoder, EditBlockCoder, etc.)
- `edit_format`: Enum of valid edit formats (diff, whole, edit-block, etc.)

### Handover Metadata
- `handover_reason`: Enum of handover reasons (manual, session_completion, etc.)
- `handover_trigger`: Enum of trigger types (user_request, automated, etc.)
- `validation_checksum`: 16-character hex validation hash

## Optional Fields

### Model Configuration (Optional)
- `editor_model`: Editor model config or null
- `weak_model`: Weak model config or null
- `model_settings`: Model-specific settings object

### File Context
- `active_files`: Array of absolute file paths (unique items)
- `read_only_files`: Array of absolute read-only file paths (unique items)
- `repository_map`: Repository metadata object
- `git_status`: Git status with untracked, modified, staged arrays

### Session Context
- `chat_history_summary`: String summary of conversation
- `conversation_context`: Object with total_cost, num_exhausted_context_windows
- `user_preferences`: User settings object
- `environment_variables`: Safe environment variables (uppercase pattern)

### Operations and Analytics
- `pending_operations`: Array of operation objects with description, type, parameters
- `analytics_data`: Analytics and telemetry object
- `session_duration`: Non-negative number (seconds)
- `token_usage`: Object with input_tokens, output_tokens, total_tokens
- `success_metrics`: Object with operation counts and success rates

## Validation Rules

### Schema Validation
- All required fields must be present
- Field types must match schema definitions
- Enum values must be from allowed lists
- String patterns must match (session_id, checksum, env vars)

### Custom Validation
- File paths should be accessible (warning if not)
- Timestamps must be valid ISO 8601 format
- Token usage totals should be consistent
- Session duration must be non-negative
- Git information completeness check

## Usage Example

```python
from aider.handover_schema import HandoverStateValidator

validator = HandoverStateValidator()
result = validator.validate_state_file('.aider.handover.state.json')

if result['is_valid']:
    print("State is valid")
else:
    print("Validation errors:", result['errors'])
    print("Warnings:", result['warnings'])
```
"""
        
        return doc.strip()


def create_minimal_valid_state() -> Dict[str, Any]:
    """Create a minimal valid handover state for testing"""
    
    return {
        "session_id": "abc123def456",
        "timestamp": datetime.now().isoformat(),
        "atlas_version": "1.0.0",
        "git_branch": "main",
        "git_commit": "abc12345",
        "working_directory": "/tmp/test",
        "main_model": {"name": "test-model"},
        "editor_model": None,
        "weak_model": None,
        "model_settings": {},
        "active_files": [],
        "read_only_files": [],
        "repository_map": {},
        "git_status": {"untracked": [], "modified": [], "staged": []},
        "chat_history_summary": "",
        "conversation_context": {},
        "user_preferences": {},
        "environment_variables": {},
        "current_coder_type": "BaseCoder",
        "edit_format": "diff",
        "pending_operations": [],
        "analytics_data": {},
        "session_duration": 0.0,
        "token_usage": {},
        "success_metrics": {},
        "handover_reason": "manual",
        "handover_trigger": "user_request",
        "validation_checksum": "1234567890abcdef"
    }