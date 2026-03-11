import argparse
import os
import shutil
import filecmp
import logging
import sys
import time

def natural_int(value: int | str) -> int:
    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' must be natural integer")
    if value <= 0:
        raise argparse.ArgumentTypeError(f"'{value}' must be larger than 0")
    return value

def parse_args():
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

def sync_dirs(logger: logging.Logger, source: str, replica: str):
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source folder '{source}' does not exist!")
    if not os.path.exists(replica):
        print(f"Destination folder '{replica}' does not exist, creating...")
        os.mkdir(replica)

    items_to_check = []
    for root, dirs, files in os.walk(source):
        for dir in dirs:
            items_to_check.append(os.path.join(root, dir))
        for file in files:
            items_to_check.append(os.path.join(root, file))

    for source_path in items_to_check:
        replica_path = os.path.join(replica, os.path.relpath(source_path, source))

        if os.path.isdir(source_path):
            if not os.path.exists(replica_path):
                logger.info(f"Copying {source_path} to {replica_path}")
                os.makedirs(replica_path)
            continue
        if (os.path.isfile(source_path)
            and not os.path.exists(replica_path)
            or not filecmp.cmp(source_path, replica_path, shallow=False)):

            logger.info(f"Copying {source_path} to {replica_path}")
            shutil.copy2(source_path, replica_path)

    items_to_delete = []
    for root, dirs, files in os.walk(replica, topdown=False):
        for dir in dirs:
            items_to_delete.append(os.path.join(root, dir))
        for file in files:
            items_to_delete.append(os.path.join(root, file))

    for replica_path in items_to_delete:
        source_path = os.path.join(source, os.path.relpath(replica_path, replica))

        if os.path.isdir(replica_path) and not os.path.exists(source_path):
            logger.info(f"Deleting dir {replica_path}")
            os.rmdir(replica_path)
        elif (not os.path.exists(source_path)
                and os.path.isfile(replica_path)):
            logger.info(f"Deleting file {replica_path}")
            os.remove(replica_path)


def main(args):
    logger = setup_logger(args.log)
    count = 0
    try:
        while count < args.syncs:
            count += 1
            logger.info(f"Sync starting...")

            start_time = time.time()
            sync_dirs(logger, args.source, args.replica)
            end_time = time.time()
            sync_duration = end_time - start_time

            if count < args.syncs:
                time.sleep(args.interval - sync_duration)
            else:
                logger.info(f"Sync finished")
    except FileNotFoundError as e:
        logger.error(e)
    except KeyboardInterrupt:
        logger.error("Ctrl+C")


if __name__ == '__main__':
    main(parse_args())
