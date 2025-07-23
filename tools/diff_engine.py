"""
Diff Engine for Atlas Code V5

Unified diff generation, patching, and intelligent code comparison
with support for multiple diff formats and visualization.
"""

import difflib
import logging
import re
from typing import List, Optional, Dict, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DiffFormat(Enum):
    """Supported diff formats."""
    UNIFIED = "unified"
    CONTEXT = "context"
    SIDE_BY_SIDE = "side_by_side"
    MINIMAL = "minimal"
    MARKDOWN = "markdown"

@dataclass
class DiffHunk:
    """Represents a single diff hunk."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]
    context: str = ""

@dataclass
class DiffResult:
    """Result of diff operation."""
    success: bool
    diff_text: str
    hunks: List[DiffHunk]
    stats: Dict[str, int]
    format: DiffFormat
    message: str = ""

class DiffEngine:
    """
    Unified diff generation and patching engine with support for
    multiple formats and intelligent code comparison.
    """
    
    def __init__(self):
        """Initialize diff engine."""
        self.diff_context_lines = 3
        self.max_diff_size = 100000  # Maximum diff size in characters
        
        logger.info("Diff engine initialized")
    
    def generate_diff(
        self,
        original: str,
        modified: str,
        original_name: str = "original",
        modified_name: str = "modified",
        format_type: DiffFormat = DiffFormat.UNIFIED,
        context_lines: Optional[int] = None
    ) -> DiffResult:
        """
        Generate diff between two text strings.
        
        Args:
            original: Original text content
            modified: Modified text content
            original_name: Name for original file in diff
            modified_name: Name for modified file in diff
            format_type: Diff format to generate
            context_lines: Number of context lines (defaults to 3)
            
        Returns:
            DiffResult with generated diff and metadata
        """
        
        if context_lines is None:
            context_lines = self.diff_context_lines
        
        try:
            # Split into lines for difflib
            original_lines = original.splitlines(keepends=True)
            modified_lines = modified.splitlines(keepends=True)
            
            # Generate appropriate diff format
            if format_type == DiffFormat.UNIFIED:
                diff_text, hunks = self._generate_unified_diff(
                    original_lines, modified_lines, original_name, modified_name, context_lines
                )
            elif format_type == DiffFormat.CONTEXT:
                diff_text, hunks = self._generate_context_diff(
                    original_lines, modified_lines, original_name, modified_name, context_lines
                )
            elif format_type == DiffFormat.SIDE_BY_SIDE:
                diff_text, hunks = self._generate_side_by_side_diff(
                    original_lines, modified_lines, original_name, modified_name
                )
            elif format_type == DiffFormat.MINIMAL:
                diff_text, hunks = self._generate_minimal_diff(
                    original_lines, modified_lines
                )
            elif format_type == DiffFormat.MARKDOWN:
                diff_text, hunks = self._generate_markdown_diff(
                    original_lines, modified_lines, original_name, modified_name
                )
            else:
                raise ValueError(f"Unsupported diff format: {format_type}")
            
            # Calculate statistics
            stats = self._calculate_diff_stats(original_lines, modified_lines, hunks)
            
            # Check diff size
            if len(diff_text) > self.max_diff_size:
                diff_text = diff_text[:self.max_diff_size] + "\n... (diff truncated due to size)"
                message = f"Diff truncated (original size: {len(diff_text)} chars)"
            else:
                message = f"Generated {format_type.value} diff successfully"
            
            return DiffResult(
                success=True,
                diff_text=diff_text,
                hunks=hunks,
                stats=stats,
                format=format_type,
                message=message
            )
        
        except Exception as e:
            logger.error(f"Failed to generate diff: {e}")
            return DiffResult(
                success=False,
                diff_text="",
                hunks=[],
                stats={},
                format=format_type,
                message=f"Diff generation failed: {e}"
            )
    
    def _generate_unified_diff(
        self,
        original_lines: List[str],
        modified_lines: List[str],
        original_name: str,
        modified_name: str,
        context_lines: int
    ) -> Tuple[str, List[DiffHunk]]:
        """Generate unified diff format."""
        
        diff_lines = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=original_name,
            tofile=modified_name,
            n=context_lines,
            lineterm=''
        ))
        
        diff_text = '\n'.join(diff_lines)
        hunks = self._parse_unified_diff_hunks(diff_lines)
        
        return diff_text, hunks
    
    def _generate_context_diff(
        self,
        original_lines: List[str],
        modified_lines: List[str],
        original_name: str,
        modified_name: str,
        context_lines: int
    ) -> Tuple[str, List[DiffHunk]]:
        """Generate context diff format."""
        
        diff_lines = list(difflib.context_diff(
            original_lines,
            modified_lines,
            fromfile=original_name,
            tofile=modified_name,
            n=context_lines,
            lineterm=''
        ))
        
        diff_text = '\n'.join(diff_lines)
        # Context diff parsing is more complex, simplified for now
        hunks = []
        
        return diff_text, hunks
    
    def _generate_side_by_side_diff(
        self,
        original_lines: List[str],
        modified_lines: List[str],
        original_name: str,
        modified_name: str
    ) -> Tuple[str, List[DiffHunk]]:
        """Generate side-by-side diff format."""
        
        # Use HtmlDiff for side-by-side comparison
        html_diff = difflib.HtmlDiff()
        
        # Generate table, but extract text version
        html_table = html_diff.make_table(
            original_lines,
            modified_lines,
            fromdesc=original_name,
            todesc=modified_name,
            context=True,
            numlines=self.diff_context_lines
        )
        
        # Convert HTML to readable text format (simplified)
        diff_text = self._html_to_text_diff(html_table)
        
        # Generate simplified hunks
        hunks = self._generate_change_hunks(original_lines, modified_lines)
        
        return diff_text, hunks
    
    def _generate_minimal_diff(
        self,
        original_lines: List[str],
        modified_lines: List[str]
    ) -> Tuple[str, List[DiffHunk]]:
        """Generate minimal diff showing only changes."""
        
        diff_lines = []
        hunks = []
        
        # Use SequenceMatcher to find changes
        matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                diff_lines.append(f"~ Lines {i1+1}-{i2}: {i2-i1} lines changed")
                hunk = DiffHunk(
                    old_start=i1+1,
                    old_count=i2-i1,
                    new_start=j1+1,
                    new_count=j2-j1,
                    lines=[f"- {line.rstrip()}" for line in original_lines[i1:i2]] +
                          [f"+ {line.rstrip()}" for line in modified_lines[j1:j2]]
                )
                hunks.append(hunk)
            elif tag == 'delete':
                diff_lines.append(f"- Lines {i1+1}-{i2}: {i2-i1} lines deleted")
                hunk = DiffHunk(
                    old_start=i1+1,
                    old_count=i2-i1,
                    new_start=j1+1,
                    new_count=0,
                    lines=[f"- {line.rstrip()}" for line in original_lines[i1:i2]]
                )
                hunks.append(hunk)
            elif tag == 'insert':
                diff_lines.append(f"+ Lines {j1+1}-{j2}: {j2-j1} lines added")
                hunk = DiffHunk(
                    old_start=i1+1,
                    old_count=0,
                    new_start=j1+1,
                    new_count=j2-j1,
                    lines=[f"+ {line.rstrip()}" for line in modified_lines[j1:j2]]
                )
                hunks.append(hunk)
        
        diff_text = '\n'.join(diff_lines)
        return diff_text, hunks
    
    def _generate_markdown_diff(
        self,
        original_lines: List[str],
        modified_lines: List[str],
        original_name: str,
        modified_name: str
    ) -> Tuple[str, List[DiffHunk]]:
        """Generate markdown-formatted diff."""
        
        # Generate unified diff first
        unified_diff, hunks = self._generate_unified_diff(
            original_lines, modified_lines, original_name, modified_name, 3
        )
        
        # Convert to markdown
        markdown_lines = [
            f"## Diff: {original_name} → {modified_name}",
            "",
            "```diff"
        ]
        
        # Add diff content
        for line in unified_diff.split('\n'):
            if line.startswith('@@'):
                # Hunk header
                markdown_lines.append(line)
            elif line.startswith('-'):
                # Deletion
                markdown_lines.append(line)
            elif line.startswith('+'):
                # Addition
                markdown_lines.append(line)
            elif line.startswith(' '):
                # Context
                markdown_lines.append(line)
            elif line.startswith('---') or line.startswith('+++'):
                # File headers
                markdown_lines.append(line)
        
        markdown_lines.append("```")
        
        diff_text = '\n'.join(markdown_lines)
        return diff_text, hunks
    
    def _parse_unified_diff_hunks(self, diff_lines: List[str]) -> List[DiffHunk]:
        """Parse unified diff to extract hunks."""
        hunks = []
        current_hunk = None
        
        for line in diff_lines:
            if line.startswith('@@'):
                # Hunk header: @@ -old_start,old_count +new_start,new_count @@
                if current_hunk:
                    hunks.append(current_hunk)
                
                # Parse hunk header
                match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)', line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1
                    context = match.group(5).strip()
                    
                    current_hunk = DiffHunk(
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                        lines=[],
                        context=context
                    )
            elif current_hunk and (line.startswith(' ') or line.startswith('-') or line.startswith('+')):
                current_hunk.lines.append(line)
        
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    def _generate_change_hunks(
        self,
        original_lines: List[str],
        modified_lines: List[str]
    ) -> List[DiffHunk]:
        """Generate simplified change hunks."""
        hunks = []
        
        matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                lines = []
                
                if tag in ['delete', 'replace']:
                    lines.extend([f"- {line.rstrip()}" for line in original_lines[i1:i2]])
                
                if tag in ['insert', 'replace']:
                    lines.extend([f"+ {line.rstrip()}" for line in modified_lines[j1:j2]])
                
                hunk = DiffHunk(
                    old_start=i1+1,
                    old_count=i2-i1,
                    new_start=j1+1,
                    new_count=j2-j1,
                    lines=lines
                )
                hunks.append(hunk)
        
        return hunks
    
    def _html_to_text_diff(self, html_table: str) -> str:
        """Convert HTML diff table to readable text (simplified)."""
        # This is a simplified conversion - in practice, you'd use an HTML parser
        text_lines = []
        
        # Extract meaningful content from HTML
        lines = html_table.split('\n')
        for line in lines:
            if '<td class="diff' in line:
                # Extract line content (very simplified)
                text = re.sub(r'<[^>]+>', '', line).strip()
                if text:
                    text_lines.append(text)
        
        return '\n'.join(text_lines[:50])  # Limit output
    
    def _calculate_diff_stats(
        self,
        original_lines: List[str],
        modified_lines: List[str],
        hunks: List[DiffHunk]
    ) -> Dict[str, int]:
        """Calculate diff statistics."""
        
        stats = {
            'original_lines': len(original_lines),
            'modified_lines': len(modified_lines),
            'hunks': len(hunks),
            'additions': 0,
            'deletions': 0,
            'modifications': 0
        }
        
        # Count changes from hunks
        for hunk in hunks:
            for line in hunk.lines:
                if line.startswith('+'):
                    stats['additions'] += 1
                elif line.startswith('-'):
                    stats['deletions'] += 1
        
        # Calculate modifications (lines that changed)
        matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                stats['modifications'] += min(i2-i1, j2-j1)
        
        return stats
    
    def apply_patch(
        self,
        original: str,
        patch_text: str,
        reverse: bool = False
    ) -> Dict[str, Any]:
        """
        Apply a unified diff patch to text.
        
        Args:
            original: Original text content
            patch_text: Unified diff patch text
            reverse: Whether to apply patch in reverse
            
        Returns:
            Dictionary with patching results
        """
        
        try:
            # Parse patch
            patch_lines = patch_text.strip().split('\n')
            hunks = self._parse_patch_hunks(patch_lines)
            
            if not hunks:
                return {
                    'success': False,
                    'result': original,
                    'message': 'No valid hunks found in patch'
                }
            
            # Apply hunks
            original_lines = original.splitlines()
            result_lines = original_lines.copy()
            
            # Apply hunks in reverse order to maintain line numbers
            for hunk in reversed(hunks):
                result_lines = self._apply_hunk(result_lines, hunk, reverse)
            
            result = '\n'.join(result_lines)
            
            return {
                'success': True,
                'result': result,
                'hunks_applied': len(hunks),
                'message': f'Successfully applied {len(hunks)} hunks'
            }
        
        except Exception as e:
            logger.error(f"Failed to apply patch: {e}")
            return {
                'success': False,
                'result': original,
                'message': f'Patch application failed: {e}'
            }
    
    def _parse_patch_hunks(self, patch_lines: List[str]) -> List[DiffHunk]:
        """Parse patch text to extract hunks."""
        hunks = []
        current_hunk = None
        
        for line in patch_lines:
            if line.startswith('@@'):
                if current_hunk:
                    hunks.append(current_hunk)
                
                # Parse hunk header
                match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1
                    
                    current_hunk = DiffHunk(
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                        lines=[]
                    )
            elif current_hunk and (line.startswith(' ') or line.startswith('-') or line.startswith('+')):
                current_hunk.lines.append(line)
        
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    def _apply_hunk(
        self,
        lines: List[str],
        hunk: DiffHunk,
        reverse: bool = False
    ) -> List[str]:
        """Apply a single hunk to text lines."""
        
        # Find the target location
        start_line = hunk.old_start - 1 if not reverse else hunk.new_start - 1
        
        # Extract changes from hunk
        context_lines = []
        deletions = []
        additions = []
        
        for line in hunk.lines:
            if line.startswith(' '):
                context_lines.append(line[1:])
            elif line.startswith('-'):
                if reverse:
                    additions.append(line[1:])
                else:
                    deletions.append(line[1:])
            elif line.startswith('+'):
                if reverse:
                    deletions.append(line[1:])
                else:
                    additions.append(line[1:])
        
        # Apply changes
        result_lines = lines.copy()
        
        # Remove deleted lines
        if deletions:
            for i, deletion in enumerate(deletions):
                del_line_idx = start_line + i
                if del_line_idx < len(result_lines) and result_lines[del_line_idx] == deletion:
                    del result_lines[del_line_idx]
        
        # Insert added lines
        if additions:
            for i, addition in enumerate(additions):
                result_lines.insert(start_line + i, addition)
        
        return result_lines
    
    def compare_files(
        self,
        file1_path: str,
        file2_path: str,
        format_type: DiffFormat = DiffFormat.UNIFIED
    ) -> DiffResult:
        """
        Compare two files and generate diff.
        
        Args:
            file1_path: Path to first file
            file2_path: Path to second file
            format_type: Diff format to generate
            
        Returns:
            DiffResult with comparison results
        """
        
        try:
            # Read files
            with open(file1_path, 'r', encoding='utf-8') as f1:
                content1 = f1.read()
            
            with open(file2_path, 'r', encoding='utf-8') as f2:
                content2 = f2.read()
            
            # Generate diff
            return self.generate_diff(
                content1,
                content2,
                file1_path,
                file2_path,
                format_type
            )
        
        except Exception as e:
            logger.error(f"Failed to compare files: {e}")
            return DiffResult(
                success=False,
                diff_text="",
                hunks=[],
                stats={},
                format=format_type,
                message=f"File comparison failed: {e}"
            )
    
    def get_diff_summary(self, diff_result: DiffResult) -> str:
        """Generate a human-readable summary of diff results."""
        
        if not diff_result.success:
            return f"❌ {diff_result.message}"
        
        stats = diff_result.stats
        
        summary_parts = []
        
        if stats.get('additions', 0) > 0:
            summary_parts.append(f"+{stats['additions']} additions")
        
        if stats.get('deletions', 0) > 0:
            summary_parts.append(f"-{stats['deletions']} deletions")
        
        if stats.get('modifications', 0) > 0:
            summary_parts.append(f"~{stats['modifications']} modifications")
        
        if not summary_parts:
            return "✅ No changes detected"
        
        changes = ", ".join(summary_parts)
        hunks = stats.get('hunks', 0)
        
        return f"📊 {changes} in {hunks} hunk{'s' if hunks != 1 else ''}"

# Example usage and testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test diff engine
    diff_engine = DiffEngine()
    
    print("🔄 Testing Diff Engine")
    print("=" * 40)
    
    # Test data
    original_code = '''def hello(name):
    if name:
        print(f"Hello, {name}!")
    else:
        print("Hello, World!")

def goodbye():
    print("Goodbye!")'''
    
    modified_code = '''def hello(name):
    if name:
        print(f"Hello, {name}!")
        print("Nice to meet you!")
    else:
        print("Hello, World!")

def goodbye(name=""):
    if name:
        print(f"Goodbye, {name}!")
    else:
        print("Goodbye!")

def new_function():
    print("This is new!")'''
    
    # Test different diff formats
    formats = [DiffFormat.UNIFIED, DiffFormat.MINIMAL, DiffFormat.MARKDOWN]
    
    for format_type in formats:
        print(f"\n--- {format_type.value.title()} Format ---")
        
        result = diff_engine.generate_diff(
            original_code,
            modified_code,
            "original.py",
            "modified.py",
            format_type
        )
        
        print(f"Success: {result.success}")
        if result.success:
            print(f"Summary: {diff_engine.get_diff_summary(result)}")
            print(f"Stats: {result.stats}")
            
            # Show first part of diff
            diff_preview = result.diff_text[:500]
            if len(result.diff_text) > 500:
                diff_preview += "..."
            print(f"Diff preview:\n{diff_preview}")
        else:
            print(f"Error: {result.message}")
    
    # Test patch application
    print(f"\n--- Patch Application ---")
    unified_result = diff_engine.generate_diff(
        original_code, modified_code, "original.py", "modified.py", DiffFormat.UNIFIED
    )
    
    if unified_result.success:
        patch_result = diff_engine.apply_patch(original_code, unified_result.diff_text)
        print(f"Patch success: {patch_result['success']}")
        if patch_result['success']:
            print(f"Applied {patch_result['hunks_applied']} hunks")
            # Verify result matches modified code
            matches_expected = patch_result['result'].strip() == modified_code.strip()
            print(f"Result matches expected: {matches_expected}")
        else:
            print(f"Patch error: {patch_result['message']}")