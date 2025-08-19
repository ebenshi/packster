"""Tests for the detect module."""

import pytest
from unittest.mock import patch, mock_open
from packster.detect import (
    detect_os,
    detect_architecture,
    detect_wsl,
    is_command_available,
    check_package_manager_availability,
    get_system_info,
    sanitize_os_string,
    is_ubuntu_or_debian,
    is_macos,
    get_homebrew_path,
    is_homebrew_available,
    run_command_safe,
    get_environment_info,
)


class TestDetectOS:
    """Test OS detection functionality."""
    
    @patch('platform.system')
    def test_detect_os_linux(self, mock_system):
        """Test Linux OS detection."""
        mock_system.return_value = "Linux"
        
        with patch('builtins.open', mock_open(read_data="ID=ubuntu")):
            result = detect_os()
            assert result == "ubuntu"
    
    @patch('platform.system')
    def test_detect_os_macos(self, mock_system):
        """Test macOS detection."""
        mock_system.return_value = "Darwin"
        result = detect_os()
        assert result == "macos"
    
    @patch('platform.system')
    def test_detect_os_windows(self, mock_system):
        """Test Windows detection."""
        mock_system.return_value = "Windows"
        result = detect_os()
        assert result == "windows"
    
    @patch('platform.system')
    def test_detect_os_unknown(self, mock_system):
        """Test unknown OS detection."""
        mock_system.return_value = "Unknown"
        result = detect_os()
        assert result == "unknown"


class TestDetectArchitecture:
    """Test architecture detection functionality."""
    
    @patch('platform.machine')
    def test_detect_architecture_x86_64(self, mock_machine):
        """Test x86_64 architecture detection."""
        mock_machine.return_value = "x86_64"
        result = detect_architecture()
        assert result == "x86_64"
    
    @patch('platform.machine')
    def test_detect_architecture_arm64(self, mock_machine):
        """Test ARM64 architecture detection."""
        mock_machine.return_value = "aarch64"
        result = detect_architecture()
        assert result == "arm64"
    
    @patch('platform.machine')
    def test_detect_architecture_unknown(self, mock_machine):
        """Test unknown architecture detection."""
        mock_machine.return_value = "unknown"
        result = detect_architecture()
        assert result == "unknown"


class TestDetectWSL:
    """Test WSL detection functionality."""
    
    def test_detect_wsl_true(self):
        """Test WSL detection when running in WSL."""
        with patch('builtins.open', mock_open(read_data="Microsoft")):
            result = detect_wsl()
            assert result is True
    
    def test_detect_wsl_false(self):
        """Test WSL detection when not running in WSL."""
        with patch('builtins.open', mock_open(read_data="Linux")):
            result = detect_wsl()
            assert result is False
    
    def test_detect_wsl_file_not_found(self):
        """Test WSL detection when /proc/version doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = detect_wsl()
            assert result is False


class TestCommandAvailability:
    """Test command availability checking."""
    
    @patch('shutil.which')
    def test_is_command_available_true(self, mock_which):
        """Test command availability when command exists."""
        mock_which.return_value = "/usr/bin/git"
        result = is_command_available("git")
        assert result is True
    
    @patch('shutil.which')
    def test_is_command_available_false(self, mock_which):
        """Test command availability when command doesn't exist."""
        mock_which.return_value = None
        result = is_command_available("nonexistent")
        assert result is False


class TestPackageManagerAvailability:
    """Test package manager availability checking."""
    
    @patch('packster.detect.is_command_available')
    def test_check_package_manager_availability(self, mock_is_available):
        """Test package manager availability checking."""
        mock_is_available.return_value = True
        
        result = check_package_manager_availability()
        
        assert isinstance(result, dict)
        assert "apt" in result
        assert "pip" in result
        assert "npm" in result
        assert "cargo" in result
        assert "gem" in result


class TestSystemInfo:
    """Test system information gathering."""
    
    @patch('packster.detect.detect_os')
    @patch('packster.detect.detect_architecture')
    @patch('packster.detect.detect_wsl')
    @patch('platform.python_version')
    @patch('platform.platform')
    @patch('platform.processor')
    def test_get_system_info(self, mock_processor, mock_platform, mock_python_version, 
                            mock_wsl, mock_arch, mock_os):
        """Test system information gathering."""
        mock_os.return_value = "ubuntu"
        mock_arch.return_value = "x86_64"
        mock_wsl.return_value = False
        mock_python_version.return_value = "3.10.0"
        mock_platform.return_value = "Linux-5.4.0-x86_64"
        mock_processor.return_value = "x86_64"
        
        result = get_system_info()
        
        assert isinstance(result, dict)
        assert result["os"] == "ubuntu"
        assert result["architecture"] == "x86_64"
        assert result["wsl"] == "False"
        assert result["python_version"] == "3.10.0"


class TestOSHelpers:
    """Test OS helper functions."""
    
    def test_sanitize_os_string(self):
        """Test OS string sanitization."""
        assert sanitize_os_string("Ubuntu 20.04") == "ubuntu20.04"
        assert sanitize_os_string("  macOS  ") == "macos"
        assert sanitize_os_string("Windows 10") == "windows10"
    
    @patch('packster.detect.detect_os')
    def test_is_ubuntu_or_debian_true(self, mock_detect_os):
        """Test Ubuntu/Debian detection when true."""
        mock_detect_os.return_value = "ubuntu"
        assert is_ubuntu_or_debian() is True
        
        mock_detect_os.return_value = "debian"
        assert is_ubuntu_or_debian() is True
    
    @patch('packster.detect.detect_os')
    def test_is_ubuntu_or_debian_false(self, mock_detect_os):
        """Test Ubuntu/Debian detection when false."""
        mock_detect_os.return_value = "macos"
        assert is_ubuntu_or_debian() is False
    
    @patch('packster.detect.detect_os')
    def test_is_macos_true(self, mock_detect_os):
        """Test macOS detection when true."""
        mock_detect_os.return_value = "macos"
        assert is_macos() is True
    
    @patch('packster.detect.detect_os')
    def test_is_macos_false(self, mock_detect_os):
        """Test macOS detection when false."""
        mock_detect_os.return_value = "ubuntu"
        assert is_macos() is False


class TestHomebrewDetection:
    """Test Homebrew detection functionality."""
    
    @patch('pathlib.Path.exists')
    def test_get_homebrew_path_apple_silicon(self, mock_exists):
        """Test Homebrew path detection on Apple Silicon."""
        mock_exists.side_effect = [False, True]  # /opt/homebrew/bin/brew exists
        result = get_homebrew_path()
        assert result is not None
        assert str(result).endswith("/usr/local")
    
    @patch('pathlib.Path.exists')
    def test_get_homebrew_path_not_found(self, mock_exists):
        """Test Homebrew path detection when not found."""
        mock_exists.return_value = False
        result = get_homebrew_path()
        assert result is None
    
    @patch('packster.detect.is_command_available')
    def test_is_homebrew_available(self, mock_is_available):
        """Test Homebrew availability checking."""
        mock_is_available.return_value = True
        assert is_homebrew_available() is True
        
        mock_is_available.return_value = False
        assert is_homebrew_available() is False


class TestCommandExecution:
    """Test command execution functionality."""
    
    @patch('subprocess.run')
    def test_run_command_safe_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "success"
        mock_run.return_value.stderr = ""
        
        exit_code, stdout, stderr = run_command_safe(["echo", "test"])
        
        assert exit_code == 0
        assert stdout == "success"
        assert stderr == ""
    
    @patch('subprocess.run')
    def test_run_command_safe_failure(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "error"
        
        exit_code, stdout, stderr = run_command_safe(["nonexistent"])
        
        assert exit_code == 1
        assert stdout == ""
        assert stderr == "error"
    
    @patch('subprocess.run')
    def test_run_command_safe_timeout(self, mock_run):
        """Test command execution timeout."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired(["sleep", "100"], 30)
        
        exit_code, stdout, stderr = run_command_safe(["sleep", "100"])
        
        assert exit_code == -1
        assert stdout == ""
        assert "timed out" in stderr


class TestEnvironmentInfo:
    """Test environment information gathering."""
    
    @patch('packster.detect.get_system_info')
    @patch('packster.detect.check_package_manager_availability')
    @patch('packster.detect.is_homebrew_available')
    @patch('packster.detect.get_homebrew_path')
    @patch('os.getenv')
    def test_get_environment_info(self, mock_getenv, mock_homebrew_path, 
                                mock_homebrew_available, mock_pm_availability, 
                                mock_system_info):
        """Test environment information gathering."""
        mock_system_info.return_value = {"os": "ubuntu"}
        mock_pm_availability.return_value = {"apt": True}
        mock_homebrew_available.return_value = False
        mock_homebrew_path.return_value = None
        mock_getenv.side_effect = ["testuser", "/usr/bin:/usr/local/bin"]
        
        result = get_environment_info()
        
        assert isinstance(result, dict)
        assert "system" in result
        assert "package_managers" in result
        assert "homebrew_available" in result
        assert "homebrew_path" in result
        assert "user" in result
        assert "path" in result
