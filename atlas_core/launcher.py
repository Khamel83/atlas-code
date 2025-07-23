"""
Aider Launcher for Atlas Code V2

Launches vanilla Aider with intelligent enhancements from:
- Smart model routing (4-tier system)
- Agent OS development standards integration
- Simple budget tracking and warnings
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from .router import ModelRouter, ModelTier
from .budget import BudgetManager

# Import the new intelligent router
try:
    from model_router import IntelligentModelRouter, is_low_confidence
    INTELLIGENT_ROUTING_AVAILABLE = True
except ImportError:
    INTELLIGENT_ROUTING_AVAILABLE = False
    logging.warning("Intelligent routing not available, falling back to pattern-based routing")

logger = logging.getLogger(__name__)


class AiderLauncher:
    """
    Launches vanilla Aider with Atlas Code enhancements.
    
    This class acts as a wrapper that:
    1. Analyzes the user's request
    2. Routes to optimal model via smart routing
    3. Enhances prompts with Agent OS standards
    4. Tracks budget and provides warnings
    5. Launches vanilla Aider with computed parameters
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the launcher.
        
        Args:
            project_root: Root directory of the project (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        # Initialize both routing systems
        self.router = ModelRouter()  # Legacy pattern-based router
        if INTELLIGENT_ROUTING_AVAILABLE:
            self.intelligent_router = IntelligentModelRouter()
        else:
            self.intelligent_router = None
        self.budget = BudgetManager()
        self.agent_os_dir = self.project_root / "agent_os"
        
        # Ensure Aider is available
        self._check_aider_installation()
    
    def _check_aider_installation(self):
        """Check if Aider is installed and accessible."""
        try:
            result = subprocess.run(['aider', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Found Aider: {result.stdout.strip()}")
            else:
                raise FileNotFoundError("Aider not responding")
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            logger.error("Aider not found or not working")
            print("❌ Aider not found!")
            print("Please install Aider first:")
            print("  pip install aider-chat")
            sys.exit(1)
    
    def load_agent_os_context(self) -> Dict[str, Any]:
        """
        Load development context from Agent OS if available.
        
        Returns:
            Dictionary with Agent OS context and standards
        """
        context = {
            'standards': [],
            'instructions': [],
            'commands': [],
            'project_info': {}
        }
        
        if not self.agent_os_dir.exists():
            logger.info("No Agent OS directory found")
            return context
        
        # Load coding standards
        standards_dir = self.agent_os_dir / "standards"
        if standards_dir.exists():
            for std_file in standards_dir.glob("*.md"):
                try:
                    content = std_file.read_text(encoding='utf-8')
                    context['standards'].append({
                        'name': std_file.stem,
                        'content': content
                    })
                except Exception as e:
                    logger.warning(f"Failed to load standard {std_file}: {e}")
        
        # Load development instructions
        instructions_dir = self.agent_os_dir / "instructions"
        if instructions_dir.exists():
            for inst_file in instructions_dir.glob("*.md"):
                try:
                    content = inst_file.read_text(encoding='utf-8')
                    context['instructions'].append({
                        'name': inst_file.stem,
                        'content': content
                    })
                except Exception as e:
                    logger.warning(f"Failed to load instruction {inst_file}: {e}")
        
        # Load project info if available
        project_info_file = self.agent_os_dir / "project_info.json"
        if project_info_file.exists():
            try:
                context['project_info'] = json.loads(project_info_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load project info: {e}")
        
        logger.info(f"Loaded Agent OS context: {len(context['standards'])} standards, "
                   f"{len(context['instructions'])} instructions")
        
        return context
    
    def enhance_prompt(self, user_prompt: str, context: Dict[str, Any]) -> str:
        """
        Enhance user prompt with relevant Agent OS standards and context.
        
        Args:
            user_prompt: Original user prompt
            context: Agent OS context from load_agent_os_context()
            
        Returns:
            Enhanced prompt with relevant standards
        """
        if not context.get('standards') and not context.get('instructions'):
            return user_prompt
        
        enhanced_parts = [user_prompt]
        
        # Add relevant coding standards
        if context.get('standards'):
            enhanced_parts.append("\n## Development Standards")
            enhanced_parts.append("Please follow these coding standards:")
            
            for standard in context['standards'][:3]:  # Limit to first 3 standards
                enhanced_parts.append(f"\n### {standard['name'].title()}")
                # Add first few lines of the standard
                lines = standard['content'].split('\n')[:5]
                enhanced_parts.append('\n'.join(lines))
        
        # Add relevant instructions
        if context.get('instructions'):
            # Look for instructions relevant to the task
            relevant_instructions = []
            user_lower = user_prompt.lower()
            
            for instruction in context['instructions']:
                inst_name = instruction['name'].lower()
                # Simple relevance matching
                if any(keyword in inst_name for keyword in 
                      ['test', 'deploy', 'auth', 'api', 'database', 'security']):
                    if any(keyword in user_lower for keyword in 
                          ['test', 'deploy', 'auth', 'api', 'database', 'security']):
                        relevant_instructions.append(instruction)
            
            if relevant_instructions:
                enhanced_parts.append("\n## Relevant Development Instructions")
                for instruction in relevant_instructions[:2]:  # Limit to 2 instructions
                    enhanced_parts.append(f"\n### {instruction['name'].title()}")
                    lines = instruction['content'].split('\n')[:5]
                    enhanced_parts.append('\n'.join(lines))
        
        enhanced_prompt = '\n'.join(enhanced_parts)
        
        # Ensure the enhanced prompt isn't too long
        if len(enhanced_prompt) > len(user_prompt) * 3:
            logger.warning("Enhanced prompt very long, using original")
            return user_prompt
        
        return enhanced_prompt
    
    def check_budget_and_warn(self, estimated_cost: float) -> bool:
        """
        Check budget status and warn user if needed.
        
        Args:
            estimated_cost: Estimated cost for the request
            
        Returns:
            True if should proceed, False if user wants to cancel
        """
        status = self.budget.check_budget_status()
        
        if status['warning_level'] == 'red':
            print(f"🚨 Budget Alert: You've used {status['percentage_used']:.1f}% "
                  f"of your ${status['daily_limit']} daily limit")
            print(f"💰 Spent today: ${status['today_spent']:.2f}")
            print(f"💸 This request estimated: ${estimated_cost:.3f}")
            
            if estimated_cost > status['remaining']:
                print("⚠️  This request would exceed your daily budget!")
                response = input("Continue anyway? (y/N): ").strip().lower()
                return response in ['y', 'yes']
        
        elif status['warning_level'] == 'yellow':
            print(f"⚠️  Budget Warning: You've used {status['percentage_used']:.1f}% "
                  f"of your ${status['daily_limit']} daily limit")
            print(f"💰 Spent today: ${status['today_spent']:.2f}")
        
        return True
    
    def launch_aider(self, user_prompt: str, files: List[str] = None, 
                    force_tier: Optional[ModelTier] = None,
                    extra_args: List[str] = None,
                    budget_check: bool = True) -> int:
        """
        Main launch function that coordinates all Atlas Code enhancements.
        
        Args:
            user_prompt: User's task description
            files: List of files to include
            force_tier: Force a specific model tier
            extra_args: Additional arguments to pass to Aider
            budget_check: Whether to check budget before proceeding
            
        Returns:
            Exit code from Aider process
        """
        logger.info("Atlas Code V2 launcher starting")
        
        # Load Agent OS context
        context = self.load_agent_os_context()
        
        # Enhance the prompt with Agent OS standards
        enhanced_prompt = self.enhance_prompt(user_prompt, context)
        
        # Route to optimal model using intelligent or legacy routing
        if self.intelligent_router and not force_tier:
            # Use intelligent AI-powered routing
            budget_remaining = self.budget.check_budget_status().get('remaining', float('inf'))
            if budget_remaining is None:
                budget_remaining = float('inf')
            
            routing_info = self.intelligent_router.route_request(
                enhanced_prompt, 
                budget_remaining,
                allow_compression=True
            )
            
            model_name = routing_info['model']
            selected_tier = routing_info['tier']
            cost_per_1k = self.intelligent_router.model_costs.get(model_name, 1.0)
            routing_reason = routing_info['reason']
            
            # Log intelligent routing decision
            print(f"🧠 AI Classification: {selected_tier} tier")
            print(f"🎯 Selected Model: {model_name}")
            print(f"💡 Reason: {routing_reason}")
            if routing_info['prompt_compressed']:
                print(f"📝 Prompt compressed: {routing_info['original_prompt_length']} → {routing_info['final_prompt_length']} chars")
            
        else:
            # Use legacy pattern-based routing (fallback or forced tier)
            project_context = {
                'file_count': len(files) if files else 0,
                'is_new_project': not (self.project_root / ".git").exists(),
                **context.get('project_info', {})
            }
            
            model_name, selected_tier_obj, cost_per_1k = self.router.route_request(
                enhanced_prompt, 
                project_context, 
                force_tier
            )
            selected_tier = selected_tier_obj.value
            routing_reason = "pattern-based routing" + (f" (forced {force_tier.value} tier)" if force_tier else "")
        
        # Estimate cost and check budget
        estimated_tokens = len(enhanced_prompt.split()) * 1.3  # Rough estimation
        estimated_cost = self.budget.estimate_cost(model_name, int(estimated_tokens))
        
        if budget_check and not self.check_budget_and_warn(estimated_cost):
            print("🛑 Request cancelled by user")
            return 1
        
        # Build Aider command
        aider_cmd = [
            'aider',
            '--model', model_name,
            '--message', enhanced_prompt
        ]
        
        # Add files if specified
        if files:
            aider_cmd.extend(files)
        
        # Add extra arguments
        if extra_args:
            aider_cmd.extend(extra_args)
        
        # Add OpenRouter API key handling
        if 'openrouter' in model_name:
            # Use OPENAI_API_KEY for OpenRouter (this is how OpenRouter integration works)
            if not os.getenv('OPENAI_API_KEY'):
                print("❌ OpenRouter API key not found!")
                print("Set OPENAI_API_KEY environment variable with your OpenRouter key")
                return 1
        
        # Display what we're doing
        print(f"🎯 Task: {user_prompt}")
        if not (self.intelligent_router and not force_tier):
            # Only show basic info for legacy routing (intelligent routing already showed details)
            print(f"🤖 Model: {model_name} ({selected_tier} tier)")
            print(f"💡 Reason: {routing_reason}")
        print(f"💰 Estimated cost: ${estimated_cost:.3f}")
        if context['standards']:
            print(f"📋 Using {len(context['standards'])} coding standards")
        print(f"🚀 Launching Aider...\n")
        
        # Launch Aider
        try:
            result = subprocess.run(aider_cmd, cwd=self.project_root)
            
            # Record usage (rough estimate)
            if result.returncode == 0:
                self.budget.record_usage(
                    model=model_name,
                    tokens_sent=int(estimated_tokens * 0.7),
                    tokens_received=int(estimated_tokens * 0.3), 
                    cost=estimated_cost,
                    task_type=selected_tier
                )
            
            return result.returncode
            
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Failed to launch Aider: {e}")
            print(f"❌ Failed to launch Aider: {e}")
            return 1
    
    def list_models(self, tier: Optional[ModelTier] = None):
        """List available models, optionally filtered by tier."""
        if tier:
            models = self.router.get_models_for_tier(tier)
            print(f"\n🎯 {tier.value.title()} Tier Models:")
            for model in models:
                print(f"  {model.name}")
                print(f"    Cost: ${model.cost_per_1k_tokens}/1K tokens")
                print(f"    Best for: {', '.join(model.best_for)}")
                print()
        else:
            print("\n🤖 Atlas Code Model Tiers:")
            for tier_enum in ModelTier:
                tier_info = self.router.get_tier_info(tier_enum)
                print(f"\n{tier_enum.value.title()} Tier:")
                for model_info in tier_info['models']:
                    print(f"  {model_info['name']} - ${model_info['cost']}/1K tokens")
    
    def show_budget_status(self):
        """Display current budget status."""
        status = self.budget.check_budget_status()
        
        print("\n💰 Budget Status:")
        if status['daily_limit']:
            print(f"Daily limit: ${status['daily_limit']}")
            print(f"Spent today: ${status['today_spent']:.2f}")
            print(f"Remaining: ${status['remaining']:.2f}")
            print(f"Usage: {status['percentage_used']:.1f}%")
            
            if status['warning_level'] == 'red':
                print("🚨 Near or over budget limit!")
            elif status['warning_level'] == 'yellow':
                print("⚠️  Approaching budget limit")
            else:
                print("✅ Budget looks good")
        else:
            print("No daily limit set")
            print(f"Spent today: ${status['today_spent']:.2f}")
            
        # Show weekly summary
        summary = self.budget.get_usage_summary(7)
        print(f"\nPast 7 days: ${summary['total_cost']:.2f}")
        print(f"Average daily: ${summary['average_daily_cost']:.2f}")
    
    def initialize_agent_os(self):
        """Initialize Agent OS directory structure if it doesn't exist."""
        if self.agent_os_dir.exists():
            print(f"Agent OS already initialized at {self.agent_os_dir}")
            return
        
        print(f"🔧 Initializing Agent OS at {self.agent_os_dir}")
        
        # Create directory structure
        (self.agent_os_dir / "standards").mkdir(parents=True)
        (self.agent_os_dir / "instructions").mkdir(parents=True)
        (self.agent_os_dir / "commands").mkdir(parents=True)
        (self.agent_os_dir / "templates").mkdir(parents=True)
        
        # Create sample files
        sample_standard = """# Coding Standards

## Python Style
- Use type hints for all function parameters and return values
- Follow PEP 8 naming conventions
- Use docstrings for all public functions and classes
- Prefer f-strings for string formatting

## Error Handling
- Use specific exception types
- Always include helpful error messages
- Log errors appropriately
"""
        
        (self.agent_os_dir / "standards" / "python.md").write_text(sample_standard)
        
        sample_instruction = """# Testing Instructions

## Unit Tests
- Write tests for all new functions
- Use pytest as the testing framework
- Aim for >80% code coverage
- Include edge cases and error conditions

## Test Structure
- One test file per module
- Group related tests in classes
- Use descriptive test names
"""
        
        (self.agent_os_dir / "instructions" / "testing.md").write_text(sample_instruction)
        
        project_info = {
            "name": self.project_root.name,
            "type": "python",  # Could be detected
            "initialized": True,
            "atlas_code_version": "2.0.0"
        }
        
        (self.agent_os_dir / "project_info.json").write_text(
            json.dumps(project_info, indent=2)
        )
        
        print("✅ Agent OS initialized with sample standards and instructions")
        print("Edit the files in agent_os/ to customize for your project")