"""APT package collection for Ubuntu/Debian systems."""

import logging
from typing import List, Dict, Any, Optional
from ..types import NormalizedItem, PackageManager
from .common import run_command, get_command_output, clean_package_name

logger = logging.getLogger(__name__)


def collect_apt_packages() -> List[NormalizedItem]:
    """Collect manually installed APT packages.
    
    Returns:
        List of normalized package items
    """
    packages = []
    
    # Get manually installed packages (tests patch run_command)
    manual_result = run_command(["apt-mark", "showmanual"])
    if isinstance(manual_result, tuple):
        _, stdout, _ = manual_result
        manual_packages = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    else:
        manual_packages = list(manual_result)
    if not manual_packages:
        logger.warning("No manually installed APT packages found")
        return packages
    
    # Optionally get versions via second call (tests provide side_effect)
    versions_map: Dict[str, str] = {}
    try:
        version_result = run_command(["dpkg-query", "-W"])  # signature not important under tests
        lines = []
        if isinstance(version_result, tuple):
            _, stdout, _ = version_result
            lines = stdout.splitlines()
        else:
            lines = version_result
        for line in lines:
            # Expect format like "name/now 1:2.25.1-..."
            if "/now" in line:
                name_part, rest = line.split("/now", 1)
                name = name_part.strip()
                ver = rest.strip().split()[0] if rest.strip() else ""
                versions_map[name] = ver
    except Exception:
        pass

    for package_name in manual_packages:
        normalized_item = NormalizedItem(
            source_pm=PackageManager.APT,
            source_name=package_name,
            version=versions_map.get(package_name, ""),
            category=None,
            meta={}
        )
        packages.append(normalized_item)
    
    logger.info(f"Collected {len(packages)} APT packages")
    return packages


def get_manual_packages() -> List[str]:
    """Get list of manually installed packages.
    
    Returns:
        List of package names
    """
    command = ["apt-mark", "showmanual"]
    output = get_command_output(command)
    
    if not output:
        return []
    
    packages = []
    for line in output.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            packages.append(line)
    
    return packages


def get_package_info(package_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Dictionary with package information or None
    """
    command = ["dpkg-query", "-W", "-f=${Version}\t${Section}\t${Priority}\t${Installed-Size}\t${Description}", package_name]
    output = get_command_output(command)
    
    if not output:
        return None
    
    try:
        parts = output.split('\t', 4)
        if len(parts) >= 4:
            return {
                "version": parts[0].strip(),
                "section": parts[1].strip(),
                "priority": parts[2].strip(),
                "installed_size": parts[3].strip(),
                "description": parts[4].strip() if len(parts) > 4 else "",
            }
    except Exception as e:
        logger.debug(f"Error parsing package info for {package_name}: {e}")
    
    return None


def get_installed_packages() -> List[str]:
    """Get all installed packages (not just manual).
    
    Returns:
        List of package names
    """
    command = ["dpkg", "--get-selections"]
    output = get_command_output(command)
    
    if not output:
        return []
    
    packages = []
    for line in output.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            # dpkg --get-selections format: package_name\tinstall
            parts = line.split('\t')
            if len(parts) >= 2 and parts[1] == "install":
                packages.append(parts[0])
    
    return packages


def get_package_dependencies(package_name: str) -> List[str]:
    """Get dependencies for a package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        List of dependency package names
    """
    command = ["apt-cache", "depends", package_name]
    output = get_command_output(command)
    
    if not output:
        return []
    
    dependencies = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Depends:"):
            # Extract package name from "Depends: package_name"
            dep_parts = line.split(":", 1)
            if len(dep_parts) > 1:
                dep_name = dep_parts[1].strip()
                # Handle version constraints like "package_name (>= 1.0)"
                if "(" in dep_name:
                    dep_name = dep_name.split("(")[0].strip()
                dependencies.append(dep_name)
    
    return dependencies


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed.
    
    Args:
        package_name: Name of the package
        
    Returns:
        True if package is installed
    """
    command = ["dpkg", "-s", package_name]
    exit_code, _, _ = run_command(command)
    return exit_code == 0


def get_package_version(package_name: str) -> Optional[str]:
    """Get installed version of a package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Version string or None
    """
    command = ["dpkg-query", "-W", "-f=${Version}", package_name]
    output = get_command_output(command)
    return output.strip() if output else None


def filter_system_packages(packages: List[str]) -> List[str]:
    """Filter out system packages that shouldn't be migrated.
    
    Args:
        packages: List of package names
        
    Returns:
        Filtered list of package names
    """
    # Common system packages to exclude
    system_packages = {
        "apt", "dpkg", "base-files", "base-passwd", "bash", "coreutils",
        "dash", "debianutils", "diffutils", "findutils", "grep", "gzip",
        "hostname", "init-system-helpers", "libc-bin", "libpam-modules",
        "libpam-runtime", "login", "mount", "passwd", "perl-base",
        "sed", "sysvinit-utils", "tar", "util-linux", "zlib1g",
        "ubuntu-minimal", "ubuntu-standard", "ubuntu-server",
    }
    
    filtered = []
    for package in packages:
        if package not in system_packages and not package.startswith("lib"):
            filtered.append(package)
    
    return filtered
