from pathlib import Path

from manifest import load_manifest, save_manifest
from probe import probe_media, summarize_media


manifest_path = Path("manifest.csv")

staging_root = Path(
    "/home/ericdencer/Video Archive/staging"
)

items = load_manifest(
    manifest_path
)

for item in items:

    # Only repair titles for which an extracted source file
    # actually exists.
    media_path = (
        staging_root
        / item.disc
        / item.output_filename
    )

    if not media_path.exists():
        continue

    print(
        f"Re-probing {item.disc} "
        f"title {item.title}: {item.name}"
    )

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

    item.audio_codec = (
        summary["audio_codec"]
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

    item.audio_channels = (
        summary["audio_channels"]
    )

save_manifest(
    manifest_path,
    items,
)

print("Probe metadata repair complete.")