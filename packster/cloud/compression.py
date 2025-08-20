"""File compression utilities for Packster."""

import json
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..detect import get_environment_info


def create_migration_archive(output_dir: Path) -> Path:
    """Create a compressed archive of migration files.
    
    Args:
        output_dir: Directory containing migration files
        
    Returns:
        Path to the created archive file
        
    Raises:
        FileNotFoundError: If output_dir doesn't exist
        OSError: If archive creation fails
    """
    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")
    
    # Generate archive filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_name = f"packster-migration-{timestamp}.tar.gz"
    
    # Create temporary directory for archive
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / archive_name
        
        # Create metadata
        metadata = _create_metadata(output_dir)
        metadata_file = temp_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create tar.gz archive
        with tarfile.open(archive_path, 'w:gz') as tar:
            # Add metadata file
            tar.add(metadata_file, arcname="metadata.json")
            
            # Add all files from output directory
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path for archive
                    arcname = file_path.relative_to(output_dir)
                    tar.add(file_path, arcname=str(arcname))
        
        # Move archive to output directory
        final_archive_path = output_dir / archive_name
        
        # Use shutil.copy2 instead of rename to handle cross-filesystem moves
        import shutil
        shutil.copy2(archive_path, final_archive_path)
        
        return final_archive_path


def _create_metadata(output_dir: Path) -> Dict[str, Any]:
    """Create metadata for the migration archive.
    
    Args:
        output_dir: Directory containing migration files
        
    Returns:
        Dictionary containing metadata
    """
    # Get system information
    env_info = get_environment_info()
    
    # Count files by type
    file_counts = {}
    for file_path in output_dir.rglob('*'):
        if file_path.is_file():
            suffix = file_path.suffix.lower()
            file_counts[suffix] = file_counts.get(suffix, 0) + 1
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in output_dir.rglob('*') if f.is_file())
    
    metadata = {
        "created_at": datetime.now().isoformat(),
        "packster_version": "1.0.0",  # TODO: Get from package
        "source_system": {
            "os": env_info["system"]["os"],
            "architecture": env_info["system"]["architecture"],
            "wsl": env_info["system"]["wsl"],
            "python_version": env_info["system"]["python_version"],
        },
        "archive_info": {
            "file_count": len(list(output_dir.rglob('*'))),
            "total_size_bytes": total_size,
            "file_types": file_counts,
        },
        "contents": {
            "has_brewfile": (output_dir / "Brewfile" / "Brewfile").exists(),
            "has_bootstrap": (output_dir / "bootstrap.sh" / "bootstrap.sh").exists(),
            "has_reports": (output_dir / "report.html").exists() or (output_dir / "report.json").exists(),
            "language_files": list(_get_language_files(output_dir)),
        }
    }
    
    return metadata


def _get_language_files(output_dir: Path) -> list:
    """Get list of language-specific files in the output directory.
    
    Args:
        output_dir: Directory containing migration files
        
    Returns:
        List of language file paths
    """
    lang_dir = output_dir / "lang"
    if not lang_dir.exists():
        return []
    
    language_files = []
    for file_path in lang_dir.glob("*.txt"):
        language_files.append(file_path.name)
    
    return language_files
