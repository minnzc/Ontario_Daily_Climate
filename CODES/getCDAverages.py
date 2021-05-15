# -*- coding: utf-8 -*-
"""
This script pulls daily updates of Ontario temperatures and precipitation data,
appends daily updates to the master climate data file, and generates weighted
2016 Census divisions averages to creates a daily temperatures data set.

Author:       Minnie Cui
Date written: 4 June 2020 
Last updated: 15 May 2021
"""
###############################################################################
# DEFINE REQUIRED VARIABLES

# Project directory
directory = ("C:/Users/minni/Research/COVID_ON/AVG_CLIMATE/DATA")

# Census divisions file (created by transformCoordinates.py)
census_d = "census_divisions"

# Census subdivisions file (created by transformCoordinates.py)
census_sd = "census_subdivisions"

# Census subdivisions population estimates file (created by cleanPop.do)
pop_sd = "subdivisions_pop"

# Output file (average climate by Census divisions)
outputfile = "daily_cd_climate.csv"

# Number of districts to average if no weather station or if weather station not working
num_district = 3

###############################################################################
# IMPORT REQUIRED PACKAGES
import os
import pandas as pd
import numpy as np
from datetime import date, timedelta
from functions import getSDAvgs, getWtAvg, closestDivisions, getAvg
import shapefile as sf
from shapely.geometry.polygon import Polygon
  
# CHANGE PROJECT DIRECTORY
os.chdir(directory)
print("\nProject directory successfully set to: " + directory)

###############################################################################
# PULL TODAY'S DATA
print("\nGetting latest climate data...")

# Generate today's date and first day to pull variables
start = date(2018, 1, 1)
today = date.today()
todayfile = "daily_climate_" + str(start) + "_to_" + str(today) + ".csv"

# Remove old master data if in daily_climate folder
if len(os.listdir("./daily_climate")) != 0 and todayfile not in os.listdir("./daily_climate"):
    os.remove("./daily_climate/" + os.listdir("./daily_climate")[0])

# Update master data with today's data if it hasn't been pulled already
if todayfile not in os.listdir("./daily_climate"):
    url = "https://geo.weather.gc.ca/geomet/features/collections/climate-daily/items?time=2018-01-01%2000:00:00/" + str(today) + "%2000:00:00&PROVINCE_CODE=ON&sortby=PROVINCE_CODE,CLIMATE_IDENTIFIER,LOCAL_DATE&f=csv&limit=1500000&startindex=0"
    master = pd.read_csv(url, parse_dates = ["LOCAL_DATE"], dtype = str)
        
    # Save new master to directory
    master.to_csv("./daily_climate/" + todayfile, index = False) 
    print("\nRaw daily climate data has been updated in folder.")
else:
    master = pd.read_csv("./daily_climate/" + todayfile, parse_dates = ["LOCAL_DATE"], dtype = str)
    print("\nToday's climate data update is already in folder.")

# Change variable type for columns that are float or int
float_cols = [v for v in master if "_FLAG" not in v]
int_cols = ["LOCAL_YEAR", "LOCAL_MONTH", "LOCAL_DAY"]
for v in ["CLIMATE_IDENTIFIER", "STATION_NAME", "PROVINCE_CODE", "LOCAL_DATE", "ID"] + int_cols:
    float_cols.remove(v)
dtypes = {}
for v in float_cols:
    dtypes[v] = float
for v in int_cols:
    dtypes[v] = int
for col, col_type in dtypes.items():
    master[col] = master[col].astype(col_type)
        
###############################################################################
# GENERATE AVERAGE CLIMATE VARIABLES BY SUBDIVISION
print("\nGetting subdivisions climate variable averages...")

# Read in subdivisions shapefile data
subdivisions = sf.Reader("./" + census_sd + "/" + census_sd, encoding="latin1")
records = subdivisions.records()
print("\nSubdivisions boundary data loaded.")

# Generate list of subdivisions in Ontario
on_sds = list(i for i in range(0, len(records)) if records[i][3] == "35")

# Read in subdivisions 2019 population estimates data
pop = pd.read_csv("./" + pop_sd + "/" + pop_sd + ".csv")

# Generate subdivisions climate averages data 
if outputfile in os.listdir(".."):
    start = today - timedelta(10)
df = getSDAvgs(master, subdivisions, on_sds, start, today) 
print("\nSubdivisions averages dataset complete.")

# Change ID variable types to int
dtypes = {"csduid": int,
          "cduid": int}
for col, col_type in dtypes.items():
    df[col] = df[col].astype(col_type)

###############################################################################
# GENERATE AVERAGE CLIMATE VARIABLES BY CENSUS DIVISION, WEIGHTED BY SUBDIVISION POPULATION
print("\nGetting divisions averages, weighted by subdivision population...")

# Merge subdivision averages with subdivision population estimates
df_pop = pd.merge(df, pop, on = ["cduid", "csduid"])
print("\nSubdivisions averages dataset successfully merged with subdivisions population estimates.")

# Generate divisions climate weighted averages data 
data = []
cduid_list = list(dict.fromkeys(list(df_pop.cduid)))
for uid in cduid_list:
    sub_df = df_pop[df_pop.cduid == uid]
    for single_date in pd.date_range(start=start, end=today):
        sub_df_date = sub_df[sub_df.date == single_date]
        if len(sub_df_date) != 0:
            data.append([uid, single_date, getWtAvg(sub_df_date, 5), getWtAvg(sub_df_date, 6), getWtAvg(sub_df_date, 7), getWtAvg(sub_df_date, 8)])
        else:
            data.append([uid, single_date, np.nan, np.nan, np.nan, np.nan])
col_names = ["cduid", "date", "avg_temp", "min_temp", "max_temp", "avg_precip"]     
df_cd = pd.DataFrame(data, columns = col_names)
print("\nDivisions averages dataset complete.")

# Drop dates that have fewer than 3 Census districts with observations
for single_date in list(dict.fromkeys(list(df_cd.date))):
    sub_df = df_cd[df_cd.date == single_date]
    if sum(sub_df.avg_temp.isnull().values) > 49 - num_district:
        df_cd = df_cd[df_cd.date != single_date]

# Check how many divisions have no weather stations
all_null = []
for uid in cduid_list:
    sub_df = df_cd[df_cd.cduid == uid]
    if sub_df.avg_temp.isnull().all() == True and sub_df.min_temp.isnull().all() == True and sub_df.max_temp.isnull().all() == True and sub_df.avg_precip.isnull().all() == True:
        all_null.append(uid)
print("\n" + str(len(all_null)) + " have no average climate variables.")
print(str(all_null))

###############################################################################
# FOR CENSUS DIVISIONS WITH NO WEATHER STATIONS OR FAILED WEATHER STATIONS, GET AVERAGE OF 3 CLOSEST DIVISIONS
print("\nGetting average of " + str(num_district) + " closest divisions for divisions with no average climate variable...")

# Create dictionaries of all division codes and dates that need filling in
empty_list = []
for _ in range(len(cduid_list)):
    empty_list.append([])

           
# Read in divisions data
divisions = sf.Reader("./" + census_d + "/" + census_d, encoding="latin1")
records = divisions.records()
print("\nDivisions boundary data loaded.") 
   
# Get average of closest 3 weather stations on the given day
for v in range(2, 6):
    data = []
    fill = dict()
    sub_df_cd = df_cd
    for j in df_cd.index:
        if str(df_cd.loc[j][v]) == "nan":
            fill[(df_cd.loc[j].cduid, df_cd.loc[j].date)] = list(df_cd.loc[j].values)
            sub_df_cd = sub_df_cd.drop(j)        
    for uid in list(dict.fromkeys(list(key[0] for key in fill.keys()))):
        for single_date in list(key[1] for key in fill.keys() if key[0] == uid):
            sub_data = fill[(uid, single_date)]
            sub_df = sub_df_cd[sub_df_cd.date == single_date]
            centroids = {}
            for i in list(i for i in range(0, len(records)) if int(records[i][0]) in list(dict.fromkeys(list(sub_df.cduid)))):
                polygon = Polygon(divisions.shape(i).points)
                centroid = polygon.centroid
                centroids[int(records[i][0])] = centroid
            polygons = {}
            for i in list(i for i in range(0, len(records)) if int(records[i][0]) in [uid]):
               polygon = Polygon(divisions.shape(i).points)
               polygons[int(records[i][0])] = polygon 
            closest = closestDivisions(polygons, centroids, num_district)
            sub_df_date = sub_df[sub_df.cduid.isin(closest[uid])]
            sub_data[v] = getAvg(sub_df_date, v)
            data.append(sub_data)
    df_cd = sub_df_cd.append(pd.DataFrame(data, columns = col_names), ignore_index = True)

print("\nDivisions averages of divisions without weather stations dataset complete.")

###############################################################################
# SAVE FINAL DATA SET
print("\nSaving final divisions averages dataset...")

# Save divisions average data to file
if start == date(2018, 1, 1):
    df_cd = df_cd.sort_values(by = ['cduid', 'date'], ignore_index = True)
    df_cd.to_csv("../" + outputfile, index = False)
else: 
    df_cd_master = pd.read_csv("../" + outputfile, parse_dates = ["date"])
    for single_date in pd.date_range(start=start, end=today):
        df_cd_master = df_cd_master[df_cd_master.date != single_date]
    df_cd_master = df_cd_master.append(df_cd, ignore_index = True)
    df_cd_master = df_cd_master.drop_duplicates(keep = "last")
    df_cd_master = df_cd_master.sort_values(by = ['cduid', 'date'], ignore_index = True)
    df_cd_master.to_csv("../" + outputfile, index = False)

print("\nFinal divisions averages dataset successfully saved.")
print("\nEnd of code.")