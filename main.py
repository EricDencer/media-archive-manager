"""
Media ingestion pipeline orchestrator.

This module coordinates the end-to-end processing workflow for a
selected archived DVD backup.

inspect -> database sync -> YAML sync -> extract -> probe -> encode -> validate

The individual processing operations are implemented in dedicated
modules. This file is responsible only for determining which items
are eligible for each stage and coordinating their execution.

SQLite is the authoritative operational persistence layer.

Per-disc YAML provides human-reviewed media identity and approval.
The processing stages use SQLite for workflow state and technical
metadata.
"""

from pathlib import Path

from config import AppConfig, load_config
import config
from encoder import encode_media, encoding_succeeded
from extractor import extract_title, extraction_succeeded
from makemkv import inspect_dvd, parse_robot_titles
from models import DVDBackup, ManifestItem
from probe import probe_media, summarize_media
from scanner import find_dvd_backups
from validator import validate_encoded_media
from yaml_metadata import synchronize_yaml_metadata
from database import (
    connect_database,
    initialize_database,
)
from repository import (
    get_manifest_items_for_disc,
    get_or_create_disc,
    get_titles_by_status,
    get_titles_ready_for_extraction,
    sync_scanned_title,
    update_title_probe_metadata,
    update_title_status,
)

# ---------------------------------------------------------------------------
# Backup discovery and inspection
# ---------------------------------------------------------------------------


def select_backup(
    config: AppConfig,
    backup_name: str,
) -> DVDBackup:
    """
    Locate a specific archived DVD backup.

    Args:
        config:
            Application filesystem configuration.

        backup_name:
            Directory name of the DVD backup to process.

    Returns:
        The matching DVDBackup.

    Raises:
        RuntimeError:
            If the requested backup cannot be found.
    """

    backups = find_dvd_backups(
        config.archive_root
    )

    try:
        return next(
            backup
            for backup in backups
            if backup.name == backup_name
        )
    except StopIteration as error:
        raise RuntimeError(
            f"Backup not found: {backup_name}"
        ) from error


def inspect_backup(
    backup: DVDBackup,
    config: AppConfig,
    connection,
) -> list[ManifestItem]:
    """
    Inspect a DVD backup and synchronize its MakeMKV title data
    with the current manifest.

    Returns:
    Pipeline working objects built from the synchronized SQLite state.

    Returns:
        The updated collection of manifest items.
    """

    print(f"Inspecting: {backup.name}")

    result = inspect_dvd(backup)

    if result.returncode != 0:
        raise RuntimeError(
            f"MakeMKV inspection failed for "
            f"{backup.name}: {result.stderr}"
        )

    titles = parse_robot_titles(
        result.stdout + result.stderr
    )

    disc_id = get_or_create_disc(
        connection,
        name=backup.name,
        backup_path=backup.path,
    )

    for title in titles:
        sync_scanned_title(
            connection,
            disc_id=disc_id,
            source_title=title.index,
            duration=title.duration or "",
            duration_seconds=title.duration_seconds or 0,
            chapters=title.chapters or 0,
            size_bytes=title.size_bytes or 0,
            output_filename=title.output_filename or "",
        )

    yaml_path = (
        backup.path
        / "ingest.yaml"
    )

    synchronize_yaml_metadata(
        connection,
        disc_id=disc_id,
        yaml_path=yaml_path,
    )

    items = get_manifest_items_for_disc(
        connection,
        disc_id,
    )

    print(
        f"Database synchronized with "
        f"{len(titles)} titles."
    )
    
    return items


# ---------------------------------------------------------------------------
# Extraction stage
# ---------------------------------------------------------------------------

def run_extraction_stage(
    backup: DVDBackup,
    items: list[ManifestItem],
    config: AppConfig,
    connection,
) -> None:
    """
    Extract titles that have been identified and approved.

    SQLite determines which source titles are eligible for extraction.

    Eligible workflow states:
        identified
        extract_failed

    Successful transition:
        identified -> extracted
    """

    disc_id = get_or_create_disc(
        connection,
        name=backup.name,
        backup_path=backup.path,
    )

    db_ready_titles = get_titles_ready_for_extraction(
        connection,
        disc_id,
    )

    ready_source_titles = {
        row["source_title"]
        for row in db_ready_titles
    }

    ready_items = [
        item
        for item in items
        if (
            item.disc == backup.name
            and item.title in ready_source_titles
        )
    ]

    if not ready_items:
        print(
            f"No titles ready for extraction "
            f"on {backup.name}."
        )
        return

    for item in ready_items:
        result = extract_title(
            backup,
            item,
            config.staging_root,
        )

        if (
            result.returncode == 0
            and extraction_succeeded(
                backup,
                item,
                config.staging_root,
            )
        ):
            item.status = "extracted"
            item.notes = ""

            print(
                f"Extraction successful: "
                f"{item.name}"
            )

        else:
            item.status = "extract_failed"
            item.notes = (
                f"MakeMKV return code "
                f"{result.returncode}"
            )

            print(
                f"Extraction failed: "
                f"{item.name}"
            )

        db_title = next(
            row
            for row in db_ready_titles
            if row["source_title"] == item.title
        )

        update_title_status(
            connection,
            title_id=db_title["id"],
            status=item.status,
            notes=item.notes or None,
        )


# ---------------------------------------------------------------------------
# Probe stage
# ---------------------------------------------------------------------------

def run_probe_stage(
    backup: DVDBackup,
    items: list[ManifestItem],
    config: AppConfig,
    connection,
) -> None:
    """
    Probe extracted titles with ffprobe.

    SQLite determines which source titles are eligible for probing.

    Eligible workflow states:
        extracted
        probe_failed

    Successful transition:
        extracted -> probed
    """

    disc_id = get_or_create_disc(
        connection,
        name=backup.name,
        backup_path=backup.path,
    )

    db_probe_titles = get_titles_by_status(
        connection,
        disc_id,
        (
            "extracted",
            "probe_failed",
        ),
    )

    probe_source_titles = {
        row["source_title"]
        for row in db_probe_titles
    }

    probe_items = [
        item
        for item in items
        if (
            item.disc == backup.name
            and item.title in probe_source_titles
        )
    ]

    for item in probe_items:
        media_path = (
            config.staging_root
            / backup.name
            / item.output_filename
        )

        print(
            f"Probing {backup.name} "
            f"title {item.title}: {item.name}"
        )

        db_title = next(
            row
            for row in db_probe_titles
            if row["source_title"] == item.title
        )

        try:
            probe_data = probe_media(
                media_path
            )

            summary = summarize_media(
                probe_data
            )

            item.duration_seconds = int(
                summary["duration_seconds"]
            )

            item.video_codec = (
                summary["video_codec"]
            )

            item.width = summary["width"]
            item.height = summary["height"]

            item.display_aspect_ratio = (
                summary[
                    "display_aspect_ratio"
                ]
            )

            item.frame_rate = (
                summary["frame_rate"]
            )

            item.field_order = (
                summary["field_order"]
            )

            item.audio_codec = (
                summary["audio_codec"]
            )

            item.audio_channels = (
                summary["audio_channels"]
            )

            item.status = "probed"
            item.notes = ""

            update_title_probe_metadata(
                connection,
                title_id=db_title["id"],
                duration_seconds=item.duration_seconds,
                video_codec=item.video_codec,
                audio_codec=item.audio_codec,
                width=item.width,
                height=item.height,
                display_aspect_ratio=item.display_aspect_ratio,
                frame_rate=item.frame_rate,
                field_order=item.field_order,
                audio_channels=item.audio_channels,
            )

            update_title_status(
                connection,
                title_id=db_title["id"],
                status=item.status,
                notes=None,
            )

            print(
                f"Probe successful: "
                f"{item.name}"
            )

        except Exception as error:
            item.status = "probe_failed"
            item.notes = str(error)

            update_title_status(
                connection,
                title_id=db_title["id"],
                status=item.status,
                notes=item.notes,
            )

            print(
                f"Probe failed: "
                f"{item.name}: {error}"
            )


# ---------------------------------------------------------------------------
# Encoding stage
# ---------------------------------------------------------------------------


def run_encode_stage(
    backup: DVDBackup,
    items: list[ManifestItem],
    config: AppConfig,
    connection,
) -> None:
    """
    Encode probed titles using the configured DVD encoding profile.

    Eligible workflow states:
        probed
        encode_failed

    Successful transition:
        probed -> encoded
    """

    disc_id = get_or_create_disc(
        connection,
        name=backup.name,
        backup_path=backup.path,
    )

    db_encode_titles = get_titles_by_status(
        connection,
        disc_id,
        (
            "probed",
            "encode_failed",
        ),
    )

    encode_source_titles = {
        row["source_title"]
        for row in db_encode_titles
    }

    encode_items = [
        item
        for item in items
        if (
            item.disc == backup.name
            and item.title in encode_source_titles
        )
    ]

    if not encode_items:
        print(
            f"No titles ready for encoding "
            f"on {backup.name}."
        )
        return

    for item in encode_items:
        db_title = next(
            row
            for row in db_encode_titles
            if row["source_title"] == item.title
        )

        input_path = (
            config.staging_root
            / backup.name
            / item.output_filename
        )

        output_path = (
            config.encoded_root
            / backup.name
            / f"{item.name}.mkv"
        )

        print(
            f"Encoding {backup.name} "
            f"title {item.title}: {item.name}"
        )

        try:
            result = encode_media(
                item,
                input_path,
                output_path,
            )

            if (
                result.returncode == 0
                and encoding_succeeded(
                    output_path
                )
            ):
                item.status = "encoded"
                item.notes = ""

                print(
                    f"Encoding successful: "
                    f"{item.name}"
                )

            else:
                item.status = "encode_failed"
                item.notes = (
                    f"ffmpeg return code "
                    f"{result.returncode}"
                )

                print(
                    f"Encoding failed: "
                    f"{item.name}"
                )

        except Exception as error:
            item.status = "encode_failed"
            item.notes = str(error)

            print(
                f"Encoding failed: "
                f"{item.name}: {error}"
            )

        update_title_status(
            connection,
            title_id=db_title["id"],
            status=item.status,
            notes=item.notes or None,
        )



# ---------------------------------------------------------------------------
# Validation stage
# ---------------------------------------------------------------------------


def run_validation_stage(
    backup: DVDBackup,
    items: list[ManifestItem],
    config: AppConfig,
    connection,
) -> None:
    """
    Validate encoded files against their extracted source.

    Eligible workflow states:
        encoded
        validation_failed

    Successful transition:
        encoded -> validated
    """
    disc_id = get_or_create_disc(
        connection,
        name=backup.name,
        backup_path=backup.path,
    )

    db_validation_titles = get_titles_by_status(
        connection,
        disc_id,
        (
            "encoded",
            "validation_failed",
        ),
    )

    validation_source_titles = {
        row["source_title"]
        for row in db_validation_titles
    }

    validation_items = [
        item
        for item in items
        if (
            item.disc == backup.name
            and item.title in validation_source_titles
        )
    ]

    if not validation_items:
        print(
            f"No titles ready for validation "
            f"on {backup.name}."
        )
        return

    for item in validation_items:
        db_title = next(
            row
            for row in db_validation_titles
            if row["source_title"] == item.title
        )

        source_path = (
            config.staging_root
            / backup.name
            / item.output_filename
        )

        encoded_path = (
            config.encoded_root
            / backup.name
            / f"{item.name}.mkv"
        )

        print(
            f"Validating {backup.name} "
            f"title {item.title}: "
            f"{item.name}"
        )

        try:
            source_data = probe_media(
                source_path
            )

            source_summary = (
                summarize_media(
                    source_data
                )
            )

            success, errors, _ = (
                validate_encoded_media(
                    source_summary,
                    encoded_path,
                )
            )

            if success:
                item.status = "validated"
                item.notes = ""

                print(
                    f"Validation successful: "
                    f"{item.name}"
                )

            else:
                item.status = (
                    "validation_failed"
                )

                item.notes = "; ".join(
                    errors
                )

                print(
                    f"Validation failed: "
                    f"{item.name}"
                )

                for error in errors:
                    print(
                        f"  - {error}"
                    )

        except Exception as error:
            item.status = (
                "validation_failed"
            )

            item.notes = str(error)

            print(
                f"Validation failed: "
                f"{item.name}: {error}"
            )

        update_title_status(
            connection,
            title_id=db_title["id"],
            status=item.status,
            notes=item.notes or None,
        )


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Run the current DVD ingestion workflow.

    The selected backup remains hard-coded during the prototype
    phase so this refactor does not alter existing behavior.
    """

    config = load_config()

    initialize_database(
        config.database_path,
        config.schema_path,
    )

    connection = connect_database(
        config.database_path
    )

    try:
        backup = select_backup(
            config,
            "Sci Fi 1a",
        )

        items = inspect_backup(
            backup,
            config,
            connection,
        )

        run_extraction_stage(
            backup,
            items,
            config,
            connection,
        )

        run_probe_stage(
            backup,
            items,
            config,
            connection,
        )

        run_encode_stage(
            backup,
            items,
            config,
            connection,
        )

        run_validation_stage(
            backup,
            items,
            config,
            connection,
        )

    finally:
        connection.close()

if __name__ == "__main__":
    main()