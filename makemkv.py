import subprocess

from models import DVDBackup, TitleInfo


def inspect_dvd(backup: DVDBackup):
    """
    Run MakeMKV in robot mode against a DVD backup.

    Robot mode (-r) gives us machine-readable TINFO/SINFO records
    instead of relying on MakeMKV's human-readable output.
    """

    command = [
        "makemkvcon",
        "-r",
        "info",
        f"file:{backup.ifo_path}",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    return result


def duration_to_seconds(duration: str) -> int:
    """
    Convert MakeMKV duration strings such as:

        1:14:39

    into total seconds.
    """

    hours, minutes, seconds = duration.split(":")

    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
    )


def parse_robot_titles(output: str):
    """
    Parse MakeMKV TINFO records into TitleInfo objects.

    MakeMKV produces multiple TINFO records for each logical title.
    We collect those records into one TitleInfo object per title.
    """

    titles = {}

    for line in output.splitlines():

        if not line.startswith("TINFO:"):
            continue

        # Separate the final quoted value from the TINFO fields.
        #
        # Example:
        # TINFO:0,9,0,"1:14:39"

        prefix, value = line.rsplit(",", 1)

        value = value.strip().strip('"')

        fields = prefix.split(",")

        title_index = int(fields[0].split(":")[1])
        attribute = int(fields[1])

        # First time we encounter this title, create it.
        if title_index not in titles:
            titles[title_index] = TitleInfo(
                index=title_index
            )

        title = titles[title_index]

        # Attribute 8 = chapter count
        if attribute == 8:
            title.chapters = int(value)

        # Attribute 9 = duration
        elif attribute == 9:
            title.duration = value
            title.duration_seconds = duration_to_seconds(value)

        # Attribute 11 = size in bytes
        elif attribute == 11:
            title.size_bytes = int(value)

        # Attribute 27 = MakeMKV output filename
        elif attribute == 27:
            title.output_filename = value

    return list(titles.values())