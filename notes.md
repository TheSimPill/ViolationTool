# Notes

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