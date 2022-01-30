from datetime import datetime
import random, re, concurrent.futures, time, os, pickle
from bs4 import BeautifulSoup as bs
import src.save_load_html as sl
from src.nhi_functions import get_proxy
from os.path import exists

# Scrape fines for relevant cases for each state using threads
# Returns hash of form: ST => (facility, date, fine) list
def scrape_fines(frame, reparse, states, dir, hashpath):
    
    # Hide download button from previous page
    frame.dl_btn.grid_forget()

    # Loop will break once all scraping is done
    while True:
        session = random.randint(900, 793293)
        params = {
        "api_key":"PHkTKJqWyIcNQ5pA8NnzXf6PLDygeGTT",
        "url":"https://projects.propublica.org/nursing-homes/summary",
        "proxy_type":"datacenter",
        "country":"us",
        "session": str(session)
        }

        try:
            # Logic: We will try and pull a webpage again under two conditions:
            #           1. We've chosen to use saved pages, but a given page doesn't have a save file
            #           2. We've chosen to rescrape (reparse) everything
            if (not reparse and not exists(dir + "/all_states_fines.html")) or reparse:
                response = get_proxy(params)
                page = response[0]
                params = response[1]

                # Page of all states
                sl.save_obj(page.content, dir + "/all_states_fines.html")
                soup = bs(page.content, 'html.parser')
            else:
                html = sl.load_obj(dir + "/all_states_fines.html")
                soup = bs(html, "lxml")
                
            # State hash: { "ST" : (facility, date, fine) list}
            states_fines = {}
            rows = soup.find(id="data").find("tbody").find_all("a")

            # Gets link for each state from page of all states
            for state_url in rows:
                params["url"] = "https://projects.propublica.org" + state_url["href"]
                params["session"] = random.randint(100,100000)

                length = len(state_url["href"])
                state = state_url["href"][(length - 2):length]
                if not state in states_fines.keys():
                    states_fines[state] = []
                
                # Set label
                frame.instructions.config(text="Scraping urls from " + state)
                print("Scraping urls from " + state + " session = " + str(params["session"]))

                # Returns a list of urls to fined homes in a state
                state_home_links = get_state_fine_links(reparse, params, state, dir)
                # Set label
                frame.instructions2.config(text=str(len(state_home_links))+ " homes to scrape")
                print(str(len(state_home_links))+ " homes to scrape")
                time.sleep(2)

                args_list = []
                facility = 1
                for home_link in state_home_links:
                    params = {
                        "api_key":"PHkTKJqWyIcNQ5pA8NnzXf6PLDygeGTT",
                        "url":home_link,
                        "proxy_type":"datacenter",
                        "country":"us",
                        "session": random.randint(9000,8000000)
                            }
                    args_list.append((facility, state, params, states, reparse, dir))
                    facility += 1

                # Concurrently parse all homes for a certain state
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    # This will be a list of (facility, date, fine) tuple lists
                    state_homes_fines = executor.map(scrape_facility, args_list)

                # Set label
                frame.instructions.config(text="Scraped " + state)
                print("Scraped " + state)

                # Adds all fine incidents for each home in a certain state to hash of all states
                for homes_fines_list in state_homes_fines:
                    for homes_fines in homes_fines_list:
                        # Appending each incident tuple from all homes in a state
                        states_fines[state].append(homes_fines)

            if not exists(hashpath + "/hashes/fines_hash.pkl"):
                os.mkdir(hashpath + "/hashes/fines_hash.pkl")
            with open(hashpath + "/hashes/fines_hash.pkl", 'wb') as outp:
                pickle.dump(states_fines, outp, pickle.HIGHEST_PROTOCOL)

            frame.advance_page()

        except AttributeError as e:
            print("Caught Exception!" + str(e) + "---------------------------------------")
            print("Session failed: " + str(params["session"]))
            time.sleep(5)
        
# Gets links from a specific states page for facilities that have fines
def get_state_fine_links(reparse, state_params, cur_state, dir):

    if (not reparse and not exists(dir + "/" + cur_state + "-html.html")) or reparse:
        response = get_proxy(state_params)
        state_page = response[0]
        state_params = response[1]
        sl.save_obj(state_page.content, dir + "/" + cur_state + "-html.html")
        page_soup = bs(state_page.content, "html.parser")
    else:
        state_page = sl.load_obj(dir + "/" + cur_state + "-html.html")
        page_soup = bs(state_page, "lxml")

    # Get each facility page that has fines
    rows = page_soup.find(id="data").find("tbody").find_all("tr")
    home_urls = []
    for col in rows: 
        fine = re.search("\$.+<", str(col))
        # Only want rows that have fines
        if not fine is None:
            # Begin grabbing home url if fine found
            home_url = col.find("a")["href"]
            home_urls.append("https://projects.propublica.org" + home_url)
    return home_urls
    
# Scrapes a specific facilities page for relevant fines.
def scrape_facility(args):
    retries = 0
    while True:
        facilitynumber = args[0]
        state = args[1]
        state_params = args[2]
        states = args[3]
        reparse = args[4]
        dir = args[5]
        
        # Regrab page if reparsing or reparsing but find a file that doesn't exist
        if (not reparse and not exists(dir + "/" + state + str(facilitynumber) + "-page.html")) or reparse or (retries != 0 and retries % 5 == 0):
            if retries != 0 and retries % 5 == 0:
                print("Max exceptions reached for " + state + str(facilitynumber) + ", retrying")
            response = get_proxy(state_params)
            home_page = response[0]
            sl.save_obj(home_page.content, dir + "/" + state + str(facilitynumber) + "-page.html")
            home_soup = bs(home_page.content, "html.parser")
        else:
            home_page = sl.load_obj(dir + "/" + state + str(facilitynumber) + "-page.html")
            home_soup = bs(home_page, "lxml")
            
        try:
            # Scrape a specific home's fines
            home_fines = []
            facility = home_soup.find(id="content").find("p", class_="big-name capital").find("b").get_text()
            for fine_incident in home_soup.find_all("div", class_="row"):
                fine = fine_incident.find("span", class_="nd-left nd-entry fine-label")
                if not fine is None:
                    lst = fine.get_text().strip().split("\n")
                    fine = re.search(".+Fine$", lst[0])
                    # Grab the fines, but only for cases we need
                    if not fine is None:
                        fine = fine.group()
                        # Want format to be MM/DD/YYYY
                        date = fine_incident.find("span", class_="nd nd-entry nd-30").find("p").get_text()
                        date = str(datetime.strptime(date, '%b %d, %Y').strftime('%m/%d/%Y'))

                        # Check if this fine relates to a relevant case
                        for incident in range(0, len(states[state])):
                            state_incident = states[state][incident]
                            if state_incident[0] == facility.upper() and state_incident[1] == date:
                                print("Matched " + fine + " in " + state + " from " + date + " at " + facility.upper())

                                # Now make fine just an int
                                numeric_filter = filter(str.isdigit, fine)
                                fine = "".join(numeric_filter)
                                home_fines.append((facility.upper(),date,int(fine)))
                                
            print("Scraped " + str(facilitynumber) + facility.upper() + " in " + state)
            return home_fines

        except AttributeError as e:
            print("Caught Exception!" + str(e) + "---------------------------------------")
            print("Session failed: " + str(state_params["session"]))
            time.sleep(5)
            retries += 1
