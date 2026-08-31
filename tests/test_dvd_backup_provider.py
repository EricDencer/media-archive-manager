"""
Tests for the dvdbackup provider.
"""

import unittest
from pathlib import Path

from dvd_backup_provider import DvdBackupProvider
from optical import OpticalMedia

import tempfile
from unittest.mock import patch
from subprocess import CompletedProcess


class DvdBackupProviderTests(
    unittest.TestCase
):
    def setUp(
        self,
    ) -> None:
        self.provider = DvdBackupProvider()

        self.dvd = OpticalMedia(
            device=Path("/dev/sr0"),
            present=True,
            media_type="dvd",
            label="TEST_DVD",
            filesystem="udf",
        )

    def test_supports_present_dvd(
        self,
    ) -> None:
        self.assertTrue(
            self.provider.supports(
                self.dvd
            )
        )

    def test_does_not_support_bluray(
        self,
    ) -> None:
        bluray = OpticalMedia(
            device=Path("/dev/sr0"),
            present=True,
            media_type="bluray",
            label="TEST_BLURAY",
            filesystem="udf",
        )

        self.assertFalse(
            self.provider.supports(
                bluray
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

    def test_builds_full_mirror_command(
        self,
    ) -> None:
        command = self.provider._build_command(
            media=self.dvd,
            destination=Path(
                "/tmp/media-backup-test"
            ),
        )

        self.assertEqual(
            command,
            [
                "dvdbackup",
                "-i",
                "/dev/sr0",
                "-o",
                "/tmp/media-backup-test",
                "-M",
            ],
        )

    def test_backup_rejects_unsupported_media(
        self,
    ) -> None:
        bluray = OpticalMedia(
            device=Path("/dev/sr0"),
            present=True,
            media_type="bluray",
            label="TEST_BLURAY",
            filesystem="udf",
        )

        with tempfile.TemporaryDirectory() as temp:
            destination = (
                Path(temp)
                / "backup"
            )

            result = self.provider.backup(
                media=bluray,
                destination=destination,
            )

            self.assertFalse(
                result.succeeded
            )
            self.assertIsNone(
                result.output_path
            )
            self.assertIsNone(
                result.return_code
            )
            self.assertFalse(
                destination.exists()
            )

    def test_backup_fails_when_tool_is_unavailable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = (
                Path(temp)
                / "backup"
            )

            with patch(
                "dvd_backup_provider.shutil.which",
                return_value=None,
            ):
                result = self.provider.backup(
                    media=self.dvd,
                    destination=destination,
                )

            self.assertFalse(
                result.succeeded
            )
            self.assertIn(
                "not found",
                result.message,
            )
            self.assertIsNone(
                result.return_code
            )
            self.assertFalse(
                destination.exists()
            )

    def test_backup_succeeds_when_video_ts_is_created(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = (
                Path(temp)
                / "backup"
            )

            def fake_run(
                command,
                capture_output,
                text,
                check,
            ):
                video_ts = (
                    destination
                    / "TEST_DVD"
                    / "VIDEO_TS"
                )

                video_ts.mkdir(
                    parents=True
                )

                return CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout="Backup complete.",
                    stderr="",
                )

            with patch(
                "dvd_backup_provider.subprocess.run",
                side_effect=fake_run,
            ) as run_mock:
                result = self.provider.backup(
                    media=self.dvd,
                    destination=destination,
                )

            self.assertTrue(
                result.succeeded
            )
            self.assertEqual(
                result.output_path,
                destination,
            )
            self.assertEqual(
                result.return_code,
                0,
            )

            run_mock.assert_called_once_with(
                [
                    "dvdbackup",
                    "-i",
                    "/dev/sr0",
                    "-o",
                    str(destination),
                    "-M",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_backup_fails_on_nonzero_return_code(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = (
                Path(temp)
                / "backup"
            )

            completed = CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="Unable to read DVD.",
            )

            with patch(
                "dvd_backup_provider.subprocess.run",
                return_value=completed,
            ):
                result = self.provider.backup(
                    media=self.dvd,
                    destination=destination,
                )

            self.assertFalse(
                result.succeeded
            )
            self.assertIsNone(
                result.output_path
            )
            self.assertEqual(
                result.return_code,
                1,
            )
            self.assertIn(
                "Unable to read DVD.",
                result.message,
            )

    def test_backup_fails_without_video_ts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = (
                Path(temp)
                / "backup"
            )

            completed = CompletedProcess(
                args=[],
                returncode=0,
                stdout="Backup complete.",
                stderr="",
            )

            with patch(
                "dvd_backup_provider.subprocess.run",
                return_value=completed,
            ):
                result = self.provider.backup(
                    media=self.dvd,
                    destination=destination,
                )

            self.assertFalse(
                result.succeeded
            )
            self.assertIsNone(
                result.output_path
            )
            self.assertEqual(
                result.return_code,
                0,
            )
            self.assertIn(
                "no VIDEO_TS",
                result.message,
            )

if __name__ == "__main__":
    unittest.main()

    def test_backup_rejects_unsupported_media(
        self,
    ) -> None:
        bluray = OpticalMedia(
            device=Path("/dev/sr0"),
            present=True,
            media_type="bluray",
            label="TEST_BLURAY",
            filesystem="udf",
        )

        with tempfile.TemporaryDirectory() as temp:
            destination = (
                Path(temp)
                / "backup"
            )

            result = self.provider.backup(
                media=bluray,
                destination=destination,
            )

            self.assertFalse(
                result.succeeded
            )
            self.assertIsNone(
                result.output_path
            )
            self.assertIsNone(
                result.return_code
            )
            self.assertFalse(
                destination.exists()
            )
            