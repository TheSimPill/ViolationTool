import pandas as pd
import pickle

# Tags usually have a zero in front
tagdata = {
    761 : "Label/Store Drugs & Biologicals",
    756 : "Drug Regimen Review, Report Irregular, Act On",
    757 : "Drug Regimen is Free From Unnecessary Drugs",
    759 : "Free of Medication Error Rate of 5% or More",
    758 : "Free from Unnec Psychotropic Meds/PRN Use",
    554 : "Resident Self-Admin Meds-Clinically Appropriate",
    760 : "Residents Are Free of Significant Med Errors",
    605 : "Right to be Free from Chemical Restraints"
}

severities = {
    "A" : "Isolated - No actual harm with potential for minimal harm",
    "B" : "Pattern - No actual harm with potential for minimal harm",
    "C" : "Widespread - No actual harm with potential for minimal harm",
    "D" : "Isolated - No actual harm with potential for more than minimal harm that is not immediate jeopardy",
    "E" : "Pattern - No actual harm with potential for more than minimal harm that is not immediate jeopardy",
    "F" : "Widespread - No actual harm with potential for more than minimal harm that is not immediate jeopardy",
    "G" : "Isolated - Actual harm that is not immediate",
    "H" : "Pattern - Actual harm that is not immediate",
    "I" : "Widespread - Actual harm that is not immediate",
    "J" : "Isolated - Immediate jeopardy to resident health or safety",
    "K" : "Pattern - Immediate jeopardy to resident health or safety",
    "L" : "Widespread - Immediate jeopardy to resident health or safety"
}

severity_ranks = {
    "A" : 1,
    "B" : 2,
    "C" : 3,
    "D" : 4,
    "E" : 5,
    "F" : 6,
    "G" : 7,
    "H" : 8,
    "I" : 9,
    "J" : 10,
    "K" : 11,
    "L" : 12
}

territories = {
    "West" : ["California", "Oregon", "Washington", "Nevada", "Idaho", "Utah", "Arizona", "Montana", "Alaska", "Hawaii"],

    "Central" : ["Wyoming", "Colorado", "New Mexico", "North Dakota", "South Dakota", "Nebraska", "Kansas", "Oklahoma",
                "Texas", "Minnesota", "Iowa", "Missouri", "Arkansas", "Louisiana", "Wisconsin", "Illinois", "Mississippi"],

    "East" : ["Michigan", "Indiana", "Kentucky", "Tennessee", "Alabama", "Ohio", "Georgia", "Florida", "South Carolina", "North Carolina",
             "Virginia", "West Virginia", "Delaware", "Maryland", "New Jersey", "Pennsylvania", "New York", "Connecticut", "Rhode Island",
             "Massachusetts", "Vermont", "New Hampshire", "Maine", "District of Columbia", "Guam"]
}

all_states = ["California", "Oregon", "Washington", "Nevada", "Idaho", "Utah", "Arizona", "Montana", "Alaska", "Hawaii", "Wyoming",
                "Colorado", "New Mexico", "North Dakota", "South Dakota", "Nebraska", "Kansas", "Oklahoma", "Texas", "Minnesota", "Iowa",
                "Missouri", "Arkansas", "Louisiana", "Wisconsin", "Illinois", "Mississippi", "Michigan", "Indiana", "Kentucky", "Tennessee", 
                "Alabama", "Ohio", "Georgia", "Florida", "South Carolina", "North Carolina", "Virginia", "West Virginia", "Delaware", "Maryland",
                "New Jersey", "Pennsylvania", "New York", "Connecticut", "Rhode Island", "Massachusetts", "Vermont", "New Hampshire", "Maine", "District of Columbia",
                "Guam"]
all_states = sorted(all_states)

# Creates hash map where key is two letter state code and value is full state
def get_state_codes(load) -> dict:
    state_codes = {}
    if load:    
        table = pd.read_html("https://www.faa.gov/air_traffic/publications/atpubs/cnt_html/appendix_a.html")[0]
        with open("state_codes_table.pkl", 'wb') as outp:
                pickle.dump(table, outp, pickle.HIGHEST_PROTOCOL)
    else:
        with open("state_codes_table.pkl", 'rb') as inp:
            table = pickle.load(inp)
               
    rows = table.values.tolist()
    for row in rows:
        state_codes[row[1]] = row[0]
        state_codes[row[3]] = row[2]
        state_codes[row[5]] = row[4]
    
    return state_codes

     


