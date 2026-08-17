from pathlib import Path
from scanner import find_dvd_backups
from makemkv import inspect_dvd, parse_robot_titles
from manifest import (
    load_manifest,
    save_manifest,
    merge_scan,
)
from extractor import extract_title
from probe import (
    probe_media,
    summarize_media,
)
from encoder import (
    encode_media,
    encoding_succeeded,
)
from validator import validate_encoded_media

root = "/home/ericdencer/Video Archive"
manifest_path = "manifest.csv"


# -----------------------------------
# Backup Stage
# -----------------------------------

backups = find_dvd_backups(root)

backup = next(
    backup
    for backup in backups
    if backup.name == "Sci Fi 1a"
)

print(f"Inspecting: {backup.name}")

result = inspect_dvd(backup)

titles = parse_robot_titles(
    result.stdout + result.stderr
)

items = load_manifest(manifest_path)

items = merge_scan(
    backup,
    titles,
    items,
)

save_manifest(
    manifest_path,
    items,
)

print(f"Manifest updated with {len(titles)} titles.")
from extractor import (
    extract_title,
    extraction_succeeded,
)

staging_root = "/home/ericdencer/Video Archive/staging"
encoded_root = "/home/ericdencer/Video Archive/encoded"

ready_items = [
    item
    for item in items
    if (
        item.disc == backup.name
        and item.ready == "yes"
        and item.status in (
            "identified",
            "extract_failed",
        )
    )
]

if not ready_items:
    print(
        f"No titles ready for extraction "
        f"on {backup.name}."
    )

for item in ready_items:

    result = extract_title(
        backup,
        item,
        staging_root,
    )

    if (
        result.returncode == 0
        and extraction_succeeded(
            backup,
            item,
            staging_root,
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

    save_manifest(
        manifest_path,
        items,
    )

probe_items = [
    item
    for item in items
    if (
        item.disc == backup.name
        and item.status == "extracted"
    )
]

for item in probe_items:

    media_path = (
        Path(staging_root)
        / backup.name
        / item.output_filename
    )

    print(
        f"Probing {backup.name} "
        f"title {item.title}: {item.name}"
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
            summary["display_aspect_ratio"]
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

        print(
            f"Probe successful: "
            f"{item.name}"
        )

    except Exception as error:
        item.status = "probe_failed"
        item.notes = str(error)

        print(
            f"Probe failed: "
            f"{item.name}: {error}"
        )

    save_manifest(
        manifest_path,
        items,
    )

# -------------------------
# Encode stage
# -------------------------

encode_items = [
    item
    for item in items
    if (
        item.disc == backup.name
        and item.status in (
            "probed",
            "encode_failed",
        )
    )
]

if not encode_items:
    print(
        f"No titles ready for encoding "
        f"on {backup.name}."
    )

for item in encode_items:

    input_path = (
        Path(staging_root)
        / backup.name
        / item.output_filename
    )

    output_dir = (
        Path(encoded_root)
        / backup.name
    )

    output_path = (
        output_dir
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

    save_manifest(
        manifest_path,
        items,
    )

# -------------------------
# Validation stage
# -------------------------

validation_items = [
    item
    for item in items
    if (
        item.disc == backup.name
        and item.status in (
            "encoded",
            "validation_failed",
        )
    )
]

if not validation_items:
    print(
        f"No titles ready for validation "
        f"on {backup.name}."
    )

for item in validation_items:

    source_path = (
        Path(staging_root)
        / backup.name
        / item.output_filename
    )

    encoded_path = (
        Path(encoded_root)
        / backup.name
        / f"{item.name}.mkv"
    )

    print(
        f"Validating {backup.name} "
        f"title {item.title}: {item.name}"
    )

    try:
        source_data = probe_media(
            source_path
        )

        source_summary = summarize_media(
            source_data
        )

        success, errors, encoded_summary = (
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
            item.status = "validation_failed"
            item.notes = "; ".join(errors)

            print(
                f"Validation failed: "
                f"{item.name}"
            )

            for error in errors:
                print(
                    f"  - {error}"
                )

    except Exception as error:
        item.status = "validation_failed"
        item.notes = str(error)

        print(
            f"Validation failed: "
            f"{item.name}: {error}"
        )

    save_manifest(
        manifest_path,
        items,
    )