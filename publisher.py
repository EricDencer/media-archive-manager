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

# -------- 
# Test Run 
# ----- 
if __name__ == "__main__":

    from manifest import load_manifest

    manifest_path = "manifest.csv"

    items = load_manifest(
        manifest_path
    )

    item = next(
        item
        for item in items
        if (
            item.disc == "Sci Fi 1a"
            and item.title == 0
        )
    )

    source_path = (
        "/home/ericdencer/Video Archive/"
        "encoded/Sci Fi 1a/"
        "Horrors of Spider Island.mkv"
    )

    library_root = (
        "/home/ericdencer/Video Archive/plex"
    )

    destination_path = publish_movie(
        item,
        source_path,
        library_root,
    )

    success = publishing_succeeded(
        source_path,
        destination_path,
    )

    print(
        f"Publishing success: {success}"
    )

    print(
        f"Destination: {destination_path}"
    )