"""
Tests for the MakeMKV backup provider.
"""

import unittest
from pathlib import Path
from unittest.mock import patch

from makemkv_backup_provider import (
    MakeMkvBackupProvider,
)
from optical import OpticalMedia


class MakeMkvBackupProviderTests(
    unittest.TestCase
):
    def setUp(
        self,
    ) -> None:
        self.provider = (
            MakeMkvBackupProvider()
        )

        self.dvd = OpticalMedia(
            device=Path("/dev/sr0"),
            present=True,
            media_type="dvd",
            label="TEST_DVD",
            filesystem="udf",
        )

        self.bluray = OpticalMedia(
            device=Path("/dev/sr1"),
            present=True,
            media_type="bluray",
            label="TEST_BLURAY",
            filesystem="udf",
        )

    def test_supports_dvd(
        self,
    ) -> None:
        self.assertTrue(
            self.provider.supports(
                self.dvd
            )
        )

    def test_supports_bluray(
        self,
    ) -> None:
        self.assertTrue(
            self.provider.supports(
                self.bluray
            )
        )

    def test_does_not_support_empty_drive(
        self,
    ) -> None:
        empty_drive = OpticalMedia(
            device=Path("/dev/sr0"),
            present=False,
            media_type=None,
            label=None,
            filesystem=None,
        )

        self.assertFalse(
            self.provider.supports(
                empty_drive
            )
        )

    def test_reports_tool_availability(
        self,
    ) -> None:
        with patch(
            "makemkv_backup_provider."
            "shutil.which",
            return_value=(
                "/usr/bin/makemkvcon"
            ),
        ):
            self.assertTrue(
                self.provider.is_available()
            )

    def test_builds_decrypted_backup_command(
        self,
    ) -> None:
        command = (
            self.provider._build_command(
                media=self.bluray,
                destination=Path(
                    "/tmp/makemkv-test"
                ),
            )
        )

        self.assertEqual(
            command,
            [
                "makemkvcon",
                "-r",
                "--decrypt",
                "backup",
                "dev:/dev/sr1",
                "/tmp/makemkv-test",
            ],
        )


if __name__ == "__main__":
    unittest.main()