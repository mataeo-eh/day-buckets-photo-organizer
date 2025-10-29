import json
import logging
import urllib.request as urq
import urllib.parse
from ENV.API import API
from ENV.HEADER import HEADERS



# Function to batch the page IDs into sets of max size 50 page IDs
def fetch_file_info(page_ids):
    files = []

    # Batch page_ids into chunks of 50
    chunk_size = 50
    for i in range(0, len(page_ids), chunk_size):
        batch = page_ids[i:i + chunk_size]
        files.extend(fetch_file_info_batch(batch))  # Call the single-batch fetch function

    return files


# function to fetch info for the batches of page IDs
def fetch_file_info_batch(page_ids):
    logging.debug(f"the list of pageID's to fetch is {page_ids}")
    if not page_ids:
        logging.warning(f"No page ids to collect metadata from")
        return [] # Returns an empty list if no valid page_ids are provided (I.E. if a category was empty)
    
    pageids_str = "|".join(page_ids) #creates a string of all the page ID's seperated by | to fetch from the API

    # Parameters of meta data to collect and store about each file 
    params = {
        "action": "query",
        "pageids": "|".join(page_ids),
        "prop": "imageinfo",
        "iiprop": "timestamp|user|url|size|extmetadata|mediatype",
        "format": "json"
    }

    try:
        query_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        url = f"{API}?{query_string}"
        req = urq.Request(url, headers=HEADERS)
        #logging.debug(f"the query string is {query_string} \n the url to fetch from is {url} \n req is {req}")
            # Code above builds the query string with the parameters, and API, and headers so the request follows the wikimedia bot rules
        with urq.urlopen(req) as response: # Opens the url and attempts and then reads the data and saves it in the data variable
            r = response.read().decode("utf-8")
        data = json.loads(r)
        logging.info(f"metadata was collected")
    except Exception as e:
        # Logs the error if an error occurs and then returns an empty list so the entire program does not crash
        logging.error(f"Error fetching file info: {e}") 
        return []

    files = [] # Creates an empty list to add the metadata from files to
    # Finds the data for each pageid given from previous fucntions and adds the metadata to the files list
    #logging.debug(json.dumps(data, indent=2))
    for pageid, page in data.get("query", {}).get("pages", {}).items():
        if "missing" in page:
            logging.warning(f"Page {pageid} is missing")
            continue
        info = page.get("imageinfo")
        if not info:
            logging.warning(f"Page {pageid} has no imageinfo (probably not a file)")
            continue
        info = info[0]
        files.append({
            "pageid": pageid,
            "title": page.get("title"),
            "url": info.get("url"),
            "upload_timestamp": info.get("timestamp"),
            "extmetadata": info.get("extmetadata", {}),
        })
        logging.info(f"Metadata for {pageid} collected and stored")
    return files