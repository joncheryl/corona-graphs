###
# Regression lines fit for each county for crowth curves of cv infections
#
# data from raw.githubusercontent.com/nytimes/covid-19-data/
# master/us-counties.csv
###

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

###
# Import data from nytimes github
###

c_days = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/'
                     'master/us-counties.csv',
                     dtype={'fips': 'string'},
                     parse_dates=['date'])

###
# Deal with 7 exceptions (NYC, KC, AS, GU, MP, PR, VI)
###
c_days.loc[c_days.county == 'Kansas City', 'fips'] = '29999'
c_days.loc[c_days.county == 'New York City', 'fips'] = '36999'
c_days.loc[c_days.county == 'American Samoa', 'fips'] = '60999'
c_days.loc[c_days.county == 'Guam', 'fips'] = '66999'
c_days.loc[c_days.county == 'Northern Mariana Islands', 'fips'] = '69999'
c_days.loc[c_days.county == 'Puerto Rico', 'fips'] = '72999'
c_days.loc[c_days.county == 'Virgin Islands', 'fips'] = '78999'

# remove days that have <= N cases
N = 10
c_days = c_days[c_days.cases > N]

# Find log_cases
c_days['log_cases'] = np.log(c_days.cases)

###
# Run a regression for each county
###

counties = c_days.fips.unique()

slope_data = []

for c in counties:
    temp = c_days.fips == c
    tempsum = temp.sum()

    # check if there's at least two data points to regress
    if tempsum > 1:
        X = c_days.date[temp]
        Y = c_days.log_cases[temp]

        # get dates in a usable format
        x_ar = X.apply(lambda x: x.toordinal())
        x_ar = x_ar.values.reshape(-1, 1)

        model = LinearRegression().fit(x_ar, Y)

        slope_data.append([c, model.coef_[0], tempsum])

slopes = pd.DataFrame(slope_data, columns=['fips',
                                           'slope',
                                           'county_days_surpassed'])

slopes.to_csv('county_slopes.csv', index=False)
