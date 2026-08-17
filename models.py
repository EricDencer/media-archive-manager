from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DVDBackup:
    name: str
    path: Path
    ifo_path: Path


@dataclass
class TitleInfo:
    index: int
    duration: str | None = None
    duration_seconds: int | None = None
    size_bytes: int | None = None
    chapters: int | None = None
    output_filename: str | None = None

    video_codec: str | None = None
    audio_codecs: list[str] = field(default_factory=list)


@dataclass
class ManifestItem:
    # Machine-owned identity
    disc: str
    title: int

    # Human-owned metadata
    media_type: str = ""
    name: str = ""
    year: str = ""
    season: str = ""
    episode: str = ""

    # Machine-owned technical metadata
    duration: str = ""
    duration_seconds: int = 0
    chapters: int = 0
    size_bytes: int = 0
    video_codec: str = ""
    audio_codec: str = ""
    output_filename: str = ""

    # Workflow controls
    status: str = "discovered"
    ready: str = "no"
    notes: str = ""

    # Extracted media technical metadata
    width: int = 0
    height: int = 0
    display_aspect_ratio: str = ""
    frame_rate: str = ""
    field_order: str = ""
    audio_channels: int = 0