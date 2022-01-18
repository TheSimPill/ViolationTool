from openpyxl.descriptors.base import String
import openpyxl.workbook
from openpyxl.workbook.workbook import Workbook
import requests, os, zipfile, openpyxl
from pathlib import Path
import smtplib, time, getpass, random, pickle
from . import info

#from info import get_state_codes
from datetime import datetime
from email.message import EmailMessage

# Download raw data if user says yes, returns ->
# Nothing
def download(save_path):
	print('Download started')
	url = 'http://downloads.cms.gov/files/Full-Statement-of-Deficiencies-October-2021.zip'
	r = requests.get(url, allow_redirects=True)

	filename = 'Raw_Data.zip'
	filepath = os.path.join(save_path, filename)
	open(filepath, 'wb').write(r.content)
	print("Download Done")

	zip_path = save_path + '/Raw_Data.zip'
	with zipfile.ZipFile(zip_path, 'r') as zip_ref:
		zip_ref.extractall(save_path)
	print("Unzip Done")

	files_in_directory = os.listdir(save_path)
	filtered_files = [file for file in files_in_directory if not file.endswith(".xlsx")]
	for file in filtered_files:
		path_to_file = os.path.join(save_path, file)
		os.remove(path_to_file)
	print("Deleted Extra Files")

# Parses raw data, returns -> 
# {ST : (facility, date, writeup, fine, severity, tag)}
'''
    Cases that took place on the same date at the same facility
    are each counted as their own incident in the excel raw data.
'''
def parse_data(save_path):
    files = os.listdir(save_path)
    states = {}
    start_time = time.time()
    numtoload = input("How many Workbooks do you want to load? ")
    if numtoload == " " or int(numtoload) > len(files) or int(numtoload) < 1:
        print("Total Workbooks to load: " + str(len(files)))
        numtoload = len(files)
    else: 
        print("Total Workbooks to load: " + str(numtoload))

    loaded = 0
    for file in files:
        if loaded >= numtoload:
            break
        xlsx_file = Path(save_path, file)
        start = time.time()
        wb = openpyxl.load_workbook(xlsx_file)
        loaded += 1

        # Search rows for relevant tags
        for sheet in wb:
            for tag in info.tagdata.keys():
                for row in sheet.iter_rows(max_col=14,min_row=14):
                    for cell in row:
                        if cell.column == 8 and str(cell.value).find(tag) != -1:
                            state = str(sheet.cell(column=5, row=cell.row).value)
                            facility = str(sheet.cell(column=1, row=cell.row).value)
                            date = str(sheet.cell(column=7, row=cell.row).value)
                            writeup = "Date of violation: " + date + "\n"
                            writeup += "Tag: " + str(sheet.cell(column=8, row=cell.row).value) + " - " + info.tagdata[tag] + "\n"
                            severity = str(sheet.cell(column=9, row=cell.row).value)
                            writeup += "Severity: " + severity + " - " + info.severities[severity] + "\n"
                            writeup += "Facility: " + facility + "\n"
                            writeup += "Address: " + str(sheet.cell(column=3, row=cell.row).value) + "\n"
                            writeup += "\t\t" + str(sheet.cell(column=4, row=cell.row).value) + ", "
                            writeup += state + " " + str(sheet.cell(column=6, row=cell.row).value) + "\n"
                            writeup += "Description: \n" + str(sheet.cell(column=14, row=cell.row).value).replace('<BR/>','  ')
                            if state in states.keys():
                                states[state].append((facility, date, writeup, "No Fine", severity, tag, "No url"))
                            else:
                                states[state] = [(facility, date, writeup, "No Fine", severity, tag, "No url")]

        print("Workbook parsed in " + str(time.time() - start) + " seconds")

    for state in states.keys():
        print(state + ": " + str(len(states[state])))

    print("Parsed Raw Data in " + str(time.time() - start_time) + " seconds")

    # Makes sure no duplicate cases
    for state in states:
        states[state] = list(set(states[state]))
    return states

# Match up incidents with corresponding fines, returns -> 
# {ST : (facility, date, writeup, fine)} with updated fine values
'''
    Incidents that took place on the same date will each have a fine added to
    their tuple, even though all incidents at the same facility on the same
    date have on total fine applied to them.

    State hash: { "ST" : (facility, date, writeup, fine) list}
    Fine hash: { "ST" : (facility, date, fine) list }
'''
def match_fines(states_hash, fines_hash, save):
    for state in fines_hash.keys():
        for fine_incident_tuple in fines_hash[state]:
            if state in states_hash.keys():
                for i in range(0, len(states_hash[state])):
                    incident_tuple = states_hash[state][i]
                    # Check to see if facility and date are the same for an incident from each hash
                    if fine_incident_tuple[0] == incident_tuple[0] and fine_incident_tuple[1] == incident_tuple[1]:
                        temp = list(incident_tuple)
                        temp[3] = fine_incident_tuple[2]
                        states_hash[state][i] = tuple(temp)

    if save:
        with open("parsed_state_data.pkl", 'wb') as outp:
            pickle.dump(states_hash, outp, pickle.HIGHEST_PROTOCOL)
            print("Successfully matched fines and saved states hash")
    
    return states_hash
        
# Matches url hash returned from url_scraper with states_hash
def match_urls(states_hash, url_hash, save):
    for state in states_hash.keys():
        for i in range(len(states_hash[state])):
            if state in url_hash.keys():
                for truple in url_hash[state]:
                    incident_tuple = states_hash[state][i]
                    if incident_tuple[0] == truple[0] and incident_tuple[1] == truple[1]:
                        temp = list(incident_tuple)
                        temp[-1] = truple[-1]
                        states_hash[state][i] = tuple(temp)

    if save:
        with open("parsed_state_data.pkl", 'wb') as outp:
            pickle.dump(states_hash, outp, pickle.HIGHEST_PROTOCOL)
            print("Successfully matched urls and saved states hash")

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

# For a given organization, returns most severe violations
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
def summarize_data(states_hash) -> None:
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
