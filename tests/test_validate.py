"""Tests for the validate module."""

import pytest
from unittest.mock import patch, mock_open
from packster.validate import (
    exists_in_brew,
    exists_in_cask,
    validate_brew_candidates,
)
from packster.types import Candidate


class TestBrewValidation:
    """Test Homebrew validation functionality."""
    
    @patch('packster.detect.run_command_safe')
    def test_exists_in_brew_true(self, mock_run_safe):
        """Test successful brew package existence check."""
        mock_run_safe.return_value = (0, "git: stable 2.39.2", "")
        
        result = exists_in_brew("git")
        
        assert result is True
        mock_run_safe.assert_called_once_with(["brew", "info", "git"])
    
    @patch('packster.detect.run_command_safe')
    def test_exists_in_brew_false(self, mock_run_safe):
        """Test failed brew package existence check."""
        mock_run_safe.return_value = (1, "", "No available formula or cask")
        
        result = exists_in_brew("nonexistent")
        
        assert result is False
    
    @patch('packster.detect.run_command_safe')
    def test_exists_in_brew_error(self, mock_run_safe):
        """Test brew package existence check with error."""
        mock_run_safe.return_value = (-1, "", "Command failed")
        
        result = exists_in_brew("git")
        
        assert result is False
    
    @patch('packster.detect.run_command_safe')
    def test_exists_in_cask_true(self, mock_run_safe):
        """Test successful cask existence check."""
        mock_run_safe.return_value = (0, "visual-studio-code: 1.85.1", "")
        
        result = exists_in_cask("visual-studio-code")
        
        assert result is True
        mock_run_safe.assert_called_once_with(["brew", "info", "--cask", "visual-studio-code"])
    
    @patch('packster.detect.run_command_safe')
    def test_exists_in_cask_false(self, mock_run_safe):
        """Test failed cask existence check."""
        mock_run_safe.return_value = (1, "", "No available formula or cask")
        
        result = exists_in_cask("nonexistent-cask")
        
        assert result is False
    
    @patch('packster.detect.run_command_safe')
    def test_exists_in_cask_error(self, mock_run_safe):
        """Test cask existence check with error."""
        mock_run_safe.return_value = (-1, "", "Command failed")
        
        result = exists_in_cask("visual-studio-code")
        
        assert result is False


class TestCandidateValidation:
    """Test candidate validation functionality."""
    
    @patch('packster.validate.brew.exists_in_brew')
    @patch('packster.validate.brew.exists_in_cask')
    def test_validate_brew_candidates_success(self, mock_exists_cask, mock_exists_brew):
        """Test successful candidate validation."""
        mock_exists_brew.return_value = True
        mock_exists_cask.return_value = False
        
        candidates = [
            Candidate(
                target_pm="brew",
                target_name="git",
                confidence=0.95,
                reason="Direct mapping"
            ),
            Candidate(
                target_pm="cask",
                target_name="visual-studio-code",
                confidence=0.90,
                reason="Direct mapping"
            )
        ]
        
        result = validate_brew_candidates(candidates)
        
        assert len(result) == 2
        assert result[0].target_name == "git"
        assert result[0].confidence == 0.95
        assert result[1].target_name == "visual-studio-code"
        assert result[1].confidence == 0.45  # Reduced by half since cask validation fails
    
    @patch('packster.validate.brew.exists_in_brew')
    @patch('packster.validate.brew.exists_in_cask')
    def test_validate_brew_candidates_not_found(self, mock_exists_cask, mock_exists_brew):
        """Test candidate validation when packages not found."""
        mock_exists_brew.return_value = False
        mock_exists_cask.return_value = False
        
        candidates = [
            Candidate(
                target_pm="brew",
                target_name="nonexistent",
                confidence=0.95,
                reason="Direct mapping"
            )
        ]
        
        result = validate_brew_candidates(candidates)
        
        assert len(result) == 1
        assert result[0].target_name == "nonexistent"
        assert result[0].confidence < 0.95  # Confidence should be reduced
    
    @patch('packster.validate.brew.exists_in_brew')
    @patch('packster.validate.brew.exists_in_cask')
    def test_validate_brew_candidates_mixed(self, mock_exists_cask, mock_exists_brew):
        """Test candidate validation with mixed results."""
        mock_exists_brew.side_effect = [True, False]
        mock_exists_cask.return_value = False
        
        candidates = [
            Candidate(
                target_pm="brew",
                target_name="git",
                confidence=0.95,
                reason="Direct mapping"
            ),
            Candidate(
                target_pm="brew",
                target_name="nonexistent",
                confidence=0.90,
                reason="Heuristic mapping"
            )
        ]
        
        result = validate_brew_candidates(candidates)
        
        assert len(result) == 2
        assert result[0].confidence == 0.95  # Unchanged
        assert result[1].confidence < 0.90  # Reduced
    
    def test_validate_brew_candidates_empty(self):
        """Test candidate validation with empty list."""
        result = validate_brew_candidates([])
        assert result == []


class TestBrewInfo:
    """Test Homebrew info functionality."""
    
    @patch('packster.detect.run_command_safe')
    def test_get_brew_info_success(self, mock_run_safe):
        """Test successful brew info retrieval."""
        mock_run_safe.return_value = (
            0,
            "git: stable 2.39.2\nGit is a distributed version control system",
            ""
        )
        
        from packster.validate.brew import get_brew_info
        
        result = get_brew_info("git")
        
        assert result is not None
        assert "git" in result
        assert "stable" in result["git"]
        mock_run_safe.assert_called_once_with(["brew", "info", "git"])
    
    @patch('packster.detect.run_command_safe')
    def test_get_brew_info_failure(self, mock_run_safe):
        """Test failed brew info retrieval."""
        mock_run_safe.return_value = (1, "", "No available formula")
        
        from packster.validate.brew import get_brew_info
        
        result = get_brew_info("nonexistent")
        
        assert result is None
    
    @patch('packster.detect.run_command_safe')
    def test_get_brew_info_cask_success(self, mock_run_safe):
        """Test successful cask info retrieval."""
        mock_run_safe.return_value = (
            0,
            "visual-studio-code: 1.85.1\nVisual Studio Code is a code editor",
            ""
        )
        
        from packster.validate.brew import get_brew_info
        
        result = get_brew_info("visual-studio-code", cask=True)
        
        assert result is not None
        assert "visual-studio-code" in result
        mock_run_safe.assert_called_once_with(["brew", "info", "--cask", "visual-studio-code"])


class TestBrewSearch:
    """Test Homebrew search functionality."""
    
    @patch('packster.detect.run_command_safe')
    def test_search_brew_success(self, mock_run_safe):
        """Test successful brew search."""
        mock_run_safe.return_value = (
            0,
            "git\ngit-crypt\ngit-extras\ngit-flow",
            ""
        )
        
        from packster.validate.brew import search_brew
        
        result = search_brew("git")
        
        assert len(result) == 4
        assert "git" in result
        assert "git-crypt" in result
        mock_run_safe.assert_called_once_with(["brew", "search", "git"])
    
    @patch('packster.detect.run_command_safe')
    def test_search_brew_no_results(self, mock_run_safe):
        """Test brew search with no results."""
        mock_run_safe.return_value = (0, "", "")
        
        from packster.validate.brew import search_brew
        
        result = search_brew("nonexistent")
        
        assert result == []
    
    @patch('packster.detect.run_command_safe')
    def test_search_brew_error(self, mock_run_safe):
        """Test brew search with error."""
        mock_run_safe.return_value = (1, "", "Search failed")
        
        from packster.validate.brew import search_brew
        
        result = search_brew("git")
        
        assert result == []


class TestBrewAvailability:
    """Test Homebrew availability checking."""
    
    @patch('packster.detect.is_command_available')
    def test_is_homebrew_available_true(self, mock_is_available):
        """Test Homebrew availability when available."""
        mock_is_available.return_value = True
        
        from packster.validate.brew import is_homebrew_available
        
        result = is_homebrew_available()
        
        assert result is True
        mock_is_available.assert_called_once_with("brew")
    
    @patch('packster.detect.is_command_available')
    def test_is_homebrew_available_false(self, mock_is_available):
        """Test Homebrew availability when not available."""
        mock_is_available.return_value = False
        
        from packster.validate.brew import is_homebrew_available
        
        result = is_homebrew_available()
        
        assert result is False
    
    @patch('packster.detect.run_command_safe')
    def test_get_homebrew_version_success(self, mock_run_safe):
        """Test successful Homebrew version retrieval."""
        mock_run_safe.return_value = (0, "Homebrew 4.0.0", "")
        
        from packster.validate.brew import get_homebrew_version
        
        result = get_homebrew_version()
        
        assert result == "4.0.0"
        mock_run_safe.assert_called_once_with(["brew", "--version"])
    
    @patch('packster.detect.run_command_safe')
    def test_get_homebrew_version_failure(self, mock_run_safe):
        """Test failed Homebrew version retrieval."""
        mock_run_safe.return_value = (1, "", "Command failed")
        
        from packster.validate.brew import get_homebrew_version
        
        result = get_homebrew_version()
        
        assert result is None


class TestBrewInstalled:
    """Test Homebrew installed packages checking."""
    
    @patch('packster.detect.run_command_safe')
    def test_get_installed_brew_packages_success(self, mock_run_safe):
        """Test successful installed brew packages retrieval."""
        mock_run_safe.return_value = (
            0,
            "git\nvim\ncurl\n",
            ""
        )
        
        from packster.validate.brew import get_installed_brew_packages
        
        result = get_installed_brew_packages()
        
        assert len(result) == 3
        assert "git" in result
        assert "vim" in result
        assert "curl" in result
        mock_run_safe.assert_called_once_with(["brew", "list"])
    
    @patch('packster.detect.run_command_safe')
    def test_get_installed_brew_packages_empty(self, mock_run_safe):
        """Test installed brew packages retrieval with no packages."""
        mock_run_safe.return_value = (0, "", "")
        
        from packster.validate.brew import get_installed_brew_packages
        
        result = get_installed_brew_packages()
        
        assert result == []
    
    @patch('packster.detect.run_command_safe')
    def test_get_installed_cask_packages_success(self, mock_run_safe):
        """Test successful installed cask packages retrieval."""
        mock_run_safe.return_value = (
            0,
            "visual-studio-code\nslack\n",
            ""
        )
        
        from packster.validate.brew import get_installed_cask_packages
        
        result = get_installed_cask_packages()
        
        assert len(result) == 2
        assert "visual-studio-code" in result
        assert "slack" in result
        mock_run_safe.assert_called_once_with(["brew", "list", "--cask"])
    
    @patch('packster.detect.run_command_safe')
    def test_get_installed_cask_packages_empty(self, mock_run_safe):
        """Test installed cask packages retrieval with no packages."""
        mock_run_safe.return_value = (0, "", "")
        
        from packster.validate.brew import get_installed_cask_packages
        
        result = get_installed_cask_packages()
        
        assert result == []


class TestValidationIntegration:
    """Test validation integration scenarios."""
    
    @patch('packster.validate.brew.exists_in_brew')
    @patch('packster.validate.brew.exists_in_cask')
    def test_validate_mixed_package_types(self, mock_exists_cask, mock_exists_brew):
        """Test validation with mixed package types."""
        mock_exists_brew.return_value = True
        mock_exists_cask.return_value = True
        
        candidates = [
            Candidate(target_pm="brew", target_name="git", confidence=0.95),
            Candidate(target_pm="cask", target_name="visual-studio-code", confidence=0.90),
            Candidate(target_pm="brew", target_name="nonexistent", confidence=0.85),
        ]
        
        # Mock the calls to return True for first two, False for third
        mock_exists_brew.side_effect = [True, False]
        mock_exists_cask.return_value = True
        
        result = validate_brew_candidates(candidates)
        
        assert len(result) == 3
        assert result[0].confidence == 0.95  # Unchanged
        assert result[1].confidence == 0.90  # Unchanged
        assert result[2].confidence < 0.85  # Reduced
    
    def test_candidate_validation_edge_cases(self):
        """Test candidate validation edge cases."""
        # Test with None confidence (should be handled gracefully)
        try:
            candidate = Candidate(
                target_pm="brew",
                target_name="test",
                confidence=None,
                reason="Test"
            )
        except Exception:
            # Expected to fail since confidence is required
            pass
        
        # Test with valid confidence
        candidate = Candidate(
            target_pm="brew",
            target_name="test",
            confidence=1.0,
            reason="Test"
        )
        
        assert candidate.target_pm == "brew"
        assert candidate.target_name == "test"
        
        # Test with very high confidence
        candidate = Candidate(
            target_pm="brew",
            target_name="test",
            confidence=1.0,
            reason="Test"
        )
        
        assert candidate.confidence == 1.0
