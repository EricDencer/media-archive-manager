import subprocess
from pathlib import Path

from models import DVDBackup, ManifestItem


def extract_title(
    backup: DVDBackup,
    item: ManifestItem,
    output_root,
):
    """
    Extract one DVD title with MakeMKV.

    The title is written into a disc-specific staging directory.
    """

    output_root = Path(output_root)

    output_dir = output_root / backup.name
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "makemkvcon",
        "-r",
        "mkv",
        f"file:{backup.ifo_path}",
        str(item.title),
        str(output_dir),
    ]

    print(
        f"Extracting {backup.name} "
        f"title {item.title}: {item.name}"
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    return result

def extraction_succeeded(
    backup: DVDBackup,
    item: ManifestItem,
    output_root,
) -> bool:
    """
    Verify that MakeMKV created the expected output file.
    """

    output_path = (
        Path(output_root)
        / backup.name
        / item.output_filename
    )

    return output_path.exists() and output_path.stat().st_size > 0