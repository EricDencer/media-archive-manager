import csv
from pathlib import Path

from models import ManifestItem

FIELDNAMES = [
    "disc",
    "title",
    "media_type",
    "name",
    "year",
    "season",
    "episode",
    "duration",
    "duration_seconds",
    "chapters",
    "size_bytes",
    "video_codec",
    "audio_codec",
    "output_filename",
    "status",
    "ready",
    "notes",
    "width",
    "height",
    "display_aspect_ratio",
    "frame_rate",
    "field_order",
    "audio_channels",
]

def load_manifest(path):
    manifest_path = Path(path)

    if not manifest_path.exists():
        return []

    items = []

    with manifest_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            item = ManifestItem(
                disc=row["disc"],
                title=int(row["title"]),
                media_type=row["media_type"],
                name=row["name"],
                year=row["year"],
                season=row["season"],
                episode=row["episode"],
                duration=row["duration"],
                duration_seconds=int(row["duration_seconds"] or 0),
                chapters=int(row["chapters"] or 0),
                size_bytes=int(row["size_bytes"] or 0),
                video_codec=row["video_codec"],
                audio_codec=row["audio_codec"],
                output_filename=row["output_filename"],
                status=row["status"],
                ready=row["ready"],
                notes=row["notes"],
                width=int(row.get("width") or 0),
                height=int(row.get("height") or 0),
                display_aspect_ratio=row.get(
                    "display_aspect_ratio",
                    "",
                ),
                frame_rate=row.get("frame_rate", ""),
                field_order=row.get("field_order", ""),
                audio_channels=int(
                    row.get("audio_channels") or 0
                ),
            )

            items.append(item)

    return items

def save_manifest(path, items):
    manifest_path = Path(path)

    with manifest_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()

        for item in items:
            writer.writerow({
                "disc": item.disc,
                "title": item.title,
                "media_type": item.media_type,
                "name": item.name,
                "year": item.year,
                "season": item.season,
                "episode": item.episode,
                "duration": item.duration,
                "duration_seconds": item.duration_seconds,
                "chapters": item.chapters,
                "size_bytes": item.size_bytes,
                "video_codec": item.video_codec,
                "audio_codec": item.audio_codec,
                "output_filename": item.output_filename,
                "status": item.status,
                "ready": item.ready,
                "notes": item.notes,
                "width": item.width,
                "height": item.height,
                "display_aspect_ratio": item.display_aspect_ratio,
                "frame_rate": item.frame_rate,
                "field_order": item.field_order,
                "audio_channels": item.audio_channels,
            })

def merge_title(
    backup,
    title,
    existing_items,
):
    for item in existing_items:
        if (
            item.disc == backup.name
            and item.title == title.index
        ):
            item.duration = title.duration or ""
            item.duration_seconds = title.duration_seconds or 0
            item.chapters = title.chapters or 0
            item.size_bytes = title.size_bytes or 0
            item.output_filename = title.output_filename or ""

            return item

    return ManifestItem(
        disc=backup.name,
        title=title.index,
        duration=title.duration or "",
        duration_seconds=title.duration_seconds or 0,
        chapters=title.chapters or 0,
        size_bytes=title.size_bytes or 0,
        video_codec=title.video_codec or "",
        audio_codec=(
            title.audio_codecs[0]
            if title.audio_codecs
            else ""
        ),
        output_filename=title.output_filename or "",
        status="discovered",
        ready="no",
    )

def merge_scan(
    backup,
    titles,
    existing_items,
):
    merged_items = list(existing_items)

    for title in titles:
        merged_item = merge_title(
            backup,
            title,
            merged_items,
        )

        if merged_item not in merged_items:
            merged_items.append(merged_item)

    return merged_items