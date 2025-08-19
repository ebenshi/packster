"""Heuristic mapping rules for packages."""

import logging
import re
from typing import List, Dict, Optional, Tuple, Union
from pydantic import BaseModel, Field
from ..types import NormalizedItem

logger = logging.getLogger(__name__)


class HeuristicRule(BaseModel):
    """A single heuristic rule for package mapping."""
    pattern: str = Field(..., description="Pattern to match (regex or simple string)")
    target_pm: str = Field(..., description="Target package manager")
    target_name: str = Field(..., description="Target package name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reason: str = Field(..., description="Reason for this mapping")
    is_regex: bool = Field(default=False, description="Whether pattern is regex")
    post_install: List[str] = Field(default_factory=list, description="Post-install commands")


# Common heuristic rules for Ubuntu -> Homebrew mapping
DEFAULT_HEURISTICS = [
    # Common name variations
    HeuristicRule(
        pattern="fd-find",
        target_pm="brew",
        target_name="fd",
        confidence=0.9,
        reason="fd-find is the Ubuntu package name for fd"
    ),
    HeuristicRule(
        pattern="python3-pip",
        target_pm="brew",
        target_name="python@3.12",
        confidence=0.6,
        reason="python3-pip suggests Python 3 installation"
    ),
    HeuristicRule(
        pattern="gnome-terminal",
        target_pm="cask",
        target_name="iterm2",
        confidence=0.8,
        reason="GUI terminal on macOS"
    ),
    HeuristicRule(
        pattern="docker.io",
        target_pm="cask",
        target_name="docker",
        confidence=0.85,
        reason="Docker Desktop on macOS"
    ),
    HeuristicRule(
        pattern="nodejs",
        target_pm="brew",
        target_name="node",
        confidence=0.9,
        reason="nodejs is the Ubuntu package name for node"
    ),
    HeuristicRule(
        pattern="python3",
        target_pm="brew",
        target_name="python@3.12",
        confidence=0.8,
        reason="Python 3 on macOS"
    ),
    HeuristicRule(
        pattern="^lib(.+)$",
        target_pm="brew",
        target_name="\\1",
        confidence=0.3,
        reason="Library packages often have lib prefix",
        is_regex=True
    ),
    HeuristicRule(
        pattern="^(.+)-dev$",
        target_pm="brew",
        target_name="\\1",
        confidence=0.4,
        reason="Development packages often have -dev suffix",
        is_regex=True
    ),
    HeuristicRule(
        pattern="^(.+)-dbg$",
        target_pm="brew",
        target_name="\\1",
        confidence=0.3,
        reason="Debug packages often have -dbg suffix",
        is_regex=True
    ),
    HeuristicRule(
        pattern="^(.+)-doc$",
        target_pm="brew",
        target_name="\\1",
        confidence=0.2,
        reason="Documentation packages often have -doc suffix",
        is_regex=True
    ),
]


def apply_heuristics(
    source_name: Union[str, NormalizedItem],
    heuristics: Optional[List[HeuristicRule]] = None
) -> List[Tuple[str, str, float, str]]:
    """Apply heuristic rules to find potential mappings.
    
    Args:
        source_name: Source package name or NormalizedItem
        heuristics: List of heuristic rules (uses defaults if None)
        
    Returns:
        List of (target_pm, target_name, confidence, reason) tuples
    """
    if heuristics is None:
        heuristics = DEFAULT_HEURISTICS
    
    # Extract source name if NormalizedItem is passed
    if isinstance(source_name, NormalizedItem):
        source_name = source_name.source_name
    
    matches = []
    
    for rule in heuristics:
        if rule.is_regex:
            # Apply regex pattern
            match = re.match(rule.pattern, source_name)
            if match:
                # Substitute capture groups in target name
                target_name = re.sub(rule.pattern, rule.target_name, source_name)
                matches.append((
                    rule.target_pm,
                    target_name,
                    rule.confidence,
                    rule.reason
                ))
        else:
            # Simple string match
            if source_name == rule.pattern:
                matches.append((
                    rule.target_pm,
                    rule.target_name,
                    rule.confidence,
                    rule.reason
                ))
    
    # Sort by confidence (highest first)
    matches.sort(key=lambda x: x[2], reverse=True)
    
    return matches


def apply_name_aliases(
    source_name: str,
    aliases: Dict[str, str]
) -> Optional[str]:
    """Apply name aliases to find alternative names.
    
    Args:
        source_name: Source package name
        aliases: Dictionary of name aliases
        
    Returns:
        Aliased name if found, None otherwise
    """
    return aliases.get(source_name)


def apply_common_patterns(source_name: str) -> List[Tuple[str, str, float, str]]:
    """Apply common naming patterns for package mapping.
    
    Args:
        source_name: Source package name
        
    Returns:
        List of potential mappings based on patterns
    """
    patterns = []
    
    # Remove common prefixes
    if source_name.startswith("python3-"):
        base_name = source_name[8:]  # Remove "python3-"
        patterns.append(("brew", base_name, 0.7, f"Python package: {base_name}"))
    
    # Remove common suffixes
    if source_name.endswith("-bin"):
        base_name = source_name[:-4]  # Remove "-bin"
        patterns.append(("brew", base_name, 0.6, f"Binary package: {base_name}"))
    
    # Handle version suffixes
    version_match = re.match(r"^(.+)-(\d+\.\d+)$", source_name)
    if version_match:
        base_name = version_match.group(1)
        patterns.append(("brew", base_name, 0.5, f"Versioned package: {base_name}"))
    
    return patterns


def apply_similarity_matching(
    source_name: str,
    known_packages: List[str],
    threshold: float = 0.8
) -> List[Tuple[str, float]]:
    """Find similar package names using string similarity.
    
    Args:
        source_name: Source package name
        known_packages: List of known package names
        threshold: Similarity threshold (0.0-1.0)
        
    Returns:
        List of (package_name, similarity_score) tuples
    """
    from difflib import SequenceMatcher
    
    similarities = []
    
    for package in known_packages:
        similarity = SequenceMatcher(None, source_name.lower(), package.lower()).ratio()
        if similarity >= threshold:
            similarities.append((package, similarity))
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities


def apply_category_based_mapping(
    source_name: str,
    category: Optional[str] = None
) -> List[Tuple[str, str, float, str]]:
    """Apply category-based mapping rules.
    
    Args:
        source_name: Source package name
        category: Package category
        
    Returns:
        List of potential mappings
    """
    mappings = []
    
    # Database packages
    if category == "databases" or any(db in source_name.lower() for db in ["postgres", "mysql", "sqlite", "redis"]):
        if "postgres" in source_name.lower():
            mappings.append(("brew", "postgresql", 0.8, "PostgreSQL database"))
        elif "mysql" in source_name.lower():
            mappings.append(("brew", "mysql", 0.8, "MySQL database"))
        elif "sqlite" in source_name.lower():
            mappings.append(("brew", "sqlite", 0.8, "SQLite database"))
        elif "redis" in source_name.lower():
            mappings.append(("brew", "redis", 0.8, "Redis database"))
    
    # Development tools
    elif category == "development" or any(dev in source_name.lower() for dev in ["git", "vim", "tmux", "htop"]):
        if "git" in source_name.lower():
            mappings.append(("brew", "git", 0.9, "Git version control"))
        elif "vim" in source_name.lower():
            mappings.append(("brew", "vim", 0.9, "Vim editor"))
        elif "tmux" in source_name.lower():
            mappings.append(("brew", "tmux", 0.9, "Tmux terminal multiplexer"))
        elif "htop" in source_name.lower():
            mappings.append(("brew", "htop", 0.9, "Htop process viewer"))
    
    # Utilities
    elif category == "utilities" or any(util in source_name.lower() for util in ["curl", "wget", "jq", "ripgrep"]):
        if "curl" in source_name.lower():
            mappings.append(("brew", "curl", 0.9, "cURL HTTP client"))
        elif "wget" in source_name.lower():
            mappings.append(("brew", "wget", 0.9, "Wget download utility"))
        elif "jq" in source_name.lower():
            mappings.append(("brew", "jq", 0.9, "jq JSON processor"))
        elif "ripgrep" in source_name.lower():
            mappings.append(("brew", "ripgrep", 0.9, "ripgrep search tool"))
    
    return mappings


def combine_heuristic_results(
    registry_matches: List[Tuple[str, str, float, str]],
    heuristic_matches: List[Tuple[str, str, float, str]],
    pattern_matches: List[Tuple[str, str, float, str]],
    category_matches: List[Tuple[str, str, float, str]]
) -> List[Tuple[str, str, float, str]]:
    """Combine results from different heuristic sources.
    
    Args:
        registry_matches: Matches from registry
        heuristic_matches: Matches from heuristic rules
        pattern_matches: Matches from pattern matching
        category_matches: Matches from category-based mapping
        
    Returns:
        Combined and deduplicated list of matches
    """
    all_matches = []
    
    # Add registry matches (highest priority)
    for target_pm, target_name, confidence, reason in registry_matches:
        all_matches.append((target_pm, target_name, confidence, f"Registry: {reason}"))
    
    # Add heuristic matches
    for target_pm, target_name, confidence, reason in heuristic_matches:
        all_matches.append((target_pm, target_name, confidence, f"Heuristic: {reason}"))
    
    # Add pattern matches
    for target_pm, target_name, confidence, reason in pattern_matches:
        all_matches.append((target_pm, target_name, confidence, f"Pattern: {reason}"))
    
    # Add category matches
    for target_pm, target_name, confidence, reason in category_matches:
        all_matches.append((target_pm, target_name, confidence, f"Category: {reason}"))
    
    # Deduplicate by target_pm:target_name combination
    seen = set()
    unique_matches = []
    
    for target_pm, target_name, confidence, reason in all_matches:
        key = f"{target_pm}:{target_name}"
        if key not in seen:
            seen.add(key)
            unique_matches.append((target_pm, target_name, confidence, reason))
    
    # Sort by confidence (highest first)
    unique_matches.sort(key=lambda x: x[2], reverse=True)
    
    return unique_matches
