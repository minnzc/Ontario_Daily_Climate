# -*- coding: utf-8 -*-
"""
This script reads in the 2016 Canada Census divisions and subdivisions 
boundaries data and transforms the boundary coordinates from Lambert conformal 
conic projection format to a standard world geodetic system projection format 
(i.e. latitude, longitude).

Author:       Minnie Cui
Date written: 1 June 2020 
Last updated: ---
"""
###############################################################################
# DEFINE REQUIRED VARIABLES

# Project directory
directory = ("C:/Users/minni/Research/COVID_ON/AVG_CLIMATE/DATA")

# Census divisions file name variables
input_census_d = "lcd_000b16a_e.shp"
output_census_d = "census_divisions"

# Census subdivisions file name variables
input_census_sd = "lcsd000b16a_e.shp"
output_census_sd = "census_subdivisions"

###############################################################################
# IMPORT REQUIRED PACKAGES
import os
import pyproj as pj
from functions import applyTransform

# CHANGE PROJECT DIRECTORY
os.chdir(directory)

###############################################################################
# DEFINE TRANSFORMATION FUNCTION 

# Source coordinate system using parameters given by StatsCan
lcc = "+proj=lcc +lon_0=-91.866667 +lat_0=63.390675 +lat_1=49.000000 +lat_2=77.000000 +x_0=6200000 +y_0=3000000"

# Output coordinate system using system programming
wgs84 = "epsg:4326"

# Define transformation function 
lcc_to_wgs84 = pj.Transformer.from_proj(lcc, wgs84)
    
###############################################################################
# TRANSFORM CENSUS DIVISIONS DATA
applyTransform(lcc_to_wgs84, input_census_d, output_census_d)
print("\nCensus divisions boundary coordinates successfully transformed!")

# TRANSFORM CENSUS SUBDIVISIONS DATA
applyTransform(lcc_to_wgs84, input_census_sd, output_census_sd)
print("\nCensus subdivisions boundary coordinates successfully transformed!")

# Finish
print("\nEnd of coordinate transformations.")