"""Package normalization utilities for Packster."""

import logging
from typing import List, Dict, Any
from .types import NormalizedItem, PackageManager
from .collect import (
    collect_apt_packages,
    collect_pip_packages,
    collect_npm_packages,
    collect_cargo_packages,
    collect_gem_packages,
)

logger = logging.getLogger(__name__)


def normalize_all_packages() -> List[NormalizedItem]:
    """Collect and normalize packages from all available package managers.
    
    Returns:
        List of normalized package items
    """
    all_packages = []
    
    # Collect from each package manager
    collectors = [
        ("apt", collect_apt_packages),
        ("pip", collect_pip_packages),
        ("npm", collect_npm_packages),
        ("cargo", collect_cargo_packages),
        ("gem", collect_gem_packages),
    ]
    
    for pm_name, collector in collectors:
        try:
            packages = collector()
            all_packages.extend(packages)
            logger.info(f"Collected {len(packages)} packages from {pm_name}")
        except Exception as e:
            logger.warning(f"Failed to collect packages from {pm_name}: {e}")
    
    # Filter and deduplicate
    filtered_packages = filter_packages(all_packages)
    deduplicated_packages = deduplicate_packages(filtered_packages)
    
    logger.info(f"Normalized {len(deduplicated_packages)} unique packages")
    return deduplicated_packages


def filter_packages(packages: List[NormalizedItem]) -> List[NormalizedItem]:
    """Filter out packages that shouldn't be migrated.
    
    Args:
        packages: List of normalized packages
        
    Returns:
        Filtered list of packages
    """
    filtered = []
    
    for package in packages:
        if should_include_package(package):
            filtered.append(package)
    
    return filtered


def should_include_package(package: NormalizedItem) -> bool:
    """Determine if a package should be included in migration.
    
    Args:
        package: Normalized package item
        
    Returns:
        True if package should be included
    """
    name = package.source_name.lower()
    
    # Skip system packages
    system_packages = {
        # APT system packages
        "apt", "dpkg", "base-files", "base-passwd", "bash", "coreutils",
        "dash", "debianutils", "diffutils", "findutils", "grep", "gzip",
        "hostname", "init-system-helpers", "libc-bin", "libpam-modules",
        "libpam-runtime", "login", "mount", "passwd", "perl-base",
        "sed", "sysvinit-utils", "tar", "util-linux", "zlib1g",
        "ubuntu-minimal", "ubuntu-standard", "ubuntu-server",
        
        # Python system packages
        "pip", "setuptools", "wheel", "distlib", "filelock", "platformdirs",
        "six", "pyparsing", "packaging", "markupsafe", "jinja2", "itsdangerous",
        "click", "blinker", "werkzeug", "urllib3", "requests", "certifi",
        "charset-normalizer", "idna", "python-dateutil", "pytz",
        
        # Node.js system packages
        "npm", "node", "npx", "corepack", "yarn", "pnpm",
        
        # Rust system packages
        "cargo", "rustc", "rustup", "rustfmt", "clippy",
        
        # Ruby system packages
        "bundler", "rake", "rdoc", "json", "minitest", "test-unit",
        "bigdecimal", "io-console", "psych", "stringio", "strscan",
    }
    
    if name in system_packages:
        return False
    
    # Skip library packages (usually start with lib)
    if name.startswith("lib"):
        return False
    
    # Skip development packages (usually end with -dev)
    if name.endswith("-dev"):
        return False
    
    # Skip debug packages (usually end with -dbg)
    if name.endswith("-dbg"):
        return False
    
    # Skip documentation packages (usually end with -doc)
    if name.endswith("-doc"):
        return False
    
    return True


def deduplicate_packages(packages: List[NormalizedItem]) -> List[NormalizedItem]:
    """Remove duplicate packages based on name and package manager.
    
    Args:
        packages: List of normalized packages
        
    Returns:
        Deduplicated list of packages
    """
    seen = set()
    deduplicated = []
    
    for package in packages:
        # Create a unique key based on package manager and name
        key = (package.source_pm, package.source_name.lower())
        
        if key not in seen:
            seen.add(key)
            deduplicated.append(package)
        else:
            # If we have a duplicate, prefer the one with more metadata
            existing_idx = next(i for i, p in enumerate(deduplicated) 
                              if (p.source_pm, p.source_name.lower()) == key)
            existing = deduplicated[existing_idx]
            
            # Replace if current package has more metadata
            if len(package.meta) > len(existing.meta):
                deduplicated[existing_idx] = package
    
    return deduplicated


def categorize_package(package: NormalizedItem) -> str:
    """Categorize a package based on its name and metadata.
    
    Args:
        package: Normalized package item
        
    Returns:
        Package category
    """
    name = package.source_name.lower()
    
    # Development tools
    dev_tools = {
        "git", "vim", "neovim", "tmux", "htop", "tree", "cmake", "make",
        "autoconf", "automake", "pkg-config", "gcc", "g++", "clang",
        "lldb", "gdb", "valgrind", "strace", "ltrace",
    }
    
    # Utilities
    utilities = {
        "curl", "wget", "jq", "ripgrep", "fd", "bat", "eza", "fzf",
        "unzip", "zip", "tar", "gzip", "bzip2", "xz", "zstd",
        "rsync", "ncdu", "httpie", "nmap", "watch", "parallel",
    }
    
    # Languages and runtimes
    languages = {
        "python", "python3", "node", "nodejs", "go", "rust", "ruby",
        "java", "kotlin", "scala", "clojure", "haskell", "ocaml",
        "erlang", "elixir", "crystal", "nim", "zig", "v",
    }
    
    # Build tools
    build_tools = {
        "maven", "gradle", "sbt", "cargo", "npm", "yarn", "pnpm",
        "pip", "poetry", "pipenv", "conda", "mamba",
    }
    
    # Databases
    databases = {
        "postgresql", "mysql", "sqlite", "redis", "mongodb", "cassandra",
        "elasticsearch", "influxdb", "timescaledb", "cockroachdb",
    }
    
    # Containers and orchestration
    containers = {
        "docker", "kubernetes", "helm", "kubectl", "minikube", "kind",
        "docker-compose", "podman", "buildah", "skopeo",
    }
    
    # Cloud tools
    cloud_tools = {
        "awscli", "terraform", "gcloud", "az", "doctl", "kubectl",
        "helm", "istioctl", "linkerd", "consul", "vault",
    }
    
    # Check categories
    if name in dev_tools:
        return "development"
    elif name in utilities:
        return "utilities"
    elif name in languages:
        return "languages"
    elif name in build_tools:
        return "build_tools"
    elif name in databases:
        return "databases"
    elif name in containers:
        return "containers"
    elif name in cloud_tools:
        return "cloud"
    else:
        return "other"


def enrich_package_metadata(package: NormalizedItem) -> NormalizedItem:
    """Enrich package metadata with additional information.
    
    Args:
        package: Normalized package item
        
    Returns:
        Enriched package item
    """
    # Add category if not present
    if not package.category:
        package.category = categorize_package(package)
    
    # Add additional metadata
    meta = package.meta.copy()
    
    # Add package manager specific metadata
    if package.source_pm == PackageManager.APT:
        meta["package_type"] = "system"
    elif package.source_pm == PackageManager.PIP:
        meta["package_type"] = "python"
    elif package.source_pm == PackageManager.NPM:
        meta["package_type"] = "nodejs"
    elif package.source_pm == PackageManager.CARGO:
        meta["package_type"] = "rust"
    elif package.source_pm == PackageManager.GEM:
        meta["package_type"] = "ruby"
    
    # Create new package with enriched metadata
    return NormalizedItem(
        source_pm=package.source_pm,
        source_name=package.source_name,
        version=package.version,
        category=package.category,
        meta=meta
    )


def get_package_statistics(packages: List[NormalizedItem]) -> Dict[str, Any]:
    """Get statistics about the collected packages.
    
    Args:
        packages: List of normalized packages
        
    Returns:
        Dictionary with package statistics
    """
    stats = {
        "total": len(packages),
        "by_package_manager": {},
        "by_category": {},
        "with_versions": 0,
        "without_versions": 0,
    }
    
    # Count by package manager
    for package in packages:
        pm = package.source_pm.value
        stats["by_package_manager"][pm] = stats["by_package_manager"].get(pm, 0) + 1
    
    # Count by category
    for package in packages:
        category = package.category or "unknown"
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
    
    # Count version information
    for package in packages:
        if package.version:
            stats["with_versions"] += 1
        else:
            stats["without_versions"] += 1
    
    return stats
