"""
Physical-media backup provider using MakeMKV.
"""

import shutil
from pathlib import Path

from optical import OpticalMedia


class MakeMkvBackupProvider:
    """
    Back up DVD and Blu-ray media using MakeMKV.
    """

    name = "makemkv"

    def supports(
        self,
        media: OpticalMedia,
    ) -> bool:
        """
        Return whether MakeMKV supports the detected media.
        """

        return (
            media.present
            and media.media_type
            in {
                "dvd",
                "bluray",
            }
        )

    def is_available(
        self,
    ) -> bool:
        """
        Return whether makemkvcon is available on the system.
        """

        return shutil.which(
            "makemkvcon"
        ) is not None

    def _build_command(
        self,
        media: OpticalMedia,
        destination: Path,
    ) -> list[str]:
        """
        Build a decrypted full-disc backup command.
        """

        return [
            "makemkvcon",
            "-r",
            "--decrypt",
            "backup",
            f"dev:{media.device}",
            str(destination),
        ]