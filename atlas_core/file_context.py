"""
File Context Manager for Atlas Code V5

Intelligent file loading, context management, and code analysis
with support for multiple programming languages and project structures.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
import mimetypes
import chardet

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """Information about a loaded file."""
    path: str
    content: str
    language: Optional[str] = None
    size_bytes: int = 0
    encoding: str = 'utf-8'
    last_modified: float = 0.0
    file_type: str = 'text'
    metadata: Dict[str, Any] = None

@dataclass
class ProjectContext:
    """Context about a project or directory."""
    root_path: str
    files: List[FileInfo]
    structure: Dict[str, Any]
    languages: Set[str]
    total_files: int = 0
    total_size: int = 0

class FileContextManager:
    """
    Intelligent file loading and context management system
    with support for multiple programming languages and project analysis.
    """
    
    def __init__(self, config_dir: str):
        """Initialize file context manager with configuration."""
        self.config_dir = config_dir
        
        # Load settings
        self.settings = self._load_settings()
        file_config = self.settings.get('file_handling', {})
        
        # Configuration
        self.max_file_size_mb = file_config.get('max_file_size_mb', 10)
        self.allowed_extensions = set(file_config.get('allowed_extensions', [
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs',
            '.rb', '.php', '.html', '.css', '.json', '.yaml', '.yml',
            '.md', '.txt', '.sh', '.sql', '.xml'
        ]))
        self.backup_before_edit = file_config.get('backup_before_edit', True)
        self.backup_directory = file_config.get('backup_directory', './backups')
        
        # Language detection mapping
        self.extension_to_language = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.sql': 'sql',
            '.r': 'r',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        
        # Binary file extensions to skip
        self.binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bin', '.o', '.obj',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.mp3', '.mp4', '.avi', '.mkv', '.wav', '.flac',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar'
        }
        
        # Cached file contents
        self.file_cache: Dict[str, FileInfo] = {}
        self.cache_max_size = 100  # Maximum files to cache
        
        logger.info("File context manager initialized")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load system settings."""
        try:
            settings_path = os.path.join(self.config_dir, 'settings.json')
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
            return self._get_default_settings()
    
    def load_file(self, file_path: str, force_reload: bool = False) -> Optional[FileInfo]:
        """
        Load a single file with intelligent content detection.
        
        Args:
            file_path: Path to the file to load
            force_reload: Force reload even if cached
            
        Returns:
            FileInfo object or None if loading failed
        """
        
        try:
            # Normalize path
            file_path = os.path.abspath(file_path)
            
            # Check cache first
            if not force_reload and file_path in self.file_cache:
                cached_info = self.file_cache[file_path]
                # Check if file was modified
                current_mtime = os.path.getmtime(file_path)
                if cached_info.last_modified >= current_mtime:
                    logger.debug(f"Using cached version of {file_path}")
                    return cached_info
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size_mb * 1024 * 1024:
                logger.warning(f"File too large ({file_size / 1024 / 1024:.1f}MB): {file_path}")
                return None
            
            # Check if extension is allowed
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.allowed_extensions:
                logger.warning(f"File extension not allowed: {file_ext}")
                return None
            
            # Check if it's a binary file
            if file_ext in self.binary_extensions:
                logger.warning(f"Binary file not supported: {file_path}")
                return None
            
            # Detect encoding
            encoding = self._detect_encoding(file_path)
            if not encoding:
                logger.warning(f"Could not detect encoding for: {file_path}")
                return None
            
            # Read file content
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Fallback to different encodings
                for fallback_encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(file_path, 'r', encoding=fallback_encoding) as f:
                            content = f.read()
                        encoding = fallback_encoding
                        logger.debug(f"Used fallback encoding {encoding} for {file_path}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    logger.error(f"Could not decode file: {file_path}")
                    return None
            
            # Detect language
            language = self._detect_language(file_path, content)
            
            # Determine file type
            file_type = self._determine_file_type(file_path, content)
            
            # Get file metadata
            metadata = self._extract_metadata(file_path, content, language)
            
            # Create FileInfo object
            file_info = FileInfo(
                path=file_path,
                content=content,
                language=language,
                size_bytes=file_size,
                encoding=encoding,
                last_modified=os.path.getmtime(file_path),
                file_type=file_type,
                metadata=metadata
            )
            
            # Cache the file info
            self._cache_file_info(file_path, file_info)
            
            logger.info(f"Loaded file: {file_path} ({file_size} bytes, {language})")
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}")
            return None
    
    def load_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_files: int = 100
    ) -> Optional[ProjectContext]:
        """
        Load multiple files from a directory with intelligent filtering.
        
        Args:
            directory_path: Path to directory to load
            recursive: Whether to recurse into subdirectories
            include_patterns: Glob patterns to include (e.g., ['*.py', '*.js'])
            exclude_patterns: Glob patterns to exclude (e.g., ['*.pyc', 'node_modules/*'])
            max_files: Maximum number of files to load
            
        Returns:
            ProjectContext with loaded files and analysis
        """
        
        try:
            directory_path = os.path.abspath(directory_path)
            
            if not os.path.isdir(directory_path):
                logger.error(f"Directory not found: {directory_path}")
                return None
            
            # Find relevant files
            file_paths = self._find_files(
                directory_path, recursive, include_patterns, exclude_patterns, max_files
            )
            
            if not file_paths:
                logger.warning(f"No suitable files found in: {directory_path}")
                return None
            
            # Load files
            loaded_files = []
            languages = set()
            total_size = 0
            
            for file_path in file_paths:
                file_info = self.load_file(file_path)
                if file_info:
                    loaded_files.append(file_info)
                    if file_info.language:
                        languages.add(file_info.language)
                    total_size += file_info.size_bytes
            
            # Generate project structure
            structure = self._generate_directory_structure(directory_path, loaded_files)
            
            # Create project context
            project_context = ProjectContext(
                root_path=directory_path,
                files=loaded_files,
                structure=structure,
                languages=languages,
                total_files=len(loaded_files),
                total_size=total_size
            )
            
            logger.info(f"Loaded project: {directory_path} ({len(loaded_files)} files, {list(languages)})")
            return project_context
            
        except Exception as e:
            logger.error(f"Failed to load directory {directory_path}: {e}")
            return None
    
    def get_file_context_summary(self, files: List[FileInfo], max_chars: int = 10000) -> str:
        """
        Generate a concise summary of file contexts for AI consumption.
        
        Args:
            files: List of FileInfo objects
            max_chars: Maximum characters in summary
            
        Returns:
            Formatted context summary
        """
        
        if not files:
            return "No files provided for context."
        
        summary_parts = []
        current_length = 0
        
        # Sort files by relevance (code files first, then by size)
        def file_priority(file_info: FileInfo) -> Tuple[int, int]:
            if file_info.language in ['python', 'javascript', 'java', 'cpp', 'go', 'rust']:
                return (0, -file_info.size_bytes)  # Code files first, larger first
            elif file_info.language in ['json', 'yaml', 'xml']:
                return (1, -file_info.size_bytes)  # Config files second
            else:
                return (2, -file_info.size_bytes)  # Other files last
        
        sorted_files = sorted(files, key=file_priority)
        
        # Add summary header
        languages = list(set(f.language for f in files if f.language))
        header = f"## File Context ({len(files)} files, languages: {', '.join(languages)})\n\n"
        summary_parts.append(header)
        current_length += len(header)
        
        for file_info in sorted_files:
            if current_length >= max_chars * 0.9:  # Leave some room
                remaining_count = len(sorted_files) - len(summary_parts) + 1
                summary_parts.append(f"... and {remaining_count} more files (truncated due to length)\n")
                break
            
            # File header
            relative_path = os.path.relpath(file_info.path)
            file_header = f"### {relative_path} ({file_info.language or 'text'})\n"
            
            # Calculate remaining space
            remaining_chars = max_chars - current_length - len(file_header) - 100  # Buffer
            
            if remaining_chars <= 0:
                break
            
            # Truncate content if needed
            content = file_info.content
            if len(content) > remaining_chars:
                content = content[:remaining_chars] + "... (truncated)"
            
            file_section = f"{file_header}```{file_info.language or ''}\n{content}\n```\n\n"
            
            summary_parts.append(file_section)
            current_length += len(file_section)
        
        return ''.join(summary_parts)
    
    def extract_functions_and_classes(self, file_info: FileInfo) -> Dict[str, List[str]]:
        """Extract function and class definitions from code files."""
        
        if not file_info.language:
            return {'functions': [], 'classes': []}
        
        functions = []
        classes = []
        
        try:
            lines = file_info.content.split('\n')
            
            if file_info.language == 'python':
                import re
                for line in lines:
                    line = line.strip()
                    # Function definitions
                    func_match = re.match(r'def\s+(\w+)\s*\(', line)
                    if func_match:
                        functions.append(func_match.group(1))
                    
                    # Class definitions
                    class_match = re.match(r'class\s+(\w+)(?:\s*\([^)]*\))?\s*:', line)
                    if class_match:
                        classes.append(class_match.group(1))
            
            elif file_info.language in ['javascript', 'typescript']:
                import re
                for line in lines:
                    line = line.strip()
                    # Function definitions
                    func_matches = re.findall(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>))', line)
                    for match in func_matches:
                        func_name = match[0] or match[1]
                        if func_name:
                            functions.append(func_name)
                    
                    # Class definitions
                    class_match = re.match(r'class\s+(\w+)', line)
                    if class_match:
                        classes.append(class_match.group(1))
            
            elif file_info.language == 'java':
                import re
                for line in lines:
                    line = line.strip()
                    # Method definitions (simplified)
                    method_match = re.search(r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(', line)
                    if method_match and not line.startswith('//'):
                        functions.append(method_match.group(1))
                    
                    # Class definitions
                    class_match = re.match(r'(?:public\s+)?class\s+(\w+)', line)
                    if class_match:
                        classes.append(class_match.group(1))
        
        except Exception as e:
            logger.warning(f"Failed to extract functions/classes from {file_info.path}: {e}")
        
        return {'functions': functions, 'classes': classes}
    
    def write_file(
        self,
        file_path: str,
        content: str,
        create_backup: bool = True,
        encoding: str = 'utf-8'
    ) -> bool:
        """
        Write content to a file with optional backup.
        
        Args:
            file_path: Path to write to
            content: Content to write
            create_backup: Whether to create backup of existing file
            encoding: File encoding to use
            
        Returns:
            True if successful, False otherwise
        """
        
        try:
            file_path = os.path.abspath(file_path)
            
            # Create backup if file exists and backup is requested
            if create_backup and os.path.exists(file_path) and self.backup_before_edit:
                self._create_backup(file_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Update cache if file was previously loaded
            if file_path in self.file_cache:
                # Reload to update cache
                self.load_file(file_path, force_reload=True)
            
            logger.info(f"Successfully wrote file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False
    
    def _detect_encoding(self, file_path: str) -> Optional[str]:
        """Detect file encoding using chardet."""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(8192)  # Read first 8KB for detection
            
            result = chardet.detect(raw_data)
            if result and result['confidence'] > 0.7:
                return result['encoding']
            
            # Fallback to UTF-8
            return 'utf-8'
            
        except Exception:
            return 'utf-8'
    
    def _detect_language(self, file_path: str, content: str) -> Optional[str]:
        """Detect programming language from file extension and content."""
        
        # Check extension first
        file_ext = Path(file_path).suffix.lower()
        if file_ext in self.extension_to_language:
            return self.extension_to_language[file_ext]
        
        # Content-based detection for files without clear extensions
        content_lower = content.lower()
        
        # Python indicators
        if any(indicator in content for indicator in ['def ', 'import ', 'from ', 'class ', '__init__']):
            return 'python'
        
        # JavaScript indicators
        if any(indicator in content for indicator in ['function', 'const ', 'let ', 'var ', '=>']):
            return 'javascript'
        
        # Java indicators
        if any(indicator in content for indicator in ['public class', 'private ', 'public static void main']):
            return 'java'
        
        # Other common patterns
        if '#include' in content:
            return 'cpp' if 'iostream' in content else 'c'
        
        return None
    
    def _determine_file_type(self, file_path: str, content: str) -> str:
        """Determine the type of file (code, config, documentation, etc.)."""
        
        file_ext = Path(file_path).suffix.lower()
        
        # Code files
        if file_ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php']:
            return 'code'
        
        # Configuration files
        if file_ext in ['.json', '.yaml', '.yml', '.xml', '.ini', '.cfg', '.conf']:
            return 'config'
        
        # Documentation files
        if file_ext in ['.md', '.txt', '.rst', '.doc']:
            return 'documentation'
        
        # Web files
        if file_ext in ['.html', '.css', '.scss', '.sass']:
            return 'web'
        
        # Script files
        if file_ext in ['.sh', '.bat', '.ps1']:
            return 'script'
        
        return 'text'
    
    def _extract_metadata(self, file_path: str, content: str, language: Optional[str]) -> Dict[str, Any]:
        """Extract metadata from file content."""
        
        metadata = {
            'line_count': len(content.split('\n')),
            'char_count': len(content),
            'word_count': len(content.split()),
            'imports': [],
            'dependencies': []
        }
        
        try:
            if language == 'python':
                # Extract imports
                import re
                imports = re.findall(r'^(?:from\s+(\S+)\s+)?import\s+([^\n#]+)', content, re.MULTILINE)
                for imp in imports:
                    if imp[0]:  # from X import Y
                        metadata['imports'].append(f"from {imp[0]} import {imp[1].strip()}")
                    else:  # import X
                        metadata['imports'].append(f"import {imp[1].strip()}")
            
            elif language in ['javascript', 'typescript']:
                # Extract imports/requires
                import re
                imports = re.findall(r'(?:import.*?from\s+[\'"]([^\'"]+)[\'"]|require\([\'"]([^\'"]+)[\'"]\))', content)
                for imp in imports:
                    module = imp[0] or imp[1]
                    if module:
                        metadata['imports'].append(module)
            
            elif language == 'java':
                # Extract imports
                import re
                imports = re.findall(r'import\s+([^;]+);', content)
                metadata['imports'] = imports
        
        except Exception as e:
            logger.debug(f"Failed to extract metadata from {file_path}: {e}")
        
        return metadata
    
    def _find_files(
        self,
        directory: str,
        recursive: bool,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
        max_files: int
    ) -> List[str]:
        """Find files in directory matching criteria."""
        
        import fnmatch
        
        found_files = []
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                # Skip common unwanted directories
                dirs[:] = [d for d in dirs if d not in {'.git', '.svn', '__pycache__', 'node_modules', '.env', 'venv'}]
                
                for file in files:
                    if len(found_files) >= max_files:
                        break
                    
                    file_path = os.path.join(root, file)
                    
                    # Check file extension
                    if Path(file).suffix.lower() not in self.allowed_extensions:
                        continue
                    
                    # Check include patterns
                    if include_patterns:
                        if not any(fnmatch.fnmatch(file, pattern) for pattern in include_patterns):
                            continue
                    
                    # Check exclude patterns
                    if exclude_patterns:
                        if any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns):
                            continue
                    
                    found_files.append(file_path)
        else:
            # Non-recursive
            for file in os.listdir(directory):
                if len(found_files) >= max_files:
                    break
                
                file_path = os.path.join(directory, file)
                
                if not os.path.isfile(file_path):
                    continue
                
                if Path(file).suffix.lower() not in self.allowed_extensions:
                    continue
                
                if include_patterns:
                    if not any(fnmatch.fnmatch(file, pattern) for pattern in include_patterns):
                        continue
                
                if exclude_patterns:
                    if any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns):
                        continue
                
                found_files.append(file_path)
        
        return found_files
    
    def _generate_directory_structure(self, root_path: str, files: List[FileInfo]) -> Dict[str, Any]:
        """Generate a tree structure of the loaded files."""
        
        structure = {}
        
        for file_info in files:
            relative_path = os.path.relpath(file_info.path, root_path)
            path_parts = relative_path.split(os.sep)
            
            current_level = structure
            for part in path_parts[:-1]:  # Navigate to parent directory
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            
            # Add file info
            filename = path_parts[-1]
            current_level[filename] = {
                'type': 'file',
                'language': file_info.language,
                'size': file_info.size_bytes,
                'file_type': file_info.file_type
            }
        
        return structure
    
    def _cache_file_info(self, file_path: str, file_info: FileInfo):
        """Cache file info with size limit."""
        self.file_cache[file_path] = file_info
        
        # Maintain cache size limit
        if len(self.file_cache) > self.cache_max_size:
            # Remove oldest entries (simple LRU approximation)
            oldest_key = min(self.file_cache.keys(), 
                           key=lambda k: self.file_cache[k].last_modified)
            del self.file_cache[oldest_key]
    
    def _create_backup(self, file_path: str):
        """Create backup of existing file."""
        try:
            backup_dir = os.path.expanduser(self.backup_directory)
            os.makedirs(backup_dir, exist_ok=True)
            
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{filename}.{timestamp}.backup"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy file to backup
            import shutil
            shutil.copy2(file_path, backup_path)
            
            logger.debug(f"Created backup: {backup_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get file cache statistics."""
        total_size = sum(len(info.content.encode('utf-8')) for info in self.file_cache.values())
        
        return {
            'cached_files': len(self.file_cache),
            'cache_limit': self.cache_max_size,
            'total_cache_size_mb': total_size / (1024 * 1024),
            'cache_utilization': len(self.file_cache) / self.cache_max_size
        }
    
    def clear_cache(self):
        """Clear the file cache."""
        self.file_cache.clear()
        logger.info("File cache cleared")
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Default settings if config missing."""
        return {
            'file_handling': {
                'max_file_size_mb': 10,
                'allowed_extensions': ['.py', '.js', '.ts', '.java', '.cpp', '.c'],
                'backup_before_edit': True,
                'backup_directory': './backups'
            }
        }

# Example usage and testing
if __name__ == "__main__":
    import logging
    from datetime import datetime
    logging.basicConfig(level=logging.INFO)
    
    # Test file context manager
    file_manager = FileContextManager("../config")
    
    print("📁 Testing File Context Manager")
    print("=" * 40)
    
    # Test single file loading
    current_file = __file__
    file_info = file_manager.load_file(current_file)
    
    if file_info:
        print(f"\nLoaded file: {os.path.basename(file_info.path)}")
        print(f"Language: {file_info.language}")
        print(f"Size: {file_info.size_bytes} bytes")
        print(f"Lines: {file_info.metadata['line_count']}")
        print(f"Encoding: {file_info.encoding}")
        
        # Extract functions and classes
        extracted = file_manager.extract_functions_and_classes(file_info)
        print(f"Functions: {len(extracted['functions'])}")
        print(f"Classes: {len(extracted['classes'])}")
    
    # Test directory loading
    current_dir = os.path.dirname(__file__)
    project_context = file_manager.load_directory(
        current_dir, 
        recursive=False,
        include_patterns=['*.py']
    )
    
    if project_context:
        print(f"\nLoaded project: {os.path.basename(project_context.root_path)}")
        print(f"Files: {project_context.total_files}")
        print(f"Languages: {', '.join(project_context.languages)}")
        print(f"Total size: {project_context.total_size / 1024:.1f} KB")
        
        # Generate context summary
        summary = file_manager.get_file_context_summary(project_context.files, max_chars=2000)
        print(f"\nContext summary length: {len(summary)} characters")
    
    # Cache statistics
    cache_stats = file_manager.get_cache_stats()
    print(f"\nCache stats:")
    print(f"- Cached files: {cache_stats['cached_files']}")
    print(f"- Cache size: {cache_stats['total_cache_size_mb']:.2f} MB")
    print(f"- Cache utilization: {cache_stats['cache_utilization']:.1%}")