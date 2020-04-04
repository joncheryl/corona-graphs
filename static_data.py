#
# Script to generate static data for analysis
#
# -Get the land area of counties data into a usable form.
# -Way harder than I thought to find the info.
# -https://tigerweb.geo.census.gov/tigerwebmain/TIGERweb_counties_current.html
#
# -Get population data from census.gov and compute density
#
# -Manually get shelter-in-place dates (by state) from nytimes April 2, 2020
#
# -Get date each state surpassed 10 cases from
# -https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv
#

import requests
import lxml.html as lh
import pandas as pd

states = ['al', 'ak', 'az', 'ar', 'as', 'ca', 'co', 'ct', 'de', 'dc', 'fl',
          'ga', 'gu', 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me',
          'md', 'ma', 'mi', 'mn', 'mp', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh',
          'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'pr', 'ri',
          'sc', 'sd', 'tn', 'tx', 'us', 'ut', 'vi', 'vt', 'va', 'wa', 'wv',
          'wi', 'wy']

# get headers
page = requests.get('https://tigerweb.geo.census.gov/tigerwebmain/Files/'
                    'bas20/tigerweb_bas20_county_al.html')
doc = lh.fromstring(page.content)
tr_elements = doc.xpath('//tr')

col = []
for t in tr_elements[0]:
    name = t.text_content()
    col.append((name, []))

# get data for each state
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

# clean up
Dict = {title: column for (title, column) in col}

area_data = pd.DataFrame(Dict)

area_data = area_data[['STATE', 'COUNTY', 'NAME', 'AREALAND']]

area_data = area_data.rename(columns={'STATE': 'state',
                                      'COUNTY': 'county',
                                      'NAME': 'name',
                                      'AREALAND': 'area'})

area_data.state.astype('str')
area_data.county.astype('str')

area_data['fips'] = area_data.state + area_data.county

###
# add population by county
# from https://www.census.gov/newsroom/press-kits/2020/
# pop-estimates-county-metro.html
###

pop_data = pd.read_csv("co-est2019-alldata.csv", encoding='latin-1',
                       usecols={'STATE', 'COUNTY', 'POPESTIMATE2019'},
                       dtype={'STATE': 'string', 'COUNTY': 'string'})

pop_data = pop_data.rename(columns={'STATE': 'state',
                                    'COUNTY': 'county',
                                    'POPESTIMATE2019': 'population'})

pop_data['fips'] = pop_data.state + pop_data.county

# join area and population tables
all_data = area_data.merge(pop_data)

# convert square meters to square miles and get density
all_data.area /= 2589988
all_data['density'] = all_data.population / all_data.area

# drop columns we no longer need
all_data = all_data.drop(columns=['area', 'county', 'population'])

# manually add New York City, Kansas City, and non-states
kc_data = pd.DataFrame({'state': ['29'],
                        'name': ['Kansas City'],
                        'fips': ['29999'],
                        'density': [1400]})
nyc_data = pd.DataFrame({'state': ['36'],
                         'name': ['New York City'],
                         'fips': ['36999'],
                         'density': [28188]})
as_data = pd.DataFrame({'state': ['60'],
                        'name': ['American Samoa'],
                        'fips': ['60999'],
                        'density': [670.8]})
gu_data = pd.DataFrame({'state': ['66'],
                        'name': ['Guam'],
                        'fips': ['66999'],
                        'density': [774.4]})
mp_data = pd.DataFrame({'state': ['69'],
                        'name': ['Northern Mariana Islands'],
                        'fips': ['69999'],
                        'density': [292.7]})
pr_data = pd.DataFrame({'state': ['72'],
                        'name': ['Puerto Rico'],
                        'fips': ['72999'],
                        'density': [909.1]})
vi_data = pd.DataFrame({'state': ['78'],
                        'name': ['Virgin Islands'],
                        'fips': ['78999'],
                        'density': [769.2]})

all_data = pd.concat([all_data, kc_data, nyc_data, as_data, gu_data, mp_data,
                      pr_data, vi_data], ignore_index=True)

###
# Data for dates by states
# manually from nytimes
###

# shelter-in-place order was put in place by state
shutdown = [('01', ''),
            ('02', '2020-03-28'),
            ('04', '2020-03-31'),
            ('05', ''),
            ('06', '2020-03-19'),
            ('08', '2020-03-26'),
            ('09', '2020-03-23'),
            ('10', '2020-03-24'),
            ('11', '2020-04-01'),
            ('12', '2020-04-03'),
            ('13', '2020-04-03'),
            ('15', '2020-03-25'),
            ('16', '2020-03-25'),
            ('17', '2020-03-21'),
            ('18', '2020-03-24'),
            ('19', ''),
            ('20', '2020-03-30'),
            ('21', '2020-03-26'),
            ('22', '2020-03-23'),
            ('23', '2020-04-02'),
            ('24', '2020-03-30'),
            ('25', '2020-03-24'),
            ('26', '2020-03-24'),
            ('27', '2020-03-27'),
            ('28', '2020-04-03'),
            ('29', ''),
            ('30', '2020-03-28'),
            ('31', ''),
            ('32', '2020-04-01'),
            ('33', '2020-03-27'),
            ('34', '2020-03-21'),
            ('35', '2020-03-24'),
            ('36', '2020-03-22'),
            ('37', '2020-03-30'),
            ('38', ''),
            ('39', '2020-03-23'),
            ('40', ''),
            ('41', '2020-03-23'),
            ('42', ''),
            ('44', '2020-03-28'),
            ('45', ''),
            ('46', ''),
            ('47', '2020-03-31'),
            ('48', ''),
            ('49', ''),
            ('50', '2020-03-25'),
            ('51', '2020-03-30'),
            ('53', '2020-03-23'),
            ('54', '2020-03-25'),
            ('55', ''),
            ('56', ''),
            ('69', ''),
            ('66', ''),
            ('72', ''),
            ('78', '')]

sd = pd.DataFrame(shutdown, columns=['state', 'date_shutdown'], dtype='string')

###
# date when cases in each state surpassed N
##
state_cases = pd.read_csv('https://raw.githubusercontent.com/nytimes/'
                          'covid-19-data/master/us-states.csv',
                          dtype={'fips': 'string'})
N = 10
states = state_cases.fips.unique()
sd['date_surpass'] = ''

for s in states:
    truth = (state_cases.fips == s) & (state_cases.cases > N)
    if sum(truth) > 0:
        sd.loc[sd.state == s, 'date_surpass'] = min(state_cases[truth].date)

all_data = all_data.merge(sd)

###
# Finish him
###

all_data.to_csv('county_data.csv', index=False)
