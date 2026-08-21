"""
Application-level persistence operations.

This module provides repository functions for storing and retrieving
Media Archive Manager domain data from SQLite.

Responsibilities:
    - Create and retrieve releases.
    - Create and retrieve discs.
    - Create and retrieve movie/show/episode identities.
    - Insert or update source titles.
    - Update title workflow state.
    - Record generated media artifacts.

This module does NOT:
    - Open or initialize databases.
    - Scan media.
    - Run MakeMKV or ffmpeg.
    - Implement ingestion workflow decisions.

Low-level connection handling belongs in database.py.
"""

import sqlite3
from pathlib import Path
from models import ManifestItem

# ---------------------------------------------------------------------------
# Releases
# ---------------------------------------------------------------------------


def create_release(
    connection: sqlite3.Connection,
    name: str,
    publisher: str | None = None,
    format: str = "dvd",
    edition: str | None = None,
    catalog_number: str | None = None,
    release_year: int | None = None,
    notes: str | None = None,
) -> int:
    """
    Create a physical media release.

    Returns:
        Database ID of the new release.
    """

    cursor = connection.execute(
        """
        INSERT INTO releases (
            name,
            publisher,
            format,
            edition,
            catalog_number,
            release_year,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            publisher,
            format,
            edition,
            catalog_number,
            release_year,
            notes,
        ),
    )

    connection.commit()

    return cursor.lastrowid


def get_release_by_name(
    connection: sqlite3.Connection,
    name: str,
):
    """Return a release row matching the supplied name."""

    return connection.execute(
        """
        SELECT *
        FROM releases
        WHERE name = ?
        """,
        (name,),
    ).fetchone()


# ---------------------------------------------------------------------------
# Discs
# ---------------------------------------------------------------------------


def get_or_create_disc(
    connection: sqlite3.Connection,
    name: str,
    backup_path: Path,
    release_id: int | None = None,
    disc_number: int | None = None,
) -> int:
    """
    Retrieve or create a physical disc record.

    backup_path is the stable unique identifier for archived discs.

    Returns:
        Database ID of the disc.
    """

    backup_path = str(Path(backup_path))

    existing = connection.execute(
        """
        SELECT id
        FROM discs
        WHERE backup_path = ?
        """,
        (backup_path,),
    ).fetchone()

    if existing:
        return existing[0]

    cursor = connection.execute(
        """
        INSERT INTO discs (
            release_id,
            name,
            disc_number,
            backup_path
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            release_id,
            name,
            disc_number,
            backup_path,
        ),
    )

    connection.commit()

    return cursor.lastrowid


def get_disc_by_name(
    connection: sqlite3.Connection,
    name: str,
):
    """Return a disc matching the supplied name."""

    return connection.execute(
        """
        SELECT *
        FROM discs
        WHERE name = ?
        """,
        (name,),
    ).fetchone()


# ---------------------------------------------------------------------------
# Movies
# ---------------------------------------------------------------------------


def get_or_create_movie(
    connection: sqlite3.Connection,
    name: str,
    year: int,
) -> int:
    """
    Retrieve or create a logical movie identity.

    Movie identity is unique by name and release year.
    """

    existing = connection.execute(
        """
        SELECT id
        FROM movies
        WHERE name = ?
          AND year = ?
        """,
        (
            name,
            year,
        ),
    ).fetchone()

    if existing:
        return existing[0]

    cursor = connection.execute(
        """
        INSERT INTO movies (
            name,
            year
        )
        VALUES (?, ?)
        """,
        (
            name,
            year,
        ),
    )

    connection.commit()

    return cursor.lastrowid


# ---------------------------------------------------------------------------
# Television
# ---------------------------------------------------------------------------


def get_or_create_show(
    connection: sqlite3.Connection,
    name: str,
    year: int,
) -> int:
    """
    Retrieve or create a logical television-series identity.
    """

    existing = connection.execute(
        """
        SELECT id
        FROM shows
        WHERE name = ?
          AND year = ?
        """,
        (
            name,
            year,
        ),
    ).fetchone()

    if existing:
        return existing[0]

    cursor = connection.execute(
        """
        INSERT INTO shows (
            name,
            year
        )
        VALUES (?, ?)
        """,
        (
            name,
            year,
        ),
    )

    connection.commit()

    return cursor.lastrowid


def get_or_create_episode(
    connection: sqlite3.Connection,
    show_id: int,
    season: int,
    episode: int,
    title: str,
) -> int:
    """
    Retrieve or create a logical television episode.

    Episode identity is unique by:
        show + season + episode number
    """

    existing = connection.execute(
        """
        SELECT id
        FROM episodes
        WHERE show_id = ?
          AND season = ?
          AND episode = ?
        """,
        (
            show_id,
            season,
            episode,
        ),
    ).fetchone()

    if existing:
        return existing[0]

    cursor = connection.execute(
        """
        INSERT INTO episodes (
            show_id,
            season,
            episode,
            title
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            show_id,
            season,
            episode,
            title,
        ),
    )

    connection.commit()

    return cursor.lastrowid


# ---------------------------------------------------------------------------
# Source titles
# ---------------------------------------------------------------------------


def upsert_title(
    connection: sqlite3.Connection,
    disc_id: int,
    source_title: int,
    duration: str | None = None,
    duration_seconds: int = 0,
    chapters: int = 0,
    size_bytes: int = 0,
    output_filename: str | None = None,
) -> int:
    """
    Insert or update machine-discovered source-title metadata.

    Human identification and workflow fields are intentionally not
    overwritten by a rescan.

    Returns:
        Database ID of the source title.
    """

    existing = connection.execute(
        """
        SELECT id
        FROM titles
        WHERE disc_id = ?
          AND source_title = ?
        """,
        (
            disc_id,
            source_title,
        ),
    ).fetchone()

    if existing:
        title_id = existing[0]

        connection.execute(
            """
            UPDATE titles
            SET
                duration = ?,
                duration_seconds = ?,
                chapters = ?,
                size_bytes = ?,
                output_filename = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                duration,
                duration_seconds,
                chapters,
                size_bytes,
                output_filename,
                title_id,
            ),
        )

        connection.commit()

        return title_id

    cursor = connection.execute(
        """
        INSERT INTO titles (
            disc_id,
            source_title,
            duration,
            duration_seconds,
            chapters,
            size_bytes,
            output_filename
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            disc_id,
            source_title,
            duration,
            duration_seconds,
            chapters,
            size_bytes,
            output_filename,
        ),
    )

    connection.commit()

    return cursor.lastrowid

def get_manifest_items_for_disc(
    connection: sqlite3.Connection,
    disc_id: int,
) -> list[ManifestItem]:
    """
    Build pipeline working objects from SQLite state.

    SQLite is authoritative for workflow state, technical metadata,
    and media relationships. ManifestItem remains a temporary
    in-memory transport object used by the existing processing stages.
    """

    rows = connection.execute(
        """
        SELECT
            d.name AS disc,
            t.source_title,
            t.duration,
            t.duration_seconds,
            t.chapters,
            t.size_bytes,
            t.output_filename,
            t.media_type,
            t.approved,
            t.status,
            t.notes,
            t.video_codec,
            t.audio_codec,
            t.width,
            t.height,
            t.display_aspect_ratio,
            t.frame_rate,
            t.field_order,
            t.audio_channels,

            m.name AS movie_name,
            m.year AS movie_year,

            s.name AS show_name,
            s.year AS show_year,

            e.season,
            e.episode,
            e.title AS episode_title

        FROM titles t

        JOIN discs d
            ON t.disc_id = d.id

        LEFT JOIN movies m
            ON t.movie_id = m.id

        LEFT JOIN episodes e
            ON t.episode_id = e.id

        LEFT JOIN shows s
            ON e.show_id = s.id

        WHERE t.disc_id = ?

        ORDER BY t.source_title
        """,
        (disc_id,),
    ).fetchall()

    items = []

    for row in rows:
        media_type = row["media_type"] or ""

        if media_type == "movie":
            name = row["movie_name"] or ""
            year = (
                str(row["movie_year"])
                if row["movie_year"] is not None
                else ""
            )

            show_name = ""
            season = ""
            episode = ""
            episode_title = ""

        elif media_type == "tv":
            name = ""

            show_name = (
                row["show_name"] or ""
            )

            year = (
                str(row["show_year"])
                if row["show_year"] is not None
                else ""
            )

            season = (
                str(row["season"])
                if row["season"] is not None
                else ""
            )

            episode = (
                str(row["episode"])
                if row["episode"] is not None
                else ""
            )

            episode_title = (
                row["episode_title"] or ""
            )

        else:
            name = ""
            year = ""
            show_name = ""
            season = ""
            episode = ""
            episode_title = ""

        item = ManifestItem(
            disc=row["disc"],
            title=row["source_title"],
            media_type=media_type,
            name=name,
            year=year,
            show_name=show_name,
            season=season,
            episode=episode,
            episode_title=episode_title,
            duration=row["duration"] or "",
            duration_seconds=row["duration_seconds"] or 0,
            chapters=row["chapters"] or 0,
            size_bytes=row["size_bytes"] or 0,
            video_codec=row["video_codec"] or "",
            audio_codec=row["audio_codec"] or "",
            output_filename=row["output_filename"] or "",
            status=row["status"] or "discovered",
            ready=(
                "yes"
                if row["approved"]
                else "no"
            ),
            notes=row["notes"] or "",
            width=row["width"] or 0,
            height=row["height"] or 0,
            display_aspect_ratio=(
                row["display_aspect_ratio"] or ""
            ),
            frame_rate=row["frame_rate"] or "",
            field_order=row["field_order"] or "",
            audio_channels=row["audio_channels"] or 0,
        )

        items.append(item)

    return items

def get_titles_for_disc(
    connection: sqlite3.Connection,
    disc_id: int,
):
    """Return all source titles belonging to a physical disc."""

    return connection.execute(
        """
        SELECT *
        FROM titles
        WHERE disc_id = ?
        ORDER BY source_title
        """,
        (disc_id,),
    ).fetchall()


# ---------------------------------------------------------------------------
# Media identification
# ---------------------------------------------------------------------------


def identify_title_as_movie(
    connection: sqlite3.Connection,
    title_id: int,
    movie_id: int,
) -> None:
    """
    Map a source title to a logical movie.
    """

    connection.execute(
        """
        UPDATE titles
        SET
            media_type = 'movie',
            movie_id = ?,
            episode_id = NULL,
            status = 'identified',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            movie_id,
            title_id,
        ),
    )

    connection.commit()


def identify_title_as_episode(
    connection: sqlite3.Connection,
    title_id: int,
    episode_id: int,
) -> None:
    """
    Map a source title to a logical television episode.
    """

    connection.execute(
        """
        UPDATE titles
        SET
            media_type = 'tv',
            movie_id = NULL,
            episode_id = ?,
            status = 'identified',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            episode_id,
            title_id,
        ),
    )

    connection.commit()


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


def set_title_approved(
    connection: sqlite3.Connection,
    title_id: int,
    approved: bool,
) -> None:
    """Set human approval for ingestion processing."""

    connection.execute(
        """
        UPDATE titles
        SET
            approved = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            int(approved),
            title_id,
        ),
    )

    connection.commit()


def update_title_status(
    connection: sqlite3.Connection,
    title_id: int,
    status: str,
    notes: str | None = None,
) -> None:
    """
    Update workflow state for a source title.
    """

    connection.execute(
        """
        UPDATE titles
        SET
            status = ?,
            notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            status,
            notes,
            title_id,
        ),
    )

    connection.commit()


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


def add_artifact(
    connection: sqlite3.Connection,
    title_id: int,
    artifact_type: str,
    path: Path,
    size_bytes: int = 0,
) -> int:
    """
    Record a media artifact generated from a source title.

    artifact_type values currently include:
        extracted
        encoded
        published
    """

    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO artifacts (
            title_id,
            artifact_type,
            path,
            size_bytes
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            title_id,
            artifact_type,
            str(Path(path)),
            size_bytes,
        ),
    )

    connection.commit()

    if cursor.lastrowid:
        return cursor.lastrowid

    existing = connection.execute(
        """
        SELECT id
        FROM artifacts
        WHERE title_id = ?
          AND artifact_type = ?
          AND path = ?
        """,
        (
            title_id,
            artifact_type,
            str(Path(path)),
        ),
    ).fetchone()

    return existing[0]

def get_title_by_disc_and_source(
    connection: sqlite3.Connection,
    disc_id: int,
    source_title: int,
):
    """
    Return one source title by disc and MakeMKV title number.
    """

    return connection.execute(
        """
        SELECT *
        FROM titles
        WHERE disc_id = ?
          AND source_title = ?
        """,
        (
            disc_id,
            source_title,
        ),
    ).fetchone()


def get_titles_by_status(
    connection: sqlite3.Connection,
    disc_id: int,
    statuses: tuple[str, ...],
):
    """
    Return titles for a disc whose workflow status matches
    one of the supplied values.
    """

    if not statuses:
        return []

    placeholders = ",".join(
        "?"
        for _ in statuses
    )

    query = f"""
        SELECT *
        FROM titles
        WHERE disc_id = ?
          AND status IN ({placeholders})
        ORDER BY source_title
    """

    parameters = (
        disc_id,
        *statuses,
    )

    return connection.execute(
        query,
        parameters,
    ).fetchall()


def update_title_probe_metadata(
    connection: sqlite3.Connection,
    title_id: int,
    *,
    duration_seconds: int,
    video_codec: str,
    audio_codec: str,
    width: int,
    height: int,
    display_aspect_ratio: str,
    frame_rate: str,
    field_order: str,
    audio_channels: int,
) -> None:
    """
    Store technical metadata discovered by ffprobe.
    """

    connection.execute(
        """
        UPDATE titles
        SET
            duration_seconds = ?,
            video_codec = ?,
            audio_codec = ?,
            width = ?,
            height = ?,
            display_aspect_ratio = ?,
            frame_rate = ?,
            field_order = ?,
            audio_channels = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            duration_seconds,
            video_codec,
            audio_codec,
            width,
            height,
            display_aspect_ratio,
            frame_rate,
            field_order,
            audio_channels,
            title_id,
        ),
    )

    connection.commit()


def get_artifacts_for_title(
    connection: sqlite3.Connection,
    title_id: int,
):
    """
    Return generated artifacts for a source title.
    """

    return connection.execute(
        """
        SELECT *
        FROM artifacts
        WHERE title_id = ?
        ORDER BY created_at
        """,
        (title_id,),
    ).fetchall()

def sync_scanned_title(
    connection,
    *,
    disc_id: int,
    source_title: int,
    duration: str,
    duration_seconds: int,
    chapters: int,
    size_bytes: int,
    output_filename: str,
) -> int:
    """
    Synchronize machine-discovered source metadata for one disc title.

    Scan synchronization may update physical source characteristics,
    but must not overwrite human identity, approval, workflow state,
    or probe-owned technical metadata.
    """

    return upsert_title(
        connection,
        disc_id=disc_id,
        source_title=source_title,
        duration=duration,
        duration_seconds=duration_seconds,
        chapters=chapters,
        size_bytes=size_bytes,
        output_filename=output_filename,
    )

def get_titles_ready_for_extraction(
    connection: sqlite3.Connection,
    disc_id: int,
):
    """
    Return source titles eligible for extraction.

    A title is eligible when:
        - it belongs to the requested disc;
        - it has been human-approved;
        - its workflow state is either identified or extract_failed.

    Returns:
        sqlite3.Row objects ordered by source title number.
    """

    return connection.execute(
        """
        SELECT *
        FROM titles
        WHERE disc_id = ?
          AND approved = 1
          AND status IN (
              'identified',
              'extract_failed'
          )
        ORDER BY source_title
        """,
        (disc_id,),
    ).fetchall()

def sync_title_movie_identity(
    connection: sqlite3.Connection,
    title_id: int,
    movie_id: int,
) -> None:
    """
    Synchronize movie identity without changing workflow state.
    """

    connection.execute(
        """
        UPDATE titles
        SET
            media_type = 'movie',
            movie_id = ?,
            episode_id = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            movie_id,
            title_id,
        ),
    )

    connection.commit()


def sync_title_episode_identity(
    connection: sqlite3.Connection,
    title_id: int,
    episode_id: int,
) -> None:
    """
    Synchronize television episode identity without changing
    workflow state.
    """

    connection.execute(
        """
        UPDATE titles
        SET
            media_type = 'tv',
            movie_id = NULL,
            episode_id = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            episode_id,
            title_id,
        ),
    )

    connection.commit()