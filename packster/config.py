"""Configuration constants and paths for Packster."""

import os
from pathlib import Path
from typing import Dict, Any

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Default registry paths
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "registry" / "apt-to-brew.yaml"
DEFAULT_ALIASES_PATH = PROJECT_ROOT / "registry" / "aliases.yaml"

# Template paths
TEMPLATE_DIR = PROJECT_ROOT / "packster" / "runtime"
BOOTSTRAP_TEMPLATE = TEMPLATE_DIR / "bootstrap.sh.j2"
REPORT_TEMPLATE = TEMPLATE_DIR / "report.html.j2"

# Output structure
OUTPUT_DIRS = {
    "lang": "lang",
    "reports": ".",
}

OUTPUT_FILES = {
    "brewfile": "Brewfile",
    "bootstrap": "bootstrap.sh",
    "report_json": "report.json",
    "report_html": "report.html",
    "requirements": "lang/requirements.txt",
    "npm_global": "lang/global-node.txt",
    "cargo": "lang/cargo.txt",
    "gems": "lang/gems.txt",
}

# Decision thresholds
DECISION_THRESHOLDS = {
    "auto": 0.90,
    "verify": 0.60,
    "manual": 0.0,
}

# Package manager commands
PACKAGE_MANAGER_COMMANDS = {
    "apt": {
        "manual_packages": ["apt-mark", "showmanual"],
        "installed_packages": ["dpkg", "--get-selections"],
    },
    "pip": {
        "global_packages": ["pip", "freeze"],
        "user_packages": ["pip", "freeze", "--user"],
    },
    "npm": {
        "global_packages": ["npm", "list", "-g", "--depth=0"],
    },
    "cargo": {
        "installed_packages": ["cargo", "install", "--list"],
    },
    "gem": {
        "installed_packages": ["gem", "list", "--local"],
    },
}

# Homebrew validation commands
HOMEBREW_COMMANDS = {
    "info": ["brew", "info"],
    "info_cask": ["brew", "info", "--cask"],
    "search": ["brew", "search"],
    "search_cask": ["brew", "search", "--cask"],
}

# Default Homebrew taps
DEFAULT_BREW_TAPS = [
    "homebrew/core",
    "homebrew/cask",
]

# Common package categories
PACKAGE_CATEGORIES = {
    "development": ["git", "vim", "neovim", "tmux", "htop", "tree"],
    "utilities": ["curl", "wget", "jq", "ripgrep", "fd", "bat"],
    "languages": ["python", "node", "go", "rust", "ruby"],
    "build_tools": ["cmake", "make", "pkg-config", "autoconf"],
    "databases": ["postgresql", "mysql", "sqlite", "redis"],
    "containers": ["docker", "kubernetes", "helm"],
    "cloud": ["awscli", "terraform", "gcloud", "az"],
}

# File extensions and patterns
FILE_PATTERNS = {
    "python": ["*.py", "*.pyc", "*.pyo"],
    "javascript": ["*.js", "*.jsx", "*.ts", "*.tsx"],
    "rust": ["*.rs", "Cargo.toml", "Cargo.lock"],
    "ruby": ["*.rb", "Gemfile", "Gemfile.lock"],
}

# Error messages
ERROR_MESSAGES = {
    "command_not_found": "Command '{command}' not found in PATH",
    "command_failed": "Command '{command}' failed with exit code {code}",
    "file_not_found": "File '{file}' not found",
    "invalid_yaml": "Invalid YAML in file '{file}': {error}",
    "invalid_json": "Invalid JSON in file '{file}': {error}",
    "template_not_found": "Template '{template}' not found",
    "output_dir_exists": "Output directory '{dir}' already exists",
    "no_packages_found": "No packages found for {pm}",
}

# Success messages
SUCCESS_MESSAGES = {
    "generation_complete": "Migration files generated successfully in '{dir}'",
    "packages_collected": "Collected {count} packages from {pm}",
    "mapping_complete": "Mapped {total} packages ({auto} auto, {verify} verify, {manual} manual)",
    "validation_complete": "Validated {valid}/{total} candidates",
}

# Console colors and styling
CONSOLE_STYLES = {
    "success": "green",
    "warning": "yellow", 
    "error": "red",
    "info": "blue",
    "header": "bold cyan",
    "subheader": "cyan",
    "code": "dim",
}

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "target": "macos",
    "verify": True,
    "format": "json",
    "include_skipped": False,
    "max_candidates": 5,
    "min_confidence": 0.1,
}
