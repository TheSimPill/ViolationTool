import pandas as pd
from os import listdir

file = r"/Users/Freddie/Impruvon/guiwebscraperproject/venv/rawdata/text2567_20211001_cms_reg1.xlsx"
df = pd.read_excel(file, usecols="A,E,G,H,I", names=["Organization", "State", "Date", "Tag", "Severity"])


print(df.head())
df.insert(5, "Fine", 0)
df.insert(6, "Url", 0)
print(df.head())
