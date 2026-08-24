"""
Generate per-disc ingest.yaml metadata stubs.

This module creates human-editable YAML files from machine-discovered
source titles.

It never overwrites an existing ingest.yaml file.
"""

from pathlib import Path

import yaml


def build_ingest_stub(
    backup,
    titles,
) -> dict:
    """
    Build a neutral ingest.yaml structure from discovered titles.
    """

    return {
        "schema_version": 1,
        "disc": {
            "name": backup.name,
        },
        "titles": [
            {
                "title": title.index,
                "approved": False,
                "media": {
                    "type": None,
                    "name": None,
                    "year": None,
                    "show": None,
                    "season": None,
                    "episode": None,
                    "episode_title": None,
                },
            }
            for title in titles
        ],
    }


def write_ingest_stub(
    backup,
    titles,
) -> Path:
    """
    Write ingest.yaml for a backup if one does not already exist.

    Raises:
        FileExistsError:
            If ingest.yaml already exists.
    """

    yaml_path = (
        Path(backup.path)
        / "ingest.yaml"
    )

    if yaml_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing YAML: "
            f"{yaml_path}"
        )

    data = build_ingest_stub(
        backup,
        titles,
    )

    with yaml_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        yaml.safe_dump(
            data,
            file,
            sort_keys=False,
            allow_unicode=True,
        )

    return yaml_path