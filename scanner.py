from pathlib import Path

from models import DVDBackup

def _is_excluded(
    path: Path,
    excluded_directories: tuple[str, ...],
) -> bool:
    """Return True when a path passes through an excluded directory."""

    excluded = {
        directory.casefold()
        for directory in excluded_directories
    }

    return any(
        part.casefold() in excluded
        for part in path.parts
    )


def find_dvd_backups(root_path):
    root = Path(root_path)

    dvd_backups = []
    seen_paths = set()

    for ifo_file in root.rglob(
        "VIDEO_TS/VIDEO_TS.IFO"
    ):
        video_ts = ifo_file.parent
        disc_path = video_ts.parent

        # Reject nested VIDEO_TS structures that would make
        # VIDEO_TS itself appear to be a disc name.
        if disc_path.name.upper() == "VIDEO_TS":
            continue

        resolved_path = disc_path.resolve()

        if resolved_path in seen_paths:
            continue

        seen_paths.add(
            resolved_path
        )

        dvd_backups.append(
            DVDBackup(
                name=disc_path.name,
                path=disc_path,
                ifo_path=ifo_file,
            )
        )

    return dvd_backups

def find_configured_dvd_backups(
    config,
) -> list[DVDBackup]:
    """
    Discover DVD backups across enabled,
    DVD-capable media locations.
    """

    backups = []

    for location in config.media_locations:
        if not location.enabled:
            continue

        if (
            location.media_types
            and "dvd" not in location.media_types
        ):
            continue

        if not location.path.exists():
            print(
                f"Skipping unavailable media location: "
                f"{location.name} "
                f"({location.path})"
            )
            continue

        discovered = find_dvd_backups(
            location.path
        )

        for backup in discovered:
            if _is_excluded(
                    backup.path,
                    config.discovery_exclude_directories,
                ):
                continue

            backups.append(
                backup
            )

    return backups