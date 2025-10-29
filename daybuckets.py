import os
import sys
import logging
import argparse
from pathlib import Path
from Logging_Funct import setup_logging
from Fetch_Category_Members import get_all_category_members
from Download_Files import save_files_and_data
from Sort_Files import file_to_sort
from Report_Generate import create_report, files_for_report_count

# Function that begins the call for all the other functions based on the CLI arguments passed 
def args_command(args):
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
    logging.info(f"Fetching category '{args.category}' into {args.dest}") # Starts the logging by saying what category is being fetched
    # Calls the function that grabs the different files within the requested category
    files = get_all_category_members(_seen=None,category=args.category, limit=args.limit) 
    # Tells how many files were found and logged from the requested category after they are fetched
    logging.info(f"Found {len(files)} files in category {args.category}")
    # Downloads the file and meta data of each file retrieved from the category by calling the downloading function
    for f in files:
        save_files_and_data(f, args.dest, args.dry_run)
    logging.info(f"saved image and metadata for {len(files)} files in category {args.category}")
    # Calls the file moving and sorting function if requested in the CLI command provided
    if args.mode: 
        file_to_sort(args)
        logging.info(f"{args.mode} performed on {len(files)} total files")
    # Calls the report generating function if requested
    if args.md or args.json:
        create_report(args)
        logging.info(f"data to collect from {files_for_report_count} total files for report generation")

# The main function with the different argparse commands
def main():
    parser = argparse.ArgumentParser(description="Daybuckets utility")
    subparsers = parser.add_subparsers(dest="command")
    # Delineates the different CLI modifiers that can be passed and gives a helpful tip for what they do below is for fetching
    fetch_parser = subparsers.add_parser("fetch", help="Fetch files from Wikimedia Commons by category")
    fetch_parser.add_argument("--category", required=True, help="Category name (e.g., 'Cathedrals')")
    fetch_parser.add_argument("--dest", default="PROJECT", help="Destination folder")
    fetch_parser.add_argument("--limit", type=int, default=None, help="Max number of files to fetch")
    fetch_parser.add_argument("--dry-run", action="store_true", help="Do everything except download")
    fetch_parser.add_argument("--verbose", action="store_true", help="Log prints to terminal and saves to log file")
    fetch_parser.add_argument("--mode", choices=["move","copy"], help="Optional argument. Would you like to 'copy' or 'move' the data")
    fetch_parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging to help program debugging")
    fetch_parser.add_argument("--clearLog", action="store_true", help="Set to clear the log manually, or let the log files clear weekly")
    fetch_parser.add_argument("--moveType", choices=["keepboth","keepnew","keepold"], help="Would you like to 'keepboth' files, only 'keepnew' file, or 'keepold' file and delete the new file")
    fetch_parser.add_argument("--md", action="store_true", help="Creates a human-readable markdown file report")
    fetch_parser.add_argument("--json", action="store_true", help="Creates a machine-readable .json file report")

    fetch_parser.set_defaults(func=args_command) # The first argument passed should be 'fetch' for fetching the files - then runs the arg command

    # A new parser subclass for organizing without fetching
    organize_parser = subparsers.add_parser("organize", help="Organize existing files")
    organize_parser.add_argument("--verbose", action="store_true", help="Log prints to terminal and saves to log file")
    organize_parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging to help program debugging")
    organize_parser.add_argument("--clearLog", action="store_true", help="Set to clear the log manually, or let the log files clear weekly")
    organize_parser.add_argument("--mode", choices=["move","copy"], help="Optional argument. Would you like to 'copy' or 'move' the data")
    organize_parser.add_argument("--moveType", choices=["keepboth","keepnew","keepold"], help="Would you like to 'keepboth' files, only 'keepnew' file, or 'keepold' file and delete the new file")
    organize_parser.add_argument("--dest", default="PROJECT", help="Destination folder")
    organize_parser.add_argument("--md", action="store_true", help="Creates a human-readable markdown file report")
    organize_parser.add_argument("--json", action="store_true", help="Creates a machine-readable .json file report")
    # A new parser subclass for creating reports without fetching


    report_parser = subparsers.add_parser("report", help="Organize existing files")
    report_parser.add_argument("--verbose", action="store_true", help="Log prints to terminal and saves to log file")
    report_parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging to help program debugging")
    report_parser.add_argument("--clearLog", action="store_true", help="Set to clear the log manually, or let the log files clear weekly")
    report_parser.add_argument("--dest", default="PROJECT", help="Destination folder")
    report_parser.add_argument("--md", action="store_true", help="Creates a human-readable markdown file report")
    report_parser.add_argument("--json", action="store_true", help="Creates a machine-readable .json file report")

    # Sets the args variable to the parser class so it can be used throughout the other code files and have the attributes defined above
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        logging.critical(f"Argument not passed, program closed. {parser}")
        sys.exit(1)

    args.func(args)


    
# A safety check so the program only runs if called as the main file, it will not run if it is called from a different file
if __name__ == "__main__":
    main()
