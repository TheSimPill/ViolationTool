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