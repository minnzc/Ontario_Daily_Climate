## Ontario COVID-19 average climate conditions by Census districts data set

Climate conditions variables (average temperature, minimum temperature, maximum temperature, and average precipitation) are recorded daily with a 2-3 day lag by weather stations. I take the mean of all weather stations non-null climate variable values contained within a Census subdivision. Then, I take the weighted mean of all Census subdivisions with non-null climate variable values within a Census division. Weights are frequency weights using 2019 Census subdivision population estimates. If a Census division contains no weather stations (8 of 49) or if weather stations in a district were shut down or for some reason did not record a measurement on a day, I take the mean of the 3 closest Census divisions with weather stations.

## Final data set

daily_cd_climate.csv

## Variables

- *cduid*: 4-digit Census division code (2-digit province code and 2-digit unique Census division code)
- *date*: date formatted YYYY-MM-DD
- *avg_temp*: average temperature in degrees Celsius
- *min_temp*: average minimum temperature in degrees Celsius
- *max_temp*: average maximum temperature in degrees Celsius
- *avg_precip*: average precipitation (rain and/or snow) in mm

## Data sources

*Census divisions and subdivisions boundary data*: https://www12.statcan.gc.ca/census-recensement/2011/geo/bound-limit/bound-limit-2016-eng.cfm
*Daily climate conditions data*: https://climate-change.canada.ca/climate-data/#/daily-climate-data
*Census subdivisions population estimates*: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710014201 

## Analysis code

Key elements of the analysis code are as follows:
- *getCDAverages.py*: a Python script run once daily to update climate contained in the *DATA* folder and calculate averages
- *functions.py*: a Python script containing all defined functions called upon by getCDAverages.py

## Contact
Minnie Cui
minniecui@bank-banque-canada.ca
