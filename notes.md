# Notes

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

