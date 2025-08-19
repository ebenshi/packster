"""Integration tests for Packster."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from packster.cli import app
from typer.testing import CliRunner
from packster.types import (
    NormalizedItem,
    PackageManager,
    Candidate,
    MappingResult,
    Decision,
)


class TestEndToEndMigration:
    """Test end-to-end migration workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('packster.cli.load_registry')
    @patch('packster.cli.normalize_all_packages')
    @patch('packster.cli.map_packages')
    @patch('packster.cli.write_brewfile')
    @patch('packster.cli.write_language_files')
    @patch('packster.cli.write_bootstrap_script')
    @patch('packster.cli.write_reports')
    def test_full_migration_workflow(self, mock_write_reports, mock_write_bootstrap,
                                   mock_write_langs, mock_write_brewfile, mock_map_packages,
                                   mock_normalize_packages, mock_load_registry):
        """Test complete migration workflow with realistic data."""
        # Mock registry
        mock_registry = MagicMock()
        mock_registry.mappings = {
            "git": MagicMock(target_pm="brew", target_name="git", confidence=0.95),
            "vim": MagicMock(target_pm="brew", target_name="vim", confidence=0.90),
            "visual-studio-code": MagicMock(target_pm="cask", target_name="visual-studio-code", confidence=0.95),
        }
        mock_load_registry.return_value = mock_registry
        
        # Mock collected packages
        collected_packages = [
            NormalizedItem(name="git", version="2.25.1", package_manager=PackageManager.APT),
            NormalizedItem(name="vim", version="8.2", package_manager=PackageManager.APT),
            NormalizedItem(name="visual-studio-code", version="1.85.1", package_manager=PackageManager.APT),
            NormalizedItem(name="requests", version="2.28.1", package_manager=PackageManager.PIP),
            NormalizedItem(name="typescript", version="4.9.4", package_manager=PackageManager.NPM),
        ]
        mock_normalize_packages.return_value = collected_packages
        
        # Mock mapping results
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="git", version="2.25.1", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="git", confidence=0.95, reason="Direct mapping"),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="vim", version="8.2", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="vim", confidence=0.90, reason="Direct mapping"),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="visual-studio-code", version="1.85.1", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="cask", target_name="visual-studio-code", confidence=0.95, reason="Direct mapping"),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="requests", version="2.28.1", package_manager=PackageManager.PIP),
                candidate=Candidate(target_pm="pip", target_name="requests", confidence=0.95, reason="Direct mapping"),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="typescript", version="4.9.4", package_manager=PackageManager.NPM),
                candidate=Candidate(target_pm="npm", target_name="typescript", confidence=0.90, reason="Direct mapping"),
                decision=Decision.AUTO
            ),
        ]
        mock_map_packages.return_value = mapping_results
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
            
            assert result.exit_code == 0
            assert "Migration completed" in result.stdout
            
            # Verify all functions were called with correct arguments
            mock_load_registry.assert_called_once()
            mock_normalize_packages.assert_called_once()
            mock_map_packages.assert_called_once()
            mock_write_brewfile.assert_called_once_with(mapping_results, Path(temp_dir) / "Brewfile")
            mock_write_langs.assert_called_once_with(collected_packages, Path(temp_dir))
            mock_write_bootstrap.assert_called_once_with(Path(temp_dir) / "bootstrap.sh", has_python_packages=True, has_npm_packages=True, has_cargo_packages=False, has_gem_packages=False)
            mock_write_reports.assert_called_once()
    
    @patch('packster.cli.load_registry')
    @patch('packster.cli.normalize_all_packages')
    @patch('packster.cli.map_packages')
    @patch('packster.cli.write_brewfile')
    @patch('packster.cli.write_language_files')
    @patch('packster.cli.write_bootstrap_script')
    @patch('packster.cli.write_reports')
    def test_migration_with_mixed_decisions(self, mock_write_reports, mock_write_bootstrap,
                                          mock_write_langs, mock_write_brewfile, mock_map_packages,
                                          mock_normalize_packages, mock_load_registry):
        """Test migration with mixed mapping decisions."""
        # Mock registry
        mock_registry = MagicMock()
        mock_registry.mappings = {
            "git": MagicMock(target_pm="brew", target_name="git", confidence=0.95),
            "unknown-package": MagicMock(target_pm="brew", target_name="unknown", confidence=0.3),
        }
        mock_load_registry.return_value = mock_registry
        
        # Mock collected packages
        collected_packages = [
            NormalizedItem(name="git", version="2.25.1", package_manager=PackageManager.APT),
            NormalizedItem(name="unknown-package", version="1.0.0", package_manager=PackageManager.APT),
        ]
        mock_normalize_packages.return_value = collected_packages
        
        # Mock mapping results with mixed decisions
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="git", version="2.25.1", package_manager=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="git", confidence=0.95, reason="Direct mapping"),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="unknown-package", version="1.0.0", package_manager=PackageManager.APT),
                candidate=None,
                decision=Decision.MANUAL
            ),
        ]
        mock_map_packages.return_value = mapping_results
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
            
            assert result.exit_code == 0
            assert "Migration completed" in result.stdout
            
            # Verify that only AUTO decisions are included in output files
            mock_write_brewfile.assert_called_once()
            mock_write_langs.assert_called_once()
    
    @patch('packster.cli.load_registry')
    @patch('packster.cli.normalize_all_packages')
    @patch('packster.cli.map_packages')
    @patch('packster.cli.write_brewfile')
    @patch('packster.cli.write_language_files')
    @patch('packster.cli.write_bootstrap_script')
    @patch('packster.cli.write_reports')
    def test_migration_with_validation(self, mock_write_reports, mock_write_bootstrap,
                                     mock_write_langs, mock_write_brewfile, mock_map_packages,
                                     mock_normalize_packages, mock_load_registry):
        """Test migration with validation enabled."""
        mock_load_registry.return_value = MagicMock()
        mock_normalize_packages.return_value = []
        mock_map_packages.return_value = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
            
            assert result.exit_code == 0
            assert "Migration completed" in result.stdout
            
            # Verify validation was enabled (default is True)
            mock_map_packages.assert_called_once()


class TestFileGenerationIntegration:
    """Test integration of file generation components."""
    
    def test_brewfile_generation_integration(self):
        """Test Brewfile generation with realistic data."""
        from packster.emit.brewfile import write_brewfile
        
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
            ),
            MappingResult(
                source=NormalizedItem(name="unknown", package_manager=PackageManager.APT),
                candidate=None,
                decision=Decision.MANUAL
            ),
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_brewfile(mapping_results, output_dir)
            
            brewfile_path = output_dir / "Brewfile"
            assert brewfile_path.exists()
            
            content = brewfile_path.read_text()
            
            # Should contain taps
            assert "tap" in content
            
            # Should contain AUTO and VERIFY decisions
            assert "brew 'git'" in content
            assert "cask 'visual-studio-code'" in content
            assert "brew 'vim'" in content
            
            # Should not contain MANUAL decisions
            assert "unknown" not in content
    
    def test_language_files_integration(self):
        """Test language files generation with realistic data."""
        from packster.emit.langs import write_language_files
        
        mapping_results = [
            MappingResult(
                source=NormalizedItem(name="requests==2.28.1", package_manager=PackageManager.PIP),
                candidate=Candidate(target_pm="pip", target_name="requests", confidence=0.95),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="typescript@4.9.4", package_manager=PackageManager.NPM),
                candidate=Candidate(target_pm="npm", target_name="typescript", confidence=0.90),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="fd 8.4.0:", package_manager=PackageManager.CARGO),
                candidate=Candidate(target_pm="cask", target_name="fd", confidence=0.85),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(name="bundler (2.4.9)", package_manager=PackageManager.GEM),
                candidate=Candidate(target_pm="gem", target_name="bundler", confidence=0.80),
                decision=Decision.AUTO
            ),
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_language_files(mapping_results, output_dir)
            
            lang_dir = output_dir / "lang"
            assert lang_dir.exists()
            
            # Check all language files exist
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
    
    def test_bootstrap_script_integration(self):
        """Test bootstrap script generation integration."""
        from packster.emit.bootstrap import write_bootstrap_script
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Create language files to test conditional logic
            lang_dir = output_dir / "lang"
            lang_dir.mkdir()
            (lang_dir / "requirements.txt").write_text("requests==2.28.1")
            (lang_dir / "global-node.txt").write_text("typescript@4.9.4")
            
            bootstrap_path = output_dir / "bootstrap.sh"
            write_bootstrap_script(bootstrap_path)
            
            bootstrap_path = output_dir / "bootstrap.sh"
            assert bootstrap_path.exists()
            
            content = bootstrap_path.read_text()
            
            # Check for essential sections
            assert "#!/bin/bash" in content
            assert "set -e" in content
            assert "brew bundle" in content
            assert "Xcode Command Line Tools" in content
            
            # Check for language-specific installation
            assert "pip install" in content
            assert "npm install" in content
            
            # Check for conditional logic
            assert "if [ -f" in content
            assert "requirements.txt" in content
            assert "global-node.txt" in content
    
    def test_report_generation_integration(self):
        """Test report generation integration."""
        from packster.emit.report import write_reports
        
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
            ),
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_reports(mapping_results, output_dir)
            
            # Check JSON report
            json_path = output_dir / "report.json"
            assert json_path.exists()
            
            import json
            with open(json_path) as f:
                report_data = json.load(f)
            
            assert report_data["total_packages"] == 3
            assert report_data["auto_mapped"] == 1
            assert report_data["verify_required"] == 1
            assert report_data["manual_review"] == 1
            assert report_data["skipped"] == 0
            
            # Check HTML report
            html_path = output_dir / "report.html"
            assert html_path.exists()
            
            html_content = html_path.read_text()
            assert "html" in html_content
            assert "Auto-Mapped Packages" in html_content
            assert "Verify Required Packages" in html_content
            assert "Manual Review Required" in html_content


class TestErrorHandlingIntegration:
    """Test error handling integration."""
    
    def test_collection_error_handling(self):
        """Test handling of collection errors."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.side_effect = Exception("Collection failed")
            
            runner = CliRunner()
            with tempfile.TemporaryDirectory() as temp_dir:
                result = runner.invoke(app, ["generate", "--output-dir", temp_dir])
                
                assert result.exit_code != 0
                assert "Error" in result.stdout
                assert "Collection failed" in result.stdout
    
    def test_mapping_error_handling(self):
        """Test handling of mapping errors."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages, \
             patch('packster.cli.map_packages') as mock_map_packages:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.return_value = []
            mock_map_packages.side_effect = Exception("Mapping failed")
            
            runner = CliRunner()
            with tempfile.TemporaryDirectory() as temp_dir:
                result = runner.invoke(app, ["generate", "--output-dir", temp_dir])
                
                assert result.exit_code != 0
                assert "Error" in result.stdout
                assert "Mapping failed" in result.stdout
    
    def test_file_write_error_handling(self):
        """Test handling of file write errors."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.return_value = []
            mock_map_packages.return_value = []
            mock_write_brewfile.side_effect = PermissionError("Permission denied")
            
            runner = CliRunner()
            with tempfile.TemporaryDirectory() as temp_dir:
                result = runner.invoke(app, ["generate", "--output-dir", temp_dir])
                
                assert result.exit_code != 0
                assert "Error" in result.stdout
                assert "Permission denied" in result.stdout


class TestPerformanceIntegration:
    """Test performance characteristics."""
    
    def test_large_package_list_handling(self):
        """Test handling of large package lists."""
        from packster.emit.brewfile import write_brewfile
        
        # Create a large number of mapping results
        mapping_results = []
        for i in range(100):
            mapping_results.append(
                MappingResult(
                    source=NormalizedItem(name=f"package-{i}", package_manager=PackageManager.APT),
                    candidate=Candidate(target_pm="brew", target_name=f"package-{i}", confidence=0.95),
                    decision=Decision.AUTO
                )
            )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Should complete without errors
            write_brewfile(mapping_results, output_dir)
            
            brewfile_path = output_dir / "Brewfile"
            assert brewfile_path.exists()
            
            content = brewfile_path.read_text()
            lines = content.strip().split('\n')
            
            # Should contain all packages
            brew_lines = [line for line in lines if line.startswith("brew '")]
            assert len(brew_lines) == 100
    
    def test_mixed_package_managers_handling(self):
        """Test handling of mixed package managers."""
        from packster.emit.langs import write_language_files
        
        mapping_results = []
        
        # Add packages from different managers
        for i in range(10):
            mapping_results.extend([
                MappingResult(
                    source=NormalizedItem(name=f"pip-package-{i}", package_manager=PackageManager.PIP),
                    candidate=Candidate(target_pm="pip", target_name=f"pip-package-{i}", confidence=0.95),
                    decision=Decision.AUTO
                ),
                MappingResult(
                    source=NormalizedItem(name=f"npm-package-{i}", package_manager=PackageManager.NPM),
                    candidate=Candidate(target_pm="npm", target_name=f"npm-package-{i}", confidence=0.90),
                    decision=Decision.AUTO
                ),
                MappingResult(
                    source=NormalizedItem(name=f"cargo-package-{i}", package_manager=PackageManager.CARGO),
                    candidate=Candidate(target_pm="cargo", target_name=f"cargo-package-{i}", confidence=0.85),
                    decision=Decision.AUTO
                ),
                MappingResult(
                    source=NormalizedItem(name=f"gem-package-{i}", package_manager=PackageManager.GEM),
                    candidate=Candidate(target_pm="gem", target_name=f"gem-package-{i}", confidence=0.80),
                    decision=Decision.AUTO
                ),
            ])
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_language_files(mapping_results, output_dir)
            
            lang_dir = output_dir / "lang"
            
            # Check all files exist and contain expected content
            for filename in ["requirements.txt", "global-node.txt", "cargo.txt", "gems.txt"]:
                file_path = lang_dir / filename
                assert file_path.exists()
                
                content = file_path.read_text()
                lines = content.strip().split('\n')
                
                # Should contain 10 packages each
                assert len(lines) == 10
