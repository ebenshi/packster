"""Pydantic data models for Packster."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict


class PackageManager(str, Enum):
    """Supported package managers."""
    APT = "apt"
    PIP = "pip"
    NPM = "npm"
    CARGO = "cargo"
    GEM = "gem"


class Decision(str, Enum):
    """Mapping decision types."""
    AUTO = "auto"
    VERIFY = "verify"
    MANUAL = "manual"
    SKIP = "skip"


class NormalizedItem(BaseModel):
    """Normalized package item from any source."""
    source_pm: PackageManager = Field(..., alias="package_manager", description="Source package manager")
    source_name: str = Field(..., alias="name", description="Package name in source")
    # Backwards-compat properties used by tests
    @property
    def package_manager(self) -> PackageManager:
        return self.source_pm

    @property
    def name(self) -> str:
        return self.source_name
    version: Optional[str] = Field(None, description="Package version if available")
    category: Optional[str] = Field(None, description="Package category/type")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Allow population by field name or alias
    model_config = ConfigDict(populate_by_name=True)


class Candidate(BaseModel):
    """Candidate mapping to target package manager."""
    target_pm: str = Field(..., description="Target package manager (e.g., 'brew', 'cask')")
    target_name: str = Field(..., description="Target package name")
    kind: Optional[str] = Field(None, description="Package kind/type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reason: Optional[str] = Field(None, description="Reason for this mapping")
    post_install: List[str] = Field(default_factory=list, description="Post-install commands")

    # Backwards-compat properties used by tests
    @property
    def pm(self) -> str:
        return self.target_pm

    @property
    def name(self) -> str:
        return self.target_name


class MappingResult(BaseModel):
    """Result of mapping a normalized item."""
    source: NormalizedItem = Field(..., description="Original normalized item")
    candidate: Optional[Candidate] = Field(None, description="Best candidate mapping")
    decision: Decision = Field(..., description="Final decision")
    notes: Optional[str] = Field(None, description="Additional notes")

    # Backwards-compat properties for template/tests expecting `item` and `candidates`
    @property
    def item(self) -> NormalizedItem:
        return self.source

    @property
    def candidates(self) -> List[Candidate]:
        return [self.candidate] if self.candidate else []


class Report(BaseModel):
    """Complete migration report."""
    mapped_auto: List[MappingResult] = Field(default_factory=list, description="Auto-mapped items")
    mapped_verify: List[MappingResult] = Field(default_factory=list, description="Verify items")
    manual: List[MappingResult] = Field(default_factory=list, description="Manual items")
    skipped: List[MappingResult] = Field(default_factory=list, description="Skipped items")
    
    @property
    def total_items(self) -> int:
        """Total number of items processed."""
        return (
            len(self.mapped_auto) + 
            len(self.mapped_verify) + 
            len(self.manual) + 
            len(self.skipped)
        )
    
    @property
    def auto_percentage(self) -> float:
        """Percentage of items auto-mapped."""
        if self.total_items == 0:
            return 0.0
        return (len(self.mapped_auto) / self.total_items) * 100
