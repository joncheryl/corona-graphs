# This is a script to get the land area of counties data into a usable form.
# Way harder than I thought to find the info.
# This is gonna be a seperate script because it takes a minute to keep making
# requests from census.gov

import requests
import lxml.html as lh
import pandas as pd

states = ['al', 'ak', 'az', 'ar', 'as', 'ca', 'co', 'ct', 'de', 'dc', 'fl',
          'ga', 'gu', 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me',
          'md', 'ma', 'mi', 'mn', 'mp', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh',
          'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'pr', 'ri',
          'sc', 'sd', 'tn', 'tx', 'us', 'ut', 'vi', 'vt', 'va', 'wa', 'wv',
          'wi', 'wy']

# get headers for dataframe
page = requests.get('https://tigerweb.geo.census.gov/tigerwebmain/Files/'
                    'bas20/tigerweb_bas20_county_al.html')
doc = lh.fromstring(page.content)
tr_elements = doc.xpath('//tr')

col = []
for t in tr_elements[0]:
    name = t.text_content()
    col.append((name, []))

# add state data
for s in states:
    page = requests.get('https://tigerweb.geo.census.gov/tigerwebmain/Files/'
                        'bas20/tigerweb_bas20_county_' + s + '.html')
    doc = lh.fromstring(page.content)
    tr_elements = doc.xpath('//tr')

    # add data
    for j in range(1, len(tr_elements)):
        T = tr_elements[j]

        i = 0    # index of column in T
        for t in T.iterchildren():
            data = t.text_content()

            if i == 11:     # make land area a number
                data = int(data)

            col[i][1].append(data)
            i += 1

Dict = {title: column for (title, column) in col}
df = pd.DataFrame(Dict)

df = df[['STATE', 'COUNTY', 'NAME', 'AREALAND']]

df = df.rename(columns={'STATE': 'state', 'COUNTY': 'county', 'NAME': 'name',
                        'AREALAND': 'area'})

df.to_csv('area_data.csv', index=False)
