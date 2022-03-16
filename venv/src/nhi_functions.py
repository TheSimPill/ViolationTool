from os.path import exists
from typing import Dict, List
from openpyxl.descriptors.base import String
import openpyxl.workbook
from openpyxl.workbook.workbook import Workbook
import requests, os, zipfile, openpyxl
from pathlib import Path
import smtplib, time, getpass, random, pickle
import info
from tkinter.ttk import Progressbar, Label
import pandas as pd
from numpy import int64


#from info import get_state_codes
from datetime import datetime, date
from email.message import EmailMessage

# Download raw data if user says yes, returns ->
# Nothing
def download(frame, save_path):
    
    frame.instructions.config(text="Download Started")
    frame.instructions2.grid_forget()
    frame.dl_btn.grid_forget()
    '''
    url = 'http://downloads.cms.gov/files/Full-Statement-of-Deficiencies-October-2021.zip'
    r = requests.get(url, allow_redirects=True)

    filename = 'Raw_Data.zip'
    filepath = os.path.join(save_path, filename)
    open(filepath, 'wb').write(r.content)
    frame.instructions.config(text="Download Done")

    zip_path = save_path + '/Raw_Data.zip'
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(save_path)
    frame.instructions.config(text="Unzip Done")

    files_in_directory = os.listdir(save_path)
    filtered_files = [file for file in files_in_directory if not file.endswith(".xlsx")]
    for file in filtered_files:
        path_to_file = os.path.join(save_path, file)
        os.remove(path_to_file)
    '''
    frame.instructions.config(text="Deleted Extra Files")
    time.sleep(1.5)
    frame.instructions.config(text="Parsing Data")
    time.sleep(1.5)
    parse_data(frame, save_path)

'''
    Cases that took place on the same date at the same facility
    are each counted as their own incident in the excel raw data.
'''
def parse_data(frame, save_path):
    files = os.listdir(save_path)
    start_time = time.time() 
    numtoload = len(files)
    
    frame.instructions.config(text="Total Workbooks to load: " + str(numtoload))
    frame.dl_btn.grid_forget()

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
        start = time.time()

        # Make excel file into a dataframe
        df = pd.read_excel(save_path+"/"+file, usecols="A,E,G,H,I", names=["Organization", "State", "Date", "Tag", "Severity"])
        df.insert(5, "Fine", 0)
        df.insert(6, "Url", "")
        df.insert(0, "Territory", 0)
        
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

    frame.instructions.config(text="Parsed Raw Data in " + str(int(time.time() - start_time)) + " seconds")
    time.sleep(2)
    
    # Create a hashes folder in chosen directory and save the states hash
    if not exists(save_path + "/dataframes"):
        os.mkdir(save_path + "/dataframes")
    with open(save_path + "/dataframes/state_df.pkl", 'wb') as outp:
            pickle.dump(result, outp, pickle.HIGHEST_PROTOCOL)

    frame.instructions.config(text="Saved as state_df.pkl in dataframes folder")
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

# Match up incidents with corresponding fines
def match_violations(dfpath, frame, state_df, fine_df):

    # Combine rows where state, org and date are the same but make a list of the tags and severities in order
    state_df = state_df.groupby(['State', 'Organization', 'Date']).agg({'Tag':lambda x: ','.join(x.astype(str)),\
        'Severity':lambda x: ','.join(x.astype(str)), 'Fine':'first', 'Url':'first'})
    
    # Format the fine_df, get rid of dupes, use it to update the state_df
    fine_df = fine_df.set_index(['State', 'Organization', 'Date'])
    fine_df = fine_df[~fine_df.index.duplicated()]
    state_df.update(fine_df)
    
    if not exists(dfpath + "/dataframes"):
        os.mkdir(dfpath + "/dataframes")
    with open(dfpath + "/dataframes/state_df.pkl", 'wb') as outp:
            pickle.dump(state_df, outp, pickle.HIGHEST_PROTOCOL)

    frame.instructions.config(text="Finished matching")
    time.sleep(1)
    frame.advance_page()
    
'''
 For a given state, formats a message of form:

 MOST SEVERE:
 1. Organization Name: 
   Date of Violation1:
   Tag1:
   Severity1:
   Fine1: 
   Description (link to it)
'''
# Formats message with top fined and top severe organizations for a state, along with top violations for each
# State list: (facility, date, writeup, fine, severity) list
def format_top_fines_emails(state_incidents_list, num_orgs, num_vios) -> String:
    severe_orgs = get_state_most_severe_organizations(state_incidents_list, num_orgs)
    fine_orgs = get_state_most_fined_organizations(state_incidents_list, num_orgs)
    descriptions = []
    msg = "MOST SEVERE:\n"
    counter = 1
    for i in range(len(severe_orgs)):
        msg += str(i+1) + ".  Organization Name: " + severe_orgs[i] +"\n"
        incidents = get_organization_most_severe_incidents(state_incidents_list, num_vios, severe_orgs[i])
        for j in range(len(incidents)):
            msg += "\t  Date of Violation " + str(j+1) + ": " + incidents[j][1] + "\n"
            msg += "\t  Tag " + str(j+1) + ": " + str(incidents[j][5]) + ", " + info.tagdata[incidents[j][5]] + "\n"
            msg += "\t  Severity " + str(j+1) + ": " + incidents[j][4] + ", " + info.severities[incidents[j][4]] + "\n"
            if incidents[j][3] != "No Fine":
                msg += "\t  Fine " + str(j+1) + ": " + "${:,.2f}".format(int(incidents[j][3])) + "\n"
            else:
                msg += "\t  Fine " + str(j+1) + ": " + incidents[j][3] + "\n"
            msg += "\t  Description: " + "In file \"severe" + str(counter) + ".txt\" below" + "\n\n"
            filename = "severe" + str(counter) + ".txt"
            counter += 1
            txt_file = open(filename, "w")
            txt_file.write(incidents[j][2])
            txt_file.close()
            descriptions.append(filename)

    msg += "\n\nMOST FINED:\n"
    counter = 1
    for i in range(len(fine_orgs)):
        msg += str(i+1) + ".  Organization Name: " + fine_orgs[i] + "\n"
        incidents = get_organization_most_fined_incidents(state_incidents_list, num_vios, fine_orgs[i])
        for j in range(len(incidents)):
            msg += "\t  Date of Violation " + str(j+1) + ": " + incidents[j][1] + "\n"
            msg += "\t  Tag " + str(j+1) + ": " + str(incidents[j][5]) + ", " + info.tagdata[incidents[j][5]] + "\n"
            msg += "\t  Severity " + str(j+1) + ": " + incidents[j][4] + ", " + info.severities[incidents[j][4]] + "\n"
            msg += "\t  Fine " + str(j+1) + ": " + "${:,.2f}".format(int(incidents[j][3])) + "\n"
            msg += "\t  Description: " + "In file \"fined" + str(counter) + ".txt\" below" + "\n\n"
            filename = "fined" + str(counter) + ".txt"
            counter += 1
            txt_file = open(filename, "w")
            txt_file.write(incidents[j][2])
            txt_file.close()
            descriptions.append(filename)

    return (msg, descriptions)

def format_top_fines_html(state, state_incidents_list, num_orgs, num_vios) -> String:
    severe_orgs = get_state_most_severe_organizations(state_incidents_list, num_orgs)
    fine_orgs = get_state_most_fined_organizations(state_incidents_list, num_orgs)
    descriptions = []
    msg = ''' 
    <!DOCTYPE html>
    <html>
        <body>
            <div style="background-color:#eee;padding:10px 20px;">
                <h2 style="font-family:Georgia, 'Times New Roman', Times, serif;color#454349;text-align:center;font-size:50px">TOP MOST SEVERE & MOST FINED ORGANIZATIONS FOR '''
    msg += state + "</h2>&nbsp;&nbsp;"
                
    counter = 1
    msg += "<h1 style=\"font-size:20px\">MOST SEVERE</h1><ol>"
    for i in range(len(severe_orgs)):
        msg += "<li style=\"font-family:Georgia, \'Times New Roman\', Times, serif;color#454349;font-weight:bold;\"> Organization Name: " + severe_orgs[i] + "</li>\n"
        incidents = get_organization_most_severe_incidents(state_incidents_list, num_vios, severe_orgs[i])
        for j in range(len(incidents)):
            msg += "<ul><li>Date of Violation " + str(j+1) + ": " + incidents[j][1] + "</li>\n"
            msg += "<li>Tag " + str(j+1) + ": " + str(incidents[j][5]) + ", " + info.tagdata[incidents[j][5]] + "</li>\n"
            msg += "<li>Severity " + str(j+1) + ": " + incidents[j][4] + ", " + info.severities[incidents[j][4]] + "</li>\n"
            if incidents[j][3] != "No Fine":
                msg += "<li>Fine " + str(j+1) + ": " + "${:,.2f}".format(int(incidents[j][3])) + "</li>\n"
            else:
                msg += "<li>Fine " + str(j+1) + ": " + incidents[j][3] + "</li>\n"
            msg += "<li>Description: " + "In file \"severe" + str(counter) + ".txt\" below" + "</li></ul>&nbsp;&nbsp;\n\n"
            filename = "severe" + str(counter) + ".txt"
            counter += 1
            txt_file = open(filename, "w")
            txt_file.write(incidents[j][2])
            txt_file.close()
            descriptions.append(filename)

    counter = 1
    msg += "</ol><h1 style=\"font-size:20px\">MOST FINED</h1><ol>"
    for i in range(len(severe_orgs)):
        msg += "<li style=\"font-family:Georgia, \'Times New Roman\', Times, serif;color#454349;font-weight:bold;\"> Organization Name: " + fine_orgs[i] + "</li>\n"
        incidents = get_organization_most_fined_incidents(state_incidents_list, num_vios, fine_orgs[i])
        for j in range(len(incidents)):
            msg += "<ul><li>Date of Violation " + str(j+1) + ": " + incidents[j][1] + "</li>\n"
            msg += "<li>Tag " + str(j+1) + ": " + str(incidents[j][5]) + ", " + info.tagdata[incidents[j][5]] + "</li>\n"
            msg += "<li>Severity " + str(j+1) + ": " + incidents[j][4] + ", " + info.severities[incidents[j][4]] + "</li>\n"
            if incidents[j][3] != "No Fine":
                msg += "<li>Fine " + str(j+1) + ": " + "${:,.2f}".format(int(incidents[j][3])) + "</li>\n"
            else:
                msg += "<li>Fine " + str(j+1) + ": " + incidents[j][3] + "</li>\n"
            msg += "<li>Description: " + "In file \"fined" + str(counter) + ".txt\" below" + "</li></ul>&nbsp;&nbsp;\n\n"
            filename = "fined" + str(counter) + ".txt"
            counter += 1
            txt_file = open(filename, "w")
            txt_file.write(incidents[j][2])
            txt_file.close()
            descriptions.append(filename)
    
    msg += "</ol></div></body></html>"
    return (msg, descriptions)
          
# Send Emails to BD Team
def send_emails(frame, emails):

    # Start the server and get the password
    path = r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\sheets" 
    password = getpass.getpass(prompt='Password: ', stream=None) 
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("freedalmond@gmail.com", password)

        # Will make an email for each territory
        for territory in emails.keys():
            msg = EmailMessage()
            msg['Subject'] = "BD DATA"
            msg['From'] = "freedalmond@gmail.com"  
            msg['To'] = ", ".join(emails[territory])

            with open(path + "\\" + territory + ".xlsx", 'rb') as file:
                msg.add_attachment(file.read(), maintype='application', subtype='octet-stream', filename=territory)
            
            server.send_message(msg)
    
    print("Sent")

    
# Makes the excel sheets based on options chosen by the user 
def make_sheets(frame, savepath, options, state_df, startdate, enddate, territories, tags, outpath):

    # Update the screen
    frame.instructions.config(text="Making sheets...")
    frame.instructions2.grid_forget()
    frame.sheet_btn.grid_forget()

    # Change state_df's indicies back to numbers for now
    state_df = state_df.reset_index()
    # Load in tag data 
    with open(r"/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/dataframes/tag_hash.pkl", 'rb') as inp:
        tag_hash = pickle.load(inp)

    # Setting defaults for missing user choices

    # Get years in range that user chose, or set a default range
    if None in {startdate, enddate}:
       startdate = datetime.strptime("01/01/2017", '%m/%d/%Y')
       enddate = datetime.strftime(date.today(), '%m/%d/%Y')
       enddate = datetime.strptime(enddate, '%m/%d/%Y')
       #enddate = datetime.strptime("12/31/2021", '%m/%d/%Y')

    # Check to see if tags were chosen and if not use all
    if len(tags) == 0:
        tags = list(tag_hash.keys())
    
    # Check to see if territories were chosen and use default if not
    if len(territories) == 0:
        territories = info.territories
    # Convert states to their two letter code
    territories = convert_states(territories)

    years = list(range(startdate.year, enddate.year+1))
    dfs = {}
    choices = 0

    # Make a dataframe for each territory (saved in a hash) and then only keep violations in date range
    t_dfs = sort_by_territories(state_df, territories)
    if not None in {startdate, enddate}:
        for terr in t_dfs.keys():
            t_dfs[terr] = get_inrange(t_dfs[terr], startdate, enddate)
            # Convert fine column to currency
            t_dfs[terr]["Fine"] = t_dfs[terr]["Fine"].apply(lambda x: 0 if x == "No Fine" else x)
            t_dfs[terr]["Fine"] = pd.to_numeric(t_dfs[terr]["Fine"], errors="coerce")
            t_dfs[terr]["Fine"] =  t_dfs[terr]["Fine"].apply(lambda x: '${:,.2f}'.format(float(x)))

    # Get dates in range for state df
    if not None in {startdate, enddate}:
        state_df = get_inrange(state_df, startdate, enddate)

    # Optional sheets
    dfs["US"] = pd.DataFrame(columns=(["Total"] + years))
    dfs["Most Fined"] = pd.DataFrame()
    dfs["Most Severe"] = pd.DataFrame()
    dfs["State Fines"] = pd.DataFrame(columns=(["Total"] + years))
    dfs["State Violations"] = pd.DataFrame(columns=(["Total"] + years))
    dfs["All Territories"] = pd.DataFrame()
    dfs["All"] = pd.DataFrame()

    # Convert fine column to numeric
    state_df["Fine"] = state_df["Fine"].apply(lambda x: 0 if x == "No Fine" else x)
    state_df["Fine"] = pd.to_numeric(state_df["Fine"], errors="coerce")

    # Sort through options
    if options != None:
        for option in options.keys():

    
            if option == "US Fines" and options[option]:
                choices += 1

                # Initialize indicies
                dfs["US"].loc["Fines"] = [0] * (len(dfs["US"].columns))
                
                # Conversion to date time objects for comparison
                oldcol = state_df["Date"]
                state_df['Date'] =  pd.to_datetime(state_df['Date'], format='%m/%d/%Y')

                # Total sum
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
                choices += 1

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
                choices += 1

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
                choices += 1

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
                choices += 1

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
                choices += 1

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
                #print(dfs["All"]["Fine"])
                #dfs["All"]["Fine"] = pd.to_numeric(dfs["All"]["Fine"], errors="coerce")
                dfs["All"]["Fine"] =   dfs["All"]["Fine"].apply(lambda x: '${:,.2f}'.format(float(x)))


    # --- Write to an excel --- #

    # Excel workbook for each territory
    for terr in t_dfs.keys():
        # Makes the sheets more organized
        t_dfs[terr] = t_dfs[terr].set_index(["Territory", "State", "Organization", "Date"]) 
        t_dfs[terr].to_excel(outpath + "/" + terr + ".xlsx", sheet_name=terr)

    start_row = 1
    with pd.ExcelWriter(outpath + '/OptionalData.xlsx') as writer:

        # Excel sheet for each set of options
        for dfname in dfs.keys():
            if not dfs[dfname].empty:
                dfs[dfname].to_excel(writer, sheet_name=dfname)
                start_row += len(dfs[dfname])

        # Excel sheet for description of tags and severities
        items1 = list(tag_hash.items())
        items2 = list(info.severities.items())
        df1 = pd.DataFrame(items1, columns=["Tag", "Description"])
        df2 = pd.DataFrame(items2, columns=["Rank", "Description"])        
        df1.to_excel(writer, sheet_name="Descriptions", startrow=1, startcol=0)
        df2.to_excel(writer, sheet_name="Descriptions", startrow=len(df1.index)+5, startcol=0)

        writer.save()
        frame.finish(territories)
    
# Converts states from full name into their two letter code
def convert_states(territories: Dict[String, List[String]]) -> Dict[String, List[String]]:
    
    # Get two letter state code hash
    codes = info.get_state_codes(False)
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
    col = df["Tag"].apply(lambda x: x.strip('][').replace("'", "").split(", ")) 
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
        df["Fine"] = pd.to_numeric(df["Fine"], errors="coerce")
        sum = df.loc[df["Organization"] == name, "Fine"].sum()
        if sum != 0:
            sums.append((name, '${:,.2f}'.format(sum)))

    # Sort the list of tuples by fine
    sums = sorted(sums, key=lambda item: item[1], reverse=True)
    # Add place holders if not enough data
    if len(sums) < num:
        sums += [("NA", "$0")] * (num - len(sums))

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
