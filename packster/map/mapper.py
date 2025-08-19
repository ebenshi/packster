"""Main package mapping logic for Packster."""

import logging
from typing import List, Optional
from ..types import NormalizedItem, Candidate, MappingResult, Decision
from ..config import DECISION_THRESHOLDS
from .registry import Registry, find_mapping
from .heuristics import (
    apply_heuristics,
    apply_common_patterns,
    apply_category_based_mapping,
    combine_heuristic_results
)
from ..validate.brew import exists_in_brew, exists_in_cask

logger = logging.getLogger(__name__)


class PackageMapper:
    """Main package mapper that coordinates all mapping logic."""
    
    def __init__(self, registry: Registry, verify: bool = True):
        """Initialize the package mapper.
        
        Args:
            registry: Package mapping registry
            verify: Whether to verify candidates with Homebrew
        """
        self.registry = registry
        self.verify = verify
    
    def map_packages(self, packages: List[NormalizedItem]) -> List[MappingResult]:
        """Map a list of packages to target package managers.
        
        Args:
            packages: List of normalized packages to map
            
        Returns:
            List of mapping results
        """
        results = []
        
        for package in packages:
            result = self.map_single_package(package)
            results.append(result)
        
        logger.info(f"Mapped {len(packages)} packages")
        return results
    
    def map_single_package(self, package: NormalizedItem) -> MappingResult:
        """Map a single package to target package managers.
        
        Args:
            package: Normalized package to map
            
        Returns:
            Mapping result for the package
        """
        source_name = package.source_name
        candidates = []
        
        # Step 1: Check registry for exact matches
        registry_mapping = find_mapping(self.registry, source_name)
        if registry_mapping:
            candidate = Candidate(
                target_pm=registry_mapping.target_pm,
                target_name=registry_mapping.target_name,
                confidence=registry_mapping.confidence,
                reason=registry_mapping.reason,
                post_install=registry_mapping.post_install
            )
            candidates.append(candidate)
        
        # Step 2: Apply heuristics if no registry match
        if not candidates:
            heuristic_matches = apply_heuristics(source_name)
            for target_pm, target_name, confidence, reason in heuristic_matches:
                candidate = Candidate(
                    target_pm=target_pm,
                    target_name=target_name,
                    confidence=confidence,
                    reason=reason
                )
                candidates.append(candidate)
        
        # Step 3: Apply common patterns
        pattern_matches = apply_common_patterns(source_name)
        for target_pm, target_name, confidence, reason in pattern_matches:
            candidate = Candidate(
                target_pm=target_pm,
                target_name=target_name,
                confidence=confidence,
                reason=reason
            )
            candidates.append(candidate)
        
        # Step 4: Apply category-based mapping
        category_matches = apply_category_based_mapping(source_name, package.category)
        for target_pm, target_name, confidence, reason in category_matches:
            candidate = Candidate(
                target_pm=target_pm,
                target_name=target_name,
                confidence=confidence,
                reason=reason
            )
            candidates.append(candidate)
        
        # Step 5: Validate candidates if verification is enabled
        if self.verify and candidates:
            validated_candidates = []
            for candidate in candidates:
                if self._validate_candidate(candidate):
                    validated_candidates.append(candidate)
            candidates = validated_candidates
        
        # Step 6: Make decision based on confidence and validation
        decision = self._make_decision(candidates)
        
        return MappingResult(
            source=package,
            candidate=candidates[0] if candidates else None,
            decision=decision
        )
    
    def _validate_candidate(self, candidate: Candidate) -> bool:
        """Validate a candidate mapping with Homebrew.
        
        Args:
            candidate: Candidate to validate
            
        Returns:
            True if candidate is valid, False otherwise
        """
        try:
            if candidate.target_pm == "brew":
                return exists_in_brew(candidate.target_name)
            elif candidate.target_pm == "cask":
                return exists_in_cask(candidate.target_name)
            else:
                # Unknown package manager, assume valid
                return True
        except Exception as e:
            logger.debug(f"Validation failed for {candidate.target_pm}:{candidate.target_name}: {e}")
            return False
    
    def _make_decision(self, candidates: List[Candidate]) -> Decision:
        """Make a decision based on candidate confidence scores.
        
        Args:
            candidates: List of validated candidates
            
        Returns:
            Decision for the package
        """
        if not candidates:
            return Decision.MANUAL
        
        # Get the best candidate (highest confidence)
        best_candidate = max(candidates, key=lambda c: c.confidence)
        
        # Apply decision thresholds
        if best_candidate.confidence >= DECISION_THRESHOLDS["auto"]:
            return Decision.AUTO
        elif best_candidate.confidence >= DECISION_THRESHOLDS["verify"]:
            return Decision.VERIFY
        else:
            return Decision.MANUAL


def map_packages(
    packages: List[NormalizedItem],
    registry: Registry,
    verify: bool = True
) -> List[MappingResult]:
    """Convenience function to map packages.
    
    Args:
        packages: List of normalized packages to map
        registry: Package mapping registry
        verify: Whether to verify candidates with Homebrew
        
    Returns:
        List of mapping results
    """
    mapper = PackageMapper(registry, verify)
    return mapper.map_packages(packages)


def get_mapping_statistics(results: List[MappingResult]) -> dict:
    """Get statistics about mapping results.
    
    Args:
        results: List of mapping results
        
    Returns:
        Dictionary with mapping statistics
    """
    stats = {
        "total": len(results),
        "auto": 0,
        "verify": 0,
        "manual": 0,
        "skipped": 0,
        "by_target_pm": {},
        "by_confidence": {
            "high": 0,    # 0.9-1.0
            "medium": 0,  # 0.6-0.89
            "low": 0,     # 0.0-0.59
        }
    }
    
    for result in results:
        # Count decisions
        stats[result.decision.value] += 1
        
        # Count by target package manager
        if result.candidate:
            pm = result.candidate.target_pm
            stats["by_target_pm"][pm] = stats["by_target_pm"].get(pm, 0) + 1
            
            # Count by confidence
            if result.candidate.confidence >= 0.9:
                stats["by_confidence"]["high"] += 1
            elif result.candidate.confidence >= 0.6:
                stats["by_confidence"]["medium"] += 1
            else:
                stats["by_confidence"]["low"] += 1
    
    return stats


def filter_mapping_results(
    results: List[MappingResult],
    decisions: Optional[List[Decision]] = None,
    min_confidence: float = 0.0
) -> List[MappingResult]:
    """Filter mapping results by decision and confidence.
    
    Args:
        results: List of mapping results
        decisions: List of decisions to include (None for all)
        min_confidence: Minimum confidence threshold
        
    Returns:
        Filtered list of mapping results
    """
    filtered = []
    
    for result in results:
        # Filter by decision
        if decisions and result.decision not in decisions:
            continue
        
        # Filter by confidence
        if result.candidate and result.candidate.confidence < min_confidence:
            continue
        
        filtered.append(result)
    
    return filtered
