"""
Test Runner for Atlas Code V5

Multi-framework test execution with support for popular testing frameworks
and intelligent test discovery.
"""

import os
import subprocess
import tempfile
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TestFramework(Enum):
    """Supported test frameworks."""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    JEST = "jest"
    MOCHA = "mocha"
    JUNIT = "junit"
    GO_TEST = "go_test"
    CARGO_TEST = "cargo_test"
    MANUAL = "manual"

@dataclass
class TestResult:
    """Individual test result."""
    name: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float = 0.0
    message: str = ""
    output: str = ""
    file: str = ""
    line: int = 0

@dataclass
class TestSuiteResult:
    """Test suite execution result."""
    success: bool
    framework: TestFramework
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    output: str
    results: List[TestResult]
    message: str = ""

class TestRunner:
    """
    Multi-framework test runner with intelligent test discovery
    and execution capabilities.
    """
    
    def __init__(self):
        """Initialize test runner with framework support."""
        
        # Framework configurations
        self.frameworks = {
            TestFramework.PYTEST: {
                'command': ['python', '-m', 'pytest'],
                'discover_patterns': ['test_*.py', '*_test.py'],
                'parser': self._parse_pytest_output,
                'json_flag': '--json-report'
            },
            TestFramework.UNITTEST: {
                'command': ['python', '-m', 'unittest'],
                'discover_patterns': ['test_*.py', '*_test.py'],
                'parser': self._parse_unittest_output,
                'json_flag': None
            },
            TestFramework.JEST: {
                'command': ['npx', 'jest'],
                'discover_patterns': ['*.test.js', '*.spec.js', '__tests__/*.js'],
                'parser': self._parse_jest_output,
                'json_flag': '--json'
            },
            TestFramework.MOCHA: {
                'command': ['npx', 'mocha'],
                'discover_patterns': ['test/*.js', '*.test.js'],
                'parser': self._parse_mocha_output,
                'json_flag': '--reporter=json'
            },
            TestFramework.JUNIT: {
                'command': ['mvn', 'test'],
                'discover_patterns': ['*Test.java', '*Tests.java'],
                'parser': self._parse_junit_output,
                'json_flag': None
            },
            TestFramework.GO_TEST: {
                'command': ['go', 'test'],
                'discover_patterns': ['*_test.go'],
                'parser': self._parse_go_test_output,
                'json_flag': '-json'
            },
            TestFramework.CARGO_TEST: {
                'command': ['cargo', 'test'],
                'discover_patterns': ['tests/*.rs', 'src/**/test*.rs'],
                'parser': self._parse_cargo_test_output,
                'json_flag': '--message-format=json'
            }
        }
        
        # Check available frameworks
        self.available_frameworks = self._check_available_frameworks()
        
        logger.info(f"Test runner initialized with {len(self.available_frameworks)} available frameworks")
    
    def _check_available_frameworks(self) -> Dict[TestFramework, bool]:
        """Check which test frameworks are available."""
        available = {}
        
        for framework, config in self.frameworks.items():
            try:
                command = config['command'][0]
                result = subprocess.run(
                    ['which', command] if os.name != 'nt' else ['where', command],
                    capture_output=True,
                    timeout=5
                )
                available[framework] = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                available[framework] = False
        
        return available
    
    def detect_test_framework(self, directory: str) -> Optional[TestFramework]:
        """
        Auto-detect the appropriate test framework for a directory.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Detected TestFramework or None
        """
        
        try:
            # Check for framework-specific files
            if os.path.exists(os.path.join(directory, 'package.json')):
                with open(os.path.join(directory, 'package.json'), 'r') as f:
                    package_data = json.load(f)
                    
                # Check dependencies
                deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                
                if 'jest' in deps:
                    return TestFramework.JEST
                elif 'mocha' in deps:
                    return TestFramework.MOCHA
            
            # Check for Python frameworks
            if os.path.exists(os.path.join(directory, 'requirements.txt')):
                with open(os.path.join(directory, 'requirements.txt'), 'r') as f:
                    reqs = f.read().lower()
                    if 'pytest' in reqs:
                        return TestFramework.PYTEST
            
            if os.path.exists(os.path.join(directory, 'pyproject.toml')):
                return TestFramework.PYTEST
            
            # Check for other language frameworks
            if os.path.exists(os.path.join(directory, 'pom.xml')):
                return TestFramework.JUNIT
            
            if os.path.exists(os.path.join(directory, 'go.mod')):
                return TestFramework.GO_TEST
            
            if os.path.exists(os.path.join(directory, 'Cargo.toml')):
                return TestFramework.CARGO_TEST
            
            # Check for test files
            for framework, config in self.frameworks.items():
                for pattern in config['discover_patterns']:
                    import glob
                    matches = glob.glob(os.path.join(directory, '**', pattern), recursive=True)
                    if matches:
                        return framework
            
            # Default fallbacks
            if any(f.endswith('.py') for f in os.listdir(directory)):
                return TestFramework.UNITTEST
            
            return None
        
        except Exception as e:
            logger.warning(f"Failed to detect test framework: {e}")
            return None
    
    def run_tests(
        self,
        directory: str,
        framework: Optional[TestFramework] = None,
        test_pattern: Optional[str] = None,
        verbose: bool = False,
        timeout: int = 300
    ) -> TestSuiteResult:
        """
        Run tests in the specified directory.
        
        Args:
            directory: Directory containing tests
            framework: Test framework to use (auto-detect if None)
            test_pattern: Pattern to match test files
            verbose: Enable verbose output
            timeout: Test execution timeout in seconds
            
        Returns:
            TestSuiteResult with execution results
        """
        
        # Auto-detect framework if not specified
        if not framework:
            framework = self.detect_test_framework(directory)
            if not framework:
                return TestSuiteResult(
                    success=False,
                    framework=TestFramework.MANUAL,
                    total_tests=0,
                    passed=0,
                    failed=0,
                    skipped=0,
                    errors=0,
                    duration=0.0,
                    output="",
                    results=[],
                    message="No test framework detected"
                )
        
        # Check if framework is available
        if not self.available_frameworks.get(framework, False):
            return TestSuiteResult(
                success=False,
                framework=framework,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=0,
                duration=0.0,
                output="",
                results=[],
                message=f"Test framework {framework.value} not available"
            )
        
        try:
            # Prepare command
            config = self.frameworks[framework]
            command = config['command'].copy()
            
            # Add JSON output flag if supported
            if config['json_flag']:
                command.append(config['json_flag'])
            
            # Add verbose flag
            if verbose:
                if framework == TestFramework.PYTEST:
                    command.append('-v')
                elif framework == TestFramework.UNITTEST:
                    command.append('-v')
                elif framework in [TestFramework.JEST, TestFramework.MOCHA]:
                    command.append('--verbose')
            
            # Add test pattern if specified
            if test_pattern:
                if framework == TestFramework.PYTEST:
                    command.extend(['-k', test_pattern])
                elif framework == TestFramework.JEST:
                    command.extend(['--testNamePattern', test_pattern])
                elif framework == TestFramework.GO_TEST:
                    command.extend(['-run', test_pattern])
            
            # Add directory or discover tests
            if framework in [TestFramework.PYTEST, TestFramework.UNITTEST]:
                command.append(directory)
            elif framework == TestFramework.JEST:
                # Jest auto-discovers tests
                pass
            elif framework == TestFramework.GO_TEST:
                command.append('./...')
            
            logger.info(f"Running tests with command: {' '.join(command)}")
            
            # Execute tests
            import time
            start_time = time.time()
            
            result = subprocess.run(
                command,
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            # Parse output
            parser = config['parser']
            parsed_results = parser(result.stdout, result.stderr, result.returncode)
            
            return TestSuiteResult(
                success=result.returncode == 0,
                framework=framework,
                total_tests=parsed_results['total'],
                passed=parsed_results['passed'],
                failed=parsed_results['failed'],
                skipped=parsed_results['skipped'],
                errors=parsed_results['errors'],
                duration=duration,
                output=result.stdout + result.stderr,
                results=parsed_results['results'],
                message=f"Tests completed in {duration:.2f}s"
            )
        
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                success=False,
                framework=framework,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=0,
                duration=timeout,
                output="",
                results=[],
                message=f"Tests timed out after {timeout}s"
            )
        
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return TestSuiteResult(
                success=False,
                framework=framework,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=0,
                duration=0.0,
                output="",
                results=[],
                message=f"Test execution failed: {e}"
            )
    
    def run_test_code(
        self,
        test_code: str,
        language: str = "python",
        framework: Optional[TestFramework] = None
    ) -> TestSuiteResult:
        """
        Run test code directly without files.
        
        Args:
            test_code: Test code to execute
            language: Programming language
            framework: Test framework to use
            
        Returns:
            TestSuiteResult with execution results
        """
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Determine framework and file extension
                if not framework:
                    if language == "python":
                        framework = TestFramework.PYTEST if self.available_frameworks.get(TestFramework.PYTEST) else TestFramework.UNITTEST
                    elif language in ["javascript", "typescript"]:
                        framework = TestFramework.JEST if self.available_frameworks.get(TestFramework.JEST) else TestFramework.MOCHA
                    else:
                        framework = TestFramework.MANUAL
                
                # Create test file
                if language == "python":
                    file_ext = ".py"
                    filename = "test_temp.py"
                elif language in ["javascript", "typescript"]:
                    file_ext = ".js"
                    filename = "temp.test.js"
                else:
                    file_ext = ".txt"
                    filename = f"test_temp{file_ext}"
                
                test_file = os.path.join(temp_dir, filename)
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_code)
                
                # Run tests
                return self.run_tests(temp_dir, framework)
        
        except Exception as e:
            logger.error(f"Failed to run test code: {e}")
            return TestSuiteResult(
                success=False,
                framework=framework or TestFramework.MANUAL,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=0,
                duration=0.0,
                output="",
                results=[],
                message=f"Test execution failed: {e}"
            )
    
    # Output parsers for different frameworks
    def _parse_pytest_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse pytest output."""
        results = []
        stats = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0}
        
        # Look for JSON report first
        try:
            if 'json-report' in stdout:
                # Parse JSON report if available
                json_start = stdout.find('{')
                if json_start >= 0:
                    json_data = json.loads(stdout[json_start:])
                    stats['total'] = json_data.get('summary', {}).get('total', 0)
                    stats['passed'] = json_data.get('summary', {}).get('passed', 0)
                    stats['failed'] = json_data.get('summary', {}).get('failed', 0)
                    stats['skipped'] = json_data.get('summary', {}).get('skipped', 0)
                    
                    for test in json_data.get('tests', []):
                        results.append(TestResult(
                            name=test.get('nodeid', ''),
                            status=test.get('outcome', 'unknown'),
                            duration=test.get('duration', 0.0),
                            message=test.get('longrepr', ''),
                            file=test.get('file', ''),
                            line=test.get('line', 0)
                        ))
                    
                    return {'results': results, **stats}
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Fallback to text parsing
        lines = stdout.split('\n')
        for line in lines:
            if '::' in line and any(status in line for status in ['PASSED', 'FAILED', 'SKIPPED']):
                parts = line.split()
                if len(parts) >= 2:
                    test_name = parts[0]
                    status = parts[-1].lower()
                    
                    results.append(TestResult(
                        name=test_name,
                        status=status,
                        duration=0.0,
                        message=line
                    ))
                    
                    if status == 'passed':
                        stats['passed'] += 1
                    elif status == 'failed':
                        stats['failed'] += 1
                    elif status == 'skipped':
                        stats['skipped'] += 1
                    
                    stats['total'] += 1
        
        return {'results': results, **stats}
    
    def _parse_unittest_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse unittest output."""
        results = []
        stats = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0}
        
        # Parse unittest output
        output = stdout + stderr
        lines = output.split('\n')
        
        # Look for test results
        for line in lines:
            if line.startswith('test_') or ' ... ' in line:
                if 'ok' in line:
                    test_name = line.split(' ... ')[0].strip()
                    results.append(TestResult(
                        name=test_name,
                        status='passed',
                        message=line
                    ))
                    stats['passed'] += 1
                    stats['total'] += 1
                elif 'FAIL' in line or 'ERROR' in line:
                    test_name = line.split(' ... ')[0].strip()
                    status = 'failed' if 'FAIL' in line else 'error'
                    results.append(TestResult(
                        name=test_name,
                        status=status,
                        message=line
                    ))
                    if status == 'failed':
                        stats['failed'] += 1
                    else:
                        stats['errors'] += 1
                    stats['total'] += 1
        
        # Look for summary line
        for line in lines:
            if 'Ran ' in line and ' test' in line:
                match = re.search(r'Ran (\d+) test', line)
                if match:
                    stats['total'] = int(match.group(1))
                    # Adjust passed count
                    stats['passed'] = stats['total'] - stats['failed'] - stats['errors'] - stats['skipped']
                break
        
        return {'results': results, **stats}
    
    def _parse_jest_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse Jest JSON output."""
        results = []
        stats = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0}
        
        try:
            # Jest outputs JSON when --json flag is used
            json_data = json.loads(stdout)
            
            stats['total'] = json_data.get('numTotalTests', 0)
            stats['passed'] = json_data.get('numPassedTests', 0)
            stats['failed'] = json_data.get('numFailedTests', 0)
            stats['skipped'] = json_data.get('numPendingTests', 0)
            
            for test_result in json_data.get('testResults', []):
                for assertion in test_result.get('assertionResults', []):
                    results.append(TestResult(
                        name=assertion.get('ancestorTitles', [])[-1] if assertion.get('ancestorTitles') else assertion.get('title', ''),
                        status=assertion.get('status', 'unknown'),
                        duration=assertion.get('duration', 0.0) / 1000,  # Convert to seconds
                        message=assertion.get('failureMessages', [''])[0] if assertion.get('failureMessages') else '',
                        file=test_result.get('name', '')
                    ))
        
        except (json.JSONDecodeError, KeyError):
            # Fallback to text parsing
            lines = stdout.split('\n')
            for line in lines:
                if ' ✓ ' in line or ' ✗ ' in line:
                    status = 'passed' if ' ✓ ' in line else 'failed'
                    test_name = line.split(' ✓ ')[-1].split(' ✗ ')[-1].strip()
                    
                    results.append(TestResult(
                        name=test_name,
                        status=status,
                        message=line
                    ))
                    
                    if status == 'passed':
                        stats['passed'] += 1
                    else:
                        stats['failed'] += 1
                    stats['total'] += 1
        
        return {'results': results, **stats}
    
    def _parse_mocha_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse Mocha JSON output."""
        results = []
        stats = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0}
        
        try:
            json_data = json.loads(stdout)
            
            stats['total'] = len(json_data.get('tests', []))
            stats['passed'] = json_data.get('stats', {}).get('passes', 0)
            stats['failed'] = json_data.get('stats', {}).get('failures', 0)
            stats['skipped'] = json_data.get('stats', {}).get('pending', 0)
            
            for test in json_data.get('tests', []):
                results.append(TestResult(
                    name=test.get('title', ''),
                    status='passed' if test.get('pass') else 'failed' if test.get('err') else 'skipped',
                    duration=test.get('duration', 0.0) / 1000,
                    message=test.get('err', {}).get('message', '') if test.get('err') else '',
                    file=test.get('file', '')
                ))
        
        except (json.JSONDecodeError, KeyError):
            # Text parsing fallback
            pass
        
        return {'results': results, **stats}
    
    def _parse_junit_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse JUnit output."""
        # JUnit parsing would be more complex, involving XML reports
        results = []
        stats = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0}
        
        # Basic text parsing
        output = stdout + stderr
        if 'Tests run:' in output:
            match = re.search(r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)', output)
            if match:
                stats['total'] = int(match.group(1))
                stats['failed'] = int(match.group(2))
                stats['errors'] = int(match.group(3))
                stats['skipped'] = int(match.group(4))
                stats['passed'] = stats['total'] - stats['failed'] - stats['errors'] - stats['skipped']
        
        return {'results': results, **stats}
    
    def _parse_go_test_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse Go test output."""
        results = []
        stats = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0}
        
        # Parse go test output
        lines = stdout.split('\n')
        for line in lines:
            if line.startswith('--- PASS:') or line.startswith('--- FAIL:'):
                parts = line.split()
                if len(parts) >= 3:
                    status = 'passed' if 'PASS' in parts[1] else 'failed'
                    test_name = parts[2]
                    duration_str = parts[3] if len(parts) > 3 else '0.00s'
                    
                    try:
                        duration = float(duration_str.rstrip('s'))
                    except ValueError:
                        duration = 0.0
                    
                    results.append(TestResult(
                        name=test_name,
                        status=status,
                        duration=duration,
                        message=line
                    ))
                    
                    if status == 'passed':
                        stats['passed'] += 1
                    else:
                        stats['failed'] += 1
                    stats['total'] += 1
        
        return {'results': results, **stats}
    
    def _parse_cargo_test_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse Cargo test output."""
        results = []
        stats = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0}
        
        # Parse cargo test output
        lines = stdout.split('\n')
        for line in lines:
            if ' ... ok' in line or ' ... FAILED' in line:
                parts = line.split(' ... ')
                if len(parts) == 2:
                    test_name = parts[0].strip()
                    status = 'passed' if parts[1].strip() == 'ok' else 'failed'
                    
                    results.append(TestResult(
                        name=test_name,
                        status=status,
                        message=line
                    ))
                    
                    if status == 'passed':
                        stats['passed'] += 1
                    else:
                        stats['failed'] += 1
                    stats['total'] += 1
        
        # Look for summary
        for line in lines:
            if 'test result:' in line:
                # Extract numbers from summary
                match = re.search(r'(\d+) passed; (\d+) failed', line)
                if match:
                    stats['passed'] = int(match.group(1))
                    stats['failed'] = int(match.group(2))
                    stats['total'] = stats['passed'] + stats['failed']
                break
        
        return {'results': results, **stats}
    
    def get_available_frameworks(self) -> List[TestFramework]:
        """Get list of available test frameworks."""
        return [fw for fw, available in self.available_frameworks.items() if available]
    
    def generate_test_summary(self, result: TestSuiteResult) -> str:
        """Generate human-readable test summary."""
        if not result.success and result.message:
            return f"❌ {result.message}"
        
        if result.total_tests == 0:
            return "📝 No tests found or executed"
        
        status_icon = "✅" if result.success else "❌"
        
        summary_parts = [
            f"{status_icon} {result.passed}/{result.total_tests} tests passed"
        ]
        
        if result.failed > 0:
            summary_parts.append(f"{result.failed} failed")
        
        if result.skipped > 0:
            summary_parts.append(f"{result.skipped} skipped")
        
        if result.errors > 0:
            summary_parts.append(f"{result.errors} errors")
        
        summary = ", ".join(summary_parts)
        summary += f" in {result.duration:.2f}s"
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test runner
    test_runner = TestRunner()
    
    print("🧪 Testing Test Runner")
    print("=" * 40)
    
    # Show available frameworks
    available = test_runner.get_available_frameworks()
    print(f"Available frameworks: {[fw.value for fw in available]}")
    
    # Test with sample Python test code
    python_test_code = '''
import unittest

class TestMath(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(2 + 2, 4)
    
    def test_subtraction(self):
        self.assertEqual(5 - 3, 2)
    
    def test_multiplication(self):
        self.assertEqual(3 * 4, 12)
    
    def test_division(self):
        self.assertEqual(10 / 2, 5)
    
    def test_failing_test(self):
        self.assertEqual(1 + 1, 3)  # This will fail

if __name__ == '__main__':
    unittest.main()
    '''
    
    print("\n--- Testing Python Code ---")
    result = test_runner.run_test_code(python_test_code, "python")
    
    print(f"Framework: {result.framework.value}")
    print(f"Summary: {test_runner.generate_test_summary(result)}")
    
    if result.results:
        print("Test Results:")
        for test_result in result.results[:5]:  # Show first 5 results
            status_icon = "✅" if test_result.status == 'passed' else "❌"
            print(f"  {status_icon} {test_result.name}: {test_result.status}")
    
    # Test JavaScript code if Jest is available
    if TestFramework.JEST in available:
        js_test_code = '''
describe('Math operations', () => {
    test('addition', () => {
        expect(2 + 2).toBe(4);
    });
    
    test('subtraction', () => {
        expect(5 - 3).toBe(2);
    });
    
    test('failing test', () => {
        expect(1 + 1).toBe(3);  // This will fail
    });
});
        '''
        
        print("\n--- Testing JavaScript Code ---")
        js_result = test_runner.run_test_code(js_test_code, "javascript")
        print(f"Summary: {test_runner.generate_test_summary(js_result)}")
    
    print(f"\n📊 Test Runner Statistics:")
    print(f"Available frameworks: {len(available)}")
    print(f"Supported frameworks: {len(test_runner.frameworks)}")