"""Cargo package collection for Rust packages."""

import logging
from typing import List, Optional
from ..types import NormalizedItem, PackageManager
from .common import run_command, get_command_output

logger = logging.getLogger(__name__)


def collect_cargo_packages() -> List[NormalizedItem]:
    """Collect installed Cargo packages.
    
    Returns:
        List of normalized package items
    """
    packages = []
    
    installed_packages = get_installed_packages()
    for name, version in installed_packages:
        normalized_item = NormalizedItem(
            source_pm=PackageManager.CARGO,
            source_name=name,
            version=version,
            category="rust",
            meta={"scope": "global"}
        )
        packages.append(normalized_item)
    
    logger.info(f"Collected {len(packages)} Cargo packages")
    return packages


def get_installed_packages() -> List[tuple[str, Optional[str]]]:
    """Get installed Cargo packages.
    
    Returns:
        List of (package_name, version) tuples
    """
    # Tests patch run_command to return simple lines like "fd 8.4.0:" or "fd:"
    result = run_command(["cargo", "install", "--list"])
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
            # Parse lines like "package-name v1.2.3:"
            if ":" in line:
                body = line.rstrip(":")
                if " " in body:
                    name, version = body.split(" ", 1)
                    packages.append((name.strip(), (version or "").strip()))
                else:
                    packages.append((body.strip(), ""))
    
    return packages


def get_package_info(package_name: str) -> Optional[dict]:
    """Get detailed information about a Cargo package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Dictionary with package information or None
    """
    # Cargo doesn't have a direct way to get package info for installed packages
    # We can try to get it from crates.io
    command = ["cargo", "search", package_name, "--limit", "1"]
    output = get_command_output(command)
    
    if not output:
        return None
    
    info = {}
    lines = output.splitlines()
    
    # Parse search output
    for line in lines:
        if package_name in line and "=" in line:
            # Format: package_name = "description"
            parts = line.split("=", 1)
            if len(parts) == 2:
                description = parts[1].strip().strip('"')
                info["description"] = description
                break
    
    return info if info else None


def is_package_installed(package_name: str) -> bool:
    """Check if a Cargo package is installed.
    
    Args:
        package_name: Name of the package
        
    Returns:
        True if package is installed
    """
    command = ["cargo", "install", "--list"]
    output = get_command_output(command)
    
    if not output:
        return False
    
    for line in output.splitlines():
        if line.strip().startswith(f"{package_name} v"):
            return True
    
    return False


def get_package_version(package_name: str) -> Optional[str]:
    """Get installed version of a Cargo package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Version string or None
    """
    command = ["cargo", "install", "--list"]
    output = get_command_output(command)
    
    if not output:
        return None
    
    for line in output.splitlines():
        line = line.strip()
        if line.startswith(f"{package_name} v") and line.endswith(":"):
            # Extract version from "package_name v1.2.3:"
            version_part = line[len(package_name) + 2:]  # +2 for " v"
            version = version_part.rstrip(":").strip()
            return version
    
    return None


def filter_cargo_packages(packages: List[tuple[str, Optional[str]]]) -> List[tuple[str, Optional[str]]]:
    """Filter out system Cargo packages that shouldn't be migrated.
    
    Args:
        packages: List of (package_name, version) tuples
        
    Returns:
        Filtered list of packages
    """
    # Common system packages to exclude
    system_packages = {
        "cargo", "rustc", "rustup", "rustfmt", "clippy",
    }
    
    filtered = []
    for name, version in packages:
        if name.lower() not in system_packages:
            filtered.append((name, version))
    
    return filtered


def get_cargo_config() -> dict:
    """Get Cargo configuration.
    
    Returns:
        Dictionary with Cargo configuration
    """
    config = {}
    
    # Get cargo version
    version_output = get_command_output(["cargo", "--version"])
    if version_output:
        config["version"] = version_output.strip()
    
    # Get rustc version
    rustc_output = get_command_output(["rustc", "--version"])
    if rustc_output:
        config["rustc_version"] = rustc_output.strip()
    
    return config


def get_cargo_home() -> Optional[str]:
    """Get Cargo home directory.
    
    Returns:
        Cargo home directory path or None
    """
    import os
    return os.getenv("CARGO_HOME") or os.path.expanduser("~/.cargo")
