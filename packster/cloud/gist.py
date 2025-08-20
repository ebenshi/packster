"""GitHub Gist integration for Packster cloud storage."""

import base64
import json
import logging
from pathlib import Path
from typing import Dict, Optional

import requests

from .security import generate_secure_url, get_url_info

logger = logging.getLogger(__name__)


class GistUploader:
    """GitHub Gist uploader for Packster migration files."""
    
    def __init__(self, github_token: str):
        """Initialize the Gist uploader.
        
        Args:
            github_token: GitHub personal access token
        """
        self.github_token = github_token
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Packster/1.0.0"
        }
    
    def upload_file(self, file_path: Path, description: str = "Packster Migration") -> Dict[str, str]:
        """Upload a file to GitHub Gist and return download information.
        
        Args:
            file_path: Path to the file to upload
            description: Description for the Gist
            
        Returns:
            Dictionary containing download URL and metadata
            
        Raises:
            FileNotFoundError: If file doesn't exist
            requests.RequestException: If upload fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Encode file content as base64
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        # Generate secure URL identifier
        secure_id = generate_secure_url()
        
        # Create Gist data
        gist_data = {
            "description": f"{description} - {secure_id}",
            "public": False,  # Private gist for security
            "files": {
                file_path.name: {
                    "content": file_content_b64,
                    "encoding": "base64"
                }
            }
        }
        
        # Upload to GitHub Gist
        response = requests.post(
            f"{self.api_base}/gists",
            headers=self.headers,
            json=gist_data,
            timeout=30
        )
        
        if response.status_code != 201:
            error_msg = f"Failed to upload to GitHub Gist: {response.status_code}"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg += f" - {error_data['message']}"
            except:
                pass
            raise requests.RequestException(error_msg)
        
        gist_info = response.json()
        
        # Extract download URL
        files = gist_info.get('files', {})
        if not files:
            raise requests.RequestException("No files found in Gist response")
        
        # Get the first (and only) file
        file_info = list(files.values())[0]
        raw_url = file_info.get('raw_url')
        
        if not raw_url:
            raise requests.RequestException("No raw URL found in Gist response")
        
        # Create secure download URL
        download_url = f"{raw_url}?token={secure_id}"
        
        return {
            "gist_id": gist_info['id'],
            "gist_url": gist_info['html_url'],
            "download_url": download_url,
            "secure_id": secure_id,
            "file_name": file_path.name,
            "file_size": len(file_content),
            "expires_at": get_url_info(secure_id)["expires_at"]
        }
    
    def delete_gist(self, gist_id: str) -> bool:
        """Delete a GitHub Gist.
        
        Args:
            gist_id: The Gist ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.api_base}/gists/{gist_id}",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 204
        except requests.RequestException as e:
            logger.warning(f"Failed to delete Gist {gist_id}: {e}")
            return False
    
    def get_gist_info(self, gist_id: str) -> Optional[Dict]:
        """Get information about a GitHub Gist.
        
        Args:
            gist_id: The Gist ID to query
            
        Returns:
            Gist information dictionary or None if not found
        """
        try:
            response = requests.get(
                f"{self.api_base}/gists/{gist_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except requests.RequestException as e:
            logger.warning(f"Failed to get Gist info for {gist_id}: {e}")
            return None


def upload_migration_archive(archive_path: Path, github_token: str, description: str = None) -> Dict[str, str]:
    """Upload a migration archive to GitHub Gist.
    
    Args:
        archive_path: Path to the migration archive
        github_token: GitHub personal access token
        description: Optional description for the Gist
        
    Returns:
        Dictionary containing upload information and download URL
    """
    if description is None:
        description = f"Packster Migration Archive - {archive_path.name}"
    
    uploader = GistUploader(github_token)
    return uploader.upload_file(archive_path, description)


def generate_download_command(download_url: str, file_name: str) -> str:
    """Generate a one-liner download command for Mac users.
    
    Args:
        download_url: The secure download URL
        file_name: Name of the file to download
        
    Returns:
        One-liner curl command for downloading and extracting
    """
    # Extract the base filename without extension
    base_name = file_name.replace('.tar.gz', '')
    
    # Create a more robust command that's easier to copy/paste
    # Use single quotes to avoid issues with URL parameters
    return f"curl -L '{download_url}' | tar -xz && cd {base_name} && ./bootstrap.sh/bootstrap.sh"


def generate_simple_download_command(download_url: str, file_name: str) -> str:
    """Generate a simple download command that avoids copy/paste issues.
    
    Args:
        download_url: The secure download URL
        file_name: Name of the file to download
        
    Returns:
        Simple download command
    """
    # Extract the base filename without extension
    base_name = file_name.replace('.tar.gz', '')
    
    # Create a simple command that works reliably
    # Use double quotes and escape the URL properly
    return f'curl -L "{download_url}" | tar -xz && cd {base_name} && bash bootstrap.sh/bootstrap.sh'


def generate_robust_download_command(download_url: str, file_name: str) -> str:
    """Generate a robust download command that handles email formatting issues.
    
    This creates a command that can handle URLs broken across multiple lines
    when copied from email clients.
    
    Args:
        download_url: The secure download URL
        file_name: Name of the file to download
        
    Returns:
        Robust download command that handles formatting issues
    """
    # Extract the base filename without extension
    base_name = file_name.replace('.tar.gz', '')
    
    # Create a command that reconstructs the URL from parts
    # This handles cases where the URL gets broken in email
    url_parts = download_url.split('?')
    base_url = url_parts[0]
    token = url_parts[1] if len(url_parts) > 1 else ""
    
    # Create a more robust command that can handle line breaks
    return f"""URL="{base_url}?{token}" && curl -L -s "$URL" | tar -xz && cd {base_name} && chmod +x bootstrap.sh/bootstrap.sh && ./bootstrap.sh/bootstrap.sh"""


def generate_download_script(download_url: str, file_name: str, output_path: Path = None) -> str:
    """Generate a download script file that can be easily shared and executed.
    
    This creates a shell script that downloads and installs the migration,
    completely avoiding copy/paste issues with long URLs.
    
    Args:
        download_url: The secure download URL
        file_name: Name of the file to download
        output_path: Optional path to save the script (defaults to current directory)
        
    Returns:
        Path to the generated script file
    """
    # Extract the base filename without extension
    base_name = file_name.replace('.tar.gz', '')
    
    # Create the script content
    script_content = f"""#!/bin/bash
# Packster Migration Download Script
# Generated automatically - safe to run on macOS

set -e  # Exit on any error

echo "Starting Packster migration download..."

# Download and extract the migration archive
echo "Downloading migration archive..."
curl -L "{download_url}" | tar -xz

# Navigate to the extracted directory
cd {base_name}

# Make the bootstrap script executable and run it
echo "Installing packages..."
chmod +x bootstrap.sh/bootstrap.sh
bash bootstrap.sh/bootstrap.sh

echo "Migration completed successfully!"
echo "Check report.html for detailed information"
"""
    
    # Determine output path
    if output_path is None:
        output_path = Path.cwd() / f"install-{base_name}.sh"
    
    # Write the script file
    with open(output_path, 'w') as f:
        f.write(script_content)
    
    # Make the script executable
    output_path.chmod(0o755)
    
    return str(output_path)


def validate_github_token(token: str) -> bool:
    """Validate a GitHub personal access token.
    
    Args:
        token: The GitHub token to validate
        
    Returns:
        True if token is valid, False otherwise
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Packster/1.0.0"
    }
    
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except requests.RequestException:
        return False
