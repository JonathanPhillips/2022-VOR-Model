import pandas as pd
import requests
from bs4 import BeautifulSoup as BS

# Read data from compiled CSV from compile.py
df = pd.read_csv('data/all_compiled.csv', index_col=0)

# Clean the commas from some of the columns
comma_columns = ['RUSH_YD', 'REC_YD', 'PASS_YD']
for column in comma_columns:
  df[column] = df[column].str.replace(',', '').astype(float)

df['PPR'] = df['RUSH_YD'] + df['REC_YD'] + df['PASS_TD']*.04 + df['RUSH_TD'] + df['REC_TD']*6 \
+ df['PASS_TD']*4 + df['REC'] + df['FL']*-2 + df['INTS']*-2

# Scrape ADP from fantasypros.com
ADP_URL = 'https://www.fantasypros.com/nfl/adp/ppr-overall.php'

res = requests.get(ADP_URL)

soup = BS(res.content, 'html.parser')

table = soup.find('table', attrs={
    'id': 'data'
})

adp_df = pd.read_html(str(table))[0]

# Clean up the data, the 'Player Team (Bye) column
adp_df['Player Team (Bye)'] = adp_df['Player Team (Bye)'].str.replace(' O', '') # delete the ' O' that indicates a player is injured
adp_df['Player'] = adp_df['Player Team (Bye)'].apply(lambda x: ' '.join(x.split()[:-2])) # create Player column
adp_df['Team'] = adp_df['Player Team (Bye)'].apply(lambda x: x.split()[-2]) # create Team column

# Modify POS from RB1 to RB, WR1 to WR, etc
adp_df['POS'] = adp_df['POS'].str[:2]
adp_df = adp_df.loc[:, ['Player', 'Team', 'POS', 'Rank']]

# Limit the ADP list to 150 and Merge with Compiled
adp_cutoff = 150
adp_cutoff_df = adp_df.sort_values(by='Rank')[:adp_cutoff] #Sort by Rank
adp_cutoff_df = adp_cutoff_df.merge(df.loc[:, ['Player', 'Team', 'POS', 'PPR']], on=['Player', 'Team', 'POS']) #Merge the compiled CSV with ADP

# Create replacement values dict
replacement_values = {}
for _, row in adp_cutoff_df.iterrows():
  replacement_values[row['POS']] = row['PPR']

# Create VOR column
vor_df = df.loc[:, ['Player', 'Team', 'POS', 'PPR']].rename({'POS': 'Position'}, axis=1)
vor_df['VOR'] = vor_df.apply(lambda row: row['PPR'] - replacement_values[row['Position']], axis=1)

# Sort and display list by VOR
vor_df.sort_values(by='VOR', ascending=False).head(100)