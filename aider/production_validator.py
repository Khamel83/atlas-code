import os
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

from .handover_manager import HandoverManager


@dataclass
class ProductionCheck:
    """Individual production readiness check"""
    name: str
    status: str  # "pass", "fail", "warning", "skip"
    message: str
    details: Optional[Dict[str, Any]] = None
    fix_suggestion: Optional[str] = None


@dataclass
class ProductionValidationResult:
    """Complete production validation results"""
    overall_status: str  # "ready", "warnings", "not_ready"
    readiness_score: float  # 0.0 to 1.0
    checks: List[ProductionCheck]
    summary: Dict[str, int]  # counts by status
    deployment_blockers: List[str]
    recommended_actions: List[str]


class ProductionReadinessValidator:
    """Validates code and project for production deployment"""
    
    def __init__(self, io=None, root_path=None):
        self.io = io
        self.root_path = root_path or os.getcwd()
        self.checks = []
        
    def validate_project(self, coder=None) -> ProductionValidationResult:
        """Perform comprehensive production readiness validation"""
        
        self.checks = []
        
        # Core validation checks
        self._check_git_status()
        self._check_dependencies()
        self._check_code_quality()
        self._check_testing()
        self._check_security()
        self._check_documentation()
        self._check_configuration()
        self._check_deployment_readiness()
        
        # Calculate overall results
        result = self._calculate_results()
        
        if self.io:
            self._report_results(result)
        
        return result
    
    def _check_git_status(self):
        """Check git repository status"""
        
        try:
            # Check if in git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.checks.append(ProductionCheck(
                    name="Git Repository",
                    status="warning",
                    message="Not in a git repository",
                    fix_suggestion="Initialize git repository: git init"
                ))
                return
            
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                uncommitted_files = len(result.stdout.strip().split('\n'))
                self.checks.append(ProductionCheck(
                    name="Git Status",
                    status="warning",
                    message=f"{uncommitted_files} uncommitted changes",
                    details={"uncommitted_files": uncommitted_files},
                    fix_suggestion="Commit or stash changes before deployment"
                ))
            else:
                self.checks.append(ProductionCheck(
                    name="Git Status",
                    status="pass",
                    message="Repository is clean"
                ))
            
            # Check for remote repository
            result = subprocess.run(
                ["git", "remote", "-v"],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                self.checks.append(ProductionCheck(
                    name="Git Remote",
                    status="warning",
                    message="No remote repository configured",
                    fix_suggestion="Add remote: git remote add origin <url>"
                ))
            else:
                self.checks.append(ProductionCheck(
                    name="Git Remote",
                    status="pass",
                    message="Remote repository configured"
                ))
                
        except FileNotFoundError:
            self.checks.append(ProductionCheck(
                name="Git",
                status="fail",
                message="Git is not installed",
                fix_suggestion="Install git"
            ))
    
    def _check_dependencies(self):
        """Check dependency management"""
        
        # Check for requirements.txt (Python)
        req_file = Path(self.root_path) / "requirements.txt"
        if req_file.exists():
            self.checks.append(ProductionCheck(
                name="Python Dependencies",
                status="pass",
                message="requirements.txt found"
            ))
            
            # Check for pinned versions
            try:
                with open(req_file, 'r') as f:
                    content = f.read()
                    lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                    unpinned = [line for line in lines if '==' not in line and '>=' not in line and '~=' not in line]
                    
                    if unpinned:
                        self.checks.append(ProductionCheck(
                            name="Dependency Pinning",
                            status="warning",
                            message=f"{len(unpinned)} dependencies not pinned",
                            details={"unpinned_deps": unpinned[:5]},
                            fix_suggestion="Pin dependency versions for reproducible builds"
                        ))
                    else:
                        self.checks.append(ProductionCheck(
                            name="Dependency Pinning",
                            status="pass",
                            message="All dependencies pinned"
                        ))
            except Exception as e:
                self.checks.append(ProductionCheck(
                    name="Dependency Analysis",
                    status="warning",
                    message=f"Could not analyze requirements.txt: {e}"
                ))
        
        # Check for package.json (Node.js)
        package_file = Path(self.root_path) / "package.json"
        if package_file.exists():
            self.checks.append(ProductionCheck(
                name="Node.js Dependencies",
                status="pass",
                message="package.json found"
            ))
            
            # Check for lock file
            lock_files = [
                Path(self.root_path) / "package-lock.json",
                Path(self.root_path) / "yarn.lock",
                Path(self.root_path) / "pnpm-lock.yaml"
            ]
            
            if any(lock_file.exists() for lock_file in lock_files):
                self.checks.append(ProductionCheck(
                    name="Dependency Lock",
                    status="pass",
                    message="Lock file found"
                ))
            else:
                self.checks.append(ProductionCheck(
                    name="Dependency Lock",
                    status="warning",
                    message="No lock file found",
                    fix_suggestion="Generate lock file: npm install or yarn install"
                ))
        
        # Check if no dependency management found
        if not req_file.exists() and not package_file.exists():
            other_dep_files = [
                "Pipfile", "pyproject.toml", "setup.py", "setup.cfg",
                "Cargo.toml", "go.mod", "composer.json", "pom.xml"
            ]
            
            found_deps = [f for f in other_dep_files if Path(self.root_path, f).exists()]
            
            if found_deps:
                self.checks.append(ProductionCheck(
                    name="Dependencies",
                    status="pass",
                    message=f"Dependency management found: {', '.join(found_deps)}"
                ))
            else:
                self.checks.append(ProductionCheck(
                    name="Dependencies",
                    status="warning",
                    message="No dependency management files found",
                    fix_suggestion="Add appropriate dependency management (requirements.txt, package.json, etc.)"
                ))
    
    def _check_code_quality(self):
        """Check code quality and linting"""
        
        # Check for Python code quality
        python_files = list(Path(self.root_path).rglob("*.py"))
        if python_files:
            # Check for common linting configs
            lint_configs = [
                ".flake8", "setup.cfg", "tox.ini", "pyproject.toml",
                ".pylintrc", ".black", ".isort.cfg"
            ]
            
            found_configs = [c for c in lint_configs if Path(self.root_path, c).exists()]
            
            if found_configs:
                self.checks.append(ProductionCheck(
                    name="Python Linting Config",
                    status="pass",
                    message=f"Linting configuration found: {', '.join(found_configs)}"
                ))
            else:
                self.checks.append(ProductionCheck(
                    name="Python Linting Config",
                    status="warning",
                    message="No linting configuration found",
                    fix_suggestion="Add linting config (.flake8, pyproject.toml, etc.)"
                ))
            
            # Try to run basic linting
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "flake8", "--version"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Run flake8 on a sample of files
                    sample_files = python_files[:5]
                    result = subprocess.run(
                        [sys.executable, "-m", "flake8"] + [str(f) for f in sample_files],
                        cwd=self.root_path,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        self.checks.append(ProductionCheck(
                            name="Code Quality",
                            status="pass",
                            message="Sample files pass linting"
                        ))
                    else:
                        issues = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                        self.checks.append(ProductionCheck(
                            name="Code Quality",
                            status="warning",
                            message=f"Linting issues found in sample files",
                            details={"issues_count": issues},
                            fix_suggestion="Run linter and fix issues"
                        ))
                        
            except FileNotFoundError:
                self.checks.append(ProductionCheck(
                    name="Code Quality Tools",
                    status="warning",
                    message="No linting tools available",
                    fix_suggestion="Install linting tools (flake8, pylint, black, etc.)"
                ))
    
    def _check_testing(self):
        """Check testing setup and coverage"""
        
        # Look for test directories and files
        test_patterns = [
            "test_*.py", "*_test.py", "tests/", "test/",
            "*.test.js", "*.spec.js", "__tests__/",
            "*_test.go", "*_test.rs"
        ]
        
        test_files = []
        for pattern in test_patterns:
            if "/" in pattern:
                # Directory pattern
                test_dir = Path(self.root_path) / pattern.rstrip("/")
                if test_dir.exists() and test_dir.is_dir():
                    test_files.extend(list(test_dir.rglob("*")))
            else:
                # File pattern
                test_files.extend(list(Path(self.root_path).rglob(pattern)))
        
        if test_files:
            self.checks.append(ProductionCheck(
                name="Test Files",
                status="pass",
                message=f"Found {len(test_files)} test files"
            ))
            
            # Check for test configuration
            test_configs = [
                "pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml",
                "jest.config.js", "karma.conf.js", "mocha.opts"
            ]
            
            found_test_configs = [c for c in test_configs if Path(self.root_path, c).exists()]
            
            if found_test_configs:
                self.checks.append(ProductionCheck(
                    name="Test Configuration",
                    status="pass",
                    message=f"Test config found: {', '.join(found_test_configs)}"
                ))
            else:
                self.checks.append(ProductionCheck(
                    name="Test Configuration",
                    status="warning",
                    message="No test configuration found",
                    fix_suggestion="Add test configuration (pytest.ini, jest.config.js, etc.)"
                ))
        else:
            self.checks.append(ProductionCheck(
                name="Testing",
                status="warning",
                message="No test files found",
                fix_suggestion="Add tests for your code"
            ))
    
    def _check_security(self):
        """Check for security considerations"""
        
        # Check for secrets in common files
        sensitive_patterns = [
            "api_key", "secret", "password", "token", "private_key",
            "aws_access", "database_url", "jwt_secret"
        ]
        
        # Check environment files
        env_files = [".env", ".env.local", ".env.production"]
        exposed_secrets = []
        
        for env_file in env_files:
            env_path = Path(self.root_path) / env_file
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        content = f.read().lower()
                        for pattern in sensitive_patterns:
                            if pattern in content and "=" in content:
                                exposed_secrets.append(f"{env_file}:{pattern}")
                except Exception:
                    pass
        
        if exposed_secrets:
            self.checks.append(ProductionCheck(
                name="Environment Security",
                status="warning",
                message=f"Potential secrets in environment files",
                details={"exposed_patterns": exposed_secrets[:5]},
                fix_suggestion="Use environment variables or secure secret management"
            ))
        else:
            self.checks.append(ProductionCheck(
                name="Environment Security",
                status="pass",
                message="No obvious secrets in environment files"
            ))
        
        # Check for .gitignore
        gitignore_path = Path(self.root_path) / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r') as f:
                    gitignore_content = f.read()
                    
                important_ignores = [".env", "*.key", "*.pem", "config/secrets"]
                missing_ignores = [ig for ig in important_ignores if ig not in gitignore_content]
                
                if missing_ignores:
                    self.checks.append(ProductionCheck(
                        name="Gitignore Security",
                        status="warning",
                        message=f"Missing important ignores: {', '.join(missing_ignores)}",
                        fix_suggestion="Add sensitive file patterns to .gitignore"
                    ))
                else:
                    self.checks.append(ProductionCheck(
                        name="Gitignore Security",
                        status="pass",
                        message="Important file types are ignored"
                    ))
            except Exception:
                self.checks.append(ProductionCheck(
                    name="Gitignore Security",
                    status="warning",
                    message="Could not analyze .gitignore"
                ))
        else:
            self.checks.append(ProductionCheck(
                name="Gitignore",
                status="warning",
                message="No .gitignore file found",
                fix_suggestion="Add .gitignore file to exclude sensitive files"
            ))
    
    def _check_documentation(self):
        """Check documentation completeness"""
        
        # Check for README
        readme_files = ["README.md", "README.txt", "README.rst", "README"]
        found_readme = None
        
        for readme in readme_files:
            if Path(self.root_path, readme).exists():
                found_readme = readme
                break
        
        if found_readme:
            # Check README content
            try:
                with open(Path(self.root_path, found_readme), 'r') as f:
                    content = f.read()
                    
                important_sections = [
                    "install", "usage", "deploy", "config", "requirement"
                ]
                
                found_sections = sum(1 for section in important_sections if section in content.lower())
                
                if found_sections >= 3:
                    self.checks.append(ProductionCheck(
                        name="Documentation",
                        status="pass",
                        message=f"Comprehensive README found ({found_readme})"
                    ))
                else:
                    self.checks.append(ProductionCheck(
                        name="Documentation",
                        status="warning",
                        message=f"README exists but may lack important sections",
                        fix_suggestion="Add installation, usage, and deployment instructions"
                    ))
            except Exception:
                self.checks.append(ProductionCheck(
                    name="Documentation",
                    status="warning",
                    message=f"README found but could not analyze content"
                ))
        else:
            self.checks.append(ProductionCheck(
                name="Documentation",
                status="warning",
                message="No README file found",
                fix_suggestion="Add README.md with project description and instructions"
            ))
    
    def _check_configuration(self):
        """Check configuration management"""
        
        # Check for environment-specific configs
        config_patterns = [
            "config/", "configs/", "settings/",
            "docker-compose.yml", "Dockerfile",
            ".env.example", "config.example.json"
        ]
        
        found_configs = []
        for pattern in config_patterns:
            if "/" in pattern:
                config_path = Path(self.root_path) / pattern.rstrip("/")
                if config_path.exists():
                    found_configs.append(pattern)
            else:
                if Path(self.root_path, pattern).exists():
                    found_configs.append(pattern)
        
        if found_configs:
            self.checks.append(ProductionCheck(
                name="Configuration",
                status="pass",
                message=f"Configuration files found: {', '.join(found_configs)}"
            ))
        else:
            self.checks.append(ProductionCheck(
                name="Configuration",
                status="warning",
                message="No configuration management found",
                fix_suggestion="Add configuration files for different environments"
            ))
    
    def _check_deployment_readiness(self):
        """Check deployment-specific requirements"""
        
        # Check for containerization
        docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]
        found_docker = [f for f in docker_files if Path(self.root_path, f).exists()]
        
        if found_docker:
            self.checks.append(ProductionCheck(
                name="Containerization",
                status="pass",
                message=f"Docker files found: {', '.join(found_docker)}"
            ))
        else:
            self.checks.append(ProductionCheck(
                name="Containerization",
                status="warning",
                message="No Docker configuration found",
                fix_suggestion="Consider adding Dockerfile for consistent deployments"
            ))
        
        # Check for CI/CD
        ci_dirs = [".github/workflows", ".gitlab-ci.yml", ".circleci", "buildspec.yml"]
        found_ci = []
        
        for ci in ci_dirs:
            if "/" in ci:
                if Path(self.root_path, ci).exists():
                    found_ci.append(ci)
            else:
                if Path(self.root_path, ci).exists():
                    found_ci.append(ci)
        
        if found_ci:
            self.checks.append(ProductionCheck(
                name="CI/CD",
                status="pass",
                message=f"CI/CD configuration found: {', '.join(found_ci)}"
            ))
        else:
            self.checks.append(ProductionCheck(
                name="CI/CD",
                status="warning",
                message="No CI/CD configuration found",
                fix_suggestion="Add CI/CD pipeline for automated testing and deployment"
            ))
    
    def _calculate_results(self) -> ProductionValidationResult:
        """Calculate overall validation results"""
        
        # Count checks by status
        summary = {
            "pass": sum(1 for c in self.checks if c.status == "pass"),
            "warning": sum(1 for c in self.checks if c.status == "warning"),
            "fail": sum(1 for c in self.checks if c.status == "fail"),
            "skip": sum(1 for c in self.checks if c.status == "skip")
        }
        
        # Calculate readiness score
        total_checks = len(self.checks)
        if total_checks == 0:
            readiness_score = 0.0
        else:
            pass_score = summary["pass"] * 1.0
            warning_score = summary["warning"] * 0.5
            fail_score = summary["fail"] * 0.0
            readiness_score = (pass_score + warning_score + fail_score) / total_checks
        
        # Determine overall status
        if summary["fail"] > 0:
            overall_status = "not_ready"
        elif summary["warning"] > 0:
            overall_status = "warnings"
        else:
            overall_status = "ready"
        
        # Collect deployment blockers
        deployment_blockers = [
            c.message for c in self.checks 
            if c.status == "fail"
        ]
        
        # Generate recommended actions
        recommended_actions = []
        high_priority_warnings = [c for c in self.checks if c.status == "warning" and c.fix_suggestion]
        
        for check in high_priority_warnings[:5]:  # Top 5 recommendations
            if check.fix_suggestion:
                recommended_actions.append(f"{check.name}: {check.fix_suggestion}")
        
        return ProductionValidationResult(
            overall_status=overall_status,
            readiness_score=readiness_score,
            checks=self.checks,
            summary=summary,
            deployment_blockers=deployment_blockers,
            recommended_actions=recommended_actions
        )
    
    def _report_results(self, result: ProductionValidationResult):
        """Report validation results to user"""
        
        if not self.io:
            return
        
        # Overall summary
        self.io.tool_output(f"\n=== Production Readiness Validation ===")
        self.io.tool_output(f"Overall Status: {result.overall_status.upper()}")
        self.io.tool_output(f"Readiness Score: {result.readiness_score:.1%}")
        
        # Status summary
        self.io.tool_output(f"\nChecks Summary:")
        self.io.tool_output(f"  ✅ Pass: {result.summary['pass']}")
        self.io.tool_output(f"  ⚠️  Warning: {result.summary['warning']}")
        self.io.tool_output(f"  ❌ Fail: {result.summary['fail']}")
        
        # Deployment blockers
        if result.deployment_blockers:
            self.io.tool_output(f"\n❌ Deployment Blockers:")
            for blocker in result.deployment_blockers:
                self.io.tool_output(f"  - {blocker}")
        
        # Recommendations
        if result.recommended_actions:
            self.io.tool_output(f"\n📝 Recommended Actions:")
            for action in result.recommended_actions:
                self.io.tool_output(f"  - {action}")
        
        # Detailed results (only failures and warnings)
        important_checks = [c for c in result.checks if c.status in ["fail", "warning"]]
        if important_checks:
            self.io.tool_output(f"\n📋 Detailed Results:")
            for check in important_checks:
                status_icon = "❌" if check.status == "fail" else "⚠️"
                self.io.tool_output(f"  {status_icon} {check.name}: {check.message}")
                if check.fix_suggestion:
                    self.io.tool_output(f"     💡 {check.fix_suggestion}")
    
    def export_results(self, result: ProductionValidationResult, format="json") -> str:
        """Export validation results in specified format"""
        
        if format == "json":
            return json.dumps(asdict(result), indent=2)
        elif format == "markdown":
            return self._format_markdown_report(result)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _format_markdown_report(self, result: ProductionValidationResult) -> str:
        """Format results as markdown report"""
        
        md = f"""# Production Readiness Report

## Summary
- **Overall Status:** {result.overall_status.upper()}
- **Readiness Score:** {result.readiness_score:.1%}
- **Generated:** {Path.cwd()}

## Checks Summary
- ✅ **Pass:** {result.summary['pass']}
- ⚠️ **Warning:** {result.summary['warning']}  
- ❌ **Fail:** {result.summary['fail']}

"""
        
        if result.deployment_blockers:
            md += "## 🚫 Deployment Blockers\n\n"
            for blocker in result.deployment_blockers:
                md += f"- {blocker}\n"
            md += "\n"
        
        if result.recommended_actions:
            md += "## 📝 Recommended Actions\n\n"
            for action in result.recommended_actions:
                md += f"- {action}\n"
            md += "\n"
        
        md += "## 📋 Detailed Results\n\n"
        for check in result.checks:
            icon = {"pass": "✅", "warning": "⚠️", "fail": "❌", "skip": "⏭️"}[check.status]
            md += f"### {icon} {check.name}\n"
            md += f"**Status:** {check.status.upper()}\n"
            md += f"**Message:** {check.message}\n"
            
            if check.fix_suggestion:
                md += f"**Fix:** {check.fix_suggestion}\n"
            
            if check.details:
                md += f"**Details:** {json.dumps(check.details, indent=2)}\n"
            
            md += "\n"
        
        return md