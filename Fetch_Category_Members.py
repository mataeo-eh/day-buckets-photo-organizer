import json
import time
import logging
import urllib.request as urq
import urllib.parse
from Fetch_File_Info import fetch_file_info
from ENV.API import API
from ENV.HEADER import HEADERS



# Fetches the different files within the requested category to allow for future processing of them
def get_all_category_members(_seen, category=None, limit=None,):
    members = [] # Creates an empty list for the fetched files
    cmcontinue = None
    if _seen is None: # Variable to prevent infinite loops
        _seen = set()
    

    if category is None: #Gracefully handles if a category is not passed in the CLI and prompts the user to enter a category
        category = input("Enter category here: ")

    if category in _seen:
        logging.warning(f"skipping previously seen category {category} to avoid infinite looping")
        return members
    _seen.add(category)

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": min(500, limit - len(members)) if limit else "500",
            "cmtype": "file|subcat",
            "format": "json"
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        try: # A try block to fetch the files and gracefully handle any errors with a (hopefuly) useful error code
            query_string = urllib.parse.urlencode(params)
            url = f"{API}?{query_string}"
            req = urq.Request(url, headers=HEADERS)
            # Opens the url, reads the data, and saves it to r for future use
            with urq.urlopen(req) as response:
                r = response.read().decode("utf-8")
            data = json.loads(r) # Creates a JSON of the data fetched from the provided category
        except Exception as e:
            logging.error(f"Error fetching category members: {e}")
            break
        logging.info(f"Saving files in category to json")
            
        # Collects the data of the files within the category
        category_members = data.get("query", {}).get("categorymembers", []) 
        logging.debug(f"{category_members} found while fetching category members")
        # if not category_members: 
        #     logging.warning(f"No members found in category '{category}'") # Breaks the while loop if the category has no files
        #     break
        files = [m for m in category_members if m.get("ns") == 6]     # ns=6 means File
        subcats = [m for m in category_members if m.get("ns") == 14]  # ns=14 means Category
        if files: # Fetch files if there are any
            page_ids = [str(f.get("pageid")) for f in files if f.get("pageid")]
            logging.debug(f"Page IDs collected: {page_ids}")
            fetched = fetch_file_info(page_ids)
            members.extend(fetched)
            logging.info(f"Fetched metadata for {len(page_ids)} files from {category}")
        else:
            logging.info(f"No files found in category '{category}', checking subcategories")

        if limit and len(members) >= limit: # Exits if the while loop if there is a limit and the files fetched exceeds that set limit
            logging.warning(f"Limit reached, no more files will be collected")
            return members[:limit]
        
        # Process subcategories recursively
        for subcat in subcats:
            subcat_name = subcat.get("title", "").replace("Category:", "")
            logging.info(f"Recursively fetching subcategory '{subcat_name}'")
            sub_members = get_all_category_members(
                category=subcat_name,
                limit=limit - len(members) if limit else None,
                _seen=_seen
            )
            members.extend(sub_members)

            if limit and len(members) >= limit:
                return members[:limit]



        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue: # Exits the while loop after every instance of continue was met and there are no more files to retrieve
            logging.info(f"All files retrieved")
            break

        


        time.sleep(0.1) # Break to not overload the API with requests too quickly
    return members[:limit] if limit else members