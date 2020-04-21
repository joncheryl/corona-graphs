import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import datetime
############################################################
#
# DATA
#
############################################################

#
# google mobility data and join to get fips codes
#
mob = pd.read_json("mobility_2020-04-05.json")
mob = mob.rename(columns={'value': 'mobility'})

fips_alpha = pd.read_csv("county_fips_master.csv", encoding='latin-1')
fips_alpha['fips'] = fips_alpha.fips.astype('str').str.zfill(5)
fips_alpha = fips_alpha.drop(['long_name', 'sumlev', 'region', 'division',
                              'state', 'county', 'crosswalk', 'region_name',
                              'division_name'],
                             axis=1)
fips_alpha = fips_alpha.rename(columns={'county_name': 'county',
                                        'state_name': 'state'})

mob = mob.merge(fips_alpha, on=['state', 'county'])
mob = mob.drop(['state', 'page', 'change', 'changecalc'], axis=1)

# average 5 New York Burroughs cause nytimes data lumps them together as 36999
ny_temp = mob.loc[mob['fips'].isin(['36005', '36081', '36047', '36061',
                                    '36085'])]
ny_temp = ny_temp.groupby(['category', 'date']).mean().reset_index()
ny_temp['county'] = 'New York City'
ny_temp['fips'] = '36999'
ny_temp['state_abbr'] = 'NY'
mob = mob.append(ny_temp)

#
# nytimes case counts
#
c_days = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/'
                     'master/us-counties.csv',
                     dtype={'fips': 'string'},
                     parse_dates=['date'])
c_days = c_days.loc[~c_days.fips.isna()]

# Deal with 7 exceptions (NYC, KC, AS, GU, MP, PR, VI)
c_days.loc[c_days.county == 'Kansas City', 'fips'] = '29999'
c_days.loc[c_days.county == 'New York City', 'fips'] = '36999'
c_days.loc[c_days.county == 'American Samoa', 'fips'] = '60999'
c_days.loc[c_days.county == 'Guam', 'fips'] = '66999'
c_days.loc[c_days.county == 'Northern Mariana Islands', 'fips'] = '69999'
c_days.loc[c_days.county == 'Puerto Rico', 'fips'] = '72999'
c_days.loc[c_days.county == 'Virgin Islands', 'fips'] = '78999'

# remove days that have <= M cases and cleanup
M = 10
c_days = c_days[c_days.cases > M]
c_days = c_days.drop(['state', 'county', 'deaths'], axis=1)

# calculate r_star by county
fips = c_days.fips.unique()
c_days['r_star'] = 0
for f in fips:
    # do we need to order by date?
    c_days.loc[c_days.fips == f, 'r_star'] = \
        c_days.loc[c_days.fips == f, 'cases'].shift(-1) / \
        c_days.loc[c_days.fips == f, 'cases']
c_days = c_days.loc[~c_days.r_star.isna()]

# compute rolling average of r_star
c_days['r_star_avg'] = c_days.groupby('fips')['r_star']. \
    transform(lambda x: x.rolling(window=5, min_periods=1).mean())

# just look at one category
mob_df = mob.loc[mob.category == 'retail/recreation']

# merge mobility and case counts. 
mob_df = mob_df.merge(c_days, how='inner', on=['fips', 'date'])

#
# add density data
#
density_data = pd.read_csv("county_data.csv", usecols=['fips', 'density'],
                           dtype={'fips': 'string'})
density_data['log_density'] = np.log(density_data['density'])
mob_df = mob_df.merge(density_data, on='fips')

############################################################
#
# Graphics
#
############################################################

# mob_df = mob_df.loc[(mob_df.r_star < 2) & (mob_df.date > marchdate)]

boston = '25025'
nyc = '36999'
san_fran = '06075'
philly = '42101'
wayne = '26163'
chicago = '17031'
slc = '49035'
orleans = '22071'
providence = '44007'  # not in mobility dataset
nashville = '47037'
charlotte = '37119'  # not really in mobility dataset
seattle = '53033'
logan = '49005'  # nope
charleston = '45019'
la = '06037'
bergenNJ = '34003'
miami = '12086'
utah = '49049'
gallatin = '30031'
san_an = '48029'
portland_maine = '23005'

where = slc
mob_df_temp = mob_df.loc[mob_df.fips == where]
# mob_df_temp['r_star_avg'] = mob_df_temp['r_star'].rolling(window=5).mean()

# maybe some dates are no good
# marchdate = datetime.datetime.strptime('2020-04-05', '%Y-%m-%d')
# mob_df_temp = mob_df_temp.loc[mob_df_temp.date > '2020-03-13']

#
# r* over time
#
# px.line(mob_df_temp, x='date', y='r_star_avg', title=where).show()

#
# should have a graph with three axes for one county
# r*, tests per capita in state (in county if possible), mobility
#

# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Scatter(x=mob_df_temp.date, y=mob_df_temp.mobility, name="mobility"),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=mob_df_temp.date, y=mob_df_temp.r_star_avg, name="r*"),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text=where
)

# Set x-axis title
fig.update_xaxes(title_text="date", range=['2020-03-05', '2020-04-05'])

# Set y-axes titles
fig.update_yaxes(title_text="<b>primary</b> Mobility change",
                 range=[-90, 20],
                 secondary_y=False)
fig.update_yaxes(title_text="<b>secondary</b> r*",
                 range=[.95, 1.4],
                 secondary_y=True)

fig.show()

#
# San fran vs Salt Lake vs Miami vs New Orleans
#
# Note, similar sizes, but they get past 50 cases at different
# times relative to when mobility tanks
mob_df_ex = mob_df[mob_df.fips.isin(['22071', '49035', '06075', '48029'])]
px.line(mob_df_ex, x='date', y='cases', color='fips').show()

#
# Make shift-correlation plots for "where" county
#
X_fdsa = mob_df_temp.mobility
Y_fdsa = mob_df_temp.r_star_avg

N = 4
subtitle_text = ["Shift of " + str(i + 1) + " days" for i in range(0, N**2)]

fig1 = make_subplots(rows=N, cols=N,
                     subplot_titles=subtitle_text)

for i in range(0, N ** 2):
    fig1.add_trace(go.Scatter(x=X_fdsa.shift(i),
                              y=Y_fdsa,
                              mode='markers',
                              text=mob_df_temp.date),
                   row=i // N + 1, col=i % N + 1)
fig1.update_layout(height=900, width=900,
                   title_text=mob_df_temp.county.iloc[0])
fig1.show()

#
# r* vs shifted mobility
#
N = 4

shifted_mob = pd.DataFrame()

for i in range(0, N ** 2):
    for k, v in mob_df.groupby('fips'):
        temp_df = pd.concat([v['r_star'], v['mobility'].shift(i), v['fips'],
                             v['log_density'], v['state_abbr'],
                             v['r_star_avg']],
                            axis=1)
        temp_df['shifty'] = i
        shifted_mob = shifted_mob.append(temp_df)

for shit in range(5, 15):
    x_ness = shifted_mob.loc[shifted_mob.shifty == shit, 'mobility']
    y_ness = shifted_mob.loc[shifted_mob.shifty == shit, 'r_star_avg']
    t_ness = shifted_mob.loc[shifted_mob.shifty == shit, 'fips']
    fig3 = go.Figure(data=go.Scatter(x=x_ness,
                                     y=y_ness,
                                     text=t_ness,
                                     mode='markers'))
    fig3.update_xaxes(range=[-80, 0])
    fig3.update_yaxes(range=[.95, 1.5])
    fig3.update_layout(title="Mobility Shifted " + str(shit) + " days")

    fig3.show()
print("")
############################################################
#
# Regress r_star ~ density + mobility
#
############################################################

shit = 7
x_ness = shifted_mob.loc[shifted_mob.shifty == shit, 'mobility']
xx_ness = shifted_mob.loc[shifted_mob.shifty == shit, 'log_density']
#xxx_ness = shifted_mob.loc[shifted_mob.shifty == shit, 'state_abbr']
y_ness = shifted_mob.loc[shifted_mob.shifty == shit, 'r_star_avg']

XandY = pd.DataFrame({'r_star_avg': y_ness,
                      'log_density': xx_ness,
                      #'state_abbr': xxx_ness,
                      'mobility': x_ness})
XandY = XandY.dropna()
Y = XandY['r_star_avg']
X = XandY[['log_density', 'mobility']]  # , 'state_abbr']]
X = sm.add_constant(X)  # pd.get_dummies(X, columns=['state_abbr']))
model_one_pre = sm.OLS(Y, X)
model_one = model_one_pre.fit()
print(model_one.summary())
