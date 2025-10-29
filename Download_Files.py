import os
import json
import logging
import urllib.request as urq
from datetime import datetime
from pathlib import Path
from ENV.HEADER import HEADERS
from dateutil import parser
import re
import time

# Function for extra robust time parsing for more robust timestamp parsing
def parse_fallback_datetime(raw_mtime):
    """
    Attempt to parse a timestamp from raw metadata.
    Returns a datetime object or None if unparseable.
    """
    if not raw_mtime:
        return None

    # Clean HTML, non-breaking spaces, and extra text
    raw_mtime = re.sub(r"<.*?>", "", raw_mtime)  # remove HTML tags
    raw_mtime = raw_mtime.replace("\xa0", " ").strip()  # normalize spaces
    raw_mtime = re.sub(r"^Taken on\s*", "", raw_mtime, flags=re.I)
    raw_mtime = re.sub(r"^before\s*", "", raw_mtime, flags=re.I)
    raw_mtime = re.sub(r"\(UTC\)|\(from.*\)", "", raw_mtime, flags=re.I).strip()

    # Try flexible parsing
    try:
        dt = parser.parse(raw_mtime, fuzzy=True)
        return dt
    except Exception:
        pass

    # Fallback: look for a 4-digit year
    match = re.search(r"\b(\d{4})\b", raw_mtime)
    if match:
        year = int(match.group(1))
        return datetime(year, 1, 1)  # default to Jan 1

    # Last resort: return current time
    return datetime.fromtimestamp(time.time())



# Function to download the files retrieved and the associated meta data
def save_files_and_data(file_info, dest="PROJECT", dry_run=False):
    incoming_dir = Path(dest) / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)
    filename = file_info.get("title", "unknown").replace("File:", "").replace(" ", "")
    filepath = incoming_dir / filename
    meta_path = filepath.with_suffix(filepath.suffix.lower() + ".meta.json")
    # Section below normalizes timestamps into ISO format in the JSON files
    raw_mtime = file_info.get("extmetadata", {}).get("DateTimeOriginal", {}).get("value") \
                or file_info.get("extmetadata", {}).get("DateTimeOriginal") \
                or file_info.get("upload_timestamp")
    iso_mtime = None
    ts = None
    # Sets the mtime for the downloaded files
    if raw_mtime:
        mtime_dt = parse_fallback_datetime(raw_mtime)
        if mtime_dt:
            iso_mtime = mtime_dt.isoformat()
            ts = mtime_dt.timestamp()
            logging.info(f"parsed timestamp of {raw_mtime} for file {file_info}")
        else:
            logging.warning(f"Could not parse timestamp '{raw_mtime}'")

    meta = {
        "title": file_info.get("title"),
        "pageid": file_info.get("pageid"),
        "original_url": file_info.get("url"),
        "upload_timestamp": file_info.get("upload_timestamp"),
        "extmetadata": {k: v.get("value") for k, v in file_info.get("extmetadata", {}).items()}
    }

    if dry_run:
        logging.info(f"[DRY RUN] Would download {filename}")
        return

    # Download the file
    if not filepath.exists() and file_info.get("url"):
        try:
            req = urq.Request(file_info["url"], headers=HEADERS)
            with urq.urlopen(req) as response:
                data = response.read()
            logging.info(f"read data for {filepath} from url")
            with open(filepath, "wb") as f:
                f.write(data)
            logging.info(f"Downloaded {filepath}")
        except Exception as e:
            logging.error(f"Failed to download {filename}: {e}")
            return
    else:
        logging.info(f"Already exists, skipping: {filepath}")

    # Write metadata
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    logging.info(f"Wrote metadata {meta_path}")

    # Set mtime
    if ts is not None:
        try:
            os.utime(filepath, (ts, ts))
            os.utime(meta_path, (ts, ts))
            logging.info(f"Set mtime of {filepath} and {meta_path} to {iso_mtime}")
        except Exception as e:
            logging.warning(f"Could not set mtime for {filepath}: {e}")
    else:
        logging.warning(f"No valid timestamp to set mtime for {filepath}")
