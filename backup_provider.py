"""
Common contracts for physical-media backup providers.

A backup provider wraps one external backup tool. It reports whether
it supports the detected media, whether its executable is available,
and the result of attempting a backup.

Provider selection and fallback policy belong to the acquisition
coordinator, not to individual providers.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from optical import OpticalMedia


@dataclass(frozen=True)
class BackupResult:
    """
    Result returned by a physical-media backup provider.
    """

    provider: str
    succeeded: bool
    output_path: Path | None
    message: str
    return_code: int | None = None


class BackupProvider(Protocol):
    """
    Interface implemented by physical-media backup providers.
    """

    name: str

    def supports(
        self,
        media: OpticalMedia,
    ) -> bool:
        """
        Return whether this provider supports the detected media.
        """

        ...

    def is_available(
        self,
    ) -> bool:
        """
        Return whether the provider's external tool is available.
        """

        ...

    def backup(
        self,
        media: OpticalMedia,
        destination: Path,
    ) -> BackupResult:
        """
        Back up the detected media into the requested destination.
        """

        ...