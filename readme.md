# Coronavirus Analysis and Graphs

This repo contains two related things: 1) a Jupyter Notebook with analysis of some coronavirus data and 2) some Javascript that creates [plots](https://johnsherrill.heliohost.org/corona_graphs.html) of that data.

## 1) Analysis of population density's relationship to infection rates

Click this badge to see some analysis [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/joncheryl/corona-graphs/master?filepath=coronavirus-density-analysis.ipynb). If you open the notebook on binder and run it yourself, the analysis is up-to-date with the latest data.

### Sources
The data is from the [NYTimes github](https://github.com/nytimes/covid-19-data) and I scrapped population data from census.gov (specific locales in Python scripts).

### Goals

The goal is to become familiar with:
- the Statsmodels analysis library for Python

And practice:
- statistical analysis (creating, fitting, and interpreting linear models, weighted regressions, mixed effect models, analysing graphics, etc.)
- using the Jupyter Notebook format for presentation
- Python in general (pandas, numpy, plotly, the Emacs elpy package)
- scrapping data off web (with lxml Python package)

## 2) Plots of coronavirus data

A [collection](https://johnsherrill.heliohost.org/corona_graphs.html) of graphics for analysing the amount of testing for infection in each state.

### Sources

The main data is from https://covidtracking.com/ and I pulled population data (for calculating per-capita statistics) off of Wikipedia or something.

### Goals

The goal is to become familiar with:
- the Plotly graphing library for Javascript

And practice:
- interacting with JSON data
- Javascript
- A little SQL was used to join two little tables of population data and state two-letter codes.

And thinking about the use of graphics for statistical inference. I was curious about which states are doing the best testing, how fast testing is increasing in each state, etc.
