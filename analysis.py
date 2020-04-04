###
# Final analysis of data
###

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import statsmodels.api as sm

###
# Regression lines fit for each county for crowth curves of cv infections
#
# data from raw.githubusercontent.com/nytimes/covid-19-data/
# master/us-counties.csv
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
        X = X.apply(lambda x: x.toordinal())
        X1 = sm.add_constant(X)
        model = sm.OLS(Y, X1).fit()

        slope_data.append([c, model.params[1], tempsum])

county_slopes = pd.DataFrame(slope_data, columns=['fips',
                                                  'slope',
                                                  'days_over'])

###
# Import all the stuff and make one final dataframe
###
county_data = pd.read_csv('county_data.csv', dtype={'fips': 'string'},
                          parse_dates=['date_shutdown', 'date_surpass'])

county_data = county_data.merge(county_slopes)

for i in county_data.index:
    if (pd.isnull(county_data.loc[i, 'date_shutdown'])):
        county_data.loc[i, 'date_shutdown'] = datetime.today()

shut_int = county_data.date_shutdown.apply(lambda x: x.toordinal())
sur_int = county_data.date_surpass.apply(lambda x: x.toordinal())
time_diff = shut_int - sur_int
county_data['days_shutdown'] = time_diff

county_data['log_density'] = np.log(county_data.density)

# we could use
# 1. subtract min (or almost min)
# 2. divide by max
# 3: lambda x: sqrt(2x - x^2)

opac = county_data.days_over.copy()
opac = opac - opac.min() + .05
opac /= max(opac)
opac = opac ** (1/3)
# opac = math.sqrt(2*opac - opac**2)

# Histogram of log_density
fig1 = px.histogram(county_data, x='log_density')
fig1.show()

# Histogram of slopes
fig2 = px.histogram(county_data, x='slope')
fig2.show()

# Scatter of slope by log_density with opacity by days_over
fig3 = go.Figure(data=go.Scatter(x=county_data.log_density,
                                 y=county_data.slope,
                                 mode='markers',
                                 marker=dict(opacity=opac),
                                 text=county_data.days_over))
fig3.add_trace(
    go.Scatter(
        x=[1, 11],
        y=[.0619 + .0213*1, .0619+.0213*11],
        mode="lines",
        line=go.scatter.Line(color="blue"),
        showlegend=False)
)
fig3.show()


# Scatter of slope by days_shutdown opacity by days_over
fig4 = go.Figure(data=go.Scatter(x=county_data.days_shutdown,
                                 y=county_data.slope,
                                 mode='markers',
                                 marker=dict(opacity=opac),
                                 text=county_data.days_over))
fig4.show()

# Scatter of slope for each state (fips encoded) with colors by log_density
colors_duke = county_data.log_density
fig5 = go.Figure(data=go.Scatter(x=county_data.state,
                                 y=county_data.slope,
                                 mode='markers',
                                 marker=dict(opacity=opac,
                                             color=colors_duke),
                                 text=county_data.days_over))
fig5.show()

# box plots of slope by state
fig55 = px.box(county_data, x='state', y='slope')
fig55.show()

###
# Model 1: slope ~ density
###
X = county_data.log_density
Y = county_data.slope
X2 = sm.add_constant(X)
est_pre = sm.OLS(Y, X2)
est = est_pre.fit()
print(est.summary())

###
# Model 1a: slope ~ density
# weight on days in data per county
###
est_wls_pre = sm.WLS(Y, X2, opac)
est_wls = est_wls_pre.fit()
print(est_wls.summary())

###
# Model 2: slope ~ density + shutdown_days
###
X1 = county_data[['log_density', 'days_shutdown']]
Y = county_data.slope
X = sm.add_constant(X1)
est2_pre = sm.OLS(Y, X)
est2 = est2_pre.fit()
print(est2.summary())

###
# Model 2a: slope ~ density + shutdown_days
# weight on days in data per county
###
est2_wls_pre = sm.WLS(Y, X, opac)
est2_wls = est2_wls_pre.fit()
print(est2_wls.summary())

###
# Model 3: slope ~ density + state_group
###
X1 = county_data[['log_density', 'state']]
Y = county_data.slope
X = sm.add_constant(pd.get_dummies(X1, columns=['state']))
est3_pre = sm.WLS(Y, X)
est3 = est3_pre.fit()
print(est3.summary())

###
# Model 3a: slope ~ density + state_group
# weighted
###
X1 = county_data[['log_density', 'state']]
Y = county_data.slope
X = sm.add_constant(pd.get_dummies(X1, columns=['state']))
est3_wls_pre = sm.WLS(Y, X, weights=opac)
est3_wls = est3_wls_pre.fit()
print(est3_wls.summary())

# This is the info I got from running the above
# POS/NEG effect, OLS/WLS effect, STATE,   COEF, P-value
#              +,        OLS/WLS,  4 AZ, 0.0887,   0.031
#              +,        OLS/WLS, 16 ID, 0.1325,   0.012
#              +,        OLS/WLS, 22 LA, 0.1680,   0.000
#              +,        OLS/WLS, 25 MA, 0.1194,   0.001
#              +,        OLS/WLS, 26 MI, 0.0800,   0.010
#              -,            WLS, 31 NE,-0.1407,   0.000 (just 3 counties)
#              +,        OLS/WLS, 34 NJ, 0.0912,   0.005
#              +,        OLS/WLS, 36 NY, 0.0667,   0.018
#              +,        OLS/WLS, 42 PA, 0.1002,   0.001
#              -,            WLS, 55 WI,-0.0491,   0.013

###
# Model 4: slope ~ density + state_group_effect
# with state_group as a mixed effect
###

model = sm.MixedLM.from_formula('slope ~ log_density',
                                county_data,
                                groups=county_data.state)
result = model.fit()
print(result.summary())
