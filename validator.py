from pathlib import Path

from probe import probe_media, summarize_media


def validate_encoded_media(
    source_summary,
    encoded_path,
):
    """
    Validate an encoded media file against the source summary.

    Returns:
        (success: bool, errors: list[str], encoded_summary: dict)
    """

    encoded_path = Path(encoded_path)

    errors = []

    if not encoded_path.exists():
        errors.append(
            f"Encoded file does not exist: "
            f"{encoded_path}"
        )

        return False, errors, {}

    if encoded_path.stat().st_size == 0:
        errors.append(
            f"Encoded file is empty: "
            f"{encoded_path}"
        )

        return False, errors, {}

    try:
        probe_data = probe_media(
            encoded_path
        )

        encoded_summary = summarize_media(
            probe_data
        )

    except Exception as error:
        errors.append(
            f"ffprobe failed: {error}"
        )

        return False, errors, {}

    #
    # Video codec
    #

    if encoded_summary["video_codec"] != "h264":
        errors.append(
            "Expected H.264 video, got "
            f"{encoded_summary['video_codec']}"
        )

    #
    # Resolution
    #

    if (
        encoded_summary["width"]
        != source_summary["width"]
    ):
        errors.append(
            "Width changed from "
            f"{source_summary['width']} to "
            f"{encoded_summary['width']}"
        )

    if (
        encoded_summary["height"]
        != source_summary["height"]
    ):
        errors.append(
            "Height changed from "
            f"{source_summary['height']} to "
            f"{encoded_summary['height']}"
        )

    #
    # Display aspect ratio
    #

    if (
        source_summary["display_aspect_ratio"]
        and encoded_summary["display_aspect_ratio"]
        != source_summary["display_aspect_ratio"]
    ):
        errors.append(
            "Display aspect ratio changed from "
            f"{source_summary['display_aspect_ratio']} "
            f"to "
            f"{encoded_summary['display_aspect_ratio']}"
        )

    #
    # Field order
    #

    encoded_field_order = (
        encoded_summary["field_order"]
    )

    if encoded_field_order not in (
        "",
        "progressive",
        "unknown",
    ):
        errors.append(
            "Encoded video is still interlaced: "
            f"{encoded_field_order}"
        )

    #
    # Audio
    #

    if not encoded_summary["audio_codec"]:
        errors.append(
            "No audio stream detected."
        )

    #
    # Duration
    #

    source_duration = float(
        source_summary["duration_seconds"]
    )

    encoded_duration = float(
        encoded_summary["duration_seconds"]
    )

    duration_difference = abs(
        source_duration - encoded_duration
    )

    if duration_difference > 2.0:
        errors.append(
            "Duration differs by more than "
            f"2 seconds: source={source_duration:.3f}, "
            f"encoded={encoded_duration:.3f}"
        )

    return (
        len(errors) == 0,
        errors,
        encoded_summary,
    )