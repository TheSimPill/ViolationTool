import pandas as pd
from os import listdir

path = "C:/Users/FreddieG3/Documents/Job/Impruvon/Web Scraper Project GUI/venv/src/rawdata/"
files = listdir(path)
dfs = []
count = 0
for wb in files:
    dfs.append(pd.read_excel(path+wb, usecols="A,E,G,H,I", names=["Organization", "State", "Date", "Tag", "Severity"]))
    dfs[count].insert(5, "Fine", 0)
    dfs[count].insert(6, "Url", 0)
    dfs[count].insert(0, "Territory", 0)

    col_list = ["Territory", "State", "Organization", "Date", "Tag", "Severity", "Fine", "Url"]
    dfs[count] = dfs[count].reindex(columns=col_list)

    dfs[count] = dfs[count].sort_values(by=["Organization"])

    print(dfs[count].head())
    count += 1


result = pd.concat(dfs, ignore_index=True)
result = result.sort_values(by=["State"])
print(result.head())
print(result.tail())

"""
print(df.head())
df.insert(5, "Fine", 0)
df.insert(6, "Url", 0)
print(df.head())
"""