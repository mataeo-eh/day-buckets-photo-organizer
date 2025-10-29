import os
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from Logging_Funct import setup_logging
from pprint import pformat
from collections import OrderedDict

files_for_report_count = 0  # Counter for more accurate tracking of how many files are looped over for report generation

def reports(args, dir=None):
    global files_for_report_count
    if dir == None: dir = Path.cwd()/args.dest
    data = OrderedDict() # Initialize an ordered dict object
    directory_size_sum=0 # Counter for size of files in directory. Will be reset for each directory
    directory_files_count=0 # Counter for number of files in a directory. Will reset for each directory
    logging.debug(f"Iterating through {dir} to see if directory or file (reports function)")
    for subdir in sorted(dir.iterdir()):
        if subdir.is_dir():
            if subdir.name == "logs" or subdir.name == "reports":
                logging.debug("Skipping logs folder in recursion")
                continue
            logging.debug(f"{subdir} is a directory, new dictionary nested. Continuing recursively until file found")
            # Below starts the recursion
            sub_data = reports(args, subdir)
            if sub_data: data[subdir.name] = sub_data # Only include folders that contain files
        elif subdir.is_file():
            timestamp=(datetime.fromtimestamp(subdir.stat().st_mtime)).strftime("%c")
            directory_size_sum+=subdir.stat().st_size
            directory_files_count+=1
            files_for_report_count+=1
            logging.info(f"File was found. New key:value pair entered into data dictionary as {subdir.name}:{(datetime.fromtimestamp(subdir.stat().st_mtime)).strftime("%c")}")
            data[f"{subdir.name}"] = timestamp
    if directory_files_count >=1:
        data["__dir_size__"] = f"{directory_size_sum/(1024**2):.2f}MB"
        data["__file_count__"] = directory_files_count
    logging.debug(f" the final dictionary is now {pformat(data)}")
    logging.info(f"Dictionary of data for report compiled and returned.")
    return data

# Function to properly call the helper functions based on CLI modifiers
def create_report(args,):
    data = reports(args) # Calls the data generating function and saves the returned nested dictionary
    if args.md: # Calls the md creating helper function if --md passed in CLI
        md_text = generate_human_readable(data)
        md_file = Path(args.dest) / "reports" / "report.md"
        md_file.parent.mkdir(parents=True, exist_ok=True)
        logging.debug(f"markdown report file created")
        with open(md_file, "w") as f:
            f.write(md_text) # Creates the MD file
        logging.info(f"markdown report saved to {md_file}")
    if args.json: #Calls the .json producing helper function if --json passed in CLI
        json_file = Path(args.dest) / "reports" / "manifest.json"
        report_json = generate_machine_readable_json(data, args)
        with open(json_file, "w") as f:
            json.dump(report_json, f, indent=4) # Creates the .json files
        logging.info(f"JSON report file created and saved to {json_file}")

# Helper function for smart unit conversion of file byte size
def bytes_to_human_readable(num_bytes):
    #Convert bytes to human-readable string (B, KB, MB, GB).
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            logging.info(f"{num_bytes:.2f}{unit} in file")
            return f"{num_bytes:.2f}{unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f}TB"

# Function to generate a markdown report of the files for human readability
def generate_human_readable(data, path_prefix=""):
    # Recursively generate Markdown tables for each day in nested dictionary data.
    # Sorted chronologically by day.
    md_output = ""
    # Separate day-level entries from subfolders
    day_entries = []
    subfolders = []
    for key, value in data.items():
        if isinstance(value, dict) and "__file_count__" in value:
            day_entries.append((key, value))
            logging.info(f"new day entry added to markdown report file")
        elif isinstance(value, dict):
            subfolders.append((key, value))
    numeric_files = [(k, v) for k, v in day_entries if k.isdigit()] # Separate numeric day folders vs other folders
    other_files = [(k, v) for k, v in day_entries if not k.isdigit()] # Separate numeric day folders vs other folders
    numeric_files.sort(key=lambda x: int(x[0])) # Sort numeric days numerically
    sorted_day_entries = numeric_files + other_files # Keep other_days in their original order (or sort alphabetically if preferred)
    for day_key, day_value in sorted_day_entries: # Generate tables for each day
        day_path = f"{path_prefix}/{day_key}" if path_prefix else day_key
        logging.debug("Day path created in .md report for all folders in args.dest target folder")
        trimmed_path = "/".join(day_path.split("/")[1:]) if "/" in day_path else day_path  # Trim off the root (first folder) for the table
        logging.debug("Created a trimmed path without the parent directory included for prettier report table creation for .md report")
        human_readable_date = trimmed_path # Convert YYYY/MM/DD into human-readable format
        try:
            parts = trimmed_path.split("/")
            if len(parts) >= 3:
                year, month, day = parts[0], parts[1], parts[2]
                dt = datetime(int(year), int(month), int(day))
                human_readable_date = dt.strftime("%b %d, %Y")  # e.g., Sep 20, 2025
                logging.debug("Changed date for .md report into a more human reading friendly format")
        except Exception as e:
            logging.warning(f"Could not parse date from {trimmed_path}: {e}")
        md_report_header = f"{path_prefix}/{day_key}" if path_prefix else day_key
        logging.debug("Created header for .md report")
        file_count = day_value.get("__file_count__", 0)
        logging.debug("File count set from data table already generated")
        total_bytes_str = day_value.get("__dir_size__", "0B")
        if isinstance(total_bytes_str, (int, float)):  # Convert total bytes to human-readable using helper function
            total_bytes_str = bytes_to_human_readable(total_bytes_str)
            logging.debug("Converted the byte size of the folder back to bytes and set it")
        mtimes = [ # Collect mtimes
            datetime.strptime(ts, "%c")
            for f, ts in day_value.items()
            if f not in ["__file_count__", "__dir_size__"]
        ]
        logging.debug(f"collected list of mtimes for each file in day folder to sort through for markdown report")
        earliest = min(mtimes).strftime("%B %d, %Y %H:%M:%S") if mtimes else "N/A"
        latest = max(mtimes).strftime("%B %d, %Y %H:%M:%S") if mtimes else "N/A"
        logging.debug(f"Found min mtime {earliest} and max mtime {latest}")
        headers = ["Date", "File Count", "Total Size", "Earliest mtime", "Latest mtime"] # Prepare table data
        rows = [[human_readable_date, str(file_count), total_bytes_str, earliest, latest]]
        logging.debug(f"table headers and rows prepped")
        col_widths = [max(len(row[i]) for row in [headers] + rows) for i in range(len(headers))]  # Compute max width for each column
        logging.debug(f"max column width calculated for table formatting")
        # Build Markdown table with aligned columns
        md_output += f"### {md_report_header}\n\n" 
        md_output += "| " + " | ".join(f"{headers[i]:{col_widths[i]}}" for i in range(len(headers))) + " |\n"
        md_output += "|-" + "-|-".join("-"*w for w in col_widths) + "-|\n"
        logging.debug(f"built markdown table using column alignment")
        for row in rows:
            md_output += "| " + " | ".join(f"{row[i]:{col_widths[i]}}" for i in range(len(headers))) + " |\n"
            logging.debug(f"Added extra rows to report as needed")
        md_output += "\n"
    # Recurse into subfolders
    for sub_key, sub_value in subfolders:
        new_prefix = f"{path_prefix}/{sub_key}" if path_prefix else sub_key
        logging.debug(f"recoursed into subfolders as necessary to produce markdown table report for every day folder present")
        md_output += generate_human_readable(sub_value, new_prefix,)
    logging.debug(f"Markdown report fully generated")
    return md_output




# Function to create a machine readable report .json file 
def generate_machine_readable_json(data, args, path_prefix=None,):
    # Recursively generate a machine-readable JSON structure with:
    # - File count
    # - Total size (in bytes)
    # - Earliest and latest mtime
    # Keeps the nested folder structure.
    report_json = {} # Create empty dictionary variable for later use
    # Ensure the relative path starts from args.dest target passed in CLI
    if path_prefix is None:
        path_prefix = args.dest if args else "" # Start path with the top-level project folder if args.dest not passed
    # Separate day-level entries from subfolders and create their empty variables for later use
    day_entries = []
    subfolders = []
    logging.debug(f"{report_json}, {day_entries}, and {subfolders} created/updated")
    for key, value in data.items():
        if isinstance(value, dict) and "__file_count__" in value:
            day_entries.append((key, value))
            logging.debug("day entries object updated ")
        elif isinstance(value, dict):
            subfolders.append((key, value))
            logging.debug("subfolders object updated")
    numeric_files = [(k, v) for k, v in day_entries if k.isdigit()] # Separate numeric day folders vs other folders
    other_files = [(k, v) for k, v in day_entries if not k.isdigit()] # Separate numeric day folders vs other folders
    numeric_files.sort(key=lambda x: int(x[0])) # Sort numeric days numerically
    sorted_day_entries = numeric_files + other_files # Keep other_days in their original order (or sort alphabetically if preferred)
    logging.info("day_entries object sorted by day integer in decreasing order")
    for day_key, day_value in sorted_day_entries:  # Process day-level entries
        day_path = f"{path_prefix}/{day_key}" if path_prefix else day_key
        file_count = day_value.get("__file_count__", 0)
        total_bytes = day_value.get("__dir_size__", 0)
        logging.debug("entries for each day processed to put into .json file")
        if isinstance(total_bytes, str) and total_bytes.endswith("MB"): # Convert human-readable MB string back to bytes if necessary
            total_bytes = float(total_bytes.replace("MB", "")) * 1024**2
            logging.debug("Human readable bytes cinverted to bytes if needed")
        elif isinstance(total_bytes, str) and total_bytes.endswith("GB"):
            total_bytes = float(total_bytes.replace("GB", "")) * 1024**3
            logging.debug("Human readable bytes cinverted to bytes if needed")
        # Collect mtimes
        mtimes = [
            datetime.strptime(ts, "%c")
            for f, ts in day_value.items()
            if f not in ["__file_count__", "__dir_size__"]
        ]
        logging.debug("Mtimes collected for .json report")
        earliest = min(mtimes).isoformat() if mtimes else None
        latest = max(mtimes).isoformat() if mtimes else None
        logging.debug("earliest and latest mtimes found and stored as variables for .json report")
        # Build folder summary
        folder_entry = {
            "path": day_path,
            "file_count": file_count,
            "total_bytes": int(total_bytes),
            "earliest_mtime": earliest,
            "latest_mtime": latest,
            "files": []
        }
        logging.debug("summary of folder created")
        # Add each file in this folder
        for f, ts in day_value.items():
            if f in ["__file_count__", "__dir_size__"]:
                logging.warning("directories that do not contain files skipped in .json report building")
                continue
            file_rel_path = f"{day_path}/{f}"
            file_mtime = datetime.strptime(ts, "%c").isoformat()
            file_size = None
            logging.debug("file path and size for each file retrieved for .json report")
            # Look up size of each file from the actual filesystem 
            try:
                abs_path = Path(args.dest) / Path(file_rel_path).relative_to(args.dest)
                if abs_path.exists():
                    file_size = abs_path.stat().st_size
                    logging.debug("File size retrieved from system for .json report")
            except Exception:
                file_size = 0
            folder_entry["files"].append({
                "path": file_rel_path,
                "size": file_size,
                "mtime": file_mtime
            })
            logging.debug(f"files key in folder dictionary of .json reported filled with path, size, and mtime of each file within the folder")
        report_json[day_key] = folder_entry # Add the entire folder entry to the report
        logging.debug("Built the .json report dictionary")
    # Recurse into subfolders
    for sub_key, sub_value in subfolders:
        new_prefix = f"{path_prefix}/{sub_key}" if path_prefix else sub_key
        logging.debug("Recurse into subfolders if they have files in them")
        sub_report = generate_machine_readable_json(sub_value, new_prefix, args)
        if sub_report:  # Only include folders that have files
            logging.debug("Should only trigger for subfolders with files in them eventually")
            report_json[sub_key] = sub_report
    return report_json


# Only used for file creation and debugging. Not used in the production code. Kept in case further debugging needed.
if __name__ == "__main__":
    #file_directory = os.path.join(os.getcwd(), "PROJECT")
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
    create_report(args)

