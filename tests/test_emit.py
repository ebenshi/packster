"""Tests for the emit module."""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open
from pathlib import Path
from packster.emit import (
    write_brewfile,
    write_language_files,
    write_bootstrap_script,
    write_reports,
)
from packster.types import (
    NormalizedItem,
    PackageManager,
    Candidate,
    MappingResult,
    Decision,
    Report,
)


class TestBrewfileGeneration:
    """Test Brewfile generation functionality."""
    
    def test_write_brewfile_success(self):
        """Test successful Brewfile generation."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="git", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="git", confidence=0.95),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="visual-studio-code", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="cask", target_name="visual-studio-code", confidence=0.90),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="vim", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="vim", confidence=0.7),
                decision=Decision.VERIFY
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_brewfile(mapping_results, output_dir)
            
            brewfile_path = output_dir / "Brewfile"
            assert brewfile_path.exists()
            
            content = brewfile_path.read_text()
            assert "brew 'git'" in content
            assert "cask 'visual-studio-code'" in content
            assert "brew 'vim'" in content
    
    def test_write_brewfile_empty_results(self):
        """Test Brewfile generation with empty results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_brewfile([], output_dir)
            
            brewfile_path = output_dir / "Brewfile"
            assert brewfile_path.exists()
            
            content = brewfile_path.read_text()
            # Should contain default taps but no packages
            assert "tap" in content
            assert "brew '" not in content
            assert "cask '" not in content
    
    def test_write_brewfile_only_manual(self):
        """Test Brewfile generation with only manual decisions."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="unknown", package_manager=PackageManager.APT),
                candidate=None,
                decision=Decision.MANUAL
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_brewfile(mapping_results, output_dir)
            
            brewfile_path = output_dir / "Brewfile"
            assert brewfile_path.exists()
            
            content = brewfile_path.read_text()
            # Should contain default taps but no packages
            assert "tap" in content
            assert "brew '" not in content
            assert "cask '" not in content


class TestLanguageFilesGeneration:
    """Test language-specific file generation."""
    
    def test_write_language_files_success(self):
        """Test successful language files generation."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="requests", package_manager=PackageManager.PIP),
                candidate=Candidate(target_pm="pip", target_name="requests", confidence=0.95),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="typescript", package_manager=PackageManager.NPM),
                candidate=Candidate(target_pm="npm", target_name="typescript", confidence=0.90),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="fd", package_manager=PackageManager.CARGO),
                candidate=Candidate(target_pm="cargo", target_name="fd", confidence=0.85),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="bundler", package_manager=PackageManager.GEM),
                candidate=Candidate(target_pm="gem", target_name="bundler", confidence=0.80),
                decision=Decision.AUTO
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_language_files(mapping_results, output_dir)
            
            # Check that lang directory was created
            lang_dir = output_dir / "lang"
            assert lang_dir.exists()
            
            # Check that language files were created
            assert (lang_dir / "requirements.txt").exists()
            assert (lang_dir / "global-node.txt").exists()
            assert (lang_dir / "cargo.txt").exists()
            assert (lang_dir / "gems.txt").exists()
            
            # Check content
            requirements_content = (lang_dir / "requirements.txt").read_text()
            assert "requests" in requirements_content
            
            node_content = (lang_dir / "global-node.txt").read_text()
            assert "typescript" in node_content
            
            cargo_content = (lang_dir / "cargo.txt").read_text()
            assert "fd" in cargo_content
            
            gems_content = (lang_dir / "gems.txt").read_text()
            assert "bundler" in gems_content
    
    def test_write_language_files_empty_results(self):
        """Test language files generation with empty results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_language_files([], output_dir)
            
            lang_dir = output_dir / "lang"
            assert lang_dir.exists()
            
            # Files should exist but be empty
            assert (lang_dir / "requirements.txt").exists()
            assert (lang_dir / "global-node.txt").exists()
            assert (lang_dir / "cargo.txt").exists()
            assert (lang_dir / "gems.txt").exists()
    
    def test_write_language_files_mixed_decisions(self):
        """Test language files generation with mixed decisions."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="requests", package_manager=PackageManager.PIP),
                candidate=Candidate(target_pm="pip", target_name="requests", confidence=0.95),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="unknown-pip", package_manager=PackageManager.PIP),
                candidate=None,
                decision=Decision.MANUAL
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_language_files(mapping_results, output_dir)
            
            lang_dir = output_dir / "lang"
            requirements_content = (lang_dir / "requirements.txt").read_text()
            
            # Should only include AUTO decisions
            assert "requests" in requirements_content
            assert "unknown-pip" not in requirements_content


class TestBootstrapScriptGeneration:
    """Test bootstrap script generation."""
    
    def test_write_bootstrap_script_success(self):
        """Test successful bootstrap script generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            bootstrap_path = output_dir / "bootstrap.sh"
            write_bootstrap_script(bootstrap_path)
            
            bootstrap_path = output_dir / "bootstrap.sh"
            assert bootstrap_path.exists()
            
            content = bootstrap_path.read_text()
            assert "#!/bin/bash" in content
            assert "set -e" in content
            assert "brew bundle" in content
            assert "Xcode Command Line Tools" in content
    
    def test_write_bootstrap_script_with_language_files(self):
        """Test bootstrap script generation with language files present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Create language files
            lang_dir = output_dir / "lang"
            lang_dir.mkdir()
            (lang_dir / "requirements.txt").write_text("requests==2.28.1")
            (lang_dir / "global-node.txt").write_text("typescript@4.9.4")
            
            bootstrap_path = output_dir / "bootstrap.sh"
            write_bootstrap_script(bootstrap_path)
            
            bootstrap_path = output_dir / "bootstrap.sh"
            content = bootstrap_path.read_text()
            
            # Should include language-specific installation
            assert "pip install" in content
            assert "npm install" in content
    
    def test_write_bootstrap_script_template_rendering(self):
        """Test bootstrap script template rendering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            bootstrap_path = output_dir / "bootstrap.sh"
            write_bootstrap_script(bootstrap_path)
            
            bootstrap_path = output_dir / "bootstrap.sh"
            content = bootstrap_path.read_text()
            
            # Check for template variables
            assert "{{" not in content
            assert "}}" not in content
            
            # Check for expected sections
            assert "Error handling" in content
            assert "Logging functions" in content
            assert "OS detection" in content
            assert "Homebrew installation" in content


class TestReportGeneration:
    """Test report generation functionality."""
    
    def test_write_reports_success(self):
        """Test successful report generation."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="git", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="git", confidence=0.95),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="vim", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="vim", confidence=0.7),
                decision=Decision.VERIFY
            ),
            MappingResult(
                source=NormalizedItem(name="unknown", package_manager=PackageManager.APT),
                candidate=None,
                decision=Decision.MANUAL
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_reports(mapping_results, output_dir)
            
            # Check JSON report
            json_path = output_dir / "report.json"
            assert json_path.exists()
            
            # Check HTML report
            html_path = output_dir / "report.html"
            assert html_path.exists()
            
            # Check HTML content
            html_content = html_path.read_text()
            assert "html" in html_content
            assert "Auto-Mapped Packages" in html_content
            assert "Verify Required Packages" in html_content
            assert "Manual Review Required" in html_content
    
    def test_write_reports_empty_results(self):
        """Test report generation with empty results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_reports([], output_dir)
            
            json_path = output_dir / "report.json"
            html_path = output_dir / "report.html"
            
            assert json_path.exists()
            assert html_path.exists()
            
            # Check that reports show zero counts
            html_content = html_path.read_text()
            assert "Total Packages: 0" in html_content
    
    def test_write_reports_json_structure(self):
        """Test JSON report structure."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="git", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="git", confidence=0.95),
                decision=Decision.AUTO
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_reports(mapping_results, output_dir)
            
            json_path = output_dir / "report.json"
            import json
            
            with open(json_path) as f:
                report_data = json.load(f)
            
            assert "total_packages" in report_data
            assert "auto_mapped" in report_data
            assert "verify_required" in report_data
            assert "manual_review" in report_data
            assert "skipped" in report_data
            assert "mapping_results" in report_data
    
    def test_write_reports_html_template_rendering(self):
        """Test HTML report template rendering."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="git", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="git", confidence=0.95),
                decision=Decision.AUTO
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_reports(mapping_results, output_dir)
            
            html_path = output_dir / "report.html"
            content = html_path.read_text()
            
            # Check for template variables
            assert "{{" not in content
            assert "}}" not in content
            
            # Check for expected sections
            assert "<!DOCTYPE html>" in content
            assert "<title>Packster Migration Report</title>" in content
            assert "Auto-Mapped Packages" in content


class TestFileValidation:
    """Test file validation functionality."""
    
    def test_brewfile_validation(self):
        """Test Brewfile validation."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="git", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="git", confidence=0.95),
                decision=Decision.AUTO
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_brewfile(mapping_results, output_dir)
            
            brewfile_path = output_dir / "Brewfile"
            content = brewfile_path.read_text()
            
            # Validate format
            lines = content.strip().split('\n')
            assert any(line.startswith("brew '") for line in lines)
            assert any(line.startswith("tap ") for line in lines)
    
    def test_language_files_validation(self):
        """Test language files validation."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="requests==2.28.1", package_manager=PackageManager.PIP),
                candidate=Candidate(target_pm="pip", target_name="requests", confidence=0.95),
                decision=Decision.AUTO
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_language_files(mapping_results, output_dir)
            
            requirements_path = output_dir / "lang" / "requirements.txt"
            content = requirements_path.read_text()
            
            # Validate format
            assert "requests" in content
            assert "==" in content or content.strip() == "requests"


class TestErrorHandling:
    """Test error handling in emit functions."""
    
    def test_write_brewfile_permission_error(self):
        """Test Brewfile generation with permission error."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="git", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="git", confidence=0.95),
                decision=Decision.AUTO
            )
        ]
        
        # Test with read-only directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            os.chmod(output_dir, 0o444)  # Read-only
            
            with pytest.raises(PermissionError):
                write_brewfile(mapping_results, output_dir)
    
    def test_write_language_files_directory_creation(self):
        """Test language files directory creation."""
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="requests", package_manager=PackageManager.PIP),
                candidate=Candidate(target_pm="pip", target_name="requests", confidence=0.95),
                decision=Decision.AUTO
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Ensure lang directory doesn't exist
            lang_dir = output_dir / "lang"
            if lang_dir.exists():
                lang_dir.rmdir()
            
            write_language_files(mapping_results, output_dir)
            
            # Should create the directory
            assert lang_dir.exists()
            assert (lang_dir / "requirements.txt").exists()
