"""
Security Sandbox for Atlas Code V5

Provides safe code execution with comprehensive sandboxing,
import restrictions, and resource limits.
"""

import os
import sys
import ast
import types
import builtins
import traceback
import threading
import signal
import resource
import tempfile
from typing import Dict, List, Set, Any, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class SecurityViolation(Exception):
    """Raised when code violates security policies."""
    pass

class ExecutionTimeout(Exception):
    """Raised when code execution times out."""
    pass

class SandboxConfig:
    """Configuration for sandbox security settings."""
    
    def __init__(self, config_dir: str):
        """Initialize sandbox configuration."""
        import json
        
        settings_path = os.path.join(config_dir, 'settings.json')
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        self.code_execution = settings['code_execution']
        self.enabled = self.code_execution.get('enable_execution', True)
        self.sandboxed = self.code_execution.get('sandboxed', True)
        self.timeout_seconds = self.code_execution.get('timeout_seconds', 10)
        self.max_memory_mb = self.code_execution.get('max_memory_mb', 100)
        
        # Import restrictions
        self.allowed_imports = set(self.code_execution.get('allowed_imports', []))
        self.blocked_imports = set(self.code_execution.get('blocked_imports', []))
        
        # File operation restrictions
        self.allowed_file_operations = set(self.code_execution.get('allowed_file_operations', ['read']))
        self.restricted_paths = set(self.code_execution.get('restricted_paths', []))
        
        logger.info(f"Sandbox initialized: enabled={self.enabled}, sandboxed={self.sandboxed}")

class ASTSecurityValidator:
    """AST-based security validation for Python code."""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        
        # Dangerous AST node types
        self.dangerous_nodes = {
            ast.Import: self._check_import,
            ast.ImportFrom: self._check_import_from,
            ast.Call: self._check_call,
            ast.Attribute: self._check_attribute,
            ast.Subscript: self._check_subscript,
        }
        
        # Dangerous function calls
        self.dangerous_functions = {
            'exec', 'eval', 'compile', '__import__',
            'open', 'file', 'input', 'raw_input',
            'reload', 'exit', 'quit', 'help',
        }
        
        # Dangerous attributes
        self.dangerous_attributes = {
            '__globals__', '__locals__', '__dict__',
            '__class__', '__bases__', '__subclasses__',
            '__import__', '__builtins__',
        }
    
    def validate_code(self, code: str) -> List[str]:
        """
        Validate code for security violations.
        
        Returns:
            List of security violation messages (empty if safe)
        """
        violations = []
        
        try:
            tree = ast.parse(code)
            violations.extend(self._analyze_tree(tree))
        except SyntaxError as e:
            violations.append(f"Syntax error: {e}")
        
        return violations
    
    def _analyze_tree(self, tree: ast.AST) -> List[str]:
        """Recursively analyze AST for security violations."""
        violations = []
        
        for node in ast.walk(tree):
            node_type = type(node)
            if node_type in self.dangerous_nodes:
                try:
                    violation = self.dangerous_nodes[node_type](node)
                    if violation:
                        violations.append(violation)
                except Exception as e:
                    violations.append(f"Security check error: {e}")
        
        return violations
    
    def _check_import(self, node: ast.Import) -> Optional[str]:
        """Check import statements for security violations."""
        for alias in node.names:
            module_name = alias.name
            
            # Check if module is explicitly blocked
            if module_name in self.config.blocked_imports:
                return f"Blocked import: {module_name}"
            
            # Check if only allowed imports are permitted
            if self.config.allowed_imports and module_name not in self.config.allowed_imports:
                return f"Import not in allowed list: {module_name}"
            
            # Check for dangerous standard library modules
            dangerous_modules = {
                'subprocess', 'os', 'sys', 'socket', 'urllib',
                'http', 'ftplib', 'smtplib', 'telnetlib',
                'ctypes', 'marshal', 'pickle', 'shelve'
            }
            
            if module_name in dangerous_modules and module_name not in self.config.allowed_imports:
                return f"Potentially dangerous import: {module_name}"
        
        return None
    
    def _check_import_from(self, node: ast.ImportFrom) -> Optional[str]:
        """Check 'from X import Y' statements."""
        if node.module:
            # Check the base module
            if node.module in self.config.blocked_imports:
                return f"Blocked import from: {node.module}"
            
            # Check imported names
            for alias in node.names:
                name = alias.name
                
                # Special case for dangerous functions
                if name in self.dangerous_functions:
                    return f"Dangerous function import: {name} from {node.module}"
        
        return None
    
    def _check_call(self, node: ast.Call) -> Optional[str]:
        """Check function calls for dangerous operations."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            if func_name in self.dangerous_functions:
                return f"Dangerous function call: {func_name}"
                
            # Check for file operations
            if func_name == 'open' and 'read' not in self.config.allowed_file_operations:
                return "File operations not permitted"
        
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            
            # Common dangerous method calls
            dangerous_methods = {
                'system', 'popen', 'spawn', 'exec',
                'call', 'check_output', 'run'
            }
            
            if attr_name in dangerous_methods:
                return f"Dangerous method call: {attr_name}"
        
        return None
    
    def _check_attribute(self, node: ast.Attribute) -> Optional[str]:
        """Check attribute access for dangerous operations."""
        attr_name = node.attr
        
        if attr_name in self.dangerous_attributes:
            return f"Dangerous attribute access: {attr_name}"
        
        return None
    
    def _check_subscript(self, node: ast.Subscript) -> Optional[str]:
        """Check subscript operations for potential violations."""
        # This could be expanded to check for dangerous dictionary access
        return None

class SecureSandbox:
    """
    Secure execution environment for untrusted code.
    """
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.validator = ASTSecurityValidator(config)
        
        # Track execution state
        self.execution_active = False
        self.execution_thread = None
        
        logger.info("Secure sandbox initialized")
    
    def execute_python_code(self, code: str, globals_dict: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute Python code in a secure sandbox.
        
        Args:
            code: Python code to execute
            globals_dict: Optional global variables
            
        Returns:
            Dictionary with execution results
        """
        if not self.config.enabled:
            return {
                'success': False,
                'error': 'Code execution is disabled',
                'output': '',
                'result': None
            }
        
        # Validate code security
        violations = self.validator.validate_code(code)
        if violations:
            return {
                'success': False,
                'error': f'Security violations: {"; ".join(violations)}',
                'output': '',
                'result': None
            }
        
        # Set up secure execution environment
        if self.config.sandboxed:
            return self._execute_sandboxed(code, globals_dict)
        else:
            return self._execute_direct(code, globals_dict)
    
    def _execute_sandboxed(self, code: str, globals_dict: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute code in a sandboxed environment."""
        # Create restricted globals
        safe_globals = self._create_safe_globals()
        
        if globals_dict:
            # Merge user globals (with validation)
            for key, value in globals_dict.items():
                if self._is_safe_value(key, value):
                    safe_globals[key] = value
        
        # Capture output
        output_capture = []
        
        def safe_print(*args, **kwargs):
            output_capture.append(' '.join(str(arg) for arg in args))
        
        safe_globals['print'] = safe_print
        
        # Set up resource limits
        if hasattr(resource, 'RLIMIT_AS'):
            try:
                # Set memory limit
                memory_limit = self.config.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
            except Exception:
                pass  # Ignore if not supported
        
        # Execute with timeout
        result = None
        error = None
        
        try:
            # Set up timeout handler
            def timeout_handler(signum, frame):
                raise ExecutionTimeout("Code execution timed out")
            
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.config.timeout_seconds)
            
            try:
                # Compile and execute
                compiled_code = compile(code, '<sandbox>', 'exec')
                exec(compiled_code, safe_globals)
                
                # Get result if there's a 'result' variable
                result = safe_globals.get('result')
                
            finally:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)  # Cancel timeout
        
        except ExecutionTimeout:
            error = f"Code execution timed out after {self.config.timeout_seconds} seconds"
        except MemoryError:
            error = f"Code execution exceeded memory limit ({self.config.max_memory_mb} MB)"
        except Exception as e:
            error = f"Execution error: {str(e)}"
            if logger.isEnabledFor(logging.DEBUG):
                error += f"\n{traceback.format_exc()}"
        
        return {
            'success': error is None,
            'error': error,
            'output': '\n'.join(output_capture),
            'result': result,
            'globals': {k: v for k, v in safe_globals.items() 
                       if not k.startswith('__') and k not in ['print']}
        }
    
    def _execute_direct(self, code: str, globals_dict: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute code directly (less secure, for trusted environments)."""
        if globals_dict is None:
            globals_dict = {}
        
        # Still capture output
        import io
        import contextlib
        
        output_capture = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(output_capture):
                exec(code, globals_dict)
            
            return {
                'success': True,
                'error': None,
                'output': output_capture.getvalue(),
                'result': globals_dict.get('result'),
                'globals': globals_dict
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': output_capture.getvalue(),
                'result': None,
                'globals': globals_dict
            }
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """Create a restricted global namespace."""
        # Start with minimal builtins
        safe_builtins = {
            'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes',
            'chr', 'complex', 'dict', 'divmod', 'enumerate', 'filter',
            'float', 'frozenset', 'hash', 'hex', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'map', 'max', 'min',
            'oct', 'ord', 'pow', 'range', 'repr', 'reversed', 'round',
            'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type',
            'zip', 'True', 'False', 'None'
        }
        
        safe_globals = {}
        
        # Add safe builtins
        for name in safe_builtins:
            if hasattr(builtins, name):
                safe_globals[name] = getattr(builtins, name)
        
        # Add commonly needed modules that are in allowed list
        safe_modules = {}
        for module_name in self.config.allowed_imports:
            try:
                if module_name in sys.modules:
                    safe_modules[module_name] = sys.modules[module_name]
                else:
                    safe_modules[module_name] = __import__(module_name)
            except ImportError:
                pass
        
        safe_globals.update(safe_modules)
        
        return safe_globals
    
    def _is_safe_value(self, key: str, value: Any) -> bool:
        """Check if a value is safe to include in globals."""
        # Don't allow private attributes
        if key.startswith('_'):
            return False
        
        # Don't allow functions/methods that could be dangerous
        if callable(value):
            return False
        
        # Don't allow modules
        if isinstance(value, types.ModuleType):
            return False
        
        return True
    
    @contextmanager
    def temporary_file(self, suffix: str = '.tmp', content: str = ''):
        """Create a temporary file for code execution."""
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w+', 
                suffix=suffix, 
                delete=False
            )
            
            if content:
                temp_file.write(content)
                temp_file.flush()
            
            yield temp_file.name
            
        finally:
            if temp_file:
                temp_file.close()
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass

# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test the sandbox
    try:
        config = SandboxConfig('../config')
        sandbox = SecureSandbox(config)
        
        # Test safe code
        safe_code = """
result = sum(range(10))
print(f"Sum of 0-9: {result}")
        """
        
        print("Testing safe code:")
        result = sandbox.execute_python_code(safe_code)
        print(f"Success: {result['success']}")
        print(f"Output: {result['output']}")
        print(f"Result: {result['result']}")
        
        # Test dangerous code
        dangerous_code = """
import os
os.system('ls')
        """
        
        print("\nTesting dangerous code:")
        result = sandbox.execute_python_code(dangerous_code)
        print(f"Success: {result['success']}")
        print(f"Error: {result['error']}")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()