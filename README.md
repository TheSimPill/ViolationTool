# Nursing Home Data Processor
The purpose of this program is to allow a user to easily filter and view data on nursing home violations from https://projects.propublica.org/nursing-homes/ in a clear and concise format via excel sheets that it creates. This repository includes all necessary data, in the form of pandas dataframes, that a user needs to be able to use the full functionality of this program. The data set includes all 50 states, plus Guam and District of Columbia.

## A Quick Foreword
The data available spans from 2015-2021. It's a lot of data. Around 370,000 rows in an excel sheet, where each row represents a violation on a given date. Given the fact that this is a lot of data, if a user chooses to view all of it, the program will take significantly longer to make the excel sheets than if a user specifies what exactly they want out of that data. The different options that a user has are described below. The program will produce one excel sheet per territory, and an extra one for additional data.

## Filter by Territories
A user is able to dynamically input territories of whatever name they choose. A territory is simply a group of states that the user gets to set. As mentioned above, a user will get one excel sheet per territory that they create. If a user skips this option, the default territories are East, West, and Central. The 52 states are divided amongst these.

## Filter by Date Range
A user is able to specify a range of dates for which they want to see data for. This date range is inclusive, meaning the start and end dates will be included. A user may choose to use the whole date range available, which, as mentioned above, is from 2015-2021. An important note on this date range: it will apply to other options. For example, one other option is to include data on the fines for the entire US. The total shown will only include data in a user's date range! This includes individual years. For example, consider if a user sets their date range as 01/10/2019-01/01/2021. The total produced for the US will include 01/10/2019-12/31/2019 (inclusive), all of 2020, and 01/01/2021. The total shown for 2019 and 2021 individually would abides by the same metrics

## Filter by Tags
Each violation recorded by Nursing Home Inspect has a corresponding tag. A tag is simply a way of categorizing a violation based on its nature. For example, tag F757's description is "Drug Regimen is Free From Unnecessary Drugs". A pdf of all F-Tags is included in this repo as "Ftags.pdf". All tags will also be listed in the "OptionalData" excel sheet that is made each time you run the program. 

