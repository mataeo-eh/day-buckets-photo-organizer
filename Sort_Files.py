import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import shutil
from Download_Files import parse_fallback_datetime
import argparse
from Logging_Funct import setup_logging

cwd = os.getcwd() #Define the current working directory globally for functions in this file
# Function to convert a datetime to a UTC based ISO string.
def to_utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None: # if no timezone, set timezone to use UTC time
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc) # Even if there is a timezone, set the timezone to UTC timezone from whatever timezone it was
    return dt.isoformat().replace("+00:00", "Z") # Return the mtime format, formatted properly

# Function to choose which files are wanted for sorting
def file_to_sort(args):
    incoming_path = Path(cwd) / args.dest/ "incoming" # Sets the path to the incoming folder (which is where fetched files go)
    if not incoming_path.exists(): # Checks the incoming path was set correctly and adds the check to the logging for debugging help
        logging.warning(f"Incoming folder {incoming_path} does not exist. Nothing to sort.")
        return
    json_files = list(incoming_path.glob("*.json"))
    if not json_files: # Adds check for .json files being found to the log for debugging
        logging.warning(f"No JSON files found in {incoming_path}, skipping sorting")
        return
    for json_file in json_files:
        with open(json_file, "r") as f:
            meta = json.load(f) # Get the meta data from each json file being sorted
        # Extract canonical timestamp from metadata
        raw_ts = meta.get("extmetadata", {}).get("DateTimeOriginal") or meta.get("upload_timestamp")
        logging.info(f"raw timestamp {raw_ts} gathered")
        if not raw_ts:
            logging.warning(f"No timestamp in {json_file}, skipping")
            continue
        file_mtime = parse_fallback_datetime(raw_ts)  # robust time parsing using helper function
        logging.info(f"Helper function used for robust timeparsing to get file mtime {file_mtime}")
        if not file_mtime:
            logging.warning(f"Could not parse timestamp {raw_ts} in {json_file}, skipping")
            continue
        # Build base name to find matching image
        base_name = json_file.stem.replace(".meta", "")
        image_extensions = [".jpg", ".jpeg", ".png"]
        images = [incoming_path / (base_name) for ext in image_extensions if (incoming_path / (base_name)).exists() and (incoming_path / (base_name)).suffix == ext]
        # Combine JSON + images for pairing
        files_to_sort = [json_file] + images
        # Sort all files (JSON + images) with same timestamp
        logging.debug(".json files paired with matching image to prep for moving in sort")
        for f in files_to_sort:
            sort_files(f, args, file_mtime)
        logging.info(f"{args.mode} performed on {len(files_to_sort)} files")

# Function to determine if the file should be moved or copied and calls the appropriate helper function
def sort_files(file, args, file_mtime):
    file_path = os.path.abspath(file)
    PROJECT_path = os.path.join(cwd, args.dest)
    filename = os.path.basename(file)
    new_dir_path = os.path.join(PROJECT_path, f"buckets/{file_mtime.year}/{file_mtime.strftime('%m')}/{file_mtime.day}")
    new_file_path = os.path.join(new_dir_path, filename)
    logging.info(f"new filepath {new_file_path} created for {file}")
    try:
        new_file_path = sorter_function(file_path, new_dir_path, new_file_path, args)
        if args.mode == "move":
            if args.moveType.lower().strip() == "keepold":
                logging.info(f"Skipping move for {file_path.name} (keepold modeType)")
                return # Skips the move if keepold is passed
            else:
                shutil.move(file_path, new_file_path) # Moves the file to its new location
                logging.info(f"{filename} successfully moved from {file_path} to {new_file_path}")
        elif args.mode == "copy":
            shutil.copy2(file_path, str(new_file_path)) # Copies the file to its new location
            logging.info(f"{filename} successfully copied from {file_path} to {new_file_path}")
    except Exception as e:
        logging.warning(f"Error sorting {file_path}: {e}")
    finally:
        if os.path.exists(new_file_path):
            ts = file_mtime.replace(tzinfo=timezone.utc).timestamp() 
            os.utime(new_file_path, (ts, ts)) # Sets the mtime of the file after moving to ensure mtime consistency
            logging.info(f"Set UTC mtime of {filename} to {to_utc_iso(file_mtime)}")
        else:
            logging.warning(f"File {new_file_path} does not exist to have mtime reset")
    
def sorter_function(file, new_dir_path, new_file_path, args):
    filename = os.path.basename(file)
    base, ext = os.path.splitext(filename)
    counter = 1
    file_path = os.path.abspath(file)
    if not os.path.exists(new_dir_path):
        os.makedirs(new_dir_path, exist_ok=True)
        logging.info(f"new directory {new_dir_path} created. ")
    if os.path.exists(new_file_path):
        if not args.moveType:
            keep=input(f"Would you like to keep both copies of {new_file_path.name}? If no, the newly saved file will be deleted. \n if replace, the new file will replace the old file: 'y' or 'n' or 'r': \n ")
        if args.moveType.lower().strip() == "keepboth":
            keep = "y" 
        if args.moveType.lower().strip() == "keepnew":
            keep = "r"
        if args.moveType.lower().strip() == "keepold":
            keep = "n"
        if keep.lower() == "n":
            os.remove(file_path) # Deletes the new file if user did not want to keep both copies
            logging.info(f"User does not want both copies. New file deleted from origin. ")
            return new_file_path
        elif keep.lower() == "r":
            os.remove(new_file_path) # Removes the file the user wants to replace to prep for moving the new file to its spot
            logging.info(f"Existing file {new_file_path.name} will be removed")
            return new_file_path
        elif keep.lower() == "y":
            candidate_path=new_file_path
            while os.path.exists(candidate_path): # Loops to continue incrementing the name hash if multiple collisions are found
                candidate_path = os.path.join(new_dir_path, f"{base}_{counter}{ext}") # Renames colliding file
                counter +=1 # Increments counter to continue avoiding name collisions if repeat name collisions occur
                logging.info(f"File {new_file_path} already exists. Name hash added to file. Kept as {candidate_path}")
            return candidate_path
    return new_file_path
    
if __name__ == "__main__":
    logging.debug(f"Initiate an args object for debugging running only this file")
    args=argparse.Namespace()
    args.dest = "PROJECT"
    args.debug=True
    args.verbose = False
    args.clearLog = True
    args.md = True
    args.json = True
    if args.clearLog: # Clears the log files if the user passes the --clearlog modifier
        if args.dest is None: # Sets the default location to check for an existing log if no location is provided
            folder = f"PROJECT/logs/"
            dest = os.path.join(os.getcwd(), folder)
            log_dir = Path(dest) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True) # Ensures a logs directory will exist by creating one if one was not there
        else:
            log_dir = Path(args.dest) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True) # If a location was provided, creates a log directory in case one was not there
        if os.path.exists(log_dir):
            for logfile in Path(log_dir).iterdir(): # Iterates through all the log files in the logs directory and deletes them in case there are multiple log files
                os.remove(logfile)
        logging.info(f"removed pre-existing log file(s)")
    logfile = setup_logging(args,) # Calls the function that starts appending to the log file
    logging.debug(f"Logging started for test run of report generation")
    file_to_sort(args)