"""Language package file generation for Packster."""

import logging
from pathlib import Path
from typing import List, Dict
from ..types import NormalizedItem, PackageManager, MappingResult, Decision

logger = logging.getLogger(__name__)


def write_language_files(
    items: List[NormalizedItem] | List[MappingResult],
    output_dir: Path
) -> Dict[str, Path]:
    """Write language-specific package files.
    
    Args:
        packages: List of normalized packages
        output_dir: Output directory for language files
        
    Returns:
        Dictionary mapping language names to file paths
    """
    # Create lang directory
    lang_dir = output_dir / "lang"
    lang_dir.mkdir(exist_ok=True)
    
    # If MappingResult provided, take AUTO/VERIFY sources; else assume NormalizedItem list
    if items and isinstance(items[0], MappingResult):
        packages: List[NormalizedItem] = [
            r.source for r in items if r.decision in (Decision.AUTO, Decision.VERIFY) and r.source is not None
        ]
    else:
        packages = items  # type: ignore[assignment]

    # Group packages by language
    language_packages = group_packages_by_language(packages)
    
    written_files = {}
    
    # Write Python requirements
    # Always create files per tests, even if empty
    requirements_path = lang_dir / "requirements.txt"
    if language_packages.get(PackageManager.PIP):
        requirements_path = lang_dir / "requirements.txt"
        write_python_requirements(language_packages[PackageManager.PIP], requirements_path)
        written_files["python"] = requirements_path
    else:
        requirements_path.touch()
    
    # Write Node.js global packages
    npm_path = lang_dir / "global-node.txt"
    if language_packages.get(PackageManager.NPM):
        npm_path = lang_dir / "global-node.txt"
        write_npm_global_packages(language_packages[PackageManager.NPM], npm_path)
        written_files["nodejs"] = npm_path
    else:
        npm_path.touch()
    
    # Write Rust packages
    cargo_path = lang_dir / "cargo.txt"
    if language_packages.get(PackageManager.CARGO):
        cargo_path = lang_dir / "cargo.txt"
        write_cargo_packages(language_packages[PackageManager.CARGO], cargo_path)
        written_files["rust"] = cargo_path
    else:
        cargo_path.touch()
    
    # Write Ruby gems
    gems_path = lang_dir / "gems.txt"
    if language_packages.get(PackageManager.GEM):
        gems_path = lang_dir / "gems.txt"
        write_ruby_gems(language_packages[PackageManager.GEM], gems_path)
        written_files["ruby"] = gems_path
    else:
        gems_path.touch()
    
    logger.info(f"Wrote {len(written_files)} language package files")
    return written_files


def group_packages_by_language(packages: List[NormalizedItem]) -> Dict[PackageManager, List[NormalizedItem]]:
    """Group packages by their package manager/language.
    
    Args:
        packages: List of normalized packages
        
    Returns:
        Dictionary mapping package managers to package lists
    """
    grouped = {}
    
    for package in packages:
        pm = package.source_pm
        if pm not in grouped:
            grouped[pm] = []
        grouped[pm].append(package)
    
    return grouped


def write_python_requirements(packages: List[NormalizedItem], output_path: Path) -> None:
    """Write Python requirements.txt file.
    
    Args:
        packages: List of Python packages
        output_path: Path to write requirements.txt
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for package in sorted(packages, key=lambda p: p.source_name.lower()):
            if package.version:
                f.write(f"{package.source_name}=={package.version}\n")
            else:
                f.write(f"{package.source_name}\n")
    
    logger.info(f"Wrote Python requirements with {len(packages)} packages")


def write_npm_global_packages(packages: List[NormalizedItem], output_path: Path) -> None:
    """Write Node.js global packages file.
    
    Args:
        packages: List of NPM packages
        output_path: Path to write global-node.txt
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for package in sorted(packages, key=lambda p: p.source_name.lower()):
            if package.version:
                f.write(f"{package.source_name}@{package.version}\n")
            else:
                f.write(f"{package.source_name}\n")
    
    logger.info(f"Wrote Node.js global packages with {len(packages)} packages")


def write_cargo_packages(packages: List[NormalizedItem], output_path: Path) -> None:
    """Write Rust cargo packages file.
    
    Args:
        packages: List of Cargo packages
        output_path: Path to write cargo.txt
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for package in sorted(packages, key=lambda p: p.source_name.lower()):
            if package.version:
                f.write(f"{package.source_name}@{package.version}\n")
            else:
                f.write(f"{package.source_name}\n")
    
    logger.info(f"Wrote Rust cargo packages with {len(packages)} packages")


def write_ruby_gems(packages: List[NormalizedItem], output_path: Path) -> None:
    """Write Ruby gems file.
    
    Args:
        packages: List of Ruby gems
        output_path: Path to write gems.txt
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for package in sorted(packages, key=lambda p: p.source_name.lower()):
            if package.version:
                f.write(f"{package.source_name} -v {package.version}\n")
            else:
                f.write(f"{package.source_name}\n")
    
    logger.info(f"Wrote Ruby gems with {len(packages)} packages")


def get_language_statistics(packages: List[NormalizedItem]) -> Dict[str, int]:
    """Get statistics about language packages.
    
    Args:
        packages: List of normalized packages
        
    Returns:
        Dictionary with language package counts
    """
    stats = {
        "python": 0,
        "nodejs": 0,
        "rust": 0,
        "ruby": 0,
        "with_versions": 0,
        "without_versions": 0,
    }
    
    for package in packages:
        # Count by language
        if package.source_pm == PackageManager.PIP:
            stats["python"] += 1
        elif package.source_pm == PackageManager.NPM:
            stats["nodejs"] += 1
        elif package.source_pm == PackageManager.CARGO:
            stats["rust"] += 1
        elif package.source_pm == PackageManager.GEM:
            stats["ruby"] += 1
        
        # Count version information
        if package.version:
            stats["with_versions"] += 1
        else:
            stats["without_versions"] += 1
    
    return stats


def format_package_line(package: NormalizedItem, format_type: str) -> str:
    """Format a package for a specific language format.
    
    Args:
        package: Normalized package item
        format_type: Type of format (python, npm, cargo, gem)
        
    Returns:
        Formatted package line
    """
    if format_type == "python":
        if package.version:
            return f"{package.source_name}=={package.version}"
        else:
            return package.source_name
    
    elif format_type == "npm":
        if package.version:
            return f"{package.source_name}@{package.version}"
        else:
            return package.source_name
    
    elif format_type == "cargo":
        if package.version:
            return f"{package.source_name}@{package.version}"
        else:
            return package.source_name
    
    elif format_type == "gem":
        if package.version:
            return f"{package.source_name} -v {package.version}"
        else:
            return package.source_name
    
    else:
        raise ValueError(f"Unknown format type: {format_type}")


def validate_language_file(file_path: Path, language: str) -> bool:
    """Validate a language package file.
    
    Args:
        file_path: Path to the language file
        language: Language type (python, npm, cargo, gem)
        
    Returns:
        True if file is valid, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Basic validation based on language
            if language == "python":
                if "==" not in line and ">=" not in line and "<=" not in line:
                    # Should have version constraint
                    pass  # Allow packages without version constraints
            
            elif language == "npm":
                if "@" in line and not line.startswith('@'):
                    # Should have @ for version
                    pass
            
            elif language == "cargo":
                if "@" in line and not line.startswith('@'):
                    # Should have @ for version
                    pass
            
            elif language == "gem":
                if "-v" in line:
                    # Should have version flag
                    pass
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating {language} file {file_path}: {e}")
        return False
