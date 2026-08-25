"""
Optical media detection.

This module inspects configured optical devices and reports
whether media is present and, when possible, whether it is
DVD, Blu-ray, CD, or unknown.

It does not perform backup operations.
"""

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class OpticalMedia:
    device: Path
    present: bool
    media_type: str | None
    label: str | None
    filesystem: str | None


def _parse_properties(output: str) -> dict[str, str]:
    properties = {}

    for line in output.splitlines():
        if "=" not in line:
            continue

        key, value = line.split(
            "=",
            1,
        )

        properties[key] = value

    return properties


def detect_optical_media(
    device: Path,
) -> OpticalMedia:
    """
    Inspect one optical device using udev properties.
    """

    device = Path(device)

    result = subprocess.run(
        [
            "udevadm",
            "info",
            "--query=property",
            f"--name={device}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Unable to inspect optical device "
            f"{device}: {result.stderr.strip()}"
        )

    properties = _parse_properties(
        result.stdout
    )

    present = (
        properties.get(
            "ID_CDROM_MEDIA"
        )
        == "1"
    )

    media_type = None

    if present:
        if (
            properties.get(
                "ID_CDROM_MEDIA_BD"
            )
            == "1"
        ):
            media_type = "bluray"

        elif (
            properties.get(
                "ID_CDROM_MEDIA_DVD"
            )
            == "1"
        ):
            media_type = "dvd"

        elif (
            properties.get(
                "ID_CDROM_MEDIA_CD"
            )
            == "1"
        ):
            media_type = "cd"

        else:
            media_type = "unknown"

    label = (
        properties.get(
            "ID_FS_LABEL"
        )
        or properties.get(
            "ID_FS_VOLUME_ID"
        )
    )

    filesystem = properties.get(
        "ID_FS_TYPE"
    )

    return OpticalMedia(
        device=device,
        present=present,
        media_type=media_type,
        label=label,
        filesystem=filesystem,
    )