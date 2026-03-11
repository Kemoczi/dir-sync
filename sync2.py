""" Pylint satisfier """
import argparse
import os
import shutil
import filecmp
import logging
import sys
import time
import pathlib

def natural_int(value: int | str) -> int:
    """ Pylint satisfier """
    try:
        value = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"'{value}' must be natural integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError(f"'{value}' must be larger than 0")
    return value


def parse_args():
    """ Pylint satisfier """
    parser = argparse.ArgumentParser(
        description="Specify source and replica dirs, sync interval and number of syncs"
    )
    parser.add_argument("source", help="Path to source dir", type=str)
    parser.add_argument("replica", help="Path to replica dir", type=str)
    parser.add_argument("interval", help="Sync interval", type=natural_int)
    parser.add_argument("syncs", help="Number of synchronizations", type=natural_int)
    parser.add_argument("log", help="Path to log file", type=str)

    return parser.parse_args()

def setup_logger(logfile: str) -> logging.Logger:
    """ Pylint satisfier """
    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')

    if not logger.handlers:
        file_handler = logging.FileHandler(logfile, 'w')
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def sync(source: pathlib.Path, replica: pathlib.Path):
    """ Pylint satisfier """
    logger = logging.getLogger('logger')
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source folder '{source}' does not exist!")
    if not os.path.exists(replica):
        logger.info("Destination folder '%s' does not exist, creating...", replica)
        os.mkdir(replica)

    for root, dirs, files in os.walk(source):
        for dirname in dirs:
            source_path = os.path.join(root, dirname)
            replica_path = os.path.join(replica, os.path.relpath(source_path, source))
            if not os.path.exists(replica_path):
                logger.info("Copying directory %s to %s", source_path, replica_path)
                os.makedirs(replica_path)
        for file in files:
            source_path = os.path.join(root, file)
            replica_path = os.path.join(replica, os.path.relpath(source_path, source))
            if (not os.path.exists(replica_path)
                    or not filecmp.cmp(source_path, replica_path, shallow=False)):
                logger.info("Copying file %s to %s", source_path, replica_path)
                shutil.copy2(source_path, replica_path)

    for root, dirs, files in os.walk(replica, topdown=False):
        for dirname in dirs:
            replica_path = os.path.join(root, dirname)
            source_path = os.path.join(source, os.path.relpath(replica_path, replica))
            if not os.path.exists(source_path):
                logger.info("Deleting directory %s", replica_path)
                os.rmdir(replica_path)
        for filename in files:
            replica_path = os.path.join(root, filename)
            source_path = os.path.join(source, os.path.relpath(replica_path, replica))
            if not os.path.exists(source_path):
                logger.info("Deleting file %s", replica_path)
                os.remove(replica_path)

def main(args):
    """ Pylint satisfier """
    logger = setup_logger(args.log)
    count = 0
    try:
        while count < args.syncs:
            count += 1
            logger.info("Sync %d/%d starting...", count, args.syncs)

            start_time = time.time()
            sync(args.source, args.replica)
            end_time = time.time()
            sync_duration = end_time - start_time

            if count < args.syncs:
                time.sleep(max(0, args.interval - sync_duration))
            else:
                logger.info("Sync finished")
    except FileNotFoundError as e:
        logger.error(e)
    except KeyboardInterrupt:
        logger.error("Ctrl+C")


if __name__ == '__main__':
    main(parse_args())
