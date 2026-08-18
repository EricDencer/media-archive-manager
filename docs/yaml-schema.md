# Per-Disc YAML Metadata Schema

## Purpose

Each archived physical disc may have an `ingest.yaml` file stored with the backup.

The YAML file is the human-readable metadata record for that disc. It describes what the disc contains and provides the metadata required to identify movies and television episodes.

SQLite is the authoritative operational store for workflow state, collection relationships, and generated artifacts.

The YAML file should not be treated as the primary runtime workflow database.

## Example Location

```text
Video Archive/
└── Sci Fi 1a/
    ├── VIDEO_TS/
    └── ingest.yaml

schema_version: 1

disc:
  name: Sci Fi 1a
  format: dvd

titles:
  - title: 0
    media:
      type: movie
      name: Horrors of Spider Island
      year: 1960

    media:
      type: tv
      show: One Step Beyond
      year: 1959
      season: 1
      episode: 3
      episode_title: The Dream
