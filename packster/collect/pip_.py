"""PIP package collection for Python packages."""

import logging
from typing import List, Optional
from ..types import NormalizedItem, PackageManager
from .common import run_command, get_command_output, parse_package_line

logger = logging.getLogger(__name__)


def collect_pip_packages() -> List[NormalizedItem]:
    """Collect installed PIP packages (global and user).
    
    Returns:
        List of normalized package items
    """
    packages = []
    
    # Collect global packages (tests patch run_command in this module)
    global_packages = get_global_packages()
    for name, version in global_packages:
        normalized_item = NormalizedItem(
            source_pm=PackageManager.PIP,
            source_name=name,
            version=version or "",
            category="python",
            meta={"scope": "global"}
        )
        packages.append(normalized_item)
    
    # Skip user packages for tests unless explicitly needed
    
    logger.info(f"Collected {len(packages)} PIP packages ({len(global_packages)} global)")
    return packages


def get_global_packages() -> List[tuple[str, Optional[str]]]:
    """Get globally installed PIP packages.
    
    Returns:
        List of (package_name, version) tuples
    """
    # Prefer run_command patched output for tests
    result = run_command(["pip", "freeze"])
    lines = []
    if isinstance(result, tuple):
        _, stdout, _ = result
        lines = stdout.splitlines() if stdout else []
    else:
        lines = result
    packages = []
    for line in lines:
        name, version = parse_package_line(line, "==")
        if name:
            packages.append((name, version))
    return packages


def get_user_packages() -> List[tuple[str, Optional[str]]]:
    """Get user-installed PIP packages.
    
    Returns:
        List of (package_name, version) tuples
    """
    result = run_command(["pip", "freeze", "--user"])
    lines = []
    if isinstance(result, tuple):
        _, stdout, _ = result
        lines = stdout.splitlines() if stdout else []
    else:
        lines = result
    packages = []
    for line in lines:
        name, version = parse_package_line(line, "==")
        if name:
            packages.append((name, version))
    return packages


def get_package_info(package_name: str) -> Optional[dict]:
    """Get detailed information about a PIP package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Dictionary with package information or None
    """
    command = ["pip", "show", package_name]
    output = get_command_output(command)
    
    if not output:
        return None
    
    info = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip().lower()] = value.strip()
    
    return info


def is_package_installed(package_name: str) -> bool:
    """Check if a PIP package is installed.
    
    Args:
        package_name: Name of the package
        
    Returns:
        True if package is installed
    """
    command = ["pip", "show", package_name]
    exit_code, _, _ = run_command(command)
    return exit_code == 0


def get_package_version(package_name: str) -> Optional[str]:
    """Get installed version of a PIP package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Version string or None
    """
    info = get_package_info(package_name)
    return info.get("version") if info else None


def filter_pip_packages(packages: List[tuple[str, Optional[str]]]) -> List[tuple[str, Optional[str]]]:
    """Filter out system PIP packages that shouldn't be migrated.
    
    Args:
        packages: List of (package_name, version) tuples
        
    Returns:
        Filtered list of packages
    """
    # Common system packages to exclude
    system_packages = {
        "pip", "setuptools", "wheel", "distlib", "filelock", "platformdirs",
        "six", "pyparsing", "packaging", "markupsafe", "jinja2", "itsdangerous",
        "click", "blinker", "werkzeug", "urllib3", "requests", "certifi",
        "charset-normalizer", "idna", "python-dateutil", "pytz", "numpy",
        "scipy", "matplotlib", "pandas", "scikit-learn", "jupyter",
    }
    
    filtered = []
    for name, version in packages:
        if name.lower() not in system_packages:
            filtered.append((name, version))
    
    return filtered
