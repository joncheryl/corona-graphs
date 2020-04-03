###
# Regression lines fit for each county for crowth curves of cv infections
###

import pandas as pd
import numpy as np
# import datetime as dt
from sklearn.linear_model import LinearRegression

###
# Import data from nytimes github
###

# just locally for now
c_days = pd.read_csv("us-counties-covid.csv", dtype={'fips': 'string'},
                     parse_dates=['date'])


# remove days that have <= N cases
N = 10
c_days = c_days[c_days.cases > N]

# Find log_cases
c_days['log_cases'] = np.log(c_days.cases)

###
# Deal with 7 exceptions (NYC, KC, AS, GU, MP, PR, VI)
###

###
# Run a regression for each county
###

counties = c_days.fips.unique()
counties = pd.DataFrame({'fips': counties})
counties['slope'] = np.nan

i = 0

for i in counties.index:
    temp = c_days.fips == counties.fips[i]

    # check if there's at least two data points to regress
    if temp.sum() > 1:
        X = c_days.date[temp]
        Y = c_days.log_cases[temp]

        # get dates in a usable format
        x_ar = X.apply(lambda x: x.toordinal())
        x_ar = x_ar.values.reshape(-1, 1)

        model = LinearRegression().fit(x_ar, Y)

        counties.loc[i, 'slope'] = model.coef_

counties.to_csv('county_slopes.csv', index=False)
