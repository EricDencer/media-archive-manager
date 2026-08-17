from pathlib import Path

from models import DVDBackup


def find_dvd_backups(root_path):
    root = Path(root_path)

    dvd_backups = []

    for ifo_file in root.rglob("VIDEO_TS/VIDEO_TS.IFO"):

        video_ts = ifo_file.parent
        disc_path = video_ts.parent

        backup = DVDBackup(
            name=disc_path.name,
            path=disc_path,
            ifo_path=ifo_file,
        )

        dvd_backups.append(backup)

    return dvd_backups