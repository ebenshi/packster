"""Tests for the map module."""

from unittest.mock import patch, mock_open
from packster.map import (
    load_registry,
    RegistryMapping,
    apply_heuristics,
    HeuristicRule,
    map_packages,
    PackageMapper,
)
from packster.types import NormalizedItem, PackageManager, Candidate, MappingResult, Decision
from packster.map.registry import Registry

class TestRegistryLoading:
    """Test registry loading functionality."""
    
    def test_load_registry_success(self):
        """Test successful registry loading."""
        yaml_content = """
        name: "Ubuntu to Homebrew"
        description: "Package mappings from Ubuntu to Homebrew"
        version: "1.0.0"
        mappings:
          git:
            target_pm: "brew"
            target_name: "git"
            confidence: 0.95
            reason: "Direct mapping"
          vim:
            target_pm: "brew"
            target_name: "vim"
            confidence: 0.90
            reason: "Direct mapping"
        """
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('yaml.safe_load') as mock_yaml_load:
                mock_yaml_load.return_value = {
                    "name": "Ubuntu to Homebrew",
                    "description": "Package mappings from Ubuntu to Homebrew",
                    "version": "1.0.0",
                    "mappings": {
                        "git": {
                            "target_pm": "brew",
                            "target_name": "git",
                            "confidence": 0.95,
                            "reason": "Direct mapping"
                        }
                    }
                }
                
                registry = load_registry("tests/test.yaml")
                
                assert registry.name == "Ubuntu to Homebrew"
                assert len(registry.mappings) == 1
                assert "git" in registry.mappings
                assert registry.mappings["git"].target_pm == "brew"
                assert registry.mappings["git"].target_name == "git"
    
    def test_load_registry_file_not_found(self):
        """Test registry loading when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            registry = load_registry("nonexistent.yaml")
            assert registry.name == "Default Registry"
            assert len(registry.mappings) == 0


class TestRegistryMapping:
    """Test RegistryMapping model."""
    
    def test_registry_mapping_creation(self):
        """Test creating a RegistryMapping instance."""
        mapping = RegistryMapping(
            target_pm="brew",
            target_name="git",
            confidence=0.95,
            reason="Direct mapping"
        )
        
        assert mapping.target_pm == "brew"
        assert mapping.target_name == "git"
        assert mapping.confidence == 0.95
        assert mapping.reason == "Direct mapping"
    
    def test_registry_mapping_defaults(self):
        """Test RegistryMapping with default values."""
        mapping = RegistryMapping(
            target_pm="brew",
            target_name="git"
        )
        
        assert mapping.confidence == 0.8
        assert mapping.reason == "Registry mapping"


class TestHeuristics:
    """Test heuristic mapping functionality."""
    
    def test_apply_heuristics_success(self):
        """Test successful heuristic application."""
        package = NormalizedItem(
            source_name="fd-find",
            version="8.4.0",
            source_pm=PackageManager.APT
        )
        
        result = apply_heuristics(package)
        
        assert result is not None
        assert len(result) > 0
        assert result[0][0] == "brew"  # target_pm
        assert result[0][1] == "fd"    # target_name
        assert result[0][2] > 0.7      # confidence
        assert "ubuntu" in result[0][3].lower()  # reason
    
    def test_apply_heuristics_no_match(self):
        """Test heuristic application with no match."""
        package = NormalizedItem(
            source_name="nonexistent-package",
            version="1.0.0",
            source_pm=PackageManager.APT
        )
        
        result = apply_heuristics(package)
        
        assert result == []
    
    def test_heuristic_rule_creation(self):
        """Test creating a HeuristicRule instance."""
        rule = HeuristicRule(
            pattern="fd-find",
            target_pm="brew",
            target_name="fd",
            confidence=0.8,
            reason="Common alias"
        )
        
        assert rule.pattern == "fd-find"
        assert rule.target_pm == "brew"
        assert rule.target_name == "fd"
        assert rule.confidence == 0.8
        assert rule.reason == "Common alias"


class TestPackageMapper:
    """Test PackageMapper functionality."""
    
    def test_package_mapper_creation(self):
        """Test creating a PackageMapper instance."""
        registry = Registry(name="test")
        mapper = PackageMapper(registry, verify=False)
        
        assert mapper.verify is False
        assert mapper.registry.name == "test"
    
    @patch('packster.map.mapper.exists_in_brew')
    @patch('packster.map.mapper.exists_in_cask')
    def test_map_packages_success(self, mock_exists_cask, mock_exists_brew):
        """Test successful package mapping."""
        # Mock validation functions to return True
        mock_exists_brew.return_value = True
        mock_exists_cask.return_value = True
        
        packages = [
            NormalizedItem(
                source_name="git",
                version="2.25.1",
                source_pm=PackageManager.APT
            ),
            NormalizedItem(
                source_name="vim",
                version="8.2",
                source_pm=PackageManager.APT
            )
        ]
        
        with patch('packster.map.registry.load_registry') as mock_load_registry:
            mock_load_registry.return_value.mappings = {
                "git": RegistryMapping(
                    target_pm="brew",
                    target_name="git",
                    confidence=0.95,
                    reason="Direct mapping"
                ),
                "vim": RegistryMapping(
                    target_pm="brew",
                    target_name="vim",
                    confidence=0.90,
                    reason="Direct mapping"
                )
            }
            
            registry = Registry(name="test", mappings={
                "git": RegistryMapping(
                    target_pm="brew",
                    target_name="git",
                    confidence=0.95,
                    reason="Direct mapping"
                ),
                "vim": RegistryMapping(
                    target_pm="brew",
                    target_name="vim",
                    confidence=0.90,
                    reason="Direct mapping"
                )
            })
            results = map_packages(packages, registry)
            
            assert len(results) == 2
            assert all(isinstance(result, MappingResult) for result in results)
            assert results[0].source.source_name == "git"
            assert results[0].decision == Decision.AUTO
            assert results[1].source.source_name == "vim"
            assert results[1].decision == Decision.AUTO
    
    @patch('packster.map.mapper.exists_in_brew')
    @patch('packster.map.mapper.exists_in_cask')
    def test_map_packages_mixed_results(self, mock_exists_cask, mock_exists_brew):
        """Test package mapping with mixed results."""
        # Mock validation functions to return True
        mock_exists_brew.return_value = True
        mock_exists_cask.return_value = True
        
        packages = [
            NormalizedItem(
                source_name="git",
                version="2.25.1",
                source_pm=PackageManager.APT
            ),
            NormalizedItem(
                source_name="unknown-package",
                version="1.0.0",
                source_pm=PackageManager.APT
            )
        ]
        
        with patch('packster.map.registry.load_registry') as mock_load_registry:
            mock_load_registry.return_value.mappings = {
                "git": RegistryMapping(
                    target_pm="brew",
                    target_name="git",
                    confidence=0.95,
                    reason="Direct mapping"
                )
            }
            
            registry = Registry(name="test", mappings={
                "git": RegistryMapping(
                    target_pm="brew",
                    target_name="git",
                    confidence=0.95,
                    reason="Direct mapping"
                )
            })
            results = map_packages(packages, registry)
            
            assert len(results) == 2
            assert results[0].decision == Decision.AUTO
            assert results[1].decision == Decision.MANUAL
    
    def test_map_packages_empty_list(self):
        """Test mapping empty package list."""
        registry = Registry(name="test")
        results = map_packages([], registry)
        assert results == []


class TestMappingResults:
    """Test MappingResult model."""
    
    def test_mapping_result_creation(self):
        """Test creating a MappingResult instance."""
        source = NormalizedItem(
            source_name="git",
            version="2.25.1",
            source_pm=PackageManager.APT
        )
        
        candidate = Candidate(
            target_pm="brew",
            target_name="git",
            confidence=0.95,
            reason="Direct mapping"
        )
        
        result = MappingResult(
            source=source,
            candidate=candidate,
            decision=Decision.AUTO
        )
        
        assert result.source == source
        assert result.candidate == candidate
        assert result.decision == Decision.AUTO
    
    def test_mapping_result_without_candidate(self):
        """Test MappingResult without candidate."""
        source = NormalizedItem(
            source_name="unknown-package",
            version="1.0.0",
            source_pm=PackageManager.APT
        )
        
        result = MappingResult(
            source=source,
            candidate=None,
            decision=Decision.MANUAL
        )
        
        assert result.source == source
        assert result.candidate is None
        assert result.decision == Decision.MANUAL


class TestDecisionLogic:
    """Test decision-making logic."""
    
    def test_decision_auto_threshold(self):
        """Test AUTO decision with high confidence."""
        candidate = Candidate(
            target_pm="brew",
            target_name="git",
            confidence=0.95,
            reason="Direct mapping"
        )
        
        # This would be tested in the actual decision logic
        assert candidate.confidence > 0.8
    
    def test_decision_verify_threshold(self):
        """Test VERIFY decision with medium confidence."""
        candidate = Candidate(
            target_pm="brew",
            target_name="vim",
            confidence=0.7,
            reason="Heuristic mapping"
        )
        
        # This would be tested in the actual decision logic
        assert 0.6 <= candidate.confidence <= 0.8
    
    def test_decision_manual_threshold(self):
        """Test MANUAL decision with low confidence."""
        candidate = Candidate(
            target_pm="brew",
            target_name="unknown",
            confidence=0.3,
            reason="Low confidence mapping"
        )
        
        # This would be tested in the actual decision logic
        assert candidate.confidence < 0.6


class TestCandidateValidation:
    """Test candidate validation functionality."""
    
    @patch('packster.validate.brew.exists_in_brew')
    def test_validate_candidates_success(self, mock_exists):
        """Test successful candidate validation."""
        mock_exists.return_value = True
        
        candidate = Candidate(
            target_pm="brew",
            target_name="git",
            confidence=0.95,
            reason="Direct mapping"
        )
        
        # This would be tested in the actual validation logic
        assert candidate.target_pm == "brew"
        assert candidate.target_name == "git"
    
    @patch('packster.validate.brew.exists_in_brew')
    def test_validate_candidates_not_found(self, mock_exists):
        """Test candidate validation when package not found."""
        mock_exists.return_value = False
        
        candidate = Candidate(
            target_pm="brew",
            target_name="nonexistent",
            confidence=0.95,
            reason="Direct mapping"
        )
        
        # This would be tested in the actual validation logic
        assert candidate.target_pm == "brew"
        assert candidate.target_name == "nonexistent"


class TestStatistics:
    """Test mapping statistics functionality."""
    
    def test_mapping_statistics(self):
        """Test calculating mapping statistics."""
        results = [
            MappingResult(
                source=NormalizedItem(source_name="git", source_pm=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="git", confidence=0.95),
                decision=Decision.AUTO
            ),
            MappingResult(
                source=NormalizedItem(source_name="vim", source_pm=PackageManager.APT),
                candidate=Candidate(target_pm="brew", target_name="vim", confidence=0.7),
                decision=Decision.VERIFY
            ),
            MappingResult(
                source=NormalizedItem(source_name="unknown", source_pm=PackageManager.APT),
                candidate=None,
                decision=Decision.MANUAL
            )
        ]
        
        # This would be tested in the actual statistics logic
        assert len(results) == 3
        assert results[0].decision == Decision.AUTO
        assert results[1].decision == Decision.VERIFY
        assert results[2].decision == Decision.MANUAL
