import shutil
from pathlib import Path

from models import ManifestItem


def build_movie_destination(
    item: ManifestItem,
    library_root,
):
    """
    Build the permanent Plex destination for a movie.

    Example:

    Movies/
        The Wasp Woman (1959)/
            The Wasp Woman (1959).mkv
    """

    library_root = Path(library_root)

    if not item.name:
        raise ValueError(
            "Cannot publish movie without a name."
        )

    if not item.year:
        raise ValueError(
            f"Cannot publish {item.name} without a year."
        )

    movie_name = (
        f"{item.name} ({item.year})"
    )

    destination_dir = (
        library_root
        / "Movies"
        / movie_name
    )

    destination_path = (
        destination_dir
        / f"{movie_name}.mkv"
    )

    return destination_path


def publish_movie(
    item: ManifestItem,
    source_path,
    library_root,
):
    """
    Copy a validated movie into the permanent library.

    Returns the destination path.
    """

    source_path = Path(source_path)

    if not source_path.exists():
        raise FileNotFoundError(
            f"Encoded source does not exist: "
            f"{source_path}"
        )

    destination_path = (
        build_movie_destination(
            item,
            library_root,
        )
    )

    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"Publishing {item.name}"
    )

    shutil.copy2(
        source_path,
        destination_path,
    )

    return destination_path


def publishing_succeeded(
    source_path,
    destination_path,
):
    """
    Verify that the published file exists and its
    size matches the validated encoded source.
    """

    source_path = Path(source_path)
    destination_path = Path(destination_path)

    if not destination_path.exists():
        return False

    if destination_path.stat().st_size == 0:
        return False

    return (
        source_path.stat().st_size
        == destination_path.stat().st_size
    )

def build_tv_destination(
    item: ManifestItem,
    library_root,
):
    library_root = Path(library_root)

    if not item.show_name:
        raise ValueError(
            "Cannot publish TV episode "
            "without a show name."
        )

    if not item.year:
        raise ValueError(
            f"Cannot publish {item.show_name} "
            "without a year."
        )

    if not item.season:
        raise ValueError(
            f"Cannot publish {item.show_name} "
            "without a season."
        )

    if not item.episode:
        raise ValueError(
            f"Cannot publish {item.show_name} "
            "without an episode."
        )

    if not item.episode_title:
        raise ValueError(
            f"Cannot publish {item.show_name} "
            "without an episode title."
        )

    season_number = int(item.season)
    episode_number = int(item.episode)

    show_folder = (
        f"{item.show_name} ({item.year})"
    )

    season_folder = (
        f"Season {season_number:02d}"
    )

    filename = (
        f"{show_folder} - "
        f"S{season_number:02d}"
        f"E{episode_number:02d} - "
        f"{item.episode_title}.mkv"
    )

    return (
        library_root
        / "TV Shows"
        / show_folder
        / season_folder
        / filename
    )