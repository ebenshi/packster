"""Pytest configuration and common fixtures for Packster tests."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from packster.types import (
    NormalizedItem,
    PackageManager,
    Candidate,
    MappingResult,
    Decision,
)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_normalized_items():
    """Provide sample NormalizedItem instances for testing."""
    return [
        NormalizedItem(
            name="git",
            version="2.25.1",
            package_manager=PackageManager.APT,
            description="Git version control system",
            category="development"
        ),
        NormalizedItem(
            name="vim",
            version="8.2",
            package_manager=PackageManager.APT,
            description="Vi IMproved text editor",
            category="editors"
        ),
        NormalizedItem(
            name="requests",
            version="2.28.1",
            package_manager=PackageManager.PIP,
            description="HTTP library for Python",
            category="python"
        ),
        NormalizedItem(
            name="typescript",
            version="4.9.4",
            package_manager=PackageManager.NPM,
            description="Typed superset of JavaScript",
            category="javascript"
        ),
        NormalizedItem(
            name="fd",
            version="8.4.0",
            package_manager=PackageManager.CARGO,
            description="Simple, fast alternative to find",
            category="utilities"
        ),
        NormalizedItem(
            name="bundler",
            version="2.4.9",
            package_manager=PackageManager.GEM,
            description="Ruby dependency manager",
            category="ruby"
        ),
    ]


@pytest.fixture
def sample_candidates():
    """Provide sample Candidate instances for testing."""
    return [
        Candidate(
            target_pm="brew",
            target_name="git",
            confidence=0.95,
            reason="Direct mapping"
        ),
        Candidate(
            target_pm="brew",
            target_name="vim",
            confidence=0.90,
            reason="Direct mapping"
        ),
        Candidate(
            target_pm="pip",
            target_name="requests",
            confidence=0.95,
            reason="Direct mapping"
        ),
        Candidate(
            target_pm="npm",
            target_name="typescript",
            confidence=0.90,
            reason="Direct mapping"
        ),
        Candidate(
            target_pm="brew",
            target_name="fd",
            confidence=0.85,
            reason="Heuristic mapping"
        ),
        Candidate(
            target_pm="gem",
            target_name="bundler",
            confidence=0.80,
            reason="Direct mapping"
        ),
    ]


@pytest.fixture
def sample_mapping_results(sample_normalized_items, sample_candidates):
    """Provide sample MappingResult instances for testing."""
    return [
        MappingResult(
            source=sample_normalized_items[0],
            candidate=sample_candidates[0],
            decision=Decision.AUTO
        ),
        MappingResult(
            source=sample_normalized_items[1],
            candidate=sample_candidates[1],
            decision=Decision.AUTO
        ),
        MappingResult(
            source=sample_normalized_items[2],
            candidate=sample_candidates[2],
            decision=Decision.AUTO
        ),
        MappingResult(
            source=sample_normalized_items[3],
            candidate=sample_candidates[3],
            decision=Decision.VERIFY
        ),
        MappingResult(
            source=sample_normalized_items[4],
            candidate=sample_candidates[4],
            decision=Decision.VERIFY
        ),
        MappingResult(
            source=sample_normalized_items[5],
            candidate=sample_candidates[5],
            decision=Decision.AUTO
        ),
    ]


@pytest.fixture
def mixed_mapping_results(sample_normalized_items, sample_candidates):
    """Provide mapping results with mixed decisions for testing."""
    return [
        MappingResult(
            source=sample_normalized_items[0],
            candidate=sample_candidates[0],
            decision=Decision.AUTO
        ),
        MappingResult(
            source=sample_normalized_items[1],
            candidate=sample_candidates[1],
            decision=Decision.VERIFY
        ),
        MappingResult(
            source=sample_normalized_items[2],
            candidate=None,
            decision=Decision.MANUAL
        ),
        MappingResult(
            source=sample_normalized_items[3],
            candidate=None,
            decision=Decision.SKIP
        ),
    ]


@pytest.fixture
def mock_registry():
    """Provide a mock registry for testing."""
    registry = MagicMock()
    registry.name = "Test Registry"
    registry.description = "Test registry for unit tests"
    registry.version = "1.0.0"
    registry.mappings = {
        "git": MagicMock(
            target_pm="brew",
            target_name="git",
            confidence=0.95,
            reason="Direct mapping"
        ),
        "vim": MagicMock(
            target_pm="brew",
            target_name="vim",
            confidence=0.90,
            reason="Direct mapping"
        ),
        "requests": MagicMock(
            target_pm="pip",
            target_name="requests",
            confidence=0.95,
            reason="Direct mapping"
        ),
    }
    return registry


@pytest.fixture
def mock_package_mapper():
    """Provide a mock PackageMapper for testing."""
    mapper = MagicMock()
    mapper.validate_candidates = False
    mapper.auto_threshold = 0.8
    mapper.verify_threshold = 0.6
    return mapper


@pytest.fixture
def sample_apt_packages():
    """Provide sample APT package data for testing."""
    return [
        "git",
        "vim",
        "curl",
        "wget",
        "htop",
        "tree",
        "tmux",
        "zsh",
        "docker.io",
        "nodejs",
    ]


@pytest.fixture
def sample_pip_packages():
    """Provide sample pip package data for testing."""
    return [
        "requests==2.28.1",
        "click==8.1.3",
        "rich==13.0.0",
        "pydantic==2.0.0",
        "pyyaml==6.0",
        "jinja2==3.1.0",
    ]


@pytest.fixture
def sample_npm_packages():
    """Provide sample npm package data for testing."""
    return [
        "typescript@4.9.4",
        "eslint@8.31.0",
        "prettier@2.8.0",
        "jest@29.3.1",
        "webpack@5.75.0",
    ]


@pytest.fixture
def sample_cargo_packages():
    """Provide sample cargo package data for testing."""
    return [
        "fd 8.4.0:",
        "ripgrep 13.0.0:",
        "bat 0.20.0:",
        "eza 0.9.0:",
        "fzf 0.35.1:",
    ]


@pytest.fixture
def sample_gem_packages():
    """Provide sample gem package data for testing."""
    return [
        "bundler (2.4.9)",
        "rails (7.0.4.2)",
        "jekyll (4.3.0)",
        "cocoapods (1.12.0)",
        "fastlane (2.210.0)",
    ]


@pytest.fixture
def sample_brew_info():
    """Provide sample Homebrew info output for testing."""
    return """git: stable 2.39.2
Git is a distributed version control system
https://git-scm.com/
/usr/local/Cellar/git/2.39.2 (1,525 files, 47.5MB) *
  Poured from bottle on 2023-01-15 at 10:30:00
From: https://github.com/Homebrew/homebrew-core/blob/HEAD/Formula/g/git.rb
License: GPL-2.0-only
==> Dependencies
Build: pkg-config ✘
Required: gettext ✘, libiconv ✘, openssl@1.1 ✘, pcre2 ✘, zlib ✘
==> Analytics
install: 1,234,567 (30 days), 3,456,789 (90 days), 9,876,543 (365 days)
install-on-request: 1,234,567 (30 days), 3,456,789 (90 days), 9,876,543 (365 days)
build-error: 0 (30 days)"""


@pytest.fixture
def sample_cask_info():
    """Provide sample Homebrew cask info output for testing."""
    return """visual-studio-code: 1.85.1
Visual Studio Code is a code editor
https://code.visualstudio.com/
/usr/local/Caskroom/visual-studio-code/1.85.1/Visual Studio Code.app (1,234 files, 567.8MB)
From: https://github.com/Homebrew/homebrew-cask/blob/HEAD/Casks/visual-studio-code.rb
==> Name
Visual Studio Code
==> Description
Code editor
==> Artifacts
Visual Studio Code.app (App)
==> Analytics
install: 12,345 (30 days), 34,567 (90 days), 98,765 (365 days)
install-on-request: 12,345 (30 days), 34,567 (90 days), 98,765 (365 days)
build-error: 0 (30 days)"""


@pytest.fixture
def sample_brew_search_results():
    """Provide sample Homebrew search results for testing."""
    return """git
git-crypt
git-extras
git-flow
git-lfs
git-secrets
git-town
git-utils"""


@pytest.fixture
def sample_installed_brew_packages():
    """Provide sample installed Homebrew packages for testing."""
    return """git
vim
curl
wget
htop
tree
tmux
zsh"""


@pytest.fixture
def sample_installed_cask_packages():
    """Provide sample installed Homebrew casks for testing."""
    return """visual-studio-code
slack
discord
spotify
vlc"""


@pytest.fixture
def mock_system_info():
    """Provide mock system information for testing."""
    return {
        "os": "ubuntu",
        "architecture": "x86_64",
        "wsl": "False",
        "python_version": "3.10.0",
        "platform": "Linux-5.4.0-x86_64",
        "processor": "x86_64"
    }


@pytest.fixture
def mock_environment_info(mock_system_info):
    """Provide mock environment information for testing."""
    return {
        "system": mock_system_info,
        "package_managers": {
            "apt": True,
            "pip": True,
            "npm": True,
            "cargo": True,
            "gem": True
        },
        "homebrew_available": False,
        "homebrew_path": None,
        "user": "testuser",
        "path": "/usr/bin:/usr/local/bin"
    }


@pytest.fixture
def sample_brewfile_content():
    """Provide sample Brewfile content for testing."""
    return """# Homebrew taps
tap "homebrew/core"
tap "homebrew/cask"
tap "homebrew/cask-fonts"

# Homebrew packages
brew "git"
brew "vim"
brew "curl"
brew "wget"
brew "htop"
brew "tree"
brew "tmux"
brew "zsh"

# Homebrew casks
cask "visual-studio-code"
cask "slack"
cask "discord"
cask "spotify"
cask "vlc"
"""


@pytest.fixture
def sample_requirements_txt_content():
    """Provide sample requirements.txt content for testing."""
    return """requests==2.28.1
click==8.1.3
rich==13.0.0
pydantic==2.0.0
pyyaml==6.0
jinja2==3.1.0
"""


@pytest.fixture
def sample_global_node_txt_content():
    """Provide sample global-node.txt content for testing."""
    return """typescript@4.9.4
eslint@8.31.0
prettier@2.8.0
jest@29.3.1
webpack@5.75.0
"""


@pytest.fixture
def sample_cargo_txt_content():
    """Provide sample cargo.txt content for testing."""
    return """fd
ripgrep
bat
eza
fzf
"""


@pytest.fixture
def sample_gems_txt_content():
    """Provide sample gems.txt content for testing."""
    return """bundler
rails
jekyll
cocoapods
fastlane
"""


@pytest.fixture
def sample_bootstrap_script_content():
    """Provide sample bootstrap.sh content for testing."""
    return """#!/bin/bash
set -e

# Error handling
set -o pipefail

# Logging functions
log_info() {
    echo -e "\\033[32m[INFO]\\033[0m $1"
}

log_warn() {
    echo -e "\\033[33m[WARN]\\033[0m $1"
}

log_error() {
    echo -e "\\033[31m[ERROR]\\033[0m $1"
}

# OS detection
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    log_error "This script is designed for macOS only"
    exit 1
fi

# Check for Xcode Command Line Tools
if ! xcode-select -p &> /dev/null; then
    log_info "Installing Xcode Command Line Tools..."
    xcode-select --install
    log_warn "Please complete the Xcode Command Line Tools installation and run this script again"
    exit 0
fi

# Install Homebrew if not present
if ! command -v brew &> /dev/null; then
    log_info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Update Homebrew
log_info "Updating Homebrew..."
brew update

# Install packages from Brewfile
if [ -f "Brewfile" ]; then
    log_info "Installing packages from Brewfile..."
    brew bundle
else
    log_warn "Brewfile not found"
fi

# Install language-specific packages
if [ -f "lang/requirements.txt" ]; then
    log_info "Installing Python packages..."
    pip3 install -r lang/requirements.txt
fi

if [ -f "lang/global-node.txt" ]; then
    log_info "Installing Node.js packages..."
    npm install -g $(cat lang/global-node.txt)
fi

if [ -f "lang/cargo.txt" ]; then
    log_info "Installing Rust packages..."
    while read -r package; do
        if [ -n "$package" ]; then
            cargo install "$package"
        fi
    done < lang/cargo.txt
fi

if [ -f "lang/gems.txt" ]; then
    log_info "Installing Ruby gems..."
    gem install $(cat lang/gems.txt)
fi

log_info "Migration completed successfully!"
"""


@pytest.fixture
def sample_report_data():
    """Provide sample report data for testing."""
    return {
        "total_packages": 6,
        "auto_mapped": 3,
        "verify_required": 2,
        "manual_review": 1,
        "skipped": 0,
        "mapping_results": [
            {
                "source": {
                    "name": "git",
                    "version": "2.25.1",
                    "package_manager": "APT",
                    "description": "Git version control system",
                    "category": "development"
                },
                "candidate": {
                    "target_pm": "brew",
                    "target_name": "git",
                    "confidence": 0.95,
                    "reason": "Direct mapping"
                },
                "decision": "AUTO"
            },
            {
                "source": {
                    "name": "vim",
                    "version": "8.2",
                    "package_manager": "APT",
                    "description": "Vi IMproved text editor",
                    "category": "editors"
                },
                "candidate": {
                    "target_pm": "brew",
                    "target_name": "vim",
                    "confidence": 0.7,
                    "reason": "Heuristic mapping"
                },
                "decision": "VERIFY"
            },
            {
                "source": {
                    "name": "unknown-package",
                    "version": "1.0.0",
                    "package_manager": "APT",
                    "description": "",
                    "category": ""
                },
                "candidate": None,
                "decision": "MANUAL"
            }
        ]
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Mark unit tests
        elif any(module in item.nodeid for module in ["test_detect", "test_collect", "test_map", "test_validate", "test_emit"]):
            item.add_marker(pytest.mark.unit)
        # Mark slow tests
        if "large" in item.nodeid or "performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)
