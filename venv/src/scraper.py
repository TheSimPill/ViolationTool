from datetime import datetime
import random, re, concurrent.futures, time, os, pickle
from turtle import home
from bs4 import BeautifulSoup as bs
import save_load_html as sl
from nhi_functions import get_proxy
from os.path import exists
from tkinter.ttk import Progressbar, Label
import nhi_functions as nhi
import pandas as pd
# Windows
# import src.save_load_html as sl
# from src.nhi_functions import get_proxy
# import src.nhi_functions as nhi

homes = 0
totalhomes = 0
curframe = None

# Scrape fines for relevant cases for each state using threads
def scrape_fines(frame, reparse, state_df, dir, dfpath, apikey):
    # Allows frame to be updated in different functions without directly passing it in
    global curframe; curframe = frame

    # Hide elements from previous screen
    frame.start_btn.grid_forget()
    frame.instructions.config(text="Starting scrape")
    frame.instructions2.grid_forget()
    curframe.instructions2 = Label(curframe, text="", font=("Times", 9))
    curframe.instructions2.grid(column=1, row=2, columnspan=3)

    # Loop will break once all scraping is done
    while True:
        # Generate a random session number, used for proxies
        session = random.randint(900, 793293)
        # Parameters to use with the requests module
        params = {
        "api_key":apikey,
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
                soup = bs(html, "html.parser")
                
            # Grab parts of each row that contains the url to each state's page
            rows = soup.find(id="data").find("tbody").find_all("a")
            
            # Initialize Progress Bar
            progress = Progressbar(frame, orient = "horizontal",
                length = 300, mode = 'determinate')
            progress.grid(column=2, row=3, pady=10)

            # Progress bar's label
            x = 0
            plabel = Label(frame, text=str(x) + " out of " + str(len(rows)) + " scraped", font=("Times", 15))
            plabel.grid(column=1, row=4, columnspan=3, pady=10)
            
            # Go through rows, go to state's page using url, scrape all of it's facilities
            states_fines = []
            for state_url in rows:
                
                params["url"] = "https://projects.propublica.org" + state_url["href"]
                params["session"] = random.randint(100,100000)

                # Extract the state
                length = len(state_url["href"])
                state = state_url["href"][(length - 2):length]
                

                # Get names of all facilities from state df
                # Used so homes that don't have relevant cases are filtered
                facilities = []

                # Creates subdata frame with rows only of current state and grabs facility names
                sdf = state_df.loc[(state_df['State'] == state)]
                fnames = sdf['Organization'].unique()

                for name in fnames:
                    facilities.append(name)
                
                # Set label
                frame.instructions.config(text="Scraping pages from " + state)

                # Returns a list of urls to fined homes in a state
                state_home_links = get_state_fine_links(reparse, params, state, dir, facilities)
                
                # Allows for home count on user's screen to be updated after each one is scraped
                global totalhomes; totalhomes = len(state_home_links)

                # Have to put arguments for scrape_facility into a tuple so we can use threads
                args_list = []
                facility = 1
                for home_link in state_home_links:
                    params = {
                        "api_key":apikey,
                        "url":home_link,
                        "proxy_type":"datacenter",
                        "country":"us",
                        "session": random.randint(9000,8000000)
                            }
                    args_list.append((facility, state, params, sdf, reparse, dir))
                    facility += 1

                # Progress bar for homes in a state
                global homes
                frame.instructions.config(text=str(homes) + " out of " + str(totalhomes) + " homes scraped")

                # Concurrently parse all homes for a certain state
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    # This will be a list of (state, facility, date, fine, url) tuple lists
                    state_homes_fines = executor.map(scrape_facility, args_list)

                # Set label
                frame.instructions.config(text="Scraped " + state)

                # Adds all fine incidents for each home in a certain state to hash of all states
                # So, state_home_fines = [[(state, facility, date, fine, url), (....), ...],[],[],....]
                for homes_fines_list in state_homes_fines:
                    # Go through list of tuples for each home
                    for homes_fines in homes_fines_list:
                        # Appending each incident tuple from all homes in a state
                        states_fines.append(homes_fines)

                # MAC - /Users/Freddie/Impruvon/guiwebscraperproject/venv/src/dataframes/states_fines.pkl
                with open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\dataframes\states_fines.pkl", 'wb') as outp:
                    pickle.dump(states_fines, outp, pickle.HIGHEST_PROTOCOL)
                
                # Updates progress bar label and value
                x += 1
                progress["value"] += (1/len(rows))*100
                plabel.config(text=str(x) + " out of " + str(len(rows)) + " states scraped")

                # Reset home count for the next state
                homes = 0

            # Convert fines hash into a data frame once everything is scraped
            fine_df = pd.DataFrame(states_fines, columns =["State", "Organization", "Date", "Fine", "Url"])

            # Check to see if folder exists and if it doesn't, create it
            # Removed for testing
            #if not exists(dfpath + "/dataframes"):
                #os.mkdir(dfpath + "/dataframes")
                #dfpath + "/dataframes/fine_df.pkl"
            # MAC - /Users/Freddie/Impruvon/guiwebscraperproject/venv/src/dataframes/fine_df.pkl
            with open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\dataframes\fine_df.pkl", 'wb') as outp:
                pickle.dump(fine_df, outp, pickle.HIGHEST_PROTOCOL)
            
            # Once all scraping is finished
            time.sleep(1)
            curframe.instructions2.grid_forget()
            progress.grid_forget()
            plabel.grid_forget()
            curframe.instructions.config(text="Saved fines_hash.pkl in dataframes folder")

            time.sleep(1)
            curframe.instructions.config(text="Matching fines...")

            # Changed for testing
            # dfpath + "/dataframes/fine_df.pkl"
            #C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\dataframes\fine_df.pkl
            #C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\dataframes\state_df.pkl
            #/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/dataframes/fine_df.pkl
            #/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/dataframes/state_df.pkl
            with open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\dataframes\fine_df.pkl", 'rb') as inp:
                fine_df = pickle.load(inp)
            with open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\dataframes\state_df.pkl", 'rb') as inp:
                state_df = pickle.load(inp)
            nhi.match_violations(dfpath, curframe, state_df, fine_df)
            
        # If parsing main page fails for some reason
        except AttributeError as e:
            print("Caught Exception at NHI page!" + str(e) + "---------------------------------------")
            print("Session failed: " + str(params["session"]))

            # Generate a new session and reparse
            params["session"] = random.randint(100, 10000000)
            reparse = True
            time.sleep(1.5)
        
# Gets links from a specific states page for facilities that have fines
def get_state_fine_links(reparse, state_params, cur_state, dir, facilities):
    while True:
        try:
            if (not reparse and not exists(dir + "/" + cur_state + "-html.html")) or reparse:
                response = get_proxy(state_params)
                state_page = response[0]
                state_params = response[1]
                sl.save_obj(state_page.content, dir + "/" + cur_state + "-html.html")
                page_soup = bs(state_page.content, "html.parser")
            else:
                state_page = sl.load_obj(dir + "/" + cur_state + "-html.html")
                page_soup = bs(state_page, "html.parser")

            home_urls = []
            # Gets list of all homes on a page
            rows = page_soup.find(id="data").find("tbody").find_all("tr")
            for col in rows: 
                # Only grab relevant homes
                name = col.find("a").contents[0].upper()
                if name in facilities:    
                    home_url = col.find("a")["href"]
                    home_urls.append("https://projects.propublica.org" + home_url)

            return home_urls
        
        # If parsing a state page fails for some reason
        except AttributeError as e:
            print("Caught Exception at state page!" + str(e) + "---------------------------------------")
        
            # Generate a new session and reparse
            state_params["session"] = random.randint(100, 10000000)
            reparse = True
    
# Scrapes a specific facilities page for relevant fines.
def scrape_facility(args):
    global homes
    global totalhomes
    global curframe
    retries = 0

    while True:
        # Load the args from the args tuple
        facilitynumber = args[0]
        state = args[1]
        state_params = args[2]
        cstate_df = args[3]
        reparse = args[4]
        dir = args[5]
        
        # Regrab page if reparsing or reparsing but find a file that doesn't exist
        if (not reparse and not exists(dir + "/" + state + str(facilitynumber) + "-page.html")) or reparse or (retries != 0 and retries % 3 == 0):
            if retries != 0 and retries % 3 == 0:
                print("Max exceptions reached for " + state + str(facilitynumber) + ", retrying")
            response = get_proxy(state_params)
            home_page = response[0]
            sl.save_obj(home_page.content, dir + "/" + state + str(facilitynumber) + "-page.html")
            home_soup = bs(home_page.content, "html.parser")
        else:
            home_page = sl.load_obj(dir + "/" + state + str(facilitynumber) + "-page.html")
            home_soup = bs(home_page, "html.parser")
            
        try:
            # Scrape a specific home's fines
            home_fines = []
            # Grab the facility name from top of page
            facility = home_soup.find(id="content").find("p", class_="big-name capital").find("b").get_text()
        
            # Iterate through incidents (rows) for a home
            for fine_incident in home_soup.find_all("div", class_="row"):
                
                # Want format to be MM/DD/YYYY
                date = fine_incident.find("span", class_="nd nd-entry nd-30")

                # This handles rows that aren't actually incident rows
                if date != None:
                    date = date.find("p").get_text()
                    date = str(datetime.strptime(date, '%b %d, %Y').strftime('%m/%d/%Y'))


                    # This checks to see if a case is relevant by comparing it to cases in our data frame
                    matches = cstate_df.loc[(cstate_df["Organization"] == facility.upper()) & (cstate_df["Date"] == date)]
                    if not matches.empty:
   
                        # Grab url for incident report
                        incident_url = fine_incident.find("a")["href"]

                        # Grabs the fine if there is one
                        fine = fine_incident.find("span", class_="nd-left nd-entry fine-label")     
                        lst = fine.get_text().strip().split("\n")
                        fine = re.search(".+Fine$", lst[0])

                        if facility == 'apache junction hlth center':
                            print(facility.upper(), fine, incident_url, date)
                            time.sleep(3)
                        if not fine is None:
                            fine = fine.group()

                            # Only let user see one fine match for a day if there are multiple
                            if len(fine) >= 5 and fine[-4:] == "Fine":
                                curframe.instructions2.config(text="Matched " + fine + " in " + state + " from " + date + " at\n    " + facility.upper())

                            # Now make fine just an int
                            numeric_filter = filter(str.isdigit, fine)
                            fine = "".join(numeric_filter)
                            home_fines.append((state, facility.upper(), date, int(fine), incident_url))

                        else:
                            home_fines.append((state, facility.upper(), date, 0, incident_url))


            # Update home count label                  
            homes += 1
            curframe.instructions.config(text=str(homes) + " out of " + str(totalhomes) + " homes scraped")

            return home_fines

        except AttributeError as e:
            print("Caught Exception!" + str(e) + "---------------------------------------")
            print("Params: ", state_params)
            print("Session failed: " + str(state_params["session"]))
            time.sleep(1.5)
            retries += 1
