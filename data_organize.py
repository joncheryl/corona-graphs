###
# Putting all the data together
###

import pandas as pd

###
# Data for density
###

# land area by county
area_data = pd.read_csv("county_area.csv", dtype={'state': 'string',
                                                  'county': 'string'})
area_data['fips'] = area_data.state + area_data.county

# population by county
pop_data = pd.read_csv("co-est2019-alldata.csv", encoding='latin-1',
                       usecols={'STATE', 'COUNTY', 'POPESTIMATE2019'},
                       dtype={'STATE': 'string', 'COUNTY': 'string'})
pop_data = pop_data.rename(columns={'STATE': 'state',
                                    'COUNTY': 'county',
                                    'POPESTIMATE2019': 'population'})
pop_data['fips'] = pop_data.state + pop_data.county

# Join area and population tables and get density
all_data = area_data.merge(pop_data)

# convert square meters to square miles
all_data.area /= 2589988

# compute population density for each county
all_data['density'] = all_data.population / all_data.area

###
# Data for dates by states
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
            ('43', ''),
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
            ('56', '')]

sd = pd.DataFrame(shutdown, columns=['state', 'date_shutdown'], dtype='string')

# date when cases in each state surpassed N
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


# drop columns we no longer need
all_data = all_data.drop(columns=['area', 'county', 'population'])

#
# manually enter data for NYC and Kansas City
#
nyc_data = pd.DataFrame({'state': ['36'],
                         'name': ['New York City'],
                         'fips': ['36999'],
                         'density': [28188],
                         'date_shutdown': sd[sd.state == '36'].date_shutdown,
                         'date_surpass': sd[sd.state == '36'].date_surpass})

kc_data = pd.DataFrame({'state': ['29'],
                        'name': ['Kansas City'],
                        'fips': ['29999'],
                        'density': [1400],
                        'date_shutdown': sd[sd.state == '29'].date_shutdown,
                        'date_surpass': sd[sd.state == '29'].date_surpass})

all_data = pd.concat([all_data, nyc_data, kc_data], ignore_index=True)

all_data.to_csv('county_data.csv', index=False)
