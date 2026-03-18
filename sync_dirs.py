"""
Directory sync script - make exact copy of source folder

Usage:

python sync_dirs.py <arguments>

Mandatory arguments (ordered):
    1. source - path to source folder
    2. replica - path to replica folder
    3. interval - interval between synchronizations (in seconds or hh:mm:ss)
    4. syncs - amount of synchronizations
    5. log - path to log file

Optional arguments:
--excluded - excluded paths

"""
import argparse
import os
import shutil
import filecmp
import logging
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_logger(logfile: Path) -> None:
    """ Configure logger format and handlers to log both to console and file """
    logger.setLevel(logging.INFO)
    logfile.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')

    logger.handlers.clear()
    file_handler = logging.FileHandler(logfile, "w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def natural_int(value: int | str) -> int:
    """ Type created to make sure that numerical arguments are natural integers above 0 """
    try:
        value = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"must be natural integer, got '{value}'") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError(f"must be larger than 0, got '{value}'")
    return value


def parse_interval(interval: str) -> int:
    """ Parser enabling user to set time interval in hh:mm:ss format (or h:m:s) """
    interval = str(interval)
    if ":" in interval:
        parts = interval.split(":")
        try:
            if len(parts) == 3:
                parsed_interval = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                parsed_interval = int(parts[0]) * 60 + int(parts[1])
            else:
                raise argparse.ArgumentTypeError("Use seconds or hh:mm:ss for interval")
            return natural_int(parsed_interval)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"must contain natural integers, got '{interval}'"
            ) from exc

    return natural_int(interval)


def parse_args() -> argparse.Namespace:
    """ Just an argument parser """
    parser = argparse.ArgumentParser(
        description="Specify source and replica dirs, sync interval and number of syncs"
    )
    parser.add_argument("source", help="path to source folder", type=Path)
    parser.add_argument("replica", help="path to replica folder", type=Path)
    parser.add_argument("interval", help="interval between synchronizations", type=parse_interval)
    parser.add_argument("syncs", help="amount of synchronizations", type=natural_int)
    parser.add_argument("log", help="path to log file", type=Path)
    parser.add_argument("--excluded", nargs="*", help="excluded paths", type=Path)

    # This way script will execute even if too many arguments will be added
    # args, unknown = parser.parse_known_args()
    # return args
    return parser.parse_args()


def copy_items(source: Path, replica: Path, excluded: set[Path]) -> None:
    """ This function handles copying files and creating directories in replica """
    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        for dirname in dirs:
            source_path = root_path / dirname
            replica_path = replica / source_path.relative_to(source)
            if source_path.resolve() in excluded:
                continue
            if not replica_path.exists():
                try:
                    logger.info("Copying directory '%s' to '%s'", source_path, replica_path)
                    replica_path.mkdir(parents=True, exist_ok=True)
                except (FileNotFoundError, PermissionError, OSError) as exc:
                    logger.error("Problem with copying directory '%s': %s", source_path, exc)
        for filename in files:
            source_path = root_path / filename
            replica_path = replica / source_path.relative_to(source)
            if source_path.resolve() in excluded:
                continue
            try:
                if (not replica_path.exists()
                    or (replica_path.stat().st_size != source_path.stat().st_size)
                    or (replica_path.stat().st_mtime != source_path.stat().st_mtime)
                    or not filecmp.cmp(source_path, replica_path, shallow=False)):
                    logger.info("Copying file '%s' to '%s'", source_path, replica_path)
                    shutil.copy2(source_path, replica_path)
            except (FileNotFoundError, PermissionError, OSError) as exc:
                logger.error("Problem with copying file '%s': %s", source_path, exc)


def delete_items(source: Path, replica: Path, excluded: set[Path]) -> None:
    """ This function handles deleting files/directories in replica if they don't exist in source """
    for root, dirs, files in os.walk(replica, topdown=False):
        root_path = Path(root)
        for dirname in dirs:
            replica_path = root_path / dirname
            source_path = source / replica_path.relative_to(replica)
            if replica_path.resolve() in excluded:
                continue
            if not source_path.exists():
                try:
                    logger.info("Deleting directory '%s'", replica_path)
                    shutil.rmtree(replica_path)
                except (FileNotFoundError, PermissionError, OSError) as exc:
                    logger.error("Problem with deleting directory '%s': %s", replica_path, exc)

        for filename in files:
            replica_path = root_path / filename
            source_path = source / replica_path.relative_to(replica)
            if replica_path.resolve() in excluded:
                continue
            if not source_path.exists():
                try:
                    logger.info("Deleting file '%s'", replica_path)
                    replica_path.unlink()
                except (FileNotFoundError, PermissionError, OSError) as exc:
                    logger.error("Problem with deleting file '%s': %s", replica_path, exc)


def sync(source: Path, replica: Path, excluded: set[Path] | None = None) -> None:
    """ Sync 'orchestrator' function """
    if excluded is None:
        excluded = set()
    if not source.exists():
        raise FileNotFoundError(f"Source folder '{source}' does not exist!")
    if not replica.exists():
        logger.info("Destination folder '%s' does not exist, creating...", replica)
        replica.mkdir(parents=True, exist_ok=True)

    copy_items(source, replica, excluded)
    delete_items(source, replica, excluded)


def main() -> None:
    """ Pylint satisfier """
    args = parse_args()
    excluded = {args.log.resolve()}
    if args.excluded is not None:
        excluded.update(path.resolve() for path in args.excluded)

    setup_logger(args.log)
    logger.info(
        "Starting synchronization of '%s' and '%s' directories, "
        "interval: %d seconds, "
        "amount of synchronizations: %d",
        args.source, args.replica, args.interval, args.syncs
    )

    count = 0

    try:
        while count < args.syncs:
            count += 1
            logger.info("Sync %d/%d started...", count, args.syncs)

            start_time = time.time()
            sync(args.source, args.replica, excluded)
            end_time = time.time()
            sync_duration = end_time - start_time
            logger.info("Sync %d/%d done, took %.2fs", count, args.syncs, sync_duration)

            if count < args.syncs:
                logger.info("Next sync in %.2fs...", max(0, args.interval - sync_duration))
                time.sleep(max(0, args.interval - sync_duration))
                # if we want the interval to start after completed sync we may go this way:
                # logger.info("Next sync in %ds...", args.interval)
                # time.sleep(args.interval)
            else:
                logger.info("Synchronization finished, logfile: %s", args.log)
    except FileNotFoundError as exc:
        logger.error(exc)
    except KeyboardInterrupt:
        logger.error("Ctrl+C")


if __name__ == '__main__':
        main()
