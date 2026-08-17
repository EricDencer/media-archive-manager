"""
Application configuration for the media ingestion engine.

This module defines filesystem locations and other configuration
required by the ingestion workflow.

Keeping configuration separate from processing logic prevents
individual workflow stages from depending on hard-coded paths.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Filesystem configuration used by the ingestion pipeline."""

    archive_root: Path
    staging_root: Path
    encoded_root: Path
    plex_root: Path
    manifest_path: Path


def load_config() -> AppConfig:
    """
    Return the current local application configuration.

    This function provides a single location for filesystem settings.
    A future application version can replace this implementation with
    environment variables or application configuration without
    changing the ingestion stages.
    """

    archive_root = Path(
        "/home/ericdencer/Video Archive"
    )

    return AppConfig(
        archive_root=archive_root,
        staging_root=archive_root / "staging",
        encoded_root=archive_root / "encoded",
        plex_root=archive_root / "plex",
        manifest_path=Path("manifest.csv"),
    )