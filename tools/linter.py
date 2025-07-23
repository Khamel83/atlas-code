"""
Code Linter for Atlas Code V5

Multi-language syntax validation and error detection with support
for popular linting tools and built-in basic validation.
"""

import os
import subprocess
import tempfile
import logging
import ast
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LintIssue:
    """Represents a linting issue."""
    line: int
    column: int
    message: str
    severity: str  # 'error', 'warning', 'info'
    rule: Optional[str] = None
    source: str = 'unknown'

class CodeLinter:
    """
    Multi-language code linter with syntax validation and error detection.
    """
    
    def __init__(self):
        """Initialize code linter with language support."""
        
        # Language-specific linter configurations
        self.linters = {
            'python': {
                'primary': {
                    'name': 'flake8',
                    'command': ['flake8', '--format=json', '--stdin-display-name=stdin', '-'],
                    'parser': self._parse_flake8_output
                },
                'fallback': {
                    'name': 'pyflakes',
                    'command': ['pyflakes'],
                    'parser': self._parse_pyflakes_output
                },
                'builtin': self._lint_python_builtin
            },
            'javascript': {
                'primary': {
                    'name': 'eslint',
                    'command': ['npx', 'eslint', '--format=json', '--stdin', '--stdin-filename=temp.js'],
                    'parser': self._parse_eslint_output
                },
                'fallback': {
                    'name': 'jshint',
                    'command': ['jshint', '--reporter=unix', '-'],
                    'parser': self._parse_jshint_output
                },
                'builtin': self._lint_javascript_builtin
            },
            'typescript': {
                'primary': {
                    'name': 'eslint',
                    'command': ['npx', 'eslint', '--format=json', '--stdin', '--stdin-filename=temp.ts'],
                    'parser': self._parse_eslint_output
                },
                'fallback': {
                    'name': 'tslint',
                    'command': ['tslint', '--format=json'],
                    'parser': self._parse_tslint_output
                },
                'builtin': self._lint_typescript_builtin
            },
            'java': {
                'primary': {
                    'name': 'checkstyle',
                    'command': ['java', '-jar', 'checkstyle.jar', '-f=json'],
                    'parser': self._parse_checkstyle_output
                },
                'builtin': self._lint_java_builtin
            },
            'cpp': {
                'primary': {
                    'name': 'cppcheck',
                    'command': ['cppcheck', '--enable=all', '--json', '-'],
                    'parser': self._parse_cppcheck_output
                },
                'builtin': self._lint_cpp_builtin
            },
            'go': {
                'primary': {
                    'name': 'golint',
                    'command': ['golint'],
                    'parser': self._parse_golint_output
                },
                'builtin': self._lint_go_builtin
            },
            'rust': {
                'primary': {
                    'name': 'clippy',
                    'command': ['cargo', 'clippy', '--message-format=json'],
                    'parser': self._parse_clippy_output
                },
                'builtin': self._lint_rust_builtin
            },
            'json': {
                'builtin': self._lint_json_builtin
            },
            'yaml': {
                'primary': {
                    'name': 'yamllint',
                    'command': ['yamllint', '--format=parsable', '-'],
                    'parser': self._parse_yamllint_output
                },
                'builtin': self._lint_yaml_builtin
            }
        }
        
        # Check available linters
        self.available_linters = self._check_available_linters()
        
        logger.info(f"Code linter initialized with {len(self.available_linters)} available linters")
    
    def _check_available_linters(self) -> Dict[str, Dict[str, Any]]:
        """Check which linters are available on the system."""
        available = {}
        
        for language, config in self.linters.items():
            linter_info = {'builtin': True}  # Always have builtin
            
            # Check primary linter
            if 'primary' in config:
                try:
                    primary_cmd = config['primary']['command'][0]
                    result = subprocess.run(
                        ['which', primary_cmd] if os.name != 'nt' else ['where', primary_cmd],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        linter_info['primary'] = config['primary']
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            # Check fallback linter
            if 'fallback' in config:
                try:
                    fallback_cmd = config['fallback']['command'][0]
                    result = subprocess.run(
                        ['which', fallback_cmd] if os.name != 'nt' else ['where', fallback_cmd],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        linter_info['fallback'] = config['fallback']
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            if linter_info:
                available[language] = linter_info
        
        return available
    
    def lint_code(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lint code and return issues found.
        
        Args:
            code: Code to lint
            language: Programming language
            filename: Optional filename for context
            
        Returns:
            Dictionary with linting results
        """
        
        if not code.strip():
            return {
                'success': True,
                'issues': [],
                'linter_used': 'none',
                'message': 'Empty code, no linting needed'
            }
        
        if language not in self.available_linters:
            return {
                'success': False,
                'issues': [],
                'linter_used': 'none',
                'message': f"No linter available for {language}"
            }
        
        linter_config = self.available_linters[language]
        issues = []
        linter_used = 'builtin'
        
        # Try primary linter first
        if 'primary' in linter_config:
            try:
                issues = self._run_external_linter(code, linter_config['primary'], filename)
                linter_used = linter_config['primary']['name']
            except Exception as e:
                logger.debug(f"Primary linter {linter_config['primary']['name']} failed: {e}")
                
                # Try fallback linter
                if 'fallback' in linter_config:
                    try:
                        issues = self._run_external_linter(code, linter_config['fallback'], filename)
                        linter_used = linter_config['fallback']['name']
                    except Exception as e2:
                        logger.debug(f"Fallback linter failed: {e2}")
                        issues = None
        
        # Use builtin linter if external linters failed
        if issues is None and 'builtin' in linter_config:
            try:
                builtin_func = self.linters[language]['builtin']
                issues = builtin_func(code, filename)
                linter_used = 'builtin'
            except Exception as e:
                logger.error(f"Builtin linter failed for {language}: {e}")
                return {
                    'success': False,
                    'issues': [],
                    'linter_used': 'none',
                    'message': f"All linters failed: {e}"
                }
        
        # Categorize issues by severity
        errors = [issue for issue in issues if issue.severity == 'error']
        warnings = [issue for issue in issues if issue.severity == 'warning']
        info = [issue for issue in issues if issue.severity == 'info']
        
        return {
            'success': True,
            'issues': issues,
            'linter_used': linter_used,
            'error_count': len(errors),
            'warning_count': len(warnings),
            'info_count': len(info),
            'message': f"Found {len(issues)} issues ({len(errors)} errors, {len(warnings)} warnings)"
        }
    
    def _run_external_linter(
        self,
        code: str,
        linter_config: Dict[str, Any],
        filename: Optional[str]
    ) -> List[LintIssue]:
        """Run external linter and parse output."""
        
        try:
            # Prepare command
            command = linter_config['command'].copy()
            
            # Some linters need the filename in the command
            if filename and '--stdin-filename' in ' '.join(command):
                # Replace temp filename with actual filename
                for i, arg in enumerate(command):
                    if arg.startswith('temp.'):
                        command[i] = filename
                        break
            
            # Run linter
            result = subprocess.run(
                command,
                input=code,
                text=True,
                capture_output=True,
                timeout=30
            )
            
            # Parse output using configured parser
            parser = linter_config['parser']
            issues = parser(result.stdout, result.stderr, result.returncode)
            
            return issues
        
        except subprocess.TimeoutExpired:
            raise Exception(f"Linter {linter_config['name']} timed out")
        except Exception as e:
            raise Exception(f"Failed to run {linter_config['name']}: {e}")
    
    # Built-in linters for basic validation
    def _lint_python_builtin(self, code: str, filename: Optional[str] = None) -> List[LintIssue]:
        """Built-in Python linter using AST parsing."""
        issues = []
        
        try:
            # Try to parse the code
            ast.parse(code)
        except SyntaxError as e:
            issues.append(LintIssue(
                line=e.lineno or 1,
                column=e.offset or 0,
                message=e.msg or "Syntax error",
                severity='error',
                rule='syntax',
                source='builtin'
            ))
        
        # Basic style checks
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 88:  # PEP 8 recommends 79, but 88 is more common now
                issues.append(LintIssue(
                    line=i,
                    column=89,
                    message="Line too long (>88 characters)",
                    severity='warning',
                    rule='line-length',
                    source='builtin'
                ))
            
            # Check for trailing whitespace
            if line.rstrip() != line:
                issues.append(LintIssue(
                    line=i,
                    column=len(line.rstrip()) + 1,
                    message="Trailing whitespace",
                    severity='info',
                    rule='trailing-whitespace',
                    source='builtin'
                ))
        
        return issues
    
    def _lint_javascript_builtin(self, code: str, filename: Optional[str] = None) -> List[LintIssue]:
        """Built-in JavaScript linter with basic checks."""
        issues = []
        
        # Basic syntax patterns that are likely issues
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for missing semicolons (simple heuristic)
            if (stripped and 
                not stripped.endswith((';', '{', '}', ':', ',')) and
                not stripped.startswith(('if', 'for', 'while', 'function', 'var', 'let', 'const', 'return', '}')) and
                not stripped.endswith(')') and
                '=' in stripped):
                issues.append(LintIssue(
                    line=i,
                    column=len(line),
                    message="Missing semicolon",
                    severity='warning',
                    rule='missing-semicolon',
                    source='builtin'
                ))
            
            # Check for == instead of ===
            if '==' in stripped and '===' not in stripped and '!=' in stripped:
                issues.append(LintIssue(
                    line=i,
                    column=stripped.find('==') + 1,
                    message="Use === instead of ==",
                    severity='warning',
                    rule='equality-operator',
                    source='builtin'
                ))
        
        return issues
    
    def _lint_typescript_builtin(self, code: str, filename: Optional[str] = None) -> List[LintIssue]:
        """Built-in TypeScript linter (similar to JavaScript)."""
        # Use JavaScript linter as base
        issues = self._lint_javascript_builtin(code, filename)
        
        # Additional TypeScript-specific checks
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for any type usage
            if ': any' in stripped:
                issues.append(LintIssue(
                    line=i,
                    column=stripped.find(': any') + 1,
                    message="Avoid using 'any' type",
                    severity='warning',
                    rule='no-any',
                    source='builtin'
                ))
        
        return issues
    
    def _lint_java_builtin(self, code: str, filename: Optional[str] = None) -> List[LintIssue]:
        """Built-in Java linter with basic checks."""
        issues = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for missing braces
            if (any(keyword in stripped for keyword in ['if ', 'for ', 'while ']) and
                ')' in stripped and '{' not in stripped and not stripped.endswith(';')):
                issues.append(LintIssue(
                    line=i,
                    column=len(line),
                    message="Consider using braces for single-statement blocks",
                    severity='info',
                    rule='missing-braces',
                    source='builtin'
                ))
        
        return issues
    
    def _lint_cpp_builtin(self, code: str, filename: Optional[str] = None) -> List[LintIssue]:
        """Built-in C++ linter with basic checks."""
        issues = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for missing includes
            if i == 1 and not stripped.startswith('#include') and 'cout' in code:
                issues.append(LintIssue(
                    line=1,
                    column=1,
                    message="Missing #include <iostream> for cout usage",
                    severity='warning',
                    rule='missing-include',
                    source='builtin'
                ))
        
        return issues
    
    def _lint_go_builtin(self, code: str, filename: Optional[str] = None) -> List[LintIssue]:
        """Built-in Go linter with basic checks."""
        issues = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for unused variables (simple heuristic)
            if stripped.startswith('var ') and ':=' not in stripped:
                var_name = stripped.split()[1]
                if var_name not in code[code.find(stripped) + len(stripped):]:
                    issues.append(LintIssue(
                        line=i,
                        column=1,
                        message=f"Variable '{var_name}' might be unused",
                        severity='info',
                        rule='unused-variable',
                        source='builtin'
                    ))
        
        return issues
    
    def _lint_rust_builtin(self, code: str, filename: Optional[str] = None) -> List[LintIssue]:
        """Built-in Rust linter with basic checks."""
        issues = []
        
        # Check for basic Rust syntax patterns
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for missing mut keyword
            if 'let ' in stripped and '=' in stripped and 'mut' not in stripped:
                var_name = stripped.split('let ')[1].split('=')[0].strip()
                # Simple check if variable might be modified later
                remaining_code = '\n'.join(lines[i:])
                if f'{var_name} =' in remaining_code:
                    issues.append(LintIssue(
                        line=i,
                        column=stripped.find('let') + 1,
                        message=f"Variable '{var_name}' might need 'mut' keyword",
                        severity='info',
                        rule='missing-mut',
                        source='builtin'
                    ))
        
        return issues
    
    def _lint_json_builtin(self, code: str, filename: Optional[str] = None) -> List[LintIssue]:
        """Built-in JSON linter."""
        issues = []
        
        try:
            json.loads(code)
        except json.JSONDecodeError as e:
            issues.append(LintIssue(
                line=e.lineno,
                column=e.colno,
                message=e.msg,
                severity='error',
                rule='json-syntax',
                source='builtin'
            ))
        
        return issues
    
    def _lint_yaml_builtin(self, code: str, filename: Optional[str] = None) -> List[LintIssue]:
        """Built-in YAML linter."""
        issues = []
        
        try:
            import yaml
            yaml.safe_load(code)
        except yaml.YAMLError as e:
            # Extract line and column if available
            line = getattr(e, 'problem_mark', None)
            issues.append(LintIssue(
                line=line.line + 1 if line else 1,
                column=line.column + 1 if line else 0,
                message=str(e),
                severity='error',
                rule='yaml-syntax',
                source='builtin'
            ))
        except ImportError:
            issues.append(LintIssue(
                line=1,
                column=1,
                message="PyYAML not available for YAML validation",
                severity='info',
                rule='missing-dependency',
                source='builtin'
            ))
        
        return issues
    
    # Output parsers for external linters
    def _parse_flake8_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse flake8 JSON output."""
        issues = []
        
        if not stdout.strip():
            return issues
        
        try:
            # Flake8 with --format=json should output JSON
            data = json.loads(stdout)
            for file_issues in data.values():
                for issue in file_issues:
                    issues.append(LintIssue(
                        line=issue['line_number'],
                        column=issue['column_number'],
                        message=issue['text'],
                        severity='error' if issue['code'].startswith('E') else 'warning',
                        rule=issue['code'],
                        source='flake8'
                    ))
        except json.JSONDecodeError:
            # Fallback to parsing text output
            for line in stdout.split('\n'):
                if ':' in line and 'error' in line.lower():
                    parts = line.split(':')
                    if len(parts) >= 4:
                        try:
                            line_num = int(parts[1])
                            col_num = int(parts[2])
                            message = ':'.join(parts[3:]).strip()
                            issues.append(LintIssue(
                                line=line_num,
                                column=col_num,
                                message=message,
                                severity='error',
                                rule='unknown',
                                source='flake8'
                            ))
                        except ValueError:
                            continue
        
        return issues
    
    def _parse_pyflakes_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse pyflakes output."""
        issues = []
        
        for line in stdout.split('\n'):
            if ':' in line:
                try:
                    parts = line.split(':')
                    line_num = int(parts[1])
                    message = ':'.join(parts[2:]).strip()
                    issues.append(LintIssue(
                        line=line_num,
                        column=0,
                        message=message,
                        severity='error',
                        rule='pyflakes',
                        source='pyflakes'
                    ))
                except (ValueError, IndexError):
                    continue
        
        return issues
    
    def _parse_eslint_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse ESLint JSON output."""
        issues = []
        
        try:
            data = json.loads(stdout)
            for file_result in data:
                for message in file_result.get('messages', []):
                    severity = 'error' if message['severity'] == 2 else 'warning'
                    issues.append(LintIssue(
                        line=message['line'],
                        column=message['column'],
                        message=message['message'],
                        severity=severity,
                        rule=message.get('ruleId'),
                        source='eslint'
                    ))
        except json.JSONDecodeError:
            # Fallback parsing
            pass
        
        return issues
    
    def _parse_jshint_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse JSHint output."""
        issues = []
        
        for line in stdout.split('\n'):
            if ' line ' in line and ', col ' in line:
                try:
                    # Parse JSHint format: "filename: line X, col Y, message"
                    parts = line.split(': line ')
                    if len(parts) >= 2:
                        rest = parts[1]
                        line_col = rest.split(', col ')
                        if len(line_col) >= 2:
                            line_num = int(line_col[0])
                            col_message = line_col[1].split(', ')
                            col_num = int(col_message[0])
                            message = ', '.join(col_message[1:])
                            
                            issues.append(LintIssue(
                                line=line_num,
                                column=col_num,
                                message=message,
                                severity='warning',
                                rule='jshint',
                                source='jshint'
                            ))
                except (ValueError, IndexError):
                    continue
        
        return issues
    
    def _parse_tslint_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse TSLint JSON output."""
        issues = []
        
        try:
            data = json.loads(stdout)
            for issue in data:
                issues.append(LintIssue(
                    line=issue['startPosition']['line'] + 1,
                    column=issue['startPosition']['character'] + 1,
                    message=issue['failure'],
                    severity='warning',
                    rule=issue['ruleName'],
                    source='tslint'
                ))
        except (json.JSONDecodeError, KeyError):
            pass
        
        return issues
    
    def _parse_checkstyle_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse Checkstyle JSON output."""
        # Checkstyle implementation would go here
        return []
    
    def _parse_cppcheck_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse cppcheck JSON output."""
        # Cppcheck implementation would go here
        return []
    
    def _parse_golint_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse golint output."""
        issues = []
        
        for line in stdout.split('\n'):
            if ':' in line:
                try:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        line_num = int(parts[1])
                        message = ':'.join(parts[2:]).strip()
                        issues.append(LintIssue(
                            line=line_num,
                            column=0,
                            message=message,
                            severity='warning',
                            rule='golint',
                            source='golint'
                        ))
                except (ValueError, IndexError):
                    continue
        
        return issues
    
    def _parse_clippy_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse Clippy JSON output."""
        # Clippy implementation would go here
        return []
    
    def _parse_yamllint_output(self, stdout: str, stderr: str, returncode: int) -> List[LintIssue]:
        """Parse yamllint output."""
        issues = []
        
        for line in stdout.split('\n'):
            if ':' in line:
                try:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        line_num = int(parts[1])
                        col_num = int(parts[2])
                        severity_message = parts[3].strip()
                        
                        if severity_message.startswith('[error]'):
                            severity = 'error'
                            message = severity_message[7:].strip()
                        elif severity_message.startswith('[warning]'):
                            severity = 'warning'
                            message = severity_message[9:].strip()
                        else:
                            severity = 'info'
                            message = severity_message
                        
                        issues.append(LintIssue(
                            line=line_num,
                            column=col_num,
                            message=message,
                            severity=severity,
                            rule='yamllint',
                            source='yamllint'
                        ))
                except (ValueError, IndexError):
                    continue
        
        return issues
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.linters.keys())
    
    def get_available_linters_info(self) -> Dict[str, Any]:
        """Get information about available linters."""
        return {
            'supported_languages': list(self.linters.keys()),
            'available_linters': self.available_linters,
            'total_supported': len(self.linters),
            'total_available': len(self.available_linters)
        }

# Example usage and testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test code linter
    linter = CodeLinter()
    
    print("🔍 Testing Code Linter")
    print("=" * 40)
    
    # Test different languages
    test_cases = [
        ('python', '''
def hello(name):
if name:
print(f"Hello, {name}!")
else:
print("Hello, World!")
x = 1    
        '''),
        ('javascript', '''
function hello(name) {
if (name) {
console.log("Hello, " + name + "!")
} else {
console.log("Hello, World!")
}
        '''),
        ('json', '''
{
"name": "test",
"value": 123,
"items": [
1,
2,
3,
}
        ''')
    ]
    
    for language, code in test_cases:
        print(f"\n--- Testing {language.title()} ---")
        result = linter.lint_code(code.strip(), language)
        
        print(f"Success: {result['success']}")
        print(f"Linter: {result.get('linter_used', 'N/A')}")
        print(f"Issues: {len(result.get('issues', []))}")
        print(f"Errors: {result.get('error_count', 0)}")
        print(f"Warnings: {result.get('warning_count', 0)}")
        
        # Show first few issues
        for issue in result.get('issues', [])[:3]:
            print(f"  Line {issue.line}: {issue.message} ({issue.severity})")
    
    # Show available linters
    info = linter.get_available_linters_info()
    print(f"\n📋 Linter Information:")
    print(f"Supported languages: {info['total_supported']}")
    print(f"Available linters: {info['total_available']}")
    print(f"Available: {', '.join(info['available_linters'].keys())}")