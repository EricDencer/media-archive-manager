"""
Application configuration for Media Archive Manager.

Global application behavior is loaded from config.yaml.

Per-disc ingest.yaml files describe media content. This module
describes how the application itself runs.

Local configuration should not be committed to source control.
Use config.example.yaml as the distributable template.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


DEFAULT_CONFIG_PATH = Path("config.yaml")

SUPPORTED_MEDIA_TYPES = {
    "dvd",
    "bluray",
}

@dataclass(frozen=True)
class MediaLocation:
    """Configured location containing archived media backups."""

    name: str
    path: Path
    enabled: bool = True
    media_types: tuple[str, ...] = ()

@dataclass(frozen=True)
class AppConfig:
    """Validated runtime configuration."""

    environment: str

    media_locations: tuple[MediaLocation, ...]

    staging_root: Path
    encoded_root: Path
    database_path: Path
    schema_path: Path

    acquisition_enabled: bool
    publishing_enabled: bool
    ai_enabled: bool

def _require_mapping(
    data: dict,
    key: str,
) -> dict:
    """Return a required configuration section."""

    value = data.get(key)

    if not isinstance(value, dict):
        raise ValueError(
            f"Configuration section '{key}' "
            f"is missing or invalid."
        )

    return value


def _require_value(
    data: dict,
    key: str,
    section: str,
):
    """Return a required configuration value."""

    value = data.get(key)

    if value is None or value == "":
        raise ValueError(
            f"Required configuration value "
            f"'{section}.{key}' is missing."
        )

    return value


def load_config(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> AppConfig:
    """Load and validate global application configuration."""

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Application configuration not found: "
            f"{config_path}\n"
            f"Copy config.example.yaml to config.yaml "
            f"and update it for this system."
        )

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Application configuration is empty "
            f"or invalid: {config_path}"
        )

    application = _require_mapping(
        data,
        "application",
    )

    paths = _require_mapping(
        data,
        "paths",
    )

    capabilities = _require_mapping(
        data,
        "capabilities",
    )

    acquisition = _require_mapping(
        capabilities,
        "acquisition",
    )

    publishing = _require_mapping(
        capabilities,
        "publishing",
    )

    ai = _require_mapping(
        capabilities,
        "ai",
    )

    media_locations_data = data.get(
        "media_locations"
    )

    if not isinstance(
        media_locations_data,
        list,
    ) or not media_locations_data:
        raise ValueError(
            "Configuration must define at least "
            "one media location."
        )

    media_locations = []
    seen_location_names = set()

    for index, location in enumerate(
        media_locations_data
    ):
        if not isinstance(location, dict):
            raise ValueError(
                f"media_locations[{index}] "
                f"is invalid."
            )

        name = location.get("name")
        path = location.get("path")

        if not name:
            raise ValueError(
                f"media_locations[{index}].name "
                f"is required."
            )

        if not path:
            raise ValueError(
                f"media_locations[{index}].path "
                f"is required."
            )

        normalized_name = str(name).strip()
        name_key = normalized_name.casefold()

        if name_key in seen_location_names:
            raise ValueError(
                f"Duplicate media location name: "
                f"{normalized_name}"
            )

        seen_location_names.add(
            name_key
        )

        media_types = location.get(
            "media_types",
            [],
        )

        if not isinstance(media_types, list):
            raise ValueError(
                f"media_locations[{index}]."
                f"media_types must be a list."
            )

        normalized_media_types = tuple(
            str(media_type).lower().strip()
            for media_type in media_types
        )

        unsupported_media_types = [
            media_type
            for media_type in normalized_media_types
            if media_type not in SUPPORTED_MEDIA_TYPES
        ]

        if unsupported_media_types:
            raise ValueError(
                f"media_locations[{index}] "
                f"contains unsupported media types: "
                f"{', '.join(unsupported_media_types)}"
            )

        media_locations.append(
            MediaLocation(
                name=normalized_name,
                path=Path(path).expanduser(),
                enabled=bool(
                    location.get(
                        "enabled",
                        True,
                    )
                ),
                media_types=normalized_media_types,
            )
        )

    return AppConfig(
        environment=str(
            _require_value(
                application,
                "environment",
                "application",
            )
        ),
        media_locations=tuple(
            media_locations
        ),
        staging_root=Path(
            _require_value(
                paths,
                "staging_root",
                "paths",
            )
        ).expanduser(),
        encoded_root=Path(
            _require_value(
                paths,
                "encoded_root",
                "paths",
            )
        ).expanduser(),
        database_path=Path(
            _require_value(
                paths,
                "database_path",
                "paths",
            )
        ).expanduser(),
        schema_path=Path(
            _require_value(
                paths,
                "schema_path",
                "paths",
            )
        ).expanduser(),
        acquisition_enabled=bool(
            acquisition.get(
                "enabled",
                False,
            )
        ),
        publishing_enabled=bool(
            publishing.get(
                "enabled",
                False,
            )
        ),
        ai_enabled=bool(
            ai.get(
                "enabled",
                False,
            )
        ),
    )
