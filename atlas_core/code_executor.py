"""
Code Executor for Atlas Code V5

Direct code execution engine with multi-language support, safety features,
and comprehensive request processing capabilities.
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import tempfile
import json

logger = logging.getLogger(__name__)

@dataclass
class ExecutionRequest:
    """Request for code execution."""
    query: str
    intent: str
    model: str
    file_context: Optional[str] = None
    language: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None

@dataclass
class ExecutionResult:
    """Result of code execution request."""
    success: bool
    response: str
    generated_code: Optional[str] = None
    execution_output: Optional[str] = None
    error: Optional[str] = None
    tokens_used: int = 0
    cost: float = 0.0
    processing_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class CodeExecutor:
    """
    Direct code execution engine that processes requests through the full
    Atlas Code V5 pipeline with multi-language support and safety features.
    """
    
    def __init__(self, config_dir: str):
        """Initialize code executor with all required components."""
        self.config_dir = config_dir
        
        # Initialize core components
        try:
            from .hybrid_router import HybridRouter
            from .budget_optimizer import BudgetOptimizer
            from .security_sandbox import SecureSandbox, SandboxConfig
            from .openrouter_client import OpenRouterClient
            
            self.router = HybridRouter(config_dir)
            self.budget_optimizer = BudgetOptimizer(config_dir)
            self.sandbox_config = SandboxConfig(config_dir)
            self.sandbox = SecureSandbox(self.sandbox_config)
            self.openrouter_client = OpenRouterClient(config_dir)
            
            logger.info("Code executor initialized with all components")
            
        except Exception as e:
            logger.error(f"Failed to initialize code executor: {e}")
            raise Exception(f"Code executor initialization failed: {e}")
        
        # Load configuration
        self.settings = self._load_settings()
        self.prompts = self._load_prompts()
        
        # Language support
        self.supported_languages = {
            'python': {
                'extensions': ['.py'],
                'executable': 'python3',
                'template': 'python_template',
                'syntax_check_cmd': 'python3 -m py_compile'
            },
            'javascript': {
                'extensions': ['.js'],
                'executable': 'node',
                'template': 'javascript_template',
                'syntax_check_cmd': 'node --check'
            },
            'typescript': {
                'extensions': ['.ts'],
                'executable': 'npx ts-node',
                'template': 'typescript_template',
                'syntax_check_cmd': 'npx tsc --noEmit'
            },
            'java': {
                'extensions': ['.java'],
                'executable': 'java',
                'template': 'java_template',
                'syntax_check_cmd': 'javac'
            },
            'cpp': {
                'extensions': ['.cpp', '.cc'],
                'executable': './a.out',
                'template': 'cpp_template',
                'compile_cmd': 'g++ -o a.out',
                'syntax_check_cmd': 'g++ -fsyntax-only'
            },
            'go': {
                'extensions': ['.go'],
                'executable': 'go run',
                'template': 'go_template',
                'syntax_check_cmd': 'go build -o /dev/null'
            },
            'rust': {
                'extensions': ['.rs'],
                'executable': 'cargo run',
                'template': 'rust_template',
                'syntax_check_cmd': 'rustc --crate-type bin -o /dev/null'
            }
        }
        
        # Execution statistics
        self.execution_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_processing_time': 0.0,
            'total_cost': 0.0
        }
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load system settings."""
        try:
            settings_path = os.path.join(self.config_dir, 'settings.json')
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
            return self._get_default_settings()
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompt templates."""
        try:
            prompts_path = os.path.join(self.config_dir, 'prompts.json')
            with open(prompts_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load prompts: {e}")
            return self._get_default_prompts()
    
    def execute_request(
        self,
        query: str,
        intent: Optional[str] = None,
        model: Optional[str] = None,
        file_context: Optional[str] = None,
        language: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute a complete request through the Atlas Code V5 pipeline.
        
        Args:
            query: User's request or question
            intent: Pre-classified intent (optional, will classify if not provided)
            model: Specific model to use (optional, will select optimal if not provided)
            file_context: Content of relevant files
            language: Programming language if known
            user_preferences: User-specific preferences
            
        Returns:
            ExecutionResult with response and metadata
        """
        start_time = time.time()
        self.execution_stats['total_requests'] += 1
        
        try:
            # Step 1: Intent Classification (if not provided)
            if not intent:
                logger.debug("Classifying intent...")
                classification = self.router.classify_intent(
                    query, file_context, language
                )
                intent = classification.intent
                complexity = classification.complexity
                estimated_tokens = classification.estimated_tokens
                
                logger.info(f"Classified as {intent} with {classification.confidence:.2f} confidence")
            else:
                # Use provided intent with defaults
                complexity = "medium"
                estimated_tokens = 500
            
            # Auto-detect language if not provided
            if not language:
                language = self._detect_language(query, file_context)
            
            # Step 2: Model Selection (if not provided)
            if not model:
                logger.debug("Selecting optimal model...")
                model_selection = self.budget_optimizer.select_model(
                    intent, complexity, estimated_tokens=estimated_tokens
                )
                model = model_selection.model
                selected_tier = model_selection.tier
                
                logger.info(f"Selected {model} ({selected_tier}): {model_selection.reasoning}")
            else:
                selected_tier = "unknown"
            
            # Step 3: Generate Response
            logger.debug("Generating AI response...")
            ai_response = self._generate_ai_response(
                query, intent, model, file_context, language, user_preferences
            )
            
            if not ai_response['success']:
                return self._create_error_result(
                    f"AI response generation failed: {ai_response['error']}",
                    processing_time=time.time() - start_time
                )
            
            # Step 4: Process Generated Code (if applicable)
            execution_output = None
            generated_code = None
            
            if self._intent_generates_code(intent):
                generated_code = self._extract_code_from_response(ai_response['content'], language)
                
                if generated_code and self._should_execute_code(intent):
                    logger.debug("Executing generated code...")
                    exec_result = self._execute_code_safely(generated_code, language)
                    
                    if exec_result['success']:
                        execution_output = exec_result['output']
                        logger.info("Code executed successfully")
                    else:
                        logger.warning(f"Code execution failed: {exec_result['error']}")
                        # Include execution error in response
                        ai_response['content'] += f"\n\n⚠️ **Execution Error**: {exec_result['error']}"
            
            # Step 5: Track Usage
            tokens_used = ai_response.get('tokens_used', 0)
            cost = ai_response.get('cost', 0.0)
            
            self.budget_optimizer.track_usage(
                model=model,
                tier=selected_tier,
                intent=intent,
                tokens_input=tokens_used // 2,  # Rough estimate
                tokens_output=tokens_used // 2,
                cost=cost,
                success=True,
                response_time=time.time() - start_time
            )
            
            # Step 6: Update Statistics
            self.execution_stats['successful_requests'] += 1
            processing_time = time.time() - start_time
            self._update_processing_stats(processing_time, cost)
            
            logger.info(f"Request completed successfully in {processing_time:.2f}s")
            
            return ExecutionResult(
                success=True,
                response=ai_response['content'],
                generated_code=generated_code,
                execution_output=execution_output,
                tokens_used=tokens_used,
                cost=cost,
                processing_time=processing_time,
                metadata={
                    'intent': intent,
                    'model': model,
                    'tier': selected_tier,
                    'language': language,
                    'complexity': complexity,
                    'code_executed': execution_output is not None
                }
            )
            
        except Exception as e:
            # Handle any unexpected errors
            self.execution_stats['failed_requests'] += 1
            processing_time = time.time() - start_time
            
            logger.error(f"Request execution failed: {e}")
            
            return self._create_error_result(
                f"Execution failed: {str(e)}",
                processing_time=processing_time
            )
    
    def _generate_ai_response(
        self,
        query: str,
        intent: str,
        model: str,
        file_context: Optional[str],
        language: Optional[str],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI response using the selected model."""
        
        try:
            # Get intent-specific prompt
            intent_prompts = self.prompts.get('intent_prompts', {})
            prompt_config = intent_prompts.get(intent, intent_prompts.get('general_query', {}))
            
            system_prompt = prompt_config.get('system', 'You are a helpful coding assistant.')
            user_template = prompt_config.get('user_template', '{query}')
            
            # Format user prompt with context
            context_vars = {
                'query': query,
                'language': language or 'auto-detect',
                'file_context': file_context or 'None provided',
                'user_preferences': user_preferences or {}
            }
            
            # Add specific context based on intent
            if intent == 'code_generation':
                context_vars.update({
                    'task': query,
                    'requirements': 'Generate clean, well-documented code',
                    'context': file_context or 'No existing code context'
                })
            elif intent == 'debugging':
                context_vars.update({
                    'code': file_context or query,
                    'error': 'Debug and fix issues',
                    'context': 'Analyze and provide solutions'
                })
            elif intent == 'code_editing':
                context_vars.update({
                    'original_code': file_context or 'No code provided',
                    'modification': query,
                    'constraints': 'Maintain functionality and style'
                })
            
            user_prompt = user_template.format(**context_vars)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Make API request
            response = self.openrouter_client.generate_response(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            if response.success:
                return {
                    'success': True,
                    'content': response.content,
                    'tokens_used': (response.usage.tokens_input + response.usage.tokens_output) if response.usage else 0,
                    'cost': response.usage.total_cost if response.usage else 0.0
                }
            else:
                return {
                    'success': False,
                    'error': response.error,
                    'tokens_used': 0,
                    'cost': 0.0
                }
        
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'tokens_used': 0,
                'cost': 0.0
            }
    
    def _detect_language(self, query: str, file_context: Optional[str] = None) -> Optional[str]:
        """Auto-detect programming language from query and context."""
        
        # Check file context for language clues
        if file_context:
            # Look for file extensions in comments
            for lang, info in self.supported_languages.items():
                for ext in info['extensions']:
                    if ext in file_context:
                        return lang
            
            # Look for language-specific syntax
            if 'def ' in file_context or 'import ' in file_context:
                return 'python'
            elif 'function ' in file_context or 'const ' in file_context:
                return 'javascript'
            elif 'public class' in file_context or 'public static void main' in file_context:
                return 'java'
            elif 'fn main()' in file_context or 'use std::' in file_context:
                return 'rust'
            elif 'func main()' in file_context or 'package main' in file_context:
                return 'go'
        
        # Check query for language mentions
        query_lower = query.lower()
        for lang in self.supported_languages.keys():
            if lang in query_lower:
                return lang
        
        # Look for language-specific terms
        if any(term in query_lower for term in ['python', 'py', 'def', 'import']):
            return 'python'
        elif any(term in query_lower for term in ['javascript', 'js', 'node', 'function']):
            return 'javascript'
        elif any(term in query_lower for term in ['java', 'class', 'public static']):
            return 'java'
        elif any(term in query_lower for term in ['rust', 'cargo', 'fn']):
            return 'rust'
        elif any(term in query_lower for term in ['go', 'golang', 'func']):
            return 'go'
        elif any(term in query_lower for term in ['c++', 'cpp', 'iostream']):
            return 'cpp'
        
        # Default to Python for code-related intents
        return 'python'
    
    def _intent_generates_code(self, intent: str) -> bool:
        """Check if intent typically generates executable code."""
        code_generating_intents = {
            'code_generation', 'code_editing', 'testing', 'file_operations'
        }
        return intent in code_generating_intents
    
    def _should_execute_code(self, intent: str) -> bool:
        """Check if generated code should be executed."""
        # Only execute for specific intents and if execution is enabled
        executable_intents = {'code_generation', 'testing', 'file_operations'}
        execution_enabled = self.settings.get('code_execution', {}).get('enable_execution', False)
        
        return intent in executable_intents and execution_enabled
    
    def _extract_code_from_response(self, response: str, language: Optional[str]) -> Optional[str]:
        """Extract code blocks from AI response."""
        
        import re
        
        # Look for code blocks with language specification
        lang_pattern = rf'```{language}\n(.*?)\n```' if language else r'```\w+\n(.*?)\n```'
        matches = re.findall(lang_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Look for generic code blocks
        generic_pattern = r'```\n(.*?)\n```'
        matches = re.findall(generic_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Look for inline code (less reliable)
        inline_pattern = r'`([^`]+)`'
        matches = re.findall(inline_pattern, response)
        
        if matches:
            # Filter for code-like content
            for match in matches:
                if any(keyword in match for keyword in ['def ', 'function ', 'class ', 'import ', 'const ', 'let ', 'var ']):
                    return match.strip()
        
        return None
    
    def _execute_code_safely(self, code: str, language: Optional[str]) -> Dict[str, Any]:
        """Execute code safely using the security sandbox."""
        
        if not language:
            language = 'python'  # Default
        
        # Currently only Python execution is fully implemented in sandbox
        if language == 'python':
            return self.sandbox.execute_python_code(code)
        
        # For other languages, create a safe execution environment
        return self._execute_other_language(code, language)
    
    def _execute_other_language(self, code: str, language: str) -> Dict[str, Any]:
        """Execute non-Python code with basic safety measures."""
        
        if language not in self.supported_languages:
            return {
                'success': False,
                'error': f"Language {language} not supported for execution",
                'output': ''
            }
        
        lang_config = self.supported_languages[language]
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create source file
                ext = lang_config['extensions'][0]
                source_file = os.path.join(temp_dir, f"code{ext}")
                
                with open(source_file, 'w') as f:
                    f.write(code)
                
                # Syntax check first (if available)
                if 'syntax_check_cmd' in lang_config:
                    syntax_cmd = f"{lang_config['syntax_check_cmd']} {source_file}"
                    syntax_result = os.system(syntax_cmd)
                    
                    if syntax_result != 0:
                        return {
                            'success': False,
                            'error': f"Syntax check failed for {language}",
                            'output': ''
                        }
                
                # Compile if needed
                if 'compile_cmd' in lang_config:
                    compile_cmd = f"cd {temp_dir} && {lang_config['compile_cmd']} {source_file}"
                    compile_result = os.system(compile_cmd)
                    
                    if compile_result != 0:
                        return {
                            'success': False,
                            'error': f"Compilation failed for {language}",
                            'output': ''
                        }
                
                # Execute (with timeout)
                if language == 'cpp':
                    exec_cmd = f"cd {temp_dir} && timeout 10s ./a.out"
                elif language == 'java':
                    # Extract class name
                    import re
                    class_match = re.search(r'public class (\w+)', code)
                    if class_match:
                        class_name = class_match.group(1)
                        exec_cmd = f"cd {temp_dir} && timeout 10s java {class_name}"
                    else:
                        return {'success': False, 'error': 'No public class found', 'output': ''}
                else:
                    exec_cmd = f"cd {temp_dir} && timeout 10s {lang_config['executable']} {source_file}"
                
                # Execute and capture output
                import subprocess
                try:
                    result = subprocess.run(
                        exec_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        return {
                            'success': True,
                            'error': None,
                            'output': result.stdout
                        }
                    else:
                        return {
                            'success': False,
                            'error': result.stderr or f"Exit code: {result.returncode}",
                            'output': result.stdout
                        }
                
                except subprocess.TimeoutExpired:
                    return {
                        'success': False,
                        'error': "Execution timed out (10 seconds)",
                        'output': ''
                    }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': ''
            }
    
    def _create_error_result(self, error_message: str, processing_time: float = 0.0) -> ExecutionResult:
        """Create an error result."""
        return ExecutionResult(
            success=False,
            response=f"❌ **Error**: {error_message}",
            error=error_message,
            processing_time=processing_time
        )
    
    def _update_processing_stats(self, processing_time: float, cost: float):
        """Update processing statistics."""
        stats = self.execution_stats
        
        # Update average processing time
        total_requests = stats['total_requests']
        current_avg = stats['avg_processing_time']
        stats['avg_processing_time'] = (current_avg * (total_requests - 1) + processing_time) / total_requests
        
        # Update total cost
        stats['total_cost'] += cost
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        stats = self.execution_stats.copy()
        
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_requests'] / stats['total_requests']
            stats['failure_rate'] = stats['failed_requests'] / stats['total_requests']
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        return stats
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return list(self.supported_languages.keys())
    
    # Default configurations
    def _get_default_settings(self) -> Dict[str, Any]:
        """Default settings if config missing."""
        return {
            'code_execution': {
                'enable_execution': False,
                'sandboxed': True,
                'timeout_seconds': 10
            }
        }
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """Default prompts if config missing."""
        return {
            'intent_prompts': {
                'code_generation': {
                    'system': 'You are a senior software engineer. Generate clean, well-documented code.',
                    'user_template': 'Language: {language}\nTask: {query}\n\nGenerate complete, working code.'
                },
                'general_query': {
                    'system': 'You are a helpful coding assistant.',
                    'user_template': '{query}'
                }
            }
        }

# Example usage and testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test code executor
    try:
        executor = CodeExecutor("../config")
        
        print("⚡ Testing Code Executor")
        print("=" * 40)
        
        # Test requests
        test_requests = [
            "write a python function to calculate factorial",
            "explain how binary search works",
            "debug this error: NameError",
            "create a simple calculator class"
        ]
        
        for query in test_requests:
            print(f"\n🔍 Query: {query}")
            result = executor.execute_request(query)
            
            print(f"✅ Success: {result.success}")
            if result.success:
                print(f"📝 Response length: {len(result.response)} chars")
                print(f"💰 Cost: ${result.cost:.4f}")
                print(f"⏱️  Time: {result.processing_time:.2f}s")
                if result.generated_code:
                    print(f"💻 Generated code: {len(result.generated_code)} chars")
                if result.execution_output:
                    print(f"🚀 Execution output: {result.execution_output[:100]}...")
            else:
                print(f"❌ Error: {result.error}")
        
        # Show statistics
        print("\n📊 Execution Statistics:")
        stats = executor.get_execution_stats()
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Success Rate: {stats['success_rate']:.1%}")
        print(f"Avg Processing Time: {stats['avg_processing_time']:.2f}s")
        print(f"Total Cost: ${stats['total_cost']:.4f}")
        
        print(f"\n🌐 Supported Languages: {', '.join(executor.get_supported_languages())}")
        
    except Exception as e:
        print(f"❌ Failed to test code executor: {e}")