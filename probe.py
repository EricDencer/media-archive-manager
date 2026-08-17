import json
import subprocess
from pathlib import Path


def probe_media(path):
    """
    Probe an extracted media file with ffprobe.

    Returns parsed ffprobe JSON.
    """

    media_path = Path(path)

    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(media_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed for {media_path}: "
            f"{result.stderr}"
        )

    return json.loads(result.stdout)

def summarize_media(probe_data):
    """
    Extract the technical fields useful to the ingest pipeline.
    """

    video_stream = next(
        (
            stream
            for stream in probe_data["streams"]
            if stream.get("codec_type") == "video"
        ),
        None,
    )

    audio_stream = next(
        (
            stream
            for stream in probe_data["streams"]
            if stream.get("codec_type") == "audio"
        ),
        None,
    )

    format_info = probe_data.get("format", {})

    summary = {
        "duration_seconds": float(
            format_info.get("duration", 0)
        ),
        "video_codec": "",
        "width": 0,
        "height": 0,
        "display_aspect_ratio": "",
        "frame_rate": "",
        "field_order": "",
        "audio_codec": "",
        "audio_channels": 0,
    }

    if video_stream:
        summary["video_codec"] = (
            video_stream.get("codec_name", "")
        )

        summary["width"] = (
            video_stream.get("width", 0)
        )

        summary["height"] = (
            video_stream.get("height", 0)
        )

        summary["display_aspect_ratio"] = (
            video_stream.get(
                "display_aspect_ratio",
                "",
            )
        )

        summary["frame_rate"] = (
            video_stream.get(
                "avg_frame_rate",
                "",
            )
        )

        summary["field_order"] = (
            video_stream.get(
                "field_order",
                "",
            )
        )

    if audio_stream:
        summary["audio_codec"] = (
            audio_stream.get("codec_name", "")
        )

        summary["audio_channels"] = (
            audio_stream.get("channels", 0)
        )

    return summary