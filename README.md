*User Guide*
For use via command line interface first pass python3, then the main code file, daybuckets.py "python3 daybuckets.py"

There are 3 different "modes" of functions that can be selected and entered as the third argument. "fetch", "organize" or "report".

fetch has several modifiers that can be passed after it:
--category is required. The next word typed after is the category of images you would like to have fetched.
--dest is optional. If not passed will be set to "PROJECT" by default. The next word typed will be the folder all files fetched will be saved to.
--limit is optional. If passed, will limit the files fetched to the integer typed next.
**It is highly recommended to use a limit while fetching. The program will recursively search every category for subcategories and will fetch every file within every subcategory until the limit is readched. If no limit is passed there will be no limit. This can fetch a huge amount of files so be wary!!**
--dry-run is optional. If passed will not download and save files.
--verbose is optional. If passed will print all the logging messages to the terminal and save them to the log file.
--mode is optional. If passed the next word typed will be the organization mode you want to use. It has 2 choices.
    The mode choices are "move" and "copy". 
        Move will organize and move the files to a new location within the --dest target folder and delete them from the folder they were saved to.
        Copy will organize the files and copy them to the new location and keep them at the poriginally downloaded location.
--debug is optional. If passed it will log the logging.debug arguments as well as the other logging messages. Helpful for debugging.
--clearLog is optional. If passed will delete any pre-existing log files.
--moveType is optional. If passed will dictate what to do for every file when sorting if file name collisions happen. It has 3 choices.
    "keepboth" if passed next will keep both files and add a name hash to the newly sorted file
    "keepnew" if passed next will delete the pre-existing file and then sort the new file to its place
    "keepold" if passed next will delete the newly saved file
--md is optional. If passed a report.md markdown file report will be created and saved in the reports folder
--json is optional. If passed a manifest.json file report will be created and saved in the reports folder

Fetch is the most versatile able to fetch new files, organize and sort them, and create reports simultaneously.

organize has several modifiers that can be passed after it:
--verbose is optional. If passed will print all the logging messages to the terminal and save them to the log file.
--debug is optional. If passed it will log the logging.debug arguments as well as the other logging messages. Helpful for debugging.
--clearLog is optional. If passed will delete any pre-existing log files.
--mode is optional. If passed the next word typed will be the organization mode you want to use. It has 2 choices. Files will be sorted by date if a file modified time is able to be found and set for the file.
    The mode choices are "move" and "copy". 
        Move will organize and move the files to a new location within the --dest target folder and delete them from the folder they were saved to.
        Copy will organize the files and copy them to the new location and keep them at the poriginally downloaded location.
--moveType is optional. If passed will dictate what to do for every file when sorting if file name collisions happen. It has 3 choices.
    "keepboth" if passed next will keep both files and add a name hash to the newly sorted file
    "keepnew" if passed next will delete the pre-existing file and then sort the new file to its place
    "keepold" if passed next will delete the newly saved file
--dest is optional. If not passed will be set to "PROJECT" by default. The next word typed will be the folder all files to be organized will be found.
--md is optional. If passed a report.md markdown file report will be created and saved in the reports folder
--json is optional. If passed a manifest.json file report will be created and saved in the reports folder

Organize cannot fetch new files, but if files have been fetched and not sorted, organize can be passed to sort them. Organize can also generate reports.

report has several modifiers that can be passed after it:
--verbose is optional. If passed will print all the logging messages to the terminal and save them to the log file.
--debug is optional. If passed it will log the logging.debug arguments as well as the other logging messages. Helpful for debugging.
--clearLog is optional. If passed will delete any pre-existing log files.
--dest is optional. If not passed will be set to "PROJECT" by default. The next word typed will be the folder all files to generate reports from will be generated from.
--md is optional. If passed a report.md markdown file report will be created and saved in the reports folder
--json is optional. If passed a manifest.json file report will be created and saved in the reports folder

report is the least flexible. It cannot be used to fetch or organize files, it is solely for generating reports from the args.dest target folder 


The category "Dogs" was used for testing

Assumptions Made:
    *Directory structure assumption
        -Files are placed inside leaf directories (not only at the root).
    *CLI argument assumptions       
        -Boolean flags (--md, --json, --debug, etc.) are expected to be present in the args namespace.
    *File system permission assumptions
        -The user has permission to read and write files and subdirectories under args.dest.
        -The program can create logs/ and reports/ subdirectories under args.dest.
        -The program can delete old log files when --clearLog is passed.
    *File metadata assumptions
        -Each file has a valid modification time (st_mtime) accessible via stat().
        -File paths and names can be safely represented in UTF-8 (no encoding conflicts).
    *Logging setup assumptions
        -The logging system writes into args.dest/logs/. (should be handled to be always true, but is possible to not have been handled properly)
    *Data representation assumptions
        -Sorting of day folders assumes folder names are numeric (e.g., "01", "02", etc.). (Should be handled to be set this way, but is possible to have been missed)
    *Recursion logic assumptions
        -The directory tree under args.dest can be fully traversed without hitting symbolic link loops or permission-denied folders.
    *Fetching assumptions
        -Assumes the target category is a valid category
    *Valid API endpoint
        -The constant API points to a functioning MediaWiki-compatible API endpoint.
    *The HEADERS dictionary contains valid headers (e.g., User-Agent) so the request isn’t blocked.
    *Namespace mapping
        -Namespace ID 6 always means File, and 14 always means Category. (This is true in MediaWiki/Wikimedia APIs.)
    *API pagination
        -The Wikimedia API will provide a cmcontinue field whenever there are more results beyond the current response.
    *File metadata availability

Edge Cases Handled:
    *Fetching
        -If a category contains only subcategories and no files, will recursively search each subcategory for files. **Highly recommend using a limit**
    *Skip irrelevant folders
        -logs/ and reports/ directories are explicitly skipped during recursion.
    *Empty directories
        -Directories with no files do not get added to the report (if sub_data: data[subdir.name] = sub_data).
    *Directories with only subfolders
        -Metadata (__file_count__, __dir_size__) is only added if directory_files_count >= 1.
    *Human-readable vs raw byte conversion handled
        -bytes_to_human_readable() safely converts file sizes into KB, MB, GB, TB units.
    *Non-numeric folder names
        -Folders with non-digit names (like misc, extra) are separated from numeric day folders, so sorting doesn’t break during recursion.
    *File size lookup errors
        -In JSON generation, if the absolute path lookup fails or stat() throws an error, the file size is set to 0 instead of crashing.
    *If no mtimes available
        -If no files exist in a folder, “earliest” and “latest” mtime fields default to "N/A" (Markdown) or None (JSON).
    *Old logs cleanup
        -When --clearLog is passed, all old logs are deleted before new logging starts.
        -Logs should cleared when 7 days old and a new log file should be created every day
    *Subfolder recursion
        -Both JSON and Markdown functions recurse into subfolders and only include them if they contain files.
    *Column width alignment (Markdown)
        -Markdown tables dynamically adjust based on longest content in each column, so alignment isn’t broken by long filenames or large numbers. Creates more reader friendly report tables. 
    *Empty category
        -Logs a warning and breaks out cleanly:
    *Recursive loops
        -Variable _seen tracks categories that have already been visited, preventing infinite recursion in circular category structures.
    *Limit exceeded
        -If the number of files collected reaches the limit, the function stops fetching more.
    *Missing or invalid page IDs
        -If no valid page_ids are passed to fetch_file_info_batch, it logs and returns an empty list.
    *API/network errors
        -Wrapped in try/except, logs the error and returns safely instead of crashing.
    *Missing or incomplete data
        -Handles cases where a page is missing, or has no imageinfo. Both are logged and skipped.
    *Non-file category members
        -Explicitly filters for files (ns=6) and categories (ns=14), ignoring irrelevant entries. (Assuming those are correct filters)
    *Rate limiting
        -time.sleep(0.1) prevents overwhelming the API with too many requests too quickly.



