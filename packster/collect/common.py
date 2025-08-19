"""Common utilities for package collection."""

import logging
from typing import List, Tuple, Optional
from .. import detect

logger = logging.getLogger(__name__)


def run_command(
    command: List[str], 
    timeout: int = 30,
    capture_output: bool = True,
    check: bool = False
) -> Tuple[int, str, str]:
    """Run a shell command with error handling.
    
    Args:
        command: List of command and arguments
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit code
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    return detect.run_command_safe(command, timeout, capture_output)


def parse_package_line(line: str, separator: str = "==") -> Tuple[str, Optional[str]]:
    """Parse a package line to extract name and version.
    
    Args:
        line: Package line to parse
        separator: Separator between name and version
        
    Returns:
        Tuple of (package_name, version)
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return "", None
        
    if separator in line:
        parts = line.split(separator, 1)
        name = parts[0].strip()
        version = parts[1].strip()
        return name, version
    else:
        return line.strip(), None


def clean_package_name(name: str) -> str:
    """Clean package name by removing common prefixes/suffixes.
    
    Args:
        name: Raw package name
        
    Returns:
        Cleaned package name
    """
    # Remove common prefixes
    prefixes = ["python-", "python3-", "lib", "lib64"]
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
    
    # Remove common suffixes
    suffixes = ["-dev", "-dbg", "-doc", "-common"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    
    return name.lower()


def filter_package_list(
    packages: List[str], 
    exclude_patterns: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None
) -> List[str]:
    """Filter package list based on patterns.
    
    Args:
        packages: List of package names
        exclude_patterns: Patterns to exclude
        include_patterns: Patterns to include (if None, include all)
        
    Returns:
        Filtered package list
    """
    if exclude_patterns is None:
        exclude_patterns = []
    if include_patterns is None:
        include_patterns = []
    
    filtered = []
    
    for package in packages:
        package_lower = package.lower()
        
        # Check exclude patterns
        excluded = False
        for pattern in exclude_patterns:
            if pattern.lower() in package_lower:
                excluded = True
                break
        
        if excluded:
            continue
            
        # Check include patterns
        if include_patterns:
            included = False
            for pattern in include_patterns:
                if pattern.lower() in package_lower:
                    included = True
                    break
            if not included:
                continue
        
        filtered.append(package)
    
    return filtered


def validate_command_availability(command: str) -> bool:
    """Validate that a command is available.
    
    Args:
        command: Command to check
        
    Returns:
        True if command is available
    """
    return detect.is_command_available(command)


def get_command_output(command: List[str], timeout: int = 30) -> Optional[str]:
    """Get command output, returning None on failure.
    
    Args:
        command: Command to run
        timeout: Command timeout
        
    Returns:
        Command output or None on failure
    """
    exit_code, stdout, stderr = run_command(command, timeout)
    
    if exit_code == 0:
        return stdout.strip()
    else:
        logger.warning(f"Command failed: {' '.join(command)} (exit code: {exit_code})")
        if stderr:
            logger.debug(f"Stderr: {stderr}")
        return None
