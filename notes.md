# Notes

In may 2022, will have to look into a new way to sign into an email 

FEATURES TO ADD:
    

Trying to figure good way to merge tables
Tables are of uneven length, can extend columns if needed though

Current Idea:
    - Concat tables and then merge rows where state, date, and organization are the same
    
New Idea:
    - Convert dfs back to hashes and merge that way, then swtich back to df


Currently:
    Combing to dict lists, combining, then combining rows where only tag differs

Just made new statedf and made backups


Now need to properly match urls to state_df and then figure out how to merge similar rows

Figured out how to merge rows but doesn't seem to work properly
Need to get rid of rows that have been merged in state_df
Maybe check if a row we find is in the new df before we process 
    -> So as we go through state's rows, when we get a match, we check if the first row of the match 
        is already in new
    -> Or can do what im doing and just drop dupes at end, probably slower and doing unnecessary work

Decided to do a check if row has already been added to the new df

Need to figure out why dupes arent working

Finished merging process

Next as of 2/18: 
    Want to work on adding the excel sheet

Now: 
    Working on excel sheet option 1

    Working on territory sheets for make_excel

    Working on detecting if a date can have multiple of the same tag so I can count violations

    Working to top fined organizations per state:
        Going to just do all states
        Plan:
            Iter through all years in range
            Get in range for those dates
            Iter through all of the states in a list
            Get unique of the organizations row
            Make a subdf of each and sum the fine column
            Add their sum to list of tuples with name and then sum
            Sort and grab the top x organizations

        Currently:
        For excel:
            Figure out hierarchical so like:

                         Year1          Year2
                State -> Org1 -> Fine   Org1 -> Fine
                         Org2 -> Fine   Org2 -> Fine 
                         .... -> .....  .... -> .....


            and the hashmaps are:
                {year -> {state -> [organizations]}}
            
            so make the columns: y1, y2, ....
            and then the rows: state org1 fines

            check history to see how to do multiple columns one header

            Current problem:
                Line 653 Getting no loc for NoneType

            Finished option 3 I think 

            Option 7 - Most severe incidents per org
        State Total Year1 Year 2
              Org Date Tags Seve


Next task: Allow users to create however many territitories and set which states are in each

Adding terrs on new branch

finished dynamic territories

Add tags to include in sheets next

Need to check tag length enetered and make page update once user is done

Want to check if each tag entered is valid and tell user if not, so need to grab all tags from pdf


UPDATE:
    parse_data now gets all rows, not just ones with certain tags


LOGIC UPDATE:
    I'm thinking that excel sheets will only include data in date range, as well chosen tags.
    Just like date range, if there are no tags chosen then all will be included by default.
    Want to add a progress bar for merging and matching. Merging takes much longer now.


Next:
    Really want to consider going back to hashing values instead of putting them into dfs right away. It takes much, much longer. 
    Fixed lol


CURRENT PROBLEM:
    I'm not getting urls for certain homes, for example PROVIDENCE KODIAK ISLAND MED LTC. It seems to work
    when I isolate it though.

CURRENT PROBLEM:
    I'm going to save the page.content and try loading it and parsing with xml and html parsers and look for dif.
    Also want to see if how I save pages is giving none type errors. GOnna try changing bs(xxx, parser) to bs(xxx)

Found a bug when I convert severities, fixed it
KeyError: "['Territory'] not found in axis" for df["All"]


Trying to make webscraping not get stuck




Don't see any difference when I load pages with missing urls or even when I use html and xml parsers. So i think it's 
a problem with multithreading or loading pages. 

Going to start working on a static version for justin. I'll make the emails part work and then branch off for static app. 

Going to make emails only send the territory sheets.

Format of send_emails:

    will change make_excel to make one whole workbook per territory.
    Will send the names of these work books along with the hash that contains
    emails per territory over to send_emails. I will then iterate through that
    hash and send an excel sheet for a territory for every corresponding email in that territory.


Working on static page

For stack overflow:
I'm writing a program that will send multiple different emails to multiple addresses. However, I see that Google is changing its policy on letting third-party apps log in to a Gmail account soon. I'm worried that this will make my program useless at that point, so I'm wondering if there are any email service providers that are easy to connect to with python. 


Scrape got all urls, state_df is up to date

Missing data for 17 rows total, 3 orgs:
    GUAM MEMORIAL HOSPITAL AUTHORITY
    ADMIRAL’S POINTE CARE CENTER
    ARK HEALTHCARE & REHABILITATION AT GOVERNOR’S

The apostrophe throws off the html so the name on the website is not the same as in the excel sheets.
Guam memorial doesn't have data on website at all.


Having problem getting the logo for my program when I build it. Going to try giving it path to the logo again
and then if that doesnt work I'll try letting user set path themself. 

Going to try path to logo way.
May use mailjet to send emails. Posted on stack overflow about logo problem. May have to scrap the logo for now.


Trying to get logo to load in exe. Tried:

    Raw path in gui, one file and added file in options
        -> Worked until I moved logo from the src directory

    Raw path in gui, one dir and added file in options
        -> Worked until I moved logo from the src directory

    Resource path (stack overflow) method, didnt add file to options, used spec file: pyinstaller --noconfirm --onefile --console "/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/gui.py" gui.spec 
            # -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['gui.py'],
             pathex=['/Users/Freddie/Impruvon/guiwebscraperproject/venv/src'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break

a.datas += [('logo.png','/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/logo.png', 'Data')]
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )



Next step - make screen update while sheets are being made
Then - finalize email sending


INCLUDES DATAFRAMES:

pyinstaller --noconfirm --onefile --console --add-data "/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/logo.png:." --add-data "/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/dataframes:dataframes/"  "/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/gui.py"

Everything seems to be bundled into exe: now just need to test it and send to drew

To run:

    download the file
    drag it onto your desktop
    type cd Desktop
    type chmod +x ./gui
    type ./gui
    Enjoy yo self


Want to
    add greyed out buttons - done

    IN STATIC V1 BRANCH:
        all data button for dates - done
        change program name - done during exe
        add icon - done during exe
        remove email screen and other unecessary stuff
        write up document with details, how to use, assumptions

