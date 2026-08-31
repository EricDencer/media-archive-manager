"""
DVD backup provider using the dvdbackup command-line tool.
"""

import shutil
import subprocess
from pathlib import Path

from backup_provider import BackupResult
from optical import OpticalMedia


class DvdBackupProvider:
    """
    Back up DVD media using dvdbackup.
    """

    name = "dvdbackup"

    def supports(
        self,
        media: OpticalMedia,
    ) -> bool:
        """
        Return whether dvdbackup supports the detected media.
        """

        return (
            media.present
            and media.media_type == "dvd"
        )

    def is_available(
        self,
    ) -> bool:
        """
        Return whether dvdbackup is available on the system.
        """

        return shutil.which(
            "dvdbackup"
        ) is not None

    def _build_command(
        self,
        media: OpticalMedia,
        destination: Path,
    ) -> list[str]:
        """
        Build the dvdbackup command for a full-disc mirror.
        """

        return [
            "dvdbackup",
            "-i",
            str(media.device),
            "-o",
            str(destination),
            "-M",
        ]

    def backup(
        self,
        media: OpticalMedia,
        destination: Path,
    ) -> BackupResult:
        """
        Back up a DVD to the requested destination.
        """

        destination = Path(
            destination
        ).expanduser()

        if not self.supports(media):
            return BackupResult(
                provider=self.name,
                succeeded=False,
                output_path=None,
                message=(
                    "dvdbackup does not support "
                    f"media type: {media.media_type}"
                ),
            )

        if not self.is_available():
            return BackupResult(
                provider=self.name,
                succeeded=False,
                output_path=None,
                message=(
                    "dvdbackup executable was not found."
                ),
            )

        try:
            destination.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as error:
            return BackupResult(
                provider=self.name,
                succeeded=False,
                output_path=None,
                message=(
                    "Unable to create backup destination: "
                    f"{error}"
                ),
            )

        command = self._build_command(
            media=media,
            destination=destination,
        )

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            return BackupResult(
                provider=self.name,
                succeeded=False,
                output_path=None,
                message=(
                    "Unable to start dvdbackup: "
                    f"{error}"
                ),
            )

        video_ts_created = any(
            path.is_dir()
            for path in destination.rglob(
                "VIDEO_TS"
            )
        )

        succeeded = (
            result.returncode == 0
            and video_ts_created
        )

        if succeeded:
            message = "DVD backup completed successfully."
            output_path = destination
        else:
            detail = (
                result.stderr.strip()
                or result.stdout.strip()
                or "No diagnostic output was produced."
            )

            message = (
                "DVD backup failed or produced no "
                f"VIDEO_TS directory: {detail}"
            )
            output_path = None

        return BackupResult(
            provider=self.name,
            succeeded=succeeded,
            output_path=output_path,
            message=message,
            return_code=result.returncode,
        )