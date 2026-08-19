"""
Bootstrap migration from the legacy CSV manifest and per-disc YAML
metadata into SQLite.

This module exists to support the transition from the prototype CSV
manifest to the new YAML + SQLite persistence model.

Responsibilities:
    - Load per-disc YAML metadata.
    - Read existing CSV manifest state.
    - Create/update release, disc, title, movie, show, and episode rows.
    - Preserve current workflow status and technical metadata.

This module does NOT:
    - Run the ingestion pipeline.
    - Modify media files.
    - Replace main.py yet.
"""

from pathlib import Path

import yaml

from database import connect_database
from manifest import load_manifest
from repository import (
    create_release,
    get_or_create_disc,
    get_or_create_episode,
    get_or_create_movie,
    get_or_create_show,
    identify_title_as_episode,
    identify_title_as_movie,
    set_title_approved,
    update_title_probe_metadata,
    update_title_status,
    upsert_title,
)


def load_disc_yaml(path: Path) -> dict:
    """Load and parse one per-disc ingest YAML file."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Disc YAML not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = yaml.safe_load(file)

    if not data:
        raise ValueError(
            f"Disc YAML is empty: {path}"
        )

    return data

def migrate_disc(
    connection,
    yaml_path: Path,
    manifest_path: Path,
) -> None:
    """
    Migrate one disc from YAML + legacy CSV into SQLite.

    YAML provides human identity and approval.
    CSV provides current workflow and technical state.
    """

    yaml_data = load_disc_yaml(
        yaml_path
    )

    manifest_items = load_manifest(
        manifest_path
    )

    disc_data = yaml_data["disc"]
    title_data = yaml_data["titles"]

    release_id = create_release(
        connection,
        name=f"{disc_data['name']} Release",
        format=disc_data["format"],
    )

    disc_id = get_or_create_disc(
        connection,
        name=disc_data["name"],
        backup_path=yaml_path.parent,
        release_id=release_id,
    )

    csv_by_title = {
        item.title: item
        for item in manifest_items
        if item.disc == disc_data["name"]
    }

    for yaml_title in title_data:
        source_title = yaml_title["title"]

        csv_item = csv_by_title.get(
            source_title
        )

        if csv_item is None:
            raise ValueError(
                f"No CSV manifest record for "
                f"{disc_data['name']} title "
                f"{source_title}"
            )

        title_id = upsert_title(
            connection,
            disc_id=disc_id,
            source_title=source_title,
            duration=csv_item.duration,
            duration_seconds=csv_item.duration_seconds,
            chapters=csv_item.chapters,
            size_bytes=csv_item.size_bytes,
            output_filename=csv_item.output_filename,
        )

        media = yaml_title.get(
            "media",
            {}
        )

        media_type = media.get("type")

        if media_type == "movie":
            movie_id = get_or_create_movie(
                connection,
                name=media["name"],
                year=int(media["year"]),
            )

            identify_title_as_movie(
                connection,
                title_id=title_id,
                movie_id=movie_id,
            )

        elif media_type == "tv":
            required = (
                "show",
                "year",
                "season",
                "episode",
                "episode_title",
            )

            missing = [
                field
                for field in required
                if not media.get(field)
            ]

            if not missing:
                show_id = get_or_create_show(
                    connection,
                    name=media["show"],
                    year=int(media["year"]),
                )

                episode_id = get_or_create_episode(
                    connection,
                    show_id=show_id,
                    season=int(media["season"]),
                    episode=int(media["episode"]),
                    title=media["episode_title"],
                )

                identify_title_as_episode(
                    connection,
                    title_id=title_id,
                    episode_id=episode_id,
                )

        set_title_approved(
            connection,
            title_id=title_id,
            approved=bool(
                yaml_title.get(
                    "approved",
                    False,
                )
            ),
        )

        update_title_probe_metadata(
            connection,
            title_id=title_id,
            duration_seconds=csv_item.duration_seconds,
            video_codec=csv_item.video_codec,
            audio_codec=csv_item.audio_codec,
            width=csv_item.width,
            height=csv_item.height,
            display_aspect_ratio=csv_item.display_aspect_ratio,
            frame_rate=csv_item.frame_rate,
            field_order=csv_item.field_order,
            audio_channels=csv_item.audio_channels,
        )

        update_title_status(
            connection,
            title_id=title_id,
            status=csv_item.status,
            notes=csv_item.notes or None,
        )

if __name__ == "__main__":
    database_path = Path(
        "/tmp/media_archive_migration_test.db"
    )
yaml_path = Path(
    "/home/ericdencer/Video Archive/"
    "Sci Fi 1a/ingest.yaml"
)

manifest_path = Path(
    "manifest.csv"
)

connection = connect_database(
    database_path
)

try:
    migrate_disc(
        connection,
        yaml_path,
        manifest_path,
    )

    print(
        "Migration completed successfully."
    )

finally:
    connection.close()