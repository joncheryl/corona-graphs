Coronavirus Analysis
=================
Analysis of population density's relationship to infection rates
--------------
Click this badge to see some analysis [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/joncheryl/corona-graphs/master?filepath=coronavirus-density-analysis.ipynb)

Description
------------------
A [collection](https://johnsherrill.heliohost.org/corona_graphs.html) of graphics for analysing the amount of testing for infection in each state. There's a big jupyter notebook in here now too with some statistical analysis.

Sources
----------------
The main data is from https://covidtracking.com/ and I pulled population data (for calculating per-capita statistics) off of Wikipedia or something.

Goals
----------------
The goal is to become familiar with:
- the Plotly graphing library for Javascript

And practice interacting with:
- JSON data
- Javascript
- A little SQL was used to join two little tables of population data and state two-letter codes.

And thinking about the use of graphics for statistical inference. I was curious about which states are doing the best testing, how fast testing is increasing in each state, etc.
