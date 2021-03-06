from tkinter import Label
from tkinter.ttk import Progressbar
from typing import Dict, List
from openpyxl.descriptors.base import String
import pickle, sys, info, os, time, requests, zipfile, random
from bs4 import BeautifulSoup as bs
import pandas as pd
from datetime import datetime

# This is where all the save data lies
abs_home = os.path.abspath(os.path.expanduser("~"))
home_folder_path = abs_home + "/ViolationTool/"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Download raw data if user says yes
def download(frame, date):
    
    frame.instructions.config(text="Downloading...")
    
    # Try and grab the download url, if not, let the user retry
    try:
        req = requests.request("GET", "https://projects.propublica.org/nursing-homes/", timeout=9)
        if req.status_code == 200:
            soup = bs(req.content, "html.parser")
            hrefs = soup.find("div", class_="home_about_data").find_all("a")
            for a in hrefs:
                if a.text == "raw data files":
                    url = a["href"]
                    break
    except:
        frame.instructions.config(text="Download failed: Please try restarting the program")

    # Download and save the excel files
    global home_folder_path
    r = requests.get(url, allow_redirects=True)
    filepath = home_folder_path + "rawdata"
    open(filepath + "/Raw_Data.zip", 'wb').write(r.content)
    frame.instructions.config(text="Download Done")

    # Unzip the download
    with zipfile.ZipFile(filepath + "/Raw_Data.zip", 'r') as zip_ref:
        filenames = zip_ref.namelist()
        zip_ref.extractall(filepath)
    frame.instructions.config(text="Unzip Done")

    # Save the date of this download
    with open(home_folder_path + "assets/lastupdate.pkl", 'wb') as outp:
        pickle.dump(date, outp, pickle.HIGHEST_PROTOCOL)

    # Update screen
    frame.instructions.config(text="Parsing Data")
    time.sleep(5)
    parse_data(frame, filenames)

'''
    Cases that took place on the same date at the same facility
    are each counted as their own incident in the excel raw data.
'''
def parse_data(frame, filenames):
    start_time = time.time() 
    files = [file for file in filenames if file.endswith(".xlsx")]
    numtoload = len(files)
    frame.instructions.config(text="Total Workbooks to load: " + str(numtoload))
    
    # Initialize Progress Bar
    progress = Progressbar(frame, orient = "horizontal",
        length = 300, mode = 'determinate')
    progress.grid(column=1, row=2, columnspan=3, pady=10)

    # Progress bar's label
    x = 0
    plabel = Label(frame, text=str(x) + " out of " + str(len(files)) + " workbooks parsed", font=("Times", 15))
    plabel.grid(column=1, row=4, columnspan=3, pady=10)
    
    counter = 1
    dfs = []

    for file in files:

        file = home_folder_path + "rawdata/" + file
        start = time.time()

        # Make excel file into a dataframe
        df = pd.read_excel(file, usecols="A,E,G,H,I", names=["Organization", "State", "Date", "Tag", "Severity"])
        df.insert(5, "Fine", 0)
        df.insert(6, "Url", "")
        
        # Format columns 
        col_list = ["State", "Organization", "Date", "Tag", "Severity", "Fine", "Url"]
        df = df.reindex(columns=col_list)

        dfs.append(df)

        # Update labels and progress bar
        
        frame.instructions.config(text="Workbook " + str(counter) + " parsed in " + str(int(time.time() - start)) + " seconds")
        x += 1
        progress["value"] += (1/len(files))*100
        plabel.config(text=str(x) + " out of " + str(len(files)) + " workbooks parsed", font=("Times", 15))
        
        counter += 1

    # Once all excel files are dataframes
    plabel.grid_forget()
    progress.grid_forget()

    # Merge dataframes and sort by state
    frame.instructions.config(text="Merging data frames...")
    result = pd.concat(dfs, ignore_index=True)
    result = result.sort_values(by=["State"])
    
    # Fix indicies
    result.reset_index(drop=True, inplace=True)

    # Get rid of the rawdata afterwords
    for file in filenames:
        os.remove(home_folder_path + "rawdata/" + file)
    os.remove(home_folder_path + "rawdata/" + "Raw_Data.zip")

    frame.instructions.config(text="Parsed Raw Data in " + str(int(time.time() - start_time)) + " seconds")
    time.sleep(2)
    
    with open(home_folder_path + "dataframes/new/state_df.pkl", 'wb') as outp:
            pickle.dump(result, outp, pickle.HIGHEST_PROTOCOL)

    frame.instructions.config(text="Saved as state_df.pkl in dataframes/new folder")
    time.sleep(2)
    frame.advance_page()

# Trys connecting to a website with proxy, refreshes proxy if needed
# Used to try and minimize number of proxies used and therefore API calls
def get_proxy(params):
    url = "https://api.webscrapingapi.com/v1"
    while True:
        # Random time interval to break up requests
        time.sleep(random.random() * random.randrange(1, 10))
        try:
            page = requests.request("GET", url, params=params, timeout=9)
            if page.status_code != 200:
                print(page.status_code)
                raise Exception()
        except:
            print("Connection to " + params["url"] + " failed, retrying with new proxy")
            print(params["session"])
            params["session"] = random.randint(1, 384179329732178238179)
        else:
            return (page, params)

    
# Makes the excel sheets based on options chosen by the user 
def make_sheets(frame, options, state_df, fine_df, startdate, enddate, territories, tags, outpath):

    # Update the screen
    frame.instructions.config(text="Making sheets...")
    frame.instructions2.grid_forget()
    frame.sheet_btn.grid_forget()
    start_time = time.time()

    # Load in tag data 
    with open(resource_path("assets/tag_hash.pkl"), 'rb') as inp:
        tag_hash = pickle.load(inp)

    # Setting defaults for missing user choices

    # Get years in range that user chose, or set a default range
    if None in {startdate, enddate}:

        # Conversion to date time objects for min and max
        oldcol = state_df['Date']
        state_df['Date'] =  pd.to_datetime(state_df['Date'], format='%m/%d/%Y')

        startdate = state_df['Date'].min()
        enddate = state_df['Date'].max()

        # Convert date column back to string 
        state_df['Date'] = oldcol
        print("Used Default Dates")

    # Check to see if territories were chosen and use default if not
    if len(territories) == 0:
        territories = info.territories
        print("Used Default Territories")
    # Convert states to their two letter code
    territories = convert_states(territories)
    print("Converted States to Two-Letter Codes")

    # Check to see if tags were chosen and if not use all
    if len(tags) == 0:
        tags = list(tag_hash.keys())
        print("Used Default Tags")
    else:
        state_df = state_df.loc[state_df["Tag"].isin(tags)] 
        print("Filtered Tags")

    # Get dates in range for state df
    state_df = get_inrange(state_df, startdate, enddate)
    print("Filtered Dates")

    # Merge rows where state, date, and organization are the same
    state_df = match_violations(state_df, fine_df)
    state_df = state_df.reset_index()

    # Optional sheets
    dfs = {}
    years = list(range(startdate.year, enddate.year+1))
    dfs["US"] = pd.DataFrame(columns=(["Total"] + years))
    dfs["Most Fined"] = pd.DataFrame()
    dfs["Most Severe"] = pd.DataFrame()
    dfs["State Fines"] = pd.DataFrame(columns=(["Total"] + years))
    dfs["State Violations"] = pd.DataFrame(columns=(["Total"] + years))
    dfs["All Territories"] = pd.DataFrame()
    dfs["All"] = pd.DataFrame()

    # Make a dataframe for each territory (saved in a hash) and then only keep violations in date range
    t_dfs = sort_by_territories(state_df, territories)
    for terr in t_dfs.keys():
        # Convert fine column to currency
        t_dfs[terr]["Fine"] = t_dfs[terr]["Fine"].apply(lambda x: 0 if x == "No Fine" else x)
        t_dfs[terr]["Fine"] = pd.to_numeric(t_dfs[terr]["Fine"], errors="coerce")
        t_dfs[terr]["Fine"] =  t_dfs[terr]["Fine"].apply(lambda x: '${:,.2f}'.format(float(x)))

    
    # Convert fine column to numeric
    state_df["Fine"] = state_df["Fine"].apply(lambda x: 0 if x == "No Fine" else x)
    state_df["Fine"] = pd.to_numeric(state_df["Fine"], errors="coerce")

    # Sort through options
    if options != None:
        for option in options.keys():

    
            if option == "US Fines" and options[option]:

                # Initialize indicies
                dfs["US"].loc["Fines"] = [0] * (len(dfs["US"].columns))
                
                # Conversion to date time objects for comparison
                oldcol = state_df["Date"]
                state_df['Date'] =  pd.to_datetime(state_df['Date'], format='%m/%d/%Y')

                # Total sum -> after the df has been filtered on tags and date 
                sum = state_df["Fine"].sum()
            
                # Sum for each year
                for year in years:
                    # Make sure we are within the users date range  
                    yearstart, yearend = get_year_range(year, years, startdate, enddate)

                    # Get the year's sum and format it as currency
                    dfs["US"].at["Fines", year] = '${:,.2f}'.format(get_inrange(state_df, yearstart, yearend)["Fine"].sum())

                # Change columns type back, add data to hash
                state_df['Date'] = oldcol
                dfs["US"].at["Fines", "Total"] = '${:,.2f}'.format(sum)
                    
                        
            elif option == "US Violations" and options[option]:

                 # Initialize indicies
                dfs["US"].loc["Violations"] = [0] * (len(dfs["US"].columns))

                # Get total number of US violations within date range
                sum = count_violations_df(state_df)
            
                # Sum for each year
                for year in years:
                    # Make sure we are within the users date range  
                    yearstart, yearend = get_year_range(year, years, startdate, enddate)

                    # Get the year's sum
                    dfs["US"].at["Violations", year] = count_violations_df(get_inrange(state_df, yearstart, yearend)) 

                # Add data to hash of dfs
                dfs["US"].at["Violations", "Total"] = sum


            elif option == "Top fined organizations per state" and options[option]:

                state_orgs: Dict[String, Dict[String, List]] = {}
                num = 3
                # For each state get the most fined overall
                state_orgs["Overall"] = {}
                for state in info.states_codes:
                    # Get subdf of a given state
                    subdf = state_df.loc[state_df["State"] == state]
                    # Get a list of the most fined organizations across entire period
                    state_orgs["Overall"][state] = get_most_fined(subdf, num)
                    
                # Go through each year in range
                for year in years:
                    state_orgs[year] = {}
                    # Make sure we are within the users date range  
                    yearstart, yearend = get_year_range(year, years, startdate, enddate)

                    # Get top fined for each year
                    for state in info.states_codes:
                        # Get subdf of a given state
                        subdf = state_df.loc[state_df["State"] == state]
                        subdf = get_inrange(subdf, yearstart, yearend)
                        # Get a list of the most fined organizations across a year
                        state_orgs[year][state] = get_most_fined(subdf, num)

                # Make the multi-index columns
                cols = [(["Overall"] + years), ["Organization", "Fines"]]
                cols = pd.MultiIndex.from_product(cols, names=["Year", "Value"])
                dfs["Most Fined"] = pd.DataFrame(columns=cols)
                dfs["Most Fined"].insert(0, "State", "Not Set")

                # Populate the new df
                for state in info.states_codes:
                    for i in range(num):
                        row = [(state + str(i+1))]
                        for year in state_orgs.keys():
                            # Turn tuple with org and fine into list and add state to front
                            tups = state_orgs[year][state]
                            row += list(tups[i])

                        # Add row to dataframe
                        dfs["Most Fined"].loc[len(dfs["Most Fined"])] = row

                # Finally, make the state the vertical index and make fines currency
                dfs["Most Fined"] = dfs["Most Fined"].set_index(["State"])
            

            elif option == "Most severe organizations per state" and options[option]:

                state_orgs: Dict[String, Dict[String, List]] = {}
                num = 3
                # For each state get the most severe overall
                state_orgs["Overall"] = {}
                for state in info.states_codes:
                    # Get subdf of a given state
                    subdf = state_df.loc[state_df["State"] == state]
                    # Get a list of the most severe organizations across entire period
                    state_orgs["Overall"][state] = get_most_severe(subdf, num)
                    
                # Go through each year in range
                for year in years:
                    state_orgs[year] = {}
                    # Make sure we are within the users date range  
                    yearstart, yearend = get_year_range(year, years, startdate, enddate)

                    # Get most severe for each year
                    for state in info.states_codes:
                        # Get subdf of a given state
                        subdf = state_df.loc[state_df["State"] == state]
                        subdf = get_inrange(subdf, yearstart, yearend)
                        # Get a list of the most severe organizations across a year
                        state_orgs[year][state] = get_most_severe(subdf, num)

                # Make the multi-index columns
                cols = [(["Overall"] + years), ["Organization", "Severity Score"]]
                cols = pd.MultiIndex.from_product(cols, names=["Year", "Value"])
                dfs["Most Severe"] = pd.DataFrame(columns=cols)
                dfs["Most Severe"].insert(0, "State", "Not Set")

                # Populate the new df
                for state in info.states_codes:
                    for i in range(num):
                        row = [(state + str(i+1))]
                        for year in state_orgs.keys():
                            # Turn tuple with org and severity into list and add state to front
                            tups = state_orgs[year][state]
                            row += list(tups[i])

                        # Add row to dataframe
                        dfs["Most Severe"].loc[len(dfs["Most Severe"])] = row

                # Finally, make the state the vertical index and make fines currency
                dfs["Most Severe"] = dfs["Most Severe"].set_index(["State"])


            elif option == "Sum of fines per state per year" and options[option]:

                # Initialize indicies
                for state in info.states_codes:
                    # Get row for each state, add total for a state first
                    subdf = state_df.loc[state_df["State"] == state]
                    row = ['${:,.2f}'.format(subdf["Fine"].sum())]
                    for year in years:
                        yearstart, yearend = get_year_range(year, years, startdate, enddate)
                        df = get_inrange(subdf, yearstart, yearend)
                        row += ['${:,.2f}'.format(df["Fine"].sum())]
                    
                    dfs["State Fines"].loc[state] = row
                

            elif option == "Sum of violations per state per year" and options[option]:

                # Initialize indicies
                for state in info.states_codes:
                    # Get row for each state, add total for a state first
                    subdf = state_df.loc[state_df["State"] == state]
                    row = [count_violations_df(subdf)]
                    for year in years:
                        yearstart, yearend = get_year_range(year, years, startdate, enddate)
                        df = get_inrange(subdf, yearstart, yearend)
                        row += [count_violations_df(df)]
                    
                    dfs["State Violations"].loc[state] = row


            elif option == "Create sheet with all territories combined" and options[option]:
                # Get a dict of dfs by territory
                tdfs = sort_by_territories(state_df, territories)
                combined = pd.DataFrame()
                for terr in tdfs.keys():
                    combined = pd.concat([combined, tdfs[terr]])
                dfs["All Territories"] = combined.reset_index()

                # Set indicies properly
                dfs["All Territories"] = dfs["All Territories"].drop(["index"], axis=1)
                dfs["All Territories"] = dfs["All Territories"].set_index(["Territory", "State", "Organization", "Date"])

                # Set fine column as currency
                dfs["All Territories"]["Fine"] = dfs["All Territories"]["Fine"].apply(lambda x: 0 if x == "No Fine" else x)
                dfs["All Territories"]["Fine"] = pd.to_numeric(dfs["All Territories"]["Fine"], errors="coerce")
                dfs["All Territories"]["Fine"] =  dfs["All Territories"]["Fine"].apply(lambda x: '${:,.2f}'.format(float(x)))


            elif option == "All Violations" and options[option]:
                dfs["All"] = state_df.set_index(["State", "Organization", "Date"])

                # Set fine column as currency
                dfs["All"]["Fine"] = dfs["All"]["Fine"].apply(lambda x: 0 if x == "No Fine" else x)
                dfs["All"]["Fine"] =   dfs["All"]["Fine"].apply(lambda x: '${:,.2f}'.format(float(x)))


    # --- Write to an excel --- #

    # Excel workbook for each territory
    for terr in t_dfs.keys():
        # Makes the sheets more organized
        if not t_dfs[terr].empty:
            t_dfs[terr] = t_dfs[terr].set_index(["Territory", "State", "Organization", "Date"])

        t_dfs[terr].to_excel(outpath + "/" + terr + ".xlsx", sheet_name=terr)

    start_row = 1
    with pd.ExcelWriter(outpath + '/OptionalData.xlsx') as writer:

        # Excel sheet for each set of options
        for dfname in dfs.keys():
            if not dfs[dfname].empty:
                dfs[dfname].to_excel(writer, sheet_name=dfname)
                start_row += len(dfs[dfname])
                print(dfname)

        # Excel sheet for description of tags and severities
        items1 = list(tag_hash.items())
        items2 = list(info.severities.items())
        df1 = pd.DataFrame(items1, columns=["Tag", "Description"])
        df2 = pd.DataFrame(items2, columns=["Rank", "Description"])        
        df1.to_excel(writer, sheet_name="Descriptions", startrow=1, startcol=0)
        df2.to_excel(writer, sheet_name="Descriptions", startrow=len(df1.index)+5, startcol=0)

        writer.save()
        
        frame.instructions.config(text="Sheets made in " + str(int(time.time() - start_time)) + " seconds")
        time.sleep(3)
        frame.finish()

# Match up incidents with corresponding fines
def match_violations(state_df, fine_df):

    # Combine rows where state, org and date are the same but make a list of the tags and severities in order
    state_df = state_df.groupby(['State', 'Organization', 'Date']).agg({'Tag':lambda x: ','.join(x.astype(str)),\
        'Severity':lambda x: ','.join(x.astype(str)), 'Fine':'first', 'Url':'first'})
    
    # Format the fine_df, get rid of dupes, use it to update the state_df
    fine_df = fine_df.set_index(['State', 'Organization', 'Date'])
    fine_df = fine_df[~fine_df.index.duplicated()]
    state_df.update(fine_df)
    
    return state_df
    
    
# Converts states from full name into their two letter code
def convert_states(territories: Dict[String, List[String]]) -> Dict[String, List[String]]:
    
    # Get two letter state code hash
    codes = info.get_state_codes()
    keys = list(codes.keys())
    vals = list(codes.values())
    for territory in territories.keys():

        # Convert actual state name to it's two letter code
        states = []
        for state in territories[territory]:
            index = vals.index(state)
            code = keys[index]
            states.append(code)

        # Replace territory in original hash with the newly translated list of states
        territories[territory] = states
    
    return territories

# Sort violations by territories for when we make an excel sheet
# Also want to update territory values as we go through the dataframe
def sort_by_territories(state_df, territories):
    tdict = {}
    territorynames = list(territories.keys())

    # Create a hash where key is territory name and value is dataframe of related rows
    for name in territorynames:
        # Get subframe, add territory column and reset indicies
        tdict[name] = state_df[state_df["State"].isin(territories[name])]
        tdict[name].insert(0,"Territory", 0)
        tdict[name] = tdict[name].reset_index(drop=True)

        # Set territory column
        tdict[name] = tdict[name].replace({"Territory": 0}, name)

    return tdict

# Gets a subframe where only violations with dates in a certain range are included
def get_inrange(df, start, end):
    # Conversion to date time objects for comparison
    oldcol = df["Date"]
    df["Date"] =  pd.to_datetime(df["Date"], format='%m/%d/%Y')
    new = df.loc[(df["Date"] >= start) & (df["Date"] <= end)]

    # Then revert columns back to strings
    new["Date"] = new["Date"].dt.strftime('%m/%d/%Y')
    df["Date"] = oldcol

    return new 

# Counts the number of violations in a dataframe by checking number of tags
def count_violations_df(df):
    # Turn the tag column into a pandas series of lists
    vios = 0
    col = df["Tag"].apply(lambda x: x.strip('][').replace("'", "").split(",")) 
    for lst in col:
        vios += len(lst)

    return vios

# Returns a sorted list of tuples where each tuple contains an organization and total fines for a period    
def get_most_fined(df, num):
    sums = []
    # Get the facility names
    facilities = df["Organization"].unique()
    for name in facilities:
        # Convert fine column to a number so we can sum
        sum = df.loc[df["Organization"] == name, "Fine"].sum()
        if sum != 0:
            sums.append((name, sum))

    # Sort the list of tuples by fine
    sums = sorted(sums, key=lambda item: item[1], reverse=True)

    # Add place holders if not enough data
    if len(sums) < num:
        sums += [("NA", "$0")] * (num - len(sums))
    
    # Format the sums to currenices
    for i, sum in enumerate(sums):
        if sum[0] != "NA":
            temp = list(sum)
            temp[1] = '${:,.2f}'.format(temp[1])
            sums[i] = tuple(temp)

    return sums[:num]

# Returns a sorted list of tuples where each tuple contains an organization and total violations for a period    
def get_most_severe(df, num):
    sums = []
    # Get the facility names
    facilities = df["Organization"].unique()
    for name in facilities:
        curdf = df.loc[df["Organization"] == name]
        # Convert the severity column to numeric and sum it
        def convert(x):
            sum = 0
            lst = x.strip('][').replace("'", "").split(",") 
            for severity in lst:
                sum += info.severity_ranks[severity]

            return sum

        sum = curdf["Severity"].apply(lambda x: convert(x)).sum()
        if sum != 0:
            sums.append((name, sum))

    # Sort the list of tuples by violations
    sums = sorted(sums, key=lambda item: item[1], reverse=True)
    # Add place holders if not enough data
    if len(sums) < num:
        sums += [("NA", 0)] * (num - len(sums))

    return sums[:num]

# Get proper bounds for a date range
def get_year_range(year, years, startdate, enddate):
    if year == years[0]:
        yearstart = startdate
        yearend = datetime.strptime("12/31/"+str(year), "%m/%d/%Y")
    elif year == years[-1]:
        yearstart = datetime.strptime("01/01/"+str(year), "%m/%d/%Y")
        yearend = enddate
    else:
        yearstart = datetime.strptime("01/01/"+str(year), "%m/%d/%Y")
        yearend = datetime.strptime("12/31/"+str(year), "%m/%d/%Y")

    return (yearstart, yearend)


# Get violations that include chosen tags
def get_tag_range(df, tags):
    newdf = df
    newdf["Tag"] = df["Tag"].apply(lambda x: x.strip('][').replace("'", "").split(","))
    newdf["Severity"] = df["Severity"].apply(lambda x: x.strip('][').replace("'", "").split(","))
    newdf = newdf.reset_index()

    for i, row in newdf.iterrows():
        # Map each tag to its severity so that we know which severities to keep
        pairs = list(map(lambda x,y: (x,y), row["Tag"], row["Severity"]))
        
        # If there are no tags in a row that are ones chosen by the user, drop the row
        matches = [pair for pair in pairs if pair[0] in tags]
        if len(matches) == 0:
            newdf = newdf.drop(index=i)
        else:
            # Update the dataframe to only keep the correct tags and matches
            newdf.at[i, "Tag"] = str([pair[0] for pair in matches])
            newdf.at[i, "Severity"] = str([pair[1] for pair in matches])

    return newdf



