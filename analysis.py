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
# Import all the stuff and make one final dataframe
###
county_data = pd.read_csv('county_data.csv', dtype={'fips': 'string'},
                          parse_dates=['date_shutdown', 'date_surpass'])

county_slopes = pd.read_csv('county_slopes.csv', dtype={'fips': 'string'},
                            skip_blank_lines=True)

county_data = county_data.merge(county_slopes)

for i in county_data.index:
    if (pd.isnull(county_data.loc[i, 'date_shutdown'])):
        county_data.loc[i, 'date_shutdown'] = datetime.today()

shut_int = county_data.date_shutdown.apply(lambda x: x.toordinal())
sur_int = county_data.date_surpass.apply(lambda x: x.toordinal())
time_diff = shut_int - sur_int
county_data['days'] = time_diff

county_data['log_density'] = np.log(county_data.density)

# we could use
# 1. subtract min (or almost min)
# 2. divide by max
# 3: lambda x: sqrt(2x - x^2)

opac = county_data.county_days_surpassed.copy()
opac = opac - opac.min() + .05
opac /= max(opac)
opac = opac ** (1/3)  # R-sq = 0.135
# opac = math.sqrt(2*opac - opac**2)

# opac = 1

fig = px.histogram(county_data, x='density')
# fig.show()

fig2 = px.histogram(county_data, x='slope')
# fig2.show()

fig22 = px.box(county_data, x='state', y='slope')
# fig22.show()

fig3 = go.Figure(data=go.Scatter(x=county_data.log_density,
                                 y=county_data.slope,
                                 mode='markers',
                                 marker=dict(opacity=opac),
                                 text=county_data.county_days_surpassed))

fig3.add_trace(
    go.Scatter(
        x=[1, 11],
        y=[.0619 + .0213*1, .0619+.0213*11],
        mode="lines",
        line=go.scatter.Line(color="blue"),
        showlegend=False)
)
fig3.show()


fig4 = go.Figure(data=go.Scatter(x=county_data.days,
                                 y=county_data.slope,
                                 mode='markers',
                                 marker=dict(opacity=opac),
                                 text=county_data.county_days_surpassed))
fig4.show()

# fig4 = px.scatter(county_data, x='days', y='slope', opac=)
# fig4.show()

colors_duke = county_data.log_density

fig5 = go.Figure(data=go.Scatter(x=county_data.state,
                                 y=county_data.slope,
                                 mode='markers',
                                 marker=dict(opacity=opac,
                                             color=colors_duke),
                                 text=county_data.county_days_surpassed))

# fig5 = px.scatter(county_data, x='state', y='slope', color='log_density')
fig5.show()

###
# Histogram of slopes
###

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
X1 = county_data[['log_density', 'days']]
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
