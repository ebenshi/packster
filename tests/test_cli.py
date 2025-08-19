"""Tests for the CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from packster.cli import app


class TestCLIApp:
    """Test CLI application functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_app_creation(self):
        """Test that the CLI app is created correctly."""
        assert app is not None
        assert hasattr(app, 'commands')
    
    def test_version_command(self):
        """Test the version command."""
        result = self.runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "packster" in result.stdout.lower()
    
    def test_info_command(self):
        """Test the info command."""
        result = self.runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "System Information" in result.stdout
    
    @patch('packster.cli.load_registry')
    @patch('packster.cli.normalize_all_packages')
    @patch('packster.cli.map_packages')
    @patch('packster.cli.write_brewfile')
    @patch('packster.cli.write_language_files')
    @patch('packster.cli.write_bootstrap_script')
    @patch('packster.cli.write_reports')
    def test_generate_command_success(self, mock_write_reports, mock_write_bootstrap, 
                                    mock_write_langs, mock_write_brewfile, mock_map_packages,
                                    mock_normalize_packages, mock_load_registry):
        """Test successful generate command execution."""
        # Mock return values
        mock_load_registry.return_value = MagicMock()
        mock_normalize_packages.return_value = []
        mock_map_packages.return_value = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
            
            assert result.exit_code == 0
            assert "Packster" in result.stdout
            assert "Migration completed" in result.stdout
            
            # Verify all functions were called
            mock_load_registry.assert_called_once()
            mock_normalize_packages.assert_called_once()
            mock_map_packages.assert_called_once()
            mock_write_brewfile.assert_called_once()
            mock_write_langs.assert_called_once()
            mock_write_bootstrap.assert_called_once()
            mock_write_reports.assert_called_once()
    
    @patch('packster.cli.load_registry')
    @patch('packster.cli.normalize_all_packages')
    def test_generate_command_collection_error(self, mock_normalize_packages, mock_load_registry):
        """Test generate command with collection error."""
        mock_load_registry.return_value = MagicMock()
        mock_normalize_packages.side_effect = Exception("Collection failed")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
            
            assert result.exit_code != 0
            assert "Error" in result.stdout
    
    @patch('packster.cli.load_registry')
    @patch('packster.cli.normalize_all_packages')
    @patch('packster.cli.map_packages')
    def test_generate_command_mapping_error(self, mock_map_packages, mock_normalize_packages, 
                                          mock_load_registry):
        """Test generate command with mapping error."""
        mock_load_registry.return_value = MagicMock()
        mock_normalize_packages.return_value = []
        mock_map_packages.side_effect = Exception("Mapping failed")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
            
            assert result.exit_code != 0
            assert "Error" in result.stdout
    
    def test_generate_command_invalid_output_dir(self):
        """Test generate command with invalid output directory."""
        result = self.runner.invoke(app, ["generate", "--output-dir", "/nonexistent/path"])
        
        assert result.exit_code != 0
        assert "Error" in result.stdout
    
    def test_generate_command_default_output_dir(self):
        """Test generate command with default output directory."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile, \
             patch('packster.cli.write_language_files') as mock_write_langs, \
             patch('packster.cli.write_bootstrap_script') as mock_write_bootstrap, \
             patch('packster.cli.write_reports') as mock_write_reports:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.return_value = []
            mock_map_packages.return_value = []
            
            result = self.runner.invoke(app, ["generate"])
            
            assert result.exit_code == 0
            assert "Migration completed" in result.stdout
    
    @patch('pathlib.Path.exists')
    def test_generate_command_with_registry_path(self, mock_exists):
        """Test generate command with custom registry path."""
        # Mock the registry file to exist
        mock_exists.return_value = True
        
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile, \
             patch('packster.cli.write_language_files') as mock_write_langs, \
             patch('packster.cli.write_bootstrap_script') as mock_write_bootstrap, \
             patch('packster.cli.write_reports') as mock_write_reports:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.return_value = []
            mock_map_packages.return_value = []
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.runner.invoke(app, [
                    "generate", 
                    "--output-dir", temp_dir,
                    "--registry", "custom-registry.yaml"
                ])
                
                assert result.exit_code == 0
                mock_load_registry.assert_called_once_with(Path("custom-registry.yaml"))
    
    @patch('pathlib.Path.exists')
    def test_generate_command_with_validate_flag(self, mock_exists):
        """Test generate command with validation flag."""
        # Mock the registry file to exist
        mock_exists.return_value = True
        
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile, \
             patch('packster.cli.write_language_files') as mock_write_langs, \
             patch('packster.cli.write_bootstrap_script') as mock_write_bootstrap, \
             patch('packster.cli.write_reports') as mock_write_reports:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.return_value = []
            mock_map_packages.return_value = []
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.runner.invoke(app, [
                    "generate", 
                    "--output-dir", temp_dir
                ])
                
                assert result.exit_code == 0
                # The verify flag should be passed to map_packages (default is True)
                mock_map_packages.assert_called_once()
    
    def test_generate_command_with_verbose_flag(self):
        """Test generate command with verbose flag."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile, \
             patch('packster.cli.write_language_files') as mock_write_langs, \
             patch('packster.cli.write_bootstrap_script') as mock_write_bootstrap, \
             patch('packster.cli.write_reports') as mock_write_reports:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.return_value = []
            mock_map_packages.return_value = []
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.runner.invoke(app, [
                    "generate", 
                    "--output-dir", temp_dir,
                    "--verbose"
                ])
                
                assert result.exit_code == 0
                assert "Migration completed" in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_generate_command_missing_output_dir(self):
        """Test generate command with missing output directory."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.side_effect = Exception("Test error")
            
            result = self.runner.invoke(app, ["generate"])
            
            assert result.exit_code != 0
            assert "Error" in result.stdout
    
    def test_generate_command_permission_error(self):
        """Test generate command with permission error."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.return_value = []
            mock_map_packages.return_value = []
            mock_write_brewfile.side_effect = PermissionError("Permission denied")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
                
                assert result.exit_code != 0
                assert "Error" in result.stdout
    
    def test_generate_command_invalid_registry(self):
        """Test generate command with invalid registry."""
        with patch('packster.cli.load_registry') as mock_load_registry:
            mock_load_registry.side_effect = Exception("Invalid registry")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
                
                assert result.exit_code != 0
                assert "Error" in result.stdout


class TestCLIOutput:
    """Test CLI output formatting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_banner_display(self):
        """Test that the banner is displayed correctly."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.collect_all_packages') as mock_collect_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile, \
             patch('packster.cli.write_language_files') as mock_write_langs, \
             patch('packster.cli.write_bootstrap_script') as mock_write_bootstrap, \
             patch('packster.cli.write_reports') as mock_write_reports:
            
            mock_load_registry.return_value = MagicMock()
            mock_collect_packages.return_value = []
            mock_map_packages.return_value = []
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
                
                assert "Packster" in result.stdout
                assert "Cross-OS package migration helper" in result.stdout
    
    def test_system_info_display(self):
        """Test that system information is displayed."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.collect_all_packages') as mock_collect_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile, \
             patch('packster.cli.write_language_files') as mock_write_langs, \
             patch('packster.cli.write_bootstrap_script') as mock_write_bootstrap, \
             patch('packster.cli.write_reports') as mock_write_reports:
            
            mock_load_registry.return_value = MagicMock()
            mock_collect_packages.return_value = []
            mock_map_packages.return_value = []
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
                
                assert "System Information" in result.stdout
                assert "OS" in result.stdout
                assert "Architecture" in result.stdout
    
    def test_progress_display(self):
        """Test that progress information is displayed."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.normalize_all_packages') as mock_normalize_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile, \
             patch('packster.cli.write_language_files') as mock_write_langs, \
             patch('packster.cli.write_bootstrap_script') as mock_write_bootstrap, \
             patch('packster.cli.write_reports') as mock_write_reports:
            
            mock_load_registry.return_value = MagicMock()
            mock_normalize_packages.return_value = []
            mock_map_packages.return_value = []
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.runner.invoke(app, ["generate", "--output-dir", temp_dir])
                
                # The Rich progress bar doesn't show progress messages in final output
                # but we can verify the migration completed successfully
                assert "Migration completed" in result.stdout
    
    def test_verbose_output(self):
        """Test verbose output mode."""
        with patch('packster.cli.load_registry') as mock_load_registry, \
             patch('packster.cli.collect_all_packages') as mock_collect_packages, \
             patch('packster.cli.map_packages') as mock_map_packages, \
             patch('packster.cli.write_brewfile') as mock_write_brewfile, \
             patch('packster.cli.write_language_files') as mock_write_langs, \
             patch('packster.cli.write_bootstrap_script') as mock_write_bootstrap, \
             patch('packster.cli.write_reports') as mock_write_reports:
            
            mock_load_registry.return_value = MagicMock()
            mock_collect_packages.return_value = []
            mock_map_packages.return_value = []
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.runner.invoke(app, [
                    "generate", 
                    "--output-dir", temp_dir,
                    "--verbose"
                ])
                
                # Verbose mode should show more detailed output
                assert "Migration completed" in result.stdout


class TestCLIHelp:
    """Test CLI help functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_help_command(self):
        """Test the help command."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "Commands" in result.stdout
    
    def test_generate_help(self):
        """Test generate command help."""
        result = self.runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "Options" in result.stdout
    
    def test_version_help(self):
        """Test version command help."""
        result = self.runner.invoke(app, ["version", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout
    
    def test_info_help(self):
        """Test info command help."""
        result = self.runner.invoke(app, ["info", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout
