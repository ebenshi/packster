"""System detection utilities for Packster."""

import os
import platform
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .config import PACKAGE_MANAGER_COMMANDS


def detect_os() -> str:
    """Detect the current operating system."""
    system = platform.system().lower()
    
    if system == "linux":
        # Try to detect specific Linux distributions
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read().lower()
                if "ubuntu" in content:
                    return "ubuntu"
                elif "debian" in content:
                    return "debian"
                elif "fedora" in content:
                    return "fedora"
                elif "centos" in content or "rhel" in content:
                    return "centos"
                elif "arch" in content:
                    return "arch"
                else:
                    return "linux"
        except (FileNotFoundError, PermissionError):
            return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return system


def detect_architecture() -> str:
    """Detect the system architecture."""
    machine = platform.machine().lower()
    
    # Normalize architecture names
    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "i386": "x86_32",
        "i686": "x86_32",
        "arm64": "arm64",
        "aarch64": "arm64",
        "armv7l": "arm32",
        "armv8l": "arm64",
    }
    
    return arch_map.get(machine, machine)


def detect_wsl() -> bool:
    """Detect if running in WSL (Windows Subsystem for Linux)."""
    try:
        with open("/proc/version", "r") as f:
            content = f.read().lower()
            return "microsoft" in content or "wsl" in content
    except (FileNotFoundError, PermissionError):
        return False


def is_command_available(command: str) -> bool:
    """Check if a command is available in PATH."""
    return shutil.which(command) is not None


def check_package_manager_availability() -> Dict[str, bool]:
    """Check which package managers are available on the system."""
    availability = {}
    
    for pm, commands in PACKAGE_MANAGER_COMMANDS.items():
        # Check if any command for this package manager is available
        pm_available = False
        for cmd_type, cmd_list in commands.items():
            if cmd_list and is_command_available(cmd_list[0]):
                pm_available = True
                break
        availability[pm] = pm_available
    
    return availability


def get_system_info() -> Dict[str, str]:
    """Get comprehensive system information."""
    return {
        "os": detect_os(),
        "architecture": detect_architecture(),
        "wsl": str(detect_wsl()),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


def sanitize_os_string(os_string: str) -> str:
    """Sanitize OS string for consistent comparison."""
    return os_string.lower().strip().replace(" ", "")


def is_ubuntu_or_debian() -> bool:
    """Check if the system is Ubuntu or Debian."""
    os_name = detect_os()
    return os_name in ["ubuntu", "debian"]


def is_macos() -> bool:
    """Check if the system is macOS."""
    return detect_os() == "macos"


def get_homebrew_path() -> Optional[Path]:
    """Get the Homebrew installation path."""
    possible_paths = [
        Path("/opt/homebrew"),  # Apple Silicon
        Path("/usr/local"),     # Intel Mac
    ]
    
    for path in possible_paths:
        if (path / "bin" / "brew").exists():
            return path
    
    return None


def is_homebrew_available() -> bool:
    """Check if Homebrew is available."""
    return is_command_available("brew")


def run_command_safe(
    command: List[str], 
    timeout: int = 30,
    capture_output: bool = True
) -> Tuple[int, str, str]:
    """Run a command safely with timeout and error handling."""
    try:
        result = subprocess.run(
            command,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return -1, "", f"Command not found: {' '.join(command)}"
    except Exception as e:
        return -1, "", f"Error running command: {str(e)}"


def get_environment_info() -> Dict[str, any]:
    """Get comprehensive environment information for debugging."""
    return {
        "system": get_system_info(),
        "package_managers": check_package_manager_availability(),
        "homebrew_available": is_homebrew_available(),
        "homebrew_path": str(get_homebrew_path()) if get_homebrew_path() else None,
        "current_directory": str(Path.cwd()),
        "user": os.getenv("USER", "unknown"),
        "path": os.getenv("PATH", "").split(":"),
    }
