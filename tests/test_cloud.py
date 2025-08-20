"""Tests for cloud storage functionality."""

import json
import tarfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from packster.cloud.compression import create_migration_archive, _create_metadata
from packster.cloud.security import (
    generate_secure_url,
    validate_secure_url,
    extract_timestamp_from_url,
    generate_readable_id,
    get_url_info,
)
from packster.cloud.gist import (
    GistUploader,
    upload_migration_archive,
    generate_download_command,
    validate_github_token,
)


class TestCompression:
    """Test compression functionality."""
    
    def test_create_migration_archive(self, tmp_path):
        """Test creating a migration archive."""
        # Create test files
        output_dir = tmp_path / "test-output"
        output_dir.mkdir()
        
        # Create some test files
        (output_dir / "Brewfile").mkdir()
        (output_dir / "Brewfile" / "Brewfile").write_text("tap 'homebrew/core'")
        
        (output_dir / "bootstrap.sh").mkdir()
        (output_dir / "bootstrap.sh" / "bootstrap.sh").write_text("#!/bin/bash")
        
        (output_dir / "lang").mkdir()
        (output_dir / "lang" / "requirements.txt").write_text("requests==2.28.0")
        
        (output_dir / "report.html").write_text("<html>Test</html>")
        
        # Create archive
        archive_path = create_migration_archive(output_dir)
        
        # Verify archive was created
        assert archive_path.exists()
        assert archive_path.suffix == ".gz"
        assert "packster-migration-" in archive_path.name
        
        # Verify archive contents
        with tarfile.open(archive_path, 'r:gz') as tar:
            members = tar.getmembers()
            member_names = [m.name for m in members]
            
            # Check that all files are included
            assert "metadata.json" in member_names
            assert "Brewfile/Brewfile" in member_names
            assert "bootstrap.sh/bootstrap.sh" in member_names
            assert "lang/requirements.txt" in member_names
            assert "report.html" in member_names
            
            # Check metadata
            metadata_member = tar.getmember("metadata.json")
            metadata_content = tar.extractfile(metadata_member).read()
            metadata = json.loads(metadata_content)
            
            assert "created_at" in metadata
            assert "source_system" in metadata
            assert "archive_info" in metadata
            assert "contents" in metadata
            assert metadata["contents"]["has_brewfile"] is True
            assert metadata["contents"]["has_bootstrap"] is True
            assert metadata["contents"]["has_reports"] is True
            assert "requirements.txt" in metadata["contents"]["language_files"]
    
    def test_create_migration_archive_nonexistent_dir(self):
        """Test creating archive with nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            create_migration_archive(Path("/nonexistent/directory"))
    
    @patch('packster.cloud.compression.get_environment_info')
    def test_create_metadata(self, mock_env_info, tmp_path):
        """Test metadata creation."""
        # Mock environment info
        mock_env_info.return_value = {
            "system": {
                "os": "Ubuntu",
                "architecture": "x86_64",
                "wsl": True,
                "python_version": "3.9.0"
            }
        }
        
        # Create test directory structure
        output_dir = tmp_path / "test-output"
        output_dir.mkdir()
        (output_dir / "test.txt").write_text("test content")
        
        metadata = _create_metadata(output_dir)
        
        # Verify metadata structure
        assert "created_at" in metadata
        assert "packster_version" in metadata
        assert "source_system" in metadata
        assert "archive_info" in metadata
        assert "contents" in metadata
        
        # Verify system info
        assert metadata["source_system"]["os"] == "Ubuntu"
        assert metadata["source_system"]["architecture"] == "x86_64"
        assert metadata["source_system"]["wsl"] is True
        
        # Verify archive info
        assert metadata["archive_info"]["file_count"] > 0
        assert metadata["archive_info"]["total_size_bytes"] > 0
        assert ".txt" in metadata["archive_info"]["file_types"]


class TestSecurity:
    """Test security functionality."""
    
    def test_generate_secure_url(self):
        """Test secure URL generation."""
        url1 = generate_secure_url()
        url2 = generate_secure_url()
        
        # URLs should be different
        assert url1 != url2
        
        # URLs should be valid
        assert validate_secure_url(url1)
        assert validate_secure_url(url2)
        
        # URLs should be URL-safe (no special chars)
        assert '=' not in url1
        assert '=' not in url2
        assert '/' not in url1
        assert '/' not in url2
        assert '+' not in url1
        assert '+' not in url2
    
    def test_generate_secure_url_with_expiry(self):
        """Test secure URL generation with custom expiry."""
        # 1 hour expiry
        url = generate_secure_url(expiry_hours=1)
        
        # Should be valid now
        assert validate_secure_url(url)
        
        # Should expire in the future
        expiry_time = extract_timestamp_from_url(url)
        assert expiry_time is not None
        assert expiry_time > datetime.now()
    
    def test_validate_secure_url_expired(self):
        """Test URL validation with expired URL."""
        # Create URL that expires in 1 second
        url = generate_secure_url(expiry_hours=1/3600)  # 1 second
        
        # Should be valid initially
        assert validate_secure_url(url)
        
        # Wait for expiration
        time.sleep(2)
        
        # Should be expired
        assert not validate_secure_url(url)
    
    def test_validate_secure_url_invalid(self):
        """Test URL validation with invalid URL."""
        # Invalid base64
        assert not validate_secure_url("invalid-url!")
        
        # Too short
        assert not validate_secure_url("abc")
        
        # Empty string
        assert not validate_secure_url("")
    
    def test_extract_timestamp_from_url(self):
        """Test timestamp extraction from URL."""
        url = generate_secure_url(expiry_hours=24)
        expiry_time = extract_timestamp_from_url(url)
        
        assert expiry_time is not None
        assert isinstance(expiry_time, datetime)
        
        # Should be in the future
        assert expiry_time > datetime.now()
    
    def test_generate_readable_id(self):
        """Test readable ID generation."""
        id1 = generate_readable_id()
        id2 = generate_readable_id()
        
        # IDs should be different
        assert id1 != id2
        
        # Should have correct format (3 groups of 6 chars)
        assert len(id1.split('-')) == 3
        assert all(len(group) == 6 for group in id1.split('-'))
        
        # Should only contain allowed characters
        allowed_chars = set("abcdefghijkmnpqrstuvwxyz23456789-")
        assert all(c in allowed_chars for c in id1)
    
    def test_get_url_info(self):
        """Test URL info retrieval."""
        url = generate_secure_url(expiry_hours=24)
        info = get_url_info(url)
        
        assert info["valid"] is True
        assert info["expires_at"] is not None
        assert info["expires_in_hours"] is not None
        assert info["expires_in_hours"] > 0
        
        # Test with expired URL
        expired_url = generate_secure_url(expiry_hours=1/3600)  # 1 second
        time.sleep(2)
        expired_info = get_url_info(expired_url)
        
        assert expired_info["valid"] is False
        assert expired_info["expires_in_hours"] == 0


class TestGist:
    """Test GitHub Gist functionality."""
    
    def test_gist_uploader_initialization(self):
        """Test GistUploader initialization."""
        token = "test_token_123"
        uploader = GistUploader(token)
        
        assert uploader.github_token == token
        assert uploader.api_base == "https://api.github.com"
        assert "Authorization" in uploader.headers
        assert "token test_token_123" in uploader.headers["Authorization"]
    
    @patch('requests.post')
    def test_upload_file_success(self, mock_post, tmp_path):
        """Test successful file upload to Gist."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "gist123",
            "html_url": "https://gist.github.com/user/gist123",
            "files": {
                "test.txt": {
                    "raw_url": "https://gist.githubusercontent.com/user/gist123/raw/test.txt"
                }
            }
        }
        mock_post.return_value = mock_response
        
        # Test upload
        uploader = GistUploader("test_token")
        result = uploader.upload_file(test_file, "Test Description")
        
        # Verify result
        assert result["gist_id"] == "gist123"
        assert result["file_name"] == "test.txt"
        assert result["file_size"] == len("test content")
        assert "secure_id" in result
        assert "download_url" in result
        assert "expires_at" in result
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.github.com/gists"
        assert call_args[1]["headers"]["Authorization"] == "token test_token"
    
    @patch('requests.post')
    def test_upload_file_not_found(self, mock_post, tmp_path):
        """Test upload with non-existent file."""
        uploader = GistUploader("test_token")
        
        with pytest.raises(FileNotFoundError):
            uploader.upload_file(tmp_path / "nonexistent.txt")
        
        # Should not make API call
        mock_post.assert_not_called()
    
    @patch('requests.post')
    def test_upload_file_api_error(self, mock_post, tmp_path):
        """Test upload with API error."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Bad credentials"}
        mock_post.return_value = mock_response
        
        # Test upload
        uploader = GistUploader("test_token")
        
        with pytest.raises(requests.RequestException) as exc_info:
            uploader.upload_file(test_file)
        
        assert "Failed to upload to GitHub Gist: 401" in str(exc_info.value)
        assert "Bad credentials" in str(exc_info.value)
    
    def test_generate_download_command(self):
        """Test download command generation."""
        download_url = "https://gist.githubusercontent.com/user/gist123/raw/test.tar.gz?token=abc123"
        file_name = "packster-migration-20241215-143022.tar.gz"
        
        command = generate_download_command(download_url, file_name)
        
        expected_base = "packster-migration-20241215-143022"
        expected_command = f'curl -L "{download_url}" | tar -xz && cd {expected_base} && ./bootstrap.sh/bootstrap.sh'
        
        assert command == expected_command
    
    @patch('requests.get')
    def test_validate_github_token_valid(self, mock_get):
        """Test GitHub token validation with valid token."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = validate_github_token("valid_token")
        assert result is True
        
        # Verify API call
        mock_get.assert_called_once_with(
            "https://api.github.com/user",
            headers={
                "Authorization": "token valid_token",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Packster/1.0.0"
            },
            timeout=10
        )
    
    @patch('requests.get')
    def test_validate_github_token_invalid(self, mock_get):
        """Test GitHub token validation with invalid token."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = validate_github_token("invalid_token")
        assert result is False
    
    @patch('requests.get')
    def test_validate_github_token_network_error(self, mock_get):
        """Test GitHub token validation with network error."""
        # Mock network error
        mock_get.side_effect = requests.RequestException("Network error")
        
        result = validate_github_token("test_token")
        assert result is False
    
    @patch('requests.delete')
    def test_delete_gist_success(self, mock_delete):
        """Test successful Gist deletion."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        uploader = GistUploader("test_token")
        result = uploader.delete_gist("gist123")
        
        assert result is True
        mock_delete.assert_called_once_with(
            "https://api.github.com/gists/gist123",
            headers=uploader.headers,
            timeout=10
        )
    
    @patch('requests.delete')
    def test_delete_gist_failure(self, mock_delete):
        """Test Gist deletion failure."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_delete.return_value = mock_response
        
        uploader = GistUploader("test_token")
        result = uploader.delete_gist("gist123")
        
        assert result is False
