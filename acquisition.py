"""
Physical media acquisition session.

This module coordinates an interactive batch session for processing
physical optical media.

Current responsibilities:
    - Select an enabled optical drive.
    - Prompt the user to insert media.
    - Detect and report inserted media.
    - Allow the user to continue processing discs or exit.

Backup providers, verification, YAML generation, and auto-eject
will be added incrementally.
"""

from config import AppConfig, OpticalDevice
from optical import detect_optical_media


def select_optical_device(
    config: AppConfig,
) -> OpticalDevice:
    """
    Select an enabled optical device for acquisition.

    For the initial implementation, automatically select the first
    enabled device.
    """

    enabled_devices = [
        device
        for device in config.optical_devices
        if device.enabled
    ]

    if not enabled_devices:
        raise RuntimeError(
            "No enabled optical devices are configured."
        )

    return enabled_devices[0]


def run_batch_acquisition(
    config: AppConfig,
) -> None:
    """
    Run an interactive physical-media acquisition session.

    The user may process multiple discs sequentially and exit
    when finished.
    """

    if not config.acquisition_enabled:
        print(
            "Physical media acquisition is disabled "
            "in configuration."
        )
        return

    device = select_optical_device(
        config
    )

    print()
    print(
        "Media Archive Manager - "
        "Physical Media Acquisition"
    )
    print()
    print(
        f"Using optical drive: "
        f"{device.name} [{device.device}]"
    )

    while True:
        print()
        response = input(
            "Insert a disc and press Enter, "
            "or type Q to finish: "
        ).strip()

        if response.casefold() == "q":
            print(
                "Batch acquisition complete."
            )
            return

        try:
            media = detect_optical_media(
                device.device
            )

        except Exception as error:
            print(
                f"Unable to inspect optical media: "
                f"{error}"
            )
            continue

        if not media.present:
            print(
                "No media detected. "
                "Insert a disc and try again."
            )
            continue

        print()
        print("Media detected:")
        print(
            f"  Type:       "
            f"{media.media_type or 'unknown'}"
        )
        print(
            f"  Label:      "
            f"{media.label or 'unknown'}"
        )
        print(
            f"  Filesystem: "
            f"{media.filesystem or 'unknown'}"
        )
        print(
            f"  Device:     "
            f"{media.device}"
        )

        response = input(
            "Process this disc? [Y/n/q]: "
        ).strip().casefold()

        if response == "q":
            print(
                "Batch acquisition complete."
            )
            return

        if response == "n":
            print(
                "Disc skipped."
            )
            continue

        print(
            "Disc accepted for acquisition."
        )
        print(
            "Backup provider integration "
            "is the next implementation step."
        )

