import subprocess
from pathlib import Path

from models import ManifestItem


def build_encode_command(
    item: ManifestItem,
    input_path,
    output_path,
):
    """
    Build an ffmpeg command for Plex-ready H.264 output.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    filters = []

    if item.field_order not in ("", "progressive", "unknown"):
        filters.append("yadif")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
    ]

    if filters:
        command += [
            "-vf",
            ",".join(filters),
        ]

    command += [
            "-c:v",
            "h264_nvenc",
            "-preset",
            "p5",
            "-cq",
            "24",
            "-c:a",
            "copy",
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            str(output_path),
        ]
    return command


def encode_media(
    item: ManifestItem,
    input_path,
    output_path,
):
    """
    Encode one extracted title.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = build_encode_command(
        item,
        input_path,
        output_path,
    )

    print(
        f"Encoding {item.name}"
    )

    result = subprocess.run(
        command
    )

    return result

# ----> First Test
if __name__ == "__main__":

    from manifest import load_manifest

    manifest_path = "manifest.csv"

    items = load_manifest(
        manifest_path
    )

    item = next(
        item
        for item in items
        if (
            item.disc == "Sci Fi 1a"
            and item.title == 0
        )
    )

    input_path = (
        "/home/ericdencer/Video Archive/"
        "staging/Sci Fi 1a/A1_t00.mkv"
    )

    output_path = (
        "/home/ericdencer/Video Archive/"
        "encoded/Sci Fi 1a/"
        "Horrors of Spider Island.mkv"
    )

    result = encode_media(
        item,
        input_path,
        output_path,
    )

    print(
        f"ffmpeg return code: "
        f"{result.returncode}"
    )

def encoding_succeeded(output_path) -> bool:
    """
    Verify that ffmpeg created a non-empty output file.
    """

    output_path = Path(output_path)

    return (
        output_path.exists()
        and output_path.stat().st_size > 0
    )