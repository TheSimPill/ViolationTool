# Used to strip a pdf that contains a table of deficiency tags.

from tabula import read_pdf
import pandas as pd
import collections
import pickle

# Grab the pdf as a list of dfs
df = read_pdf('ftags.pdf', pages='all')

# Up to tag F732
page1 = df[0]
# Rest of tags, starting at F740
page2 = df[2]

# Go through rows and match tags with description of tag
tags = {}
def parse_rows(start, end, step, spacing, page):
    for _, row in page.iterrows():
        for i in range(start, end, step):

            tag = row[i]
            desc = row[i+spacing]

            if isinstance(tag, str) and tag[0] == 'F':
                # Convert tags to desired form
                tag = list(tag)
                tag[0] = '0'
                tag = "".join(tag)
                tags[tag] = desc

parse_rows(0, 6, 2, 1, page1)
parse_rows(1, 13, 4, 2, page2)

# Now have a hash where key is string of tag with 0 in front and value is the description
tags = collections.OrderedDict(sorted(tags.items()))

with open("tag_hash.pkl", 'wb') as outp:
    pickle.dump(tags, outp, pickle.HIGHEST_PROTOCOL)




    








    
    




