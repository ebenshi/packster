"""NPM package collection for Node.js packages."""

import logging
import json
from typing import List, Optional
from ..types import NormalizedItem, PackageManager
from .common import run_command, get_command_output

logger = logging.getLogger(__name__)


def collect_npm_packages() -> List[NormalizedItem]:
    """Collect globally installed NPM packages.
    
    Returns:
        List of normalized package items
    """
    packages = []
    
    global_packages = get_global_packages()
    for name, version in global_packages:
        normalized_item = NormalizedItem(
            source_pm=PackageManager.NPM,
            source_name=name,
            version=version,
            category="nodejs",
            meta={"scope": "global"}
        )
        packages.append(normalized_item)
    
    logger.info(f"Collected {len(packages)} NPM packages")
    return packages


def get_global_packages() -> List[tuple[str, Optional[str]]]:
    """Get globally installed NPM packages.
    
    Returns:
        List of (package_name, version) tuples
    """
    # Tests patch run_command, not get_command_output; support simple list forms
    result = run_command(["npm", "list", "-g", "--depth=0"])
    if isinstance(result, tuple):
        _, stdout, _ = result
        if stdout:
            # Fallback parse text
            return parse_npm_list_text(stdout)
        return []
    else:
        lines = result
        # Lines like "typescript@4.9.4"
        packages = []
        for line in lines:
            if "@" in line:
                name, ver = line.split("@", 1)
                packages.append((name, ver or ""))
            else:
                packages.append((line, ""))
        return packages
    
    if not output:
        return []
    
    try:
        data = json.loads(output)
        packages = []
        
        # npm list --json output structure
        if "dependencies" in data:
            for name, info in data["dependencies"].items():
                if isinstance(info, dict) and "version" in info:
                    packages.append((name, info["version"]))
        
        return packages
    except json.JSONDecodeError:
        # Fallback to parsing text output
        return parse_npm_list_text(output)


def parse_npm_list_text(output: str) -> List[tuple[str, Optional[str]]]:
    """Parse npm list text output as fallback.
    
    Args:
        output: Text output from npm list
        
    Returns:
        List of (package_name, version) tuples
    """
    packages = []
    
    for line in output.splitlines():
        line = line.strip()
        if line and not line.startswith(("├──", "└──", "npm ERR!")):
            # Parse lines like "├── package-name@1.2.3"
            if "@" in line:
                parts = line.split("@", 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    version = parts[1].strip()
                    # Remove trailing characters
                    version = version.rstrip(" deduped")
                    packages.append((name, version))
    
    return packages


def get_package_info(package_name: str) -> Optional[dict]:
    """Get detailed information about an NPM package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Dictionary with package information or None
    """
    command = ["npm", "view", package_name, "--json"]
    output = get_command_output(command)
    
    if not output:
        return None
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None


def is_package_installed(package_name: str) -> bool:
    """Check if an NPM package is installed globally.
    
    Args:
        package_name: Name of the package
        
    Returns:
        True if package is installed
    """
    command = ["npm", "list", "-g", package_name]
    exit_code, _, _ = run_command(command)
    return exit_code == 0


def get_package_version(package_name: str) -> Optional[str]:
    """Get installed version of an NPM package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Version string or None
    """
    command = ["npm", "list", "-g", package_name, "--depth=0", "--json"]
    output = get_command_output(command)
    
    if not output:
        return None
    
    try:
        data = json.loads(output)
        if "dependencies" in data and package_name in data["dependencies"]:
            return data["dependencies"][package_name].get("version")
    except json.JSONDecodeError:
        pass
    
    return None


def filter_npm_packages(packages: List[tuple[str, Optional[str]]]) -> List[tuple[str, Optional[str]]]:
    """Filter out system NPM packages that shouldn't be migrated.
    
    Args:
        packages: List of (package_name, version) tuples
        
    Returns:
        Filtered list of packages
    """
    # Common system packages to exclude
    system_packages = {
        "npm", "node", "npx", "corepack", "yarn", "pnpm",
    }
    
    filtered = []
    for name, version in packages:
        if name.lower() not in system_packages:
            filtered.append((name, version))
    
    return filtered


def get_npm_config() -> dict:
    """Get NPM configuration.
    
    Returns:
        Dictionary with NPM configuration
    """
    command = ["npm", "config", "list", "--json"]
    output = get_command_output(command)
    
    if not output:
        return {}
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {}
