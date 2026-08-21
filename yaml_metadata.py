"""
Per-disc YAML metadata synchronization.

This module synchronizes human-owned media identity and approval
from ingest.yaml into SQLite.

Responsibilities:
    - Load per-disc ingest.yaml.
    - Match YAML title numbers to SQLite source titles.
    - Create/find movie, show, and episode identities.
    - Synchronize human-owned identity fields.
    - Synchronize approval.
    - Preserve workflow state and machine-owned technical metadata.

This module does NOT:
    - Scan media.
    - Run MakeMKV or ffmpeg.
    - Change workflow state.
    - Publish media.
"""

from pathlib import Path

import yaml

from repository import (
    get_or_create_episode,
    get_or_create_movie,
    get_or_create_show,
    get_title_by_disc_and_source,
    set_title_approved,
    sync_title_episode_identity,
    sync_title_movie_identity,
)


def load_ingest_yaml(
    yaml_path: Path,
) -> dict:
    """Load and parse one ingest.yaml file."""

    yaml_path = Path(yaml_path)

    if not yaml_path.exists():
        raise FileNotFoundError(
            f"ingest.yaml not found: {yaml_path}"
        )

    with yaml_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = yaml.safe_load(file)

    if not data:
        raise ValueError(
            f"ingest.yaml is empty: {yaml_path}"
        )

    return data


def synchronize_yaml_metadata(
    connection,
    disc_id: int,
    yaml_path: Path,
) -> None:
    """
    Synchronize human-owned metadata from ingest.yaml into SQLite.

    Workflow state and technical metadata are preserved.
    """

    data = load_ingest_yaml(
        yaml_path
    )

    titles = data.get(
        "titles",
        [],
    )

    for yaml_title in titles:
        source_title = yaml_title.get(
            "title"
        )

        if source_title is None:
            print(
                "Skipping YAML entry without "
                "a source title number."
            )
            continue

        db_title = get_title_by_disc_and_source(
            connection,
            disc_id,
            int(source_title),
        )

        if db_title is None:
            print(
                f"Skipping YAML title "
                f"{source_title}: "
                f"not found in SQLite."
            )
            continue

        approved = bool(
            yaml_title.get(
                "approved",
                False,
            )
        )

        set_title_approved(
            connection,
            title_id=db_title["id"],
            approved=approved,
        )

        media = yaml_title.get(
            "media",
            {},
        )

        media_type = media.get(
            "type"
        )

        if media_type == "movie":
            name = media.get("name")
            year = media.get("year")

            if not name or not year:
                print(
                    f"Title {source_title}: "
                    f"incomplete movie metadata."
                )
                continue

            movie_id = get_or_create_movie(
                connection,
                name=name,
                year=int(year),
            )

            sync_title_movie_identity(
                connection,
                title_id=db_title["id"],
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

            if missing:
                print(
                    f"Title {source_title}: "
                    f"incomplete TV metadata "
                    f"({', '.join(missing)})."
                )
                continue

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

            sync_title_episode_identity(
                connection,
                title_id=db_title["id"],
                episode_id=episode_id,
            )

        else:
            print(
                f"Title {source_title}: "
                f"unsupported or missing "
                f"media type."
            )