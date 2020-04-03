###
# Regression lines fit for each county for crowth curves of cv infections
###

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

###
# Import data from nytimes github
###

# just locally for now
c_days = pd.read_csv("us-counties-covid.csv", dtype={'fips': 'string'},
                     parse_dates=['date'])

###
# Deal with 7 exceptions (NYC, KC, AS, GU, MP, PR, VI)
###

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

    # check if there's at least two data points to regress
    if temp.sum() > 1:
        X = c_days.date[temp]
        Y = c_days.log_cases[temp]

        # get dates in a usable format
        x_ar = X.apply(lambda x: x.toordinal())
        x_ar = x_ar.values.reshape(-1, 1)

        model = LinearRegression().fit(x_ar, Y)

        slope_data.append([c, model.coef_[0]])

slopes = pd.DataFrame(slope_data, columns=['fips', 'slope'])

slopes.to_csv('county_slopes.csv', index=False)
