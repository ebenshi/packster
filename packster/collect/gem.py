"""Gem package collection for Ruby gems."""

import logging
from typing import List, Optional
from ..types import NormalizedItem, PackageManager
from .common import run_command, get_command_output

logger = logging.getLogger(__name__)


def collect_gem_packages() -> List[NormalizedItem]:
    """Collect installed Ruby gems.
    
    Returns:
        List of normalized package items
    """
    packages = []
    
    installed_packages = get_installed_packages()
    for name, version in installed_packages:
        normalized_item = NormalizedItem(
            source_pm=PackageManager.GEM,
            source_name=name,
            version=version,
            category="ruby",
            meta={"scope": "global"}
        )
        packages.append(normalized_item)
    
    logger.info(f"Collected {len(packages)} Gem packages")
    return packages


def get_installed_packages() -> List[tuple[str, Optional[str]]]:
    """Get installed Ruby gems.
    
    Returns:
        List of (package_name, version) tuples
    """
    # Tests patch run_command to return simple lines like "bundler (2.4.9)" or "bundler"
    result = run_command(["gem", "list", "--local"])
    lines = []
    if isinstance(result, tuple):
        _, stdout, _ = result
        lines = stdout.splitlines() if stdout else []
    else:
        lines = result
    if not lines:
        return []
    
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            # Parse lines like "package-name (1.2.3, 1.2.2)"
            if "(" in line and line.endswith(")"):
                name_part, version_part = line.rsplit("(", 1)
                name = name_part.strip()
                versions_str = version_part.rstrip(")").strip()
                
                # Get the latest version (first one)
                if "," in versions_str:
                    latest_version = versions_str.split(",")[0].strip()
                else:
                    latest_version = versions_str
                
                packages.append((name, latest_version or ""))
            else:
                # No version provided
                packages.append((line, ""))
    
    return packages


def get_package_info(package_name: str) -> Optional[dict]:
    """Get detailed information about a Ruby gem.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Dictionary with package information or None
    """
    command = ["gem", "info", package_name]
    output = get_command_output(command)
    
    if not output:
        return None
    
    info = {}
    current_key = None
    current_value = []
    
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
            
        if ":" in line and not line.startswith(" "):
            # Save previous key-value pair
            if current_key and current_value:
                info[current_key.lower()] = " ".join(current_value).strip()
            
            # Start new key-value pair
            key_value = line.split(":", 1)
            if len(key_value) == 2:
                current_key = key_value[0].strip()
                current_value = [key_value[1].strip()]
        elif line.startswith(" ") and current_key:
            # Continuation of previous value
            current_value.append(line.strip())
    
    # Save last key-value pair
    if current_key and current_value:
        info[current_key.lower()] = " ".join(current_value).strip()
    
    return info


def is_package_installed(package_name: str) -> bool:
    """Check if a Ruby gem is installed.
    
    Args:
        package_name: Name of the package
        
    Returns:
        True if package is installed
    """
    command = ["gem", "list", package_name, "--local"]
    output = get_command_output(command)
    
    if not output:
        return False
    
    # Check if the package name appears in the output
    return package_name in output


def get_package_version(package_name: str) -> Optional[str]:
    """Get installed version of a Ruby gem.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Version string or None
    """
    command = ["gem", "list", package_name, "--local"]
    output = get_command_output(command)
    
    if not output:
        return None
    
    for line in output.splitlines():
        line = line.strip()
        if line.startswith(f"{package_name} (") and line.endswith(")"):
            # Extract version from "package_name (1.2.3, 1.2.2)"
            version_part = line[len(package_name) + 2:]  # +2 for " ("
            versions_str = version_part.rstrip(")").strip()
            
            # Get the latest version (first one)
            if "," in versions_str:
                return versions_str.split(",")[0].strip()
            else:
                return versions_str
    
    return None


def filter_gem_packages(packages: List[tuple[str, Optional[str]]]) -> List[tuple[str, Optional[str]]]:
    """Filter out system Ruby gems that shouldn't be migrated.
    
    Args:
        packages: List of (package_name, version) tuples
        
    Returns:
        Filtered list of packages
    """
    # Common system packages to exclude
    system_packages = {
        "bundler", "rake", "rdoc", "json", "minitest", "test-unit",
        "bigdecimal", "io-console", "psych", "stringio", "strscan",
    }
    
    filtered = []
    for name, version in packages:
        if name.lower() not in system_packages:
            filtered.append((name, version))
    
    return filtered


def get_gem_environment() -> dict:
    """Get Ruby gem environment information.
    
    Returns:
        Dictionary with gem environment
    """
    command = ["gem", "environment"]
    output = get_command_output(command)
    
    if not output:
        return {}
    
    env = {}
    current_key = None
    current_value = []
    
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
            
        if ":" in line and not line.startswith(" "):
            # Save previous key-value pair
            if current_key and current_value:
                env[current_key.lower()] = " ".join(current_value).strip()
            
            # Start new key-value pair
            key_value = line.split(":", 1)
            if len(key_value) == 2:
                current_key = key_value[0].strip()
                current_value = [key_value[1].strip()]
        elif line.startswith(" ") and current_key:
            # Continuation of previous value
            current_value.append(line.strip())
    
    # Save last key-value pair
    if current_key and current_value:
        env[current_key.lower()] = " ".join(current_value).strip()
    
    return env


def get_ruby_version() -> Optional[str]:
    """Get Ruby version.
    
    Returns:
        Ruby version string or None
    """
    command = ["ruby", "--version"]
    output = get_command_output(command)
    
    if not output:
        return None
    
    # Extract version from output like "ruby 3.2.2 (2023-03-30 revision e51014f9c0) [x86_64-linux]"
    parts = output.split()
    if len(parts) >= 2:
        return parts[1]
    
    return None
