import os
import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler as trfh
import time


# A function to convert a timestamp to UTC time
def utc_time_conversion(*args):
    return time.gmtime(*args)


# A function to set up the logging
def setup_logging(args,):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO) 
    folder = f"PROJECT/logs/"
    if args.dest is None:
        args.dest = os.path.join(os.getcwd(), folder)
    log_dir = Path(args.dest) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logfile = log_dir / "daybuckets.log"

    # Clear any old handlers to prevent duplicates if setup_logging is called again
    logger.handlers.clear()

# Rotate the log file every day and only keep 7 days worth of log files
    timed_handler = trfh(
        logfile,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )

    formatter = logging.Formatter( # The format of the logged messages
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt = "%Y-%m-%dT%H:%M:%SZ" # ISO style timestamp for each log entry
    )
    formatter.converter = utc_time_conversion
    timed_handler.setFormatter(formatter)
    logger.addHandler(timed_handler)
    logger.info(f"Logging to {logfile}") # Creates a logging message saying the logging is being sent to the log file
    if args.verbose: # Makes the verbose CLI modifier also print the logging messages to the terminal
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        logger.info(f"Logs print to terminal as well as logfile with --verbose passed in CLI")
    return logfile