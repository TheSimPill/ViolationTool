from os.path import exists
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
from datetime import datetime
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

# Parses raw data, returns -> 
# {ST : (facility, date, writeup, fine, severity, tag)}
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
        col_list = ["Territory", "State", "Organization", "Date", "Tag", "Severity", "Fine", "Url"]
        df = df.reindex(columns=col_list)

        # Get rid of rows that don't have tags we want
        df = df[df['Tag'].isin(list(info.tagdata.keys()))]

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
        try:
            page = requests.request("GET", url, params=params, timeout=9)
        except:
            print("Connection to " + params["url"] + " failed, retrying with new proxy")
            params["session"] = random.randint(9000, 8000000)
        else:
            return (page, params)

# Match up incidents with corresponding fines
# state_df -> "Territory", "State", "Organization", "Date", "Tag", "Severity", "Fine", "Url"
# fine_df -> "State", "Organization", "Date", "Fine", "Url"
def match_violations(dfpath, frame, state_df, fine_df):
    
    # Convert dfs to dictionary lists
    finelst = fine_df.to_dict("record")
    statelst = state_df.to_dict("record")
    
    for fvio in finelst:
        for svio in statelst:
            if fvio["State"] == svio["State"] and fvio["Date"] == svio["Date"] and \
            fvio["Organization"] == svio["Organization"]:
                svio["Fine"] = fvio["Fine"]
                svio["Url"] = fvio["Url"]

    # Convert back to dataframe
    state_df = pd.DataFrame(statelst)

    if not exists(dfpath + "/dataframes"):
        os.mkdir(dfpath + "/dataframes")
    with open(dfpath + "/dataframes/state_df.pkl", 'wb') as outp:
            pickle.dump(state_df, outp, pickle.HIGHEST_PROTOCOL)

    #frame.instructions.config(text="Finished matching")
    time.sleep(1)
    print("Finished matching")
    #merge_violations(dfpath, frame, state_df)

# Merge rows that represent the same violation but with a different tag into on row
# Takes about 5 min 
def merge_violations(dfpath, frame, state_df):
    
    # Convert tags row into str
    state_df["Tag"] = state_df["Tag"].astype(str)

    #frame.instructions.config(text="Condensing data...")
    new = pd.DataFrame(columns=["Territory", "State", "Organization", "Date", "Tag", "Severity", "Fine", "Url"])
    for row in state_df.iterrows():
            # Grab rows where state, date, and organization are the same
            matches = state_df.loc[(state_df["State"] == row[1]["State"]) & (state_df["Date"] == row[1]["Date"]) & (state_df["Organization"] == row[1]["Organization"])]
            # So that only rows that have the unique columns we're checking for aren't processed
            if len(matches.index) > 1:
                
                # Get all tags into a list     
                c = matches["Tag"].tolist()
                # Combine all rows into 
                r = matches.groupby(matches["State"]).aggregate({"Territory":"first", "State":"first", \
                        "Organization":"first", "Date":"first", "Tag":"first", \
                        "Severity":"first", "Fine":"first", "Url":"first"})
                
                # Make the tag columns a string of the list of tags
                r["Tag"] = str(c)
                new.append(r)
                new = pd.concat([new, r])

                # Remove rows that were merged so we don't proccess them again later down the line
                state_df = state_df.merge(matches, how='left', indicator=True)
                state_df = state_df[state_df['_merge'] == 'left_only']
                state_df = state_df.drop("_merge", axis=1)

    # Reset indicies to be numbers
    new = new.reset_index()
    new = new.drop("index", axis=1)
    # Save newly condensed state df
    state_df = new
    with open(dfpath + "/dataframes/state_df.pkl", 'wb') as outp:
        pickle.dump(state_df, outp, pickle.HIGHEST_PROTOCOL)

    frame.instructions.config(text="Finished condensing")
    time.sleep(1)
    frame.advance_page()
        
# Sums up fines for a state
def sum_fines_state(state_incidents_list) -> int:
    sum = 0
    incidents_added = []
    for incident_tuple in state_incidents_list:
        tup = (incident_tuple[0], incident_tuple[1])
        year = incident_tuple[1][6:10]
        if (not tup in incidents_added) and incident_tuple[3] != "No Fine" and (year == "2019" or year == "2020" or year == "2021"):
            sum += int(incident_tuple[3])
            incidents_added.append(tup)

    return sum

# Breaks up a states fines into years 2019-2021
def state_fines_by_year(state_incidents_list) -> int:
    sum19 = 0
    sum20 = 0
    sum21 = 0
    incidents_added = []
    for incident_tuple in state_incidents_list:
        tup = (incident_tuple[0], incident_tuple[1])
        if (not tup in incidents_added) and incident_tuple[3] != "No Fine":
            year = incident_tuple[1][6:10]
            if year == "2019":
                sum19 += incident_tuple[3]
            elif year == "2020":
                sum20 += incident_tuple[3]
            elif year == "2021":
                sum21 += incident_tuple[3]
            incidents_added.append(tup)
    
    return (sum19, sum20, sum21)

# Writes total fines for each state to a hash
def all_states_fines_by_year(states_hash) -> dict:
    output = {}
    for state in states_hash.keys():
        output[state] = state_fines_by_year(states_hash[state])
    return output

# Gets total number of incidents for a state that resulted in a fine
def state_fine_incidents(state_incident_list):
    total = 0
    for i in range(0, len(state_incident_list)):
        year = state_incident_list[i][1][6:10]
        if state_incident_list[i][3] != "No Fine" and (year == "2019" or year == "2020" or year == "2021"):
            total += 1
    return total

# Gets number of incidents in a state by year
def state_violations_by_year(state_incident_list) -> tuple:
    sum19 = 0
    sum20 = 0
    sum21 = 0
    for incident_tuple in state_incident_list:
        year = incident_tuple[1][6:10]
        if year == "2019":
            sum19 += 1
        elif year == "2020":
            sum20 += 1
        elif year == "2021":
            sum21 += 1
            
    return (sum19, sum20, sum21) 

# Gets all violations for a state between 2019-21
def state_violations(state_incident_list) -> int:
    total = 0
    for incident_tuple in state_incident_list:
        year = incident_tuple[1][6:10]
        if year == "2019" or year == "2020" or year == "2021":
            total += 1

    return total

# Gets summary of information and writes to an excel sheet
'''
    Specifically, gets:
        Total violations in US, for each year starting in 2019
        Total violations per state, for each year starting in 2019
        Total dollar amount of fines in US
        Total dollar amount of fines per state, for each year starting in 2019

    * All of these numbers are based on relevant cases, which are the ones in the
    state hash, of course. 
'''
def summarize_totals(states_hash) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "NHI Summaries"
    ws["A1"] = "State"
    ws["C1"] = "Total Violations"
    ws["D1"] = "2021 Violations"
    ws["E1"] = "2020 Violations"
    ws["F1"] = "2019 Violations"
    ws["H1"] = "Total Fined Violations"
    ws["I1"] = "Total Fines"
    fine_total = 0
    ws["J1"] = "2021 Fines"
    fine_total_21 = 0
    ws["K1"] = "2020 Fines"
    fine_total_20 = 0
    ws["L1"] = "2019 Fines"
    fine_total_19 = 0

    # Populates rows
    counter = 2
    state_codes = info.get_state_codes(False)
    sorted_states = sorted(list(states_hash.keys()))
    for state in sorted_states:
        # Populates state column 
        cell = "A" + str(counter)
        ws[cell] = state_codes[state]
        # Populates Total Violations column
        cell = "C" + str(counter)
        ws[cell] = state_violations(states_hash[state])
        violations_tuple = state_violations_by_year(states_hash[state])
        # 2021 Violations
        cell = "D" + str(counter)
        ws[cell] = violations_tuple[2]
        # 2020 Violations
        cell = "E" + str(counter)
        ws[cell] = violations_tuple[1]
        # 2019 Violations
        cell = "F" + str(counter)
        ws[cell] = violations_tuple[0]
        # Total Fined Violations
        cell = "H" + str(counter)
        ws[cell] = state_fine_incidents(states_hash[state])
        # Total Fines
        cell = "I" + str(counter)
        total = sum_fines_state(states_hash[state])
        fine_total += total
        ws[cell] = "${:,.2f}".format(total)
        fines_tuple = state_fines_by_year(states_hash[state])
        # 2021 Fines
        cell = "J" + str(counter)
        fine_total_21 += fines_tuple[2]
        ws[cell] = "${:,.2f}".format(fines_tuple[2])
        # 2020 Fines
        cell = "K" + str(counter)
        fine_total_20 += fines_tuple[1]
        ws[cell] = "${:,.2f}".format(fines_tuple[1])
        # 2019 Fines
        cell = "L" + str(counter)
        fine_total_19 += fines_tuple[0]
        ws[cell] = "${:,.2f}".format(fines_tuple[0])
        counter += 1

    cell = "A" + str(counter)
    ws[cell] = "All of US"
    cell = "I" + str(counter)
    ws[cell] = fine_total
    cell = "J" + str(counter)
    ws[cell] = fine_total_21
    cell = "K" + str(counter)
    ws[cell] = fine_total_20
    cell = "L" + str(counter)
    ws[cell] = fine_total_19

    wb.save("BD Summary.xlsx")
      
# Gets a list of violations within certain date range, takes date in format MM/DD/YYYY
def get_state_date_range(state_incident_list, start, end) -> list:
    output = []
    start = datetime.strptime(start, '%m/%d/%Y')
    end = datetime.strptime(end, '%m/%d/%Y')
    for incident_tuple in state_incident_list:
        cur = datetime.strptime(incident_tuple[1], '%m/%d/%Y')
        if cur >= start and cur <= end:
            output.append(incident_tuple)

    return output

# For a given state, returns top organizations based on severity
def get_state_most_severe_organizations(state_incident_list, num_orgs) -> list:
    organizations = {}
    for incident_tuple in state_incident_list:
        if not incident_tuple[0] in organizations.keys():
            organizations[incident_tuple[0]] = info.severity_ranks[incident_tuple[4]]
        else:
            organizations[incident_tuple[0]] += info.severity_ranks[incident_tuple[4]]

    i = 0
    sorted_orgs = list(dict(sorted(organizations.items(), key=lambda item: item[1], reverse=True)).keys())
    output = []
    while i < num_orgs:
        output.append(sorted_orgs[i])
        i += 1

    return output

# For a given organization, returns most severe violations
def get_organization_most_severe_incidents(state_incident_list, num_vios, org_name) -> list:
    org_vios = []
    dates = []
    for incident_tuple in state_incident_list:
        if incident_tuple[0] == org_name and not incident_tuple[1] in dates:
            org_vios.append(incident_tuple)
            dates.append(incident_tuple[1])

    sorted_vios = sorted(org_vios, key=lambda incident: incident[4], reverse=True)
    output = []
    count = 0
    while count < num_vios:
        output.append(sorted_vios[count])
        count += 1

    return output

# For a given state, returns top organizations based on fines
def get_state_most_fined_organizations(state_incident_list, num_orgs) -> list:
    organizations = {}
    for incident_tuple in state_incident_list:
        if not incident_tuple[0] in organizations.keys():
            if incident_tuple[3] != "No Fine":
                organizations[incident_tuple[0]] = incident_tuple[3]
            else:
                organizations[incident_tuple[0]] = 0
        else:
            if incident_tuple[3] != "No Fine":
                organizations[incident_tuple[0]] += incident_tuple[3]

    i = 0
    sorted_orgs = list(dict(sorted(organizations.items(), key=lambda item: item[1], reverse=True)).keys())
    output = []
    while i < num_orgs:
        output.append(sorted_orgs[i])
        i += 1

    return output

# For a given organization, returns most fined violations
def get_organization_most_fined_incidents(state_incident_list, num_vios, org_name) -> list:
    org_vios = []
    dates = []
    for incident_tuple in state_incident_list:
        if incident_tuple[0] == org_name and incident_tuple[3] != "No Fine" and not incident_tuple[1] in dates:
            org_vios.append(incident_tuple)
            dates.append(incident_tuple[1])

    sorted_vios = sorted(org_vios, key=lambda incident: incident[3], reverse=True)
    output = []
    count = 0
    while count < num_vios and count < len(sorted_vios):
        output.append(sorted_vios[count])
        count += 1

    return output

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
          
# Send Email - just a test for now
def send_emails(states):
    msg = EmailMessage()
    msg['Subject'] = "BD DATA"
    msg['From'] = "freedalmond@gmail.com"  
    msg['To'] = "freedalmond@gmail.com"
    #info = format_top_fines_emails(states["MD"], 3, 2)
    #msg.set_content(info[0])
    info = format_top_fines_html("MD", states["MD"], 3, 2)
    msg.set_content(info[0], subtype="html")

    for filename in info[1]:
        with open(filename, 'rb') as file:
            msg.add_attachment(file.read(), maintype='application', subtype='octet-stream', filename=file.name)


    password = getpass.getpass(prompt='Password: ', stream=None) 
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("freedalmond@gmail.com", password)
        server.send_message(msg)

# Sorts violations in a state by date
def sort_by_date(state_incident_list):
    # Convert dates to objects
    for i in range(len(state_incident_list)):
        temp = list(state_incident_list[i])
        temp[1] = datetime.strptime(temp[1], '%m/%d/%Y')
        state_incident_list[i] = tuple(temp)

    return sorted(state_incident_list, key=lambda item: item[1], reverse=True)
    
# Creates excel file with all relevant cases
def summarize_data(states_hash, thisframe) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "NHI Summaries"
    ws["A1"] = "Territory"
    ws["B1"] = "State"
    ws["C1"] = "Facility"
    ws["D1"] = "Violation Date"
    ws["E1"] = "Violations"
    ws["F1"] = "Violation Link"
    ws["G1"] = "Violation Severity"
    ws["H1"] = "Fine"
    

    # Populates rows
    counter = 2
    state_codes = info.get_state_codes(False)
    for state in states_hash:
        by_date = sort_by_date(states_hash[state])
        same_as_last = False
        same = 1
        for incident_tuple in by_date:
            # Populates territory column 
            cell = "A" + str(counter)
            if state_codes[state] in info.territories["West"]:
                ws[cell] = "West"
            elif state_codes[state] in info.territories["Central"]:
                ws[cell] = "Central"
            else:
                ws[cell] = "East"
            # Populates State Column
            cell = "B" + str(counter)
            ws[cell] = state
            # Facility
            cell = "C" + str(counter)
            ws[cell] = incident_tuple[0]
            # Date
            cell = "D" + str(counter)

            ws[cell] = incident_tuple[1].strftime("%m/%d/%Y")

            if counter != 2 and ws["D" + str(counter - 1)].value == ws[cell].value:
                same += 1
                same_as_last = True
            elif same_as_last:
                ws.merge_cells("H" + str(counter - same) + ":H" + str(counter - 1))
                ws.cell(row = counter, column = 8).value = incident_tuple[3]
                same = 1
                same_as_last = False
            else: 
                # Fine
                cell = "H" + str(counter)
                ws[cell] = incident_tuple[3]
            
            # Violation
            cell = "E" + str(counter)
            ws[cell] = incident_tuple[5] + " - " + info.tagdata[incident_tuple[5]]
            # Violation Links
            cell = "F" + str(counter)
            ws[cell] = incident_tuple[-1]
            # Violation Severity
            cell = "G" + str(counter)
            ws[cell] = incident_tuple[4]
            counter += 1
            
    wb.save("BD Data.xlsx")
    thisframe.instructions("")

# For summarizing data using options chosen by user in the gui
# Creates excel file with all relevant cases
def summarize_gui(states_hash, options) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "NHI Summaries"
    ws["A1"] = "Territory"
    ws["B1"] = "State"
    ws["C1"] = "Facility"
    ws["D1"] = "Violation Date"
    ws["E1"] = "Violations"
    ws["F1"] = "Violation Link"
    ws["G1"] = "Violation Severity"
    ws["H1"] = "Fine"

    # Add options
    col = 9
    for option in options.keys():

        if option == "Total US Fines" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Total US Fines per year" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Total US Violations" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Total US Violations per year" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Top fined organizations per state" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1
        
        elif option == "Most severe organizations per state" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Sum of fines per state" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Sum of fines per state per year" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Sum of fined violations per state" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Sum of fined violations per state per year" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Most severe incidents per organization" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Incidents with highest fines per organization" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1

        elif option == "Create sheet with all territories combined" and options[option]:
            ws.cell(row=1, column=col).value = option
            col += 1
        
        
    # Populates rows
    counter = 2
    state_codes = info.get_state_codes(False)
    for state in states_hash:
        by_date = sort_by_date(states_hash[state])
        same_as_last = False
        same = 1
        for incident_tuple in by_date:
            # Populates territory column 
            cell = "A" + str(counter)
            if state_codes[state] in info.territories["West"]:
                ws[cell] = "West"
            elif state_codes[state] in info.territories["Central"]:
                ws[cell] = "Central"
            else:
                ws[cell] = "East"
            # Populates State Column
            cell = "B" + str(counter)
            ws[cell] = state
            # Facility
            cell = "C" + str(counter)
            ws[cell] = incident_tuple[0]
            # Date
            cell = "D" + str(counter)

            ws[cell] = incident_tuple[1].strftime("%m/%d/%Y")

            if counter != 2 and ws["D" + str(counter - 1)].value == ws[cell].value:
                same += 1
                same_as_last = True
            elif same_as_last:
                ws.merge_cells("H" + str(counter - same) + ":H" + str(counter - 1))
                ws.cell(row = counter, column = 8).value = incident_tuple[3]
                same = 1
                same_as_last = False
            else: 
                # Fine
                cell = "H" + str(counter)
                ws[cell] = incident_tuple[3]
            
            # Violation
            cell = "E" + str(counter)
            ws[cell] = incident_tuple[5] + " - " + info.tagdata[incident_tuple[5]]
            # Violation Links
            cell = "F" + str(counter)
            ws[cell] = incident_tuple[-1]
            # Violation Severity
            cell = "G" + str(counter)
            ws[cell] = incident_tuple[4]
            counter += 1
            
    wb.save("BD Data.xlsx")

# Sort violations by territories
def sort_by_territories(states_hash, east, central, west):
    evios = {}
    cvios = {}
    wvios = {}
    

    for state in states_hash.keys():
        if state in east:
            pass
        elif state in central:
            pass
        else:
            pass

# Makes the excel sheets based on options chosen by the user 
def make_sheets(frame, savepath, options, state_df, startdate, enddate):
    choices = 0
    chosen = {}

    # Get years in range that user chose
    years = list(range(startdate.year, enddate.year+1))

    # Dict that will hold new dataframes
    dfs = {}
    dfs["US"] = pd.DataFrame(columns=years)

    # Sort through options
    for option in options.keys():

        # Option 1
        if option == "US Fines" and options[option]:
            choices += 1

            # Rename indicies
            dfs["US"].loc["Fines"] = [0] * len(years)
            dfs["US"].loc["Violations"] = [0] * len(years)

            # Turn all values in fine column to numbers
            state_df["Fine"] = pd.to_numeric(state_df["Fine"], errors="coerce")
            oldcol = state_df["Date"]

            # Conversion to date time objects for comparison
            state_df['Date'] =  pd.to_datetime(state_df['Date'], format='%m/%d/%Y')

            # Total sum for dates in range
            sum = state_df.loc[(state_df["Date"] >= startdate) & (state_df["Date"] <= enddate), ["Fine"]].sum()[0]
            # Sum for each year
            for year in years:
                # The branches make sure we are within the users date range
                if year == years[0]:
                    yearstart = startdate
                    yearend = datetime.strptime("12/31/"+str(year), "%m/%d/%Y")
                elif year == years[-1]:
                    yearstart = datetime.strptime("01/01/"+str(year), "%m/%d/%Y")
                    yearend = enddate
                else:
                    yearstart = datetime.strptime("01/01/"+str(year), "%m/%d/%Y")
                    yearend = datetime.strptime("12/31/"+str(year), "%m/%d/%Y")

                # Get the year's sum
                dfs["US"].at["Fines", year] = state_df.loc[(state_df["Date"] >= yearstart) & (state_df["Date"] <= yearend), ["Fine"]].sum()[0] 

            # Change columns type back
            state_df['Date'] = oldcol
            
            # Add data to hash
            dfs["US"].insert(0, "Total", [sum, 0])
                 
            
            
        elif option == "Total US Violations" and options[option]:
            pass

        elif option == "Total US Violations per year" and options[option]:
            pass

        elif option == "Top fined organizations per state" and options[option]:
            pass
        
        elif option == "Most severe organizations per state" and options[option]:
            pass

        elif option == "Sum of fines per state" and options[option]:
            pass

        elif option == "Sum of fines per state per year" and options[option]:
            pass

        elif option == "Sum of fined violations per state" and options[option]:
            pass

        elif option == "Sum of fined violations per state per year" and options[option]:
            pass

        elif option == "Most severe incidents per organization" and options[option]:
            pass

        elif option == "Incidents with highest fines per organization" and options[option]:
            pass

        elif option == "Create sheet with all territories combined" and options[option]:
            pass

    # Write to an excel
    start_row = 1
    with pd.ExcelWriter('output.xlsx') as writer:
        for dfname in dfs.keys():
            dfs[dfname].to_excel(writer, sheet_name=dfname)
            start_row += len(dfs[dfname])
        writer.save()
    frame.finish()
     



