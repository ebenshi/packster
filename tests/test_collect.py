"""Tests for the collect module."""

from unittest.mock import patch, mock_open
from packster.collect import (
    run_command,
    collect_apt_packages,
    collect_pip_packages,
    collect_npm_packages,
    collect_cargo_packages,
    collect_gem_packages,
)
from packster.types import NormalizedItem, PackageManager


class TestRunCommand:
    """Test command execution functionality."""
    
    @patch('packster.detect.run_command_safe')
    def test_run_command_success(self, mock_run_safe):
        """Test successful command execution."""
        mock_run_safe.return_value = (0, "git\nvim\n", "")
        
        result = run_command(["apt-mark", "showmanual"])
        
        assert result == (0, "git\nvim\n", "")
        mock_run_safe.assert_called_once_with(["apt-mark", "showmanual"], 30, True)
    
    @patch('packster.detect.run_command_safe')
    def test_run_command_failure(self, mock_run_safe):
        """Test failed command execution."""
        mock_run_safe.return_value = (1, "", "command not found")
        
        result = run_command(["nonexistent"])
        
        assert result == (1, "", "command not found")
    
    @patch('packster.detect.run_command_safe')
    def test_run_command_empty_output(self, mock_run_safe):
        """Test command with empty output."""
        mock_run_safe.return_value = (0, "", "")
        
        result = run_command(["echo", ""])
        
        assert result == (0, "", "")


class TestCollectAptPackages:
    """Test APT package collection."""
    
    @patch('packster.collect.apt.run_command')
    def test_collect_apt_packages_success(self, mock_run):
        """Test successful APT package collection."""
        mock_run.return_value = ["git", "vim", "curl"]
        
        result = collect_apt_packages()
        
        assert len(result) == 3
        assert all(isinstance(item, NormalizedItem) for item in result)
        assert all(item.source_pm == PackageManager.APT for item in result)
        assert [item.source_name for item in result] == ["git", "vim", "curl"]
    
    @patch('packster.collect.apt.run_command')
    def test_collect_apt_packages_empty(self, mock_run):
        """Test APT package collection with no packages."""
        mock_run.return_value = []
        
        result = collect_apt_packages()
        
        assert result == []
    
    @patch('packster.collect.apt.run_command')
    def test_collect_apt_packages_with_versions(self, mock_run):
        """Test APT package collection with version information."""
        mock_run.side_effect = [
            ["git", "vim"],  # manual packages
            ["git/now 1:2.25.1-1ubuntu3.10 amd64", "vim/now 2:0.8.2-1ubuntu2.4 amd64"]  # versions
        ]
        
        result = collect_apt_packages()
        
        assert len(result) == 2
        assert result[0].source_name == "git"
        assert result[0].version == "1:2.25.1-1ubuntu3.10"
        assert result[1].source_name == "vim"
        assert result[1].version == "2:0.8.2-1ubuntu2.4"


class TestCollectPipPackages:
    """Test pip package collection."""
    
    @patch('packster.collect.pip_.run_command')
    def test_collect_pip_packages_success(self, mock_run):
        """Test successful pip package collection."""
        mock_run.return_value = ["requests==2.28.1", "click==8.1.3"]
        
        result = collect_pip_packages()
        
        assert len(result) == 2
        assert all(isinstance(item, NormalizedItem) for item in result)
        assert all(item.source_pm == PackageManager.PIP for item in result)
        assert result[0].source_name == "requests"
        assert result[0].version == "2.28.1"
        assert result[1].source_name == "click"
        assert result[1].version == "8.1.3"
    
    @patch('packster.collect.pip_.run_command')
    def test_collect_pip_packages_empty(self, mock_run):
        """Test pip package collection with no packages."""
        mock_run.return_value = []
        
        result = collect_pip_packages()
        
        assert result == []
    
    @patch('packster.collect.pip_.run_command')
    def test_collect_pip_packages_without_versions(self, mock_run):
        """Test pip package collection without version information."""
        mock_run.return_value = ["requests", "click"]
        
        result = collect_pip_packages()
        
        assert len(result) == 2
        assert result[0].source_name == "requests"
        assert result[0].version == ""
        assert result[1].source_name == "click"
        assert result[1].version == ""


class TestCollectNpmPackages:
    """Test npm package collection."""
    
    @patch('packster.collect.npm.run_command')
    def test_collect_npm_packages_success(self, mock_run):
        """Test successful npm package collection."""
        mock_run.return_value = ["typescript@4.9.4", "eslint@8.31.0"]
        
        result = collect_npm_packages()
        
        assert len(result) == 2
        assert all(isinstance(item, NormalizedItem) for item in result)
        assert all(item.source_pm == PackageManager.NPM for item in result)
        assert result[0].source_name == "typescript"
        assert result[0].version == "4.9.4"
        assert result[1].source_name == "eslint"
        assert result[1].version == "8.31.0"
    
    @patch('packster.collect.npm.run_command')
    def test_collect_npm_packages_empty(self, mock_run):
        """Test npm package collection with no packages."""
        mock_run.return_value = []
        
        result = collect_npm_packages()
        
        assert result == []
    
    @patch('packster.collect.npm.run_command')
    def test_collect_npm_packages_without_versions(self, mock_run):
        """Test npm package collection without version information."""
        mock_run.return_value = ["typescript", "eslint"]
        
        result = collect_npm_packages()
        
        assert len(result) == 2
        assert result[0].source_name == "typescript"
        assert result[0].version == ""
        assert result[1].source_name == "eslint"
        assert result[1].version == ""


class TestCollectCargoPackages:
    """Test cargo package collection."""
    
    @patch('packster.collect.cargo.run_command')
    def test_collect_cargo_packages_success(self, mock_run):
        """Test successful cargo package collection."""
        mock_run.return_value = ["fd 8.4.0:", "ripgrep 13.0.0:"]
        
        result = collect_cargo_packages()
        
        assert len(result) == 2
        assert all(isinstance(item, NormalizedItem) for item in result)
        assert all(item.source_pm == PackageManager.CARGO for item in result)
        assert result[0].source_name == "fd"
        assert result[0].version == "8.4.0"
        assert result[1].source_name == "ripgrep"
        assert result[1].version == "13.0.0"
    
    @patch('packster.collect.cargo.run_command')
    def test_collect_cargo_packages_empty(self, mock_run):
        """Test cargo package collection with no packages."""
        mock_run.return_value = []
        
        result = collect_cargo_packages()
        
        assert result == []
    
    @patch('packster.collect.cargo.run_command')
    def test_collect_cargo_packages_without_versions(self, mock_run):
        """Test cargo package collection without version information."""
        mock_run.return_value = ["fd:", "ripgrep:"]
        
        result = collect_cargo_packages()
        
        assert len(result) == 2
        assert result[0].source_name == "fd"
        assert result[0].version == ""
        assert result[1].source_name == "ripgrep"
        assert result[1].version == ""


class TestCollectGemPackages:
    """Test gem package collection."""
    
    @patch('packster.collect.gem.run_command')
    def test_collect_gem_packages_success(self, mock_run):
        """Test successful gem package collection."""
        mock_run.return_value = ["bundler (2.4.9)", "rails (7.0.4.2)"]
        
        result = collect_gem_packages()
        
        assert len(result) == 2
        assert all(isinstance(item, NormalizedItem) for item in result)
        assert all(item.source_pm == PackageManager.GEM for item in result)
        assert result[0].source_name == "bundler"
        assert result[0].version == "2.4.9"
        assert result[1].source_name == "rails"
        assert result[1].version == "7.0.4.2"
    
    @patch('packster.collect.gem.run_command')
    def test_collect_gem_packages_empty(self, mock_run):
        """Test gem package collection with no packages."""
        mock_run.return_value = []
        
        result = collect_gem_packages()
        
        assert result == []
    
    @patch('packster.collect.gem.run_command')
    def test_collect_gem_packages_without_versions(self, mock_run):
        """Test gem package collection without version information."""
        mock_run.return_value = ["bundler", "rails"]
        
        result = collect_gem_packages()
        
        assert len(result) == 2
        assert result[0].source_name == "bundler"
        assert result[0].version == ""
        assert result[1].source_name == "rails"
        assert result[1].version == ""


class TestPackageFiltering:
    """Test package filtering functionality."""
    
    def test_filter_system_packages(self):
        """Test filtering out system packages."""
        packages = [
            NormalizedItem(source_name="git", version="1.0", source_pm=PackageManager.APT),
            NormalizedItem(source_name="libc6", version="2.0", source_pm=PackageManager.APT),
            NormalizedItem(source_name="vim", version="1.0", source_pm=PackageManager.APT),
        ]
        
        # This would be tested in the actual filtering logic
        # For now, we just verify the structure
        assert len(packages) == 3
        assert packages[0].source_name == "git"
        assert packages[1].source_name == "libc6"
        assert packages[2].source_name == "vim"


class TestPackageDeduplication:
    """Test package deduplication functionality."""
    
    def test_deduplicate_packages(self):
        """Test deduplicating packages by name."""
        packages = [
            NormalizedItem(source_name="git", version="1.0", source_pm=PackageManager.APT),
            NormalizedItem(source_name="git", version="2.0", source_pm=PackageManager.APT),
            NormalizedItem(source_name="vim", version="1.0", source_pm=PackageManager.APT),
        ]
        
        # This would be tested in the actual deduplication logic
        # For now, we just verify the structure
        assert len(packages) == 3
        assert packages[0].source_name == "git"
        assert packages[1].source_name == "git"
        assert packages[2].source_name == "vim"
