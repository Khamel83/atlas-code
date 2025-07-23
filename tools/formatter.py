"""
Code Formatter for Atlas Code V5

Multi-language code formatting with support for popular formatters
and consistent style enforcement.
"""

import os
import subprocess
import tempfile
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class CodeFormatter:
    """
    Multi-language code formatter with support for popular formatting tools.
    """
    
    def __init__(self):
        """Initialize code formatter with language support."""
        
        # Language-specific formatter configurations
        self.formatters = {
            'python': {
                'name': 'black',
                'command': ['black', '--quiet', '--code'],
                'fallback_command': ['autopep8', '--'],
                'extensions': ['.py']
            },
            'javascript': {
                'name': 'prettier',
                'command': ['npx', 'prettier', '--parser', 'babel'],
                'fallback_command': ['js-beautify'],
                'extensions': ['.js', '.jsx']
            },
            'typescript': {
                'name': 'prettier',
                'command': ['npx', 'prettier', '--parser', 'typescript'],
                'fallback_command': ['tsfmt'],
                'extensions': ['.ts', '.tsx']
            },
            'java': {
                'name': 'google-java-format',
                'command': ['java', '-jar', 'google-java-format.jar', '-'],
                'fallback_command': None,
                'extensions': ['.java']
            },
            'cpp': {
                'name': 'clang-format',
                'command': ['clang-format', '--style=Google'],
                'fallback_command': ['astyle', '--style=google'],
                'extensions': ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp']
            },
            'go': {
                'name': 'gofmt',
                'command': ['gofmt'],
                'fallback_command': None,
                'extensions': ['.go']
            },
            'rust': {
                'name': 'rustfmt',
                'command': ['rustfmt', '--emit', 'stdout'],
                'fallback_command': None,
                'extensions': ['.rs']
            },
            'json': {
                'name': 'jq',
                'command': ['jq', '.'],
                'fallback_command': None,
                'extensions': ['.json']
            },
            'yaml': {
                'name': 'prettier',
                'command': ['npx', 'prettier', '--parser', 'yaml'],
                'fallback_command': None,
                'extensions': ['.yaml', '.yml']
            },
            'html': {
                'name': 'prettier',
                'command': ['npx', 'prettier', '--parser', 'html'],
                'fallback_command': ['tidy', '-quiet', '-indent'],
                'extensions': ['.html', '.htm']
            },
            'css': {
                'name': 'prettier',
                'command': ['npx', 'prettier', '--parser', 'css'],
                'fallback_command': ['css-beautify'],
                'extensions': ['.css']
            }
        }
        
        # Check available formatters
        self.available_formatters = self._check_available_formatters()
        
        logger.info(f"Code formatter initialized with {len(self.available_formatters)} available formatters")
    
    def _check_available_formatters(self) -> Dict[str, Dict[str, Any]]:
        """Check which formatters are available on the system."""
        available = {}
        
        for language, config in self.formatters.items():
            formatter_available = False
            
            # Check primary formatter
            try:
                primary_cmd = config['command'][0]
                result = subprocess.run(
                    ['which', primary_cmd] if os.name != 'nt' else ['where', primary_cmd],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    formatter_available = True
                    available[language] = {
                        'formatter': config['name'],
                        'command': config['command'],
                        'type': 'primary'
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Check fallback formatter if primary not available
            if not formatter_available and config.get('fallback_command'):
                try:
                    fallback_cmd = config['fallback_command'][0]
                    result = subprocess.run(
                        ['which', fallback_cmd] if os.name != 'nt' else ['where', fallback_cmd],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        available[language] = {
                            'formatter': fallback_cmd,
                            'command': config['fallback_command'],
                            'type': 'fallback'
                        }
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
        
        return available
    
    def format_code(
        self,
        code: str,
        language: str,
        style_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format code using appropriate formatter for the language.
        
        Args:
            code: Code to format
            language: Programming language
            style_options: Optional style configuration
            
        Returns:
            Dictionary with formatting results
        """
        
        if not code.strip():
            return {
                'success': True,
                'formatted_code': code,
                'changes_made': False,
                'formatter_used': 'none',
                'message': 'Empty code, no formatting needed'
            }
        
        # Check if formatter is available for this language
        if language not in self.available_formatters:
            return self._fallback_format(code, language)
        
        formatter_config = self.available_formatters[language]
        
        try:
            # Format using external tool
            if language in ['python', 'go', 'rust']:
                formatted_code = self._format_with_stdin(code, formatter_config['command'])
            elif language in ['javascript', 'typescript', 'html', 'css', 'yaml']:
                formatted_code = self._format_with_prettier(code, formatter_config['command'])
            elif language == 'cpp':
                formatted_code = self._format_with_clang_format(code, formatter_config['command'])
            elif language == 'json':
                formatted_code = self._format_json(code)
            else:
                formatted_code = self._format_with_stdin(code, formatter_config['command'])
            
            # Check if changes were made
            changes_made = formatted_code.strip() != code.strip()
            
            return {
                'success': True,
                'formatted_code': formatted_code,
                'changes_made': changes_made,
                'formatter_used': formatter_config['formatter'],
                'message': f"Formatted with {formatter_config['formatter']}" if changes_made else "No changes needed"
            }
        
        except Exception as e:
            logger.warning(f"Formatting failed with {formatter_config['formatter']}: {e}")
            return self._fallback_format(code, language)
    
    def _format_with_stdin(self, code: str, command: List[str]) -> str:
        """Format code by passing it through stdin."""
        
        try:
            result = subprocess.run(
                command,
                input=code,
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                raise Exception(f"Formatter error: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            raise Exception("Formatter timed out")
    
    def _format_with_prettier(self, code: str, command: List[str]) -> str:
        """Format code using Prettier (requires stdin)."""
        
        try:
            # Prettier expects input via stdin
            result = subprocess.run(
                command + ['--stdin-filepath', 'temp.js'],  # Add filepath for parser detection
                input=code,
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                raise Exception(f"Prettier error: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            raise Exception("Prettier timed out")
    
    def _format_with_clang_format(self, code: str, command: List[str]) -> str:
        """Format C/C++ code using clang-format."""
        
        try:
            result = subprocess.run(
                command,
                input=code,
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                raise Exception(f"clang-format error: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            raise Exception("clang-format timed out")
    
    def _format_json(self, code: str) -> str:
        """Format JSON code using built-in JSON module."""
        
        try:
            import json
            # Parse and re-serialize with indentation
            parsed = json.loads(code)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON: {e}")
    
    def _fallback_format(self, code: str, language: str) -> Dict[str, Any]:
        """Fallback formatting using basic rules."""
        
        try:
            formatted_code = self._basic_format(code, language)
            changes_made = formatted_code != code
            
            return {
                'success': True,
                'formatted_code': formatted_code,
                'changes_made': changes_made,
                'formatter_used': 'basic',
                'message': f"Basic formatting applied (no {language} formatter available)"
            }
        
        except Exception as e:
            logger.error(f"Even fallback formatting failed: {e}")
            return {
                'success': False,
                'formatted_code': code,
                'changes_made': False,
                'formatter_used': 'none',
                'message': f"Formatting failed: {e}"
            }
    
    def _basic_format(self, code: str, language: str) -> str:
        """Apply basic formatting rules."""
        
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Language-specific indentation rules
            if language == 'python':
                # Decrease indent for dedent keywords
                if any(stripped.startswith(kw) for kw in ['except', 'elif', 'else', 'finally']):
                    current_indent = max(0, indent_level - 1)
                else:
                    current_indent = indent_level
                
                # Add indented line
                formatted_lines.append('    ' * current_indent + stripped)
                
                # Increase indent after colon
                if stripped.endswith(':'):
                    indent_level += 1
                # Decrease indent for dedent keywords
                elif any(stripped.startswith(kw) for kw in ['except', 'elif', 'else', 'finally']):
                    pass  # Already handled above
                # Handle return to previous level
                elif indent_level > 0 and not stripped.startswith(('    ', '\t')):
                    indent_level = max(0, indent_level - 1)
            
            elif language in ['javascript', 'typescript', 'java', 'cpp', 'c']:
                # C-style braces
                if stripped.endswith('{'):
                    formatted_lines.append('    ' * indent_level + stripped)
                    indent_level += 1
                elif stripped.startswith('}'):
                    indent_level = max(0, indent_level - 1)
                    formatted_lines.append('    ' * indent_level + stripped)
                else:
                    formatted_lines.append('    ' * indent_level + stripped)
            
            else:
                # Default: preserve original indentation but clean up
                formatted_lines.append(stripped)
        
        return '\n'.join(formatted_lines)
    
    def format_file(self, file_path: str, backup: bool = True) -> Dict[str, Any]:
        """
        Format a file in place.
        
        Args:
            file_path: Path to file to format
            backup: Whether to create backup before formatting
            
        Returns:
            Dictionary with formatting results
        """
        
        if not os.path.exists(file_path):
            return {
                'success': False,
                'message': f"File not found: {file_path}"
            }
        
        # Detect language from file extension
        file_ext = Path(file_path).suffix.lower()
        language = self._detect_language_from_extension(file_ext)
        
        if not language:
            return {
                'success': False,
                'message': f"Unsupported file type: {file_ext}"
            }
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Format code
            result = self.format_code(original_code, language)
            
            if not result['success']:
                return result
            
            # Check if changes were made
            if not result['changes_made']:
                return {
                    'success': True,
                    'message': f"File already properly formatted: {file_path}",
                    'changes_made': False
                }
            
            # Create backup if requested
            if backup:
                backup_path = f"{file_path}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_code)
            
            # Write formatted code
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result['formatted_code'])
            
            return {
                'success': True,
                'message': f"File formatted successfully: {file_path}",
                'changes_made': True,
                'formatter_used': result['formatter_used'],
                'backup_created': backup
            }
        
        except Exception as e:
            logger.error(f"Failed to format file {file_path}: {e}")
            return {
                'success': False,
                'message': f"Failed to format file: {e}"
            }
    
    def _detect_language_from_extension(self, extension: str) -> Optional[str]:
        """Detect language from file extension."""
        
        for language, config in self.formatters.items():
            if extension in config['extensions']:
                return language
        
        return None
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.formatters.keys())
    
    def get_available_formatters_info(self) -> Dict[str, Any]:
        """Get information about available formatters."""
        return {
            'supported_languages': list(self.formatters.keys()),
            'available_formatters': self.available_formatters,
            'total_supported': len(self.formatters),
            'total_available': len(self.available_formatters)
        }
    
    def validate_formatting(self, code: str, language: str) -> Dict[str, Any]:
        """
        Validate that code would format correctly without actually formatting.
        
        Args:
            code: Code to validate
            language: Programming language
            
        Returns:
            Dictionary with validation results
        """
        
        if language not in self.available_formatters:
            return {
                'valid': True,
                'message': f"No formatter available for {language}, assuming valid"
            }
        
        try:
            # Try to format the code
            result = self.format_code(code, language)
            
            return {
                'valid': result['success'],
                'message': result.get('message', 'Validation complete'),
                'formatter_used': result.get('formatter_used')
            }
        
        except Exception as e:
            return {
                'valid': False,
                'message': f"Validation failed: {e}"
            }

# Example usage and testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test code formatter
    formatter = CodeFormatter()
    
    print("🎨 Testing Code Formatter")
    print("=" * 40)
    
    # Test different languages
    test_cases = [
        ('python', '''
def hello(name):
if name:
print(f"Hello, {name}!")
else:
print("Hello, World!")
        '''),
        ('javascript', '''
function hello(name) {
if (name) {
console.log(`Hello, ${name}!`);
} else {
console.log("Hello, World!");
}
}
        '''),
        ('json', '''
{
"name": "test",
"value": 123,
"items": [
1,
2,
3
]
}
        ''')
    ]
    
    for language, code in test_cases:
        print(f"\n--- Testing {language.title()} ---")
        result = formatter.format_code(code.strip(), language)
        
        print(f"Success: {result['success']}")
        print(f"Formatter: {result.get('formatter_used', 'N/A')}")
        print(f"Changes made: {result.get('changes_made', False)}")
        
        if result['success'] and result.get('changes_made'):
            print("Formatted code:")
            print(result['formatted_code'][:200] + "..." if len(result['formatted_code']) > 200 else result['formatted_code'])
    
    # Show available formatters
    info = formatter.get_available_formatters_info()
    print(f"\n📋 Formatter Information:")
    print(f"Supported languages: {info['total_supported']}")
    print(f"Available formatters: {info['total_available']}")
    print(f"Available: {', '.join(info['available_formatters'].keys())}")