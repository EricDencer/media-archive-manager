# Media Archive Manager

A Python-based media ingestion and archival project for managing physical
DVD/Blu-ray backups and producing media suitable for a Plex library.

## Current Status

The current prototype implements a working DVD ingestion pipeline:

1. Inspect an archived DVD backup with MakeMKV.
2. Maintain title identification and workflow state.
3. Extract selected titles with MakeMKV.
4. Probe extracted media with ffprobe.
5. Encode DVD video to H.264 using NVIDIA NVENC.
6. Preserve source AC3 audio where appropriate.
7. Validate encoded output before publication.

The current DVD encoding profile uses:

- H.264 NVENC
- CQ 24
- YADIF deinterlacing for interlaced sources
- Original audio stream copy

The initial vertical slice has been successfully tested with multiple movie
titles from a compilation DVD.

## Project Direction

The next development phases will:

- Refactor and document the existing Python modules.
- Replace the CSV manifest with per-disc YAML metadata.
- Add SQLite for collection and workflow state.
- Complete Plex publishing for movies and television episodes.
- Preserve the existing working ingestion pipeline during these changes.

A future major version may provide a containerized web application for
managing the media collection and ingestion workflow.

## Requirements

The current prototype expects the following external tools:

- Python 3
- MakeMKV / `makemkvcon`
- FFmpeg / `ffmpeg`
- `ffprobe`
- NVIDIA NVENC-capable hardware for the current encoding profile

## License

License has not yet been selected.
