# -*- coding: utf-8 -*-
"""
This script defines various functions required by the main codes to generate
a daily average climate data set for Ontario using Census divisions.

Author:       Minnie Cui
Date written: 3 June 2020 
Last updated: ---
"""
###############################################################################
# IMPORT REQUIRED PACKAGES
import pandas as pd
import numpy as np
import shapefile as sf
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

###############################################################################
# FUNCTIONS REQUIRED BY transformCoordinates.py

# Define apply transformation function
def applyTransform(transformation, inputfile, outputfile):
    """
    Returns shapefile with transformed coordinates projections.
    
    Parameters
    ----------
    transformation : pyproj.Transformer.from_proj
        Function defining type of coordinate transformation to apply to the 
        shapes of inputfile.
    inputfile : shapefile
        Input shapefile whose shape coordinates will be transformed by 
        transformation.
    outputfile : shapefile
        Output shapefile with identical records as inputfile and shape 
        coordinates that have been transformed by transformation.

    Returns
    -------
    None.

    """
    # Read in input data
    data = sf.Reader("./" + outputfile + "/" + inputfile, encoding="latin1")
    
    # Write out required attributes
    shape_data = data.shapes()
    nonshape_data = data.records()
    
    # Write output data
    output = sf.Writer("./" + outputfile + "/" + outputfile)
    
    # Duplicate fields
    fields = data.fields
    for name in fields:
        if type(name) == "tuple":
            continue
        else:
            args = name
            output.field(*args)
    
    # Duplicate records
    for row in nonshape_data:
        args = row
        output.record(*args)
        
    # Apply transformations to polygons
    for i in range(0, len(shape_data)):
        points_list = []
        for pt in transformation.itransform(data.shape(i).points):
            points_list.append([pt[0], pt[1]])
        output.poly([points_list])
            
    # Save file
    output.close()

###############################################################################
# FUNCTIONS REQUIRED BY getCDAverages.py

# Define function to get average with given list
def getListAvg(num_list):
    """
    Returns the average of all values in list num_list.
    
    Parameters
    ----------
    num_list : list of floats
        A list of numbers

    Returns
    -------
    float
        Average of all values in num_list
    """
    if len(num_list) > 0:
        return sum(num_list) / len(num_list)
    else: 
        return np.nan

# Define function to get a dataframe of average daily climate (temp, precipitation) by Census subdivisions
def getSDAvgs(master, subdivisions, id_list, start_date, end_date):
    """
    Returns dataframe containing daily series of average climate variables by 
    Census subdivisions.
    
    Parameters
    ----------
    master : dataframe
        Dataframe containing daily temperature and precipitation readings from
        all Canadian weather stations from January 1, 2018 onwards.
    subdivisions : shapefile
        Shapefile containing Census subdivisions with WGS-84 coordinates.
    id_list : list of ints
        List containing indices based on subdivisions of Census subdivisions 
        for which to generate averages. 
    start_date : datetime
        Date to begin averages calculation.
    end_date : datetime
        Date to end averages calculation.

    Returns
    -------
    dataframe
        Panel dataframe containing time series daily average temperature and 
        precipitation variables by Census subdivision.
    """
    records = subdivisions.records()
    data = []
    for i in id_list:
        polygon = Polygon(subdivisions.shape(i).points)
        for single_date in pd.date_range(start=start_date, end=end_date):
            sub_master = master[master.LOCAL_DATE == single_date]
            day_list = []
            station_id = []
            avg_temp = []
            min_temp = []
            max_temp = []
            avg_precip = []
            count = 0
            for j in range(0, len(sub_master)):
                point = Point(sub_master.iloc[j, 0], sub_master.iloc[j, 1])
                if polygon.contains(point):
                    station_id.append(sub_master.iloc[j, 3])
                    avg_temp.append(sub_master.iloc[j, 10])
                    min_temp.append(sub_master.iloc[j, 12])
                    max_temp.append(sub_master.iloc[j, 14])
                    avg_precip.append(sub_master.iloc[j, 16])
                    count += 1
            for item in [0, 3, 5]:
                day_list.append(records[i][item])
            day_list.append(single_date)
            day_list.append(station_id)
            for var in [avg_temp, min_temp, max_temp, avg_precip]:
                day_list.append(getListAvg(var))
            data.append(day_list)
    col_names = ["csduid", "puid", "cduid", "date", "wsuid_list", "avg_temp", 
                 "min_temp", "max_temp", "avg_precip"]     
    return pd.DataFrame(data, columns = col_names)

# Define function to get weighted mean of all non-null values
def getWtAvg(df, col):
    """
    Gets weighted mean of all non-null values of given the variable in column 
    col in dataframe df. Weighting is done using Census subdivision population 
    estimates (column 10 of df).

    Parameters
    ----------
    df : dataframe
        Dataframe containing all subdivision climate data on a given day in a 
        given Census division.
    col : int
        Column index of variable to get weighted mean.

    Returns
    -------
    float
        Weighted mean or np.nan if all subdivisions are empty.

    """
    wt_sum = 0
    pop = 0
    count_empty = 0
    for i in range(0, len(df)):
        if str(df.iloc[i, col]) != "nan":
            wt_sum += df.iloc[i, col] * df.iloc[i, 10]
            pop += df.iloc[i, 10]
        else:
            count_empty += 1
    if count_empty == len(df):
        return np.nan
    else:
        return wt_sum / pop
    
# Define function to get a given number of closest divisions to a given division
def closestDivisions(polygon_dict, point_dict, num_closest):
        """
        Returns a dictionary that contains a list of num_closest Census 
        divisions to each key in polygon_dict.

        Parameters
        ----------
        polygon_dict : dictionary, int -> shapely.geometry.polygon.Polygon
            Dictionary of Census divisions without weather stations and the 
            corresponding division boundary polygon.
        point_dict : dictionary, int -> shapely.geometry.point.Point
            Dictionary of Census division codes not in polygon_dict and the 
            corresponding centroid of the division boundary polygon. 
        num_closest : int
            Number of divisions to identify as closest to each division in 
            polygon_dict. 

        Raises
        ------
        ValueError
            If num_closest is greater than the number of possible Census 
            divisions to search through in point_dict.

        Returns
        -------
        closest_divisions : dictionary, int -> list of ints
            Dictionary of Census divisions without weather stations and a list
            of division codes of the num_closest divisions.

        """
        if num_closest < len(point_dict) - 1:
            closest_divisions = {}
            for uid1 in polygon_dict.keys():
                distances = {}
                polygon = polygon_dict[uid1]
                for uid2 in point_dict.keys():
                    if uid1 != uid2:
                        point = point_dict[uid2]
                        distances[uid2] = point.distance(polygon)
                closest_list = []
                for _ in range(num_closest):
                    min_dis_uid = min(distances, key = distances.get)
                    closest_list.append(min_dis_uid)
                    del distances[min_dis_uid]
                closest_divisions[uid1] = closest_list
            return closest_divisions
        else:
            raise ValueError("ERROR! There are fewer Census divisions than the number of closest divisions you're looking for.")

# Define function to get unweighted mean of all non-null values
def getAvg(df, col):
        """
        Returns the average of all non-null values of the given variable in 
        column col in dataframe df.

        Parameters
        ----------
        df : dataframe
            Dataframe containing selected Census division climate data on a 
            given day.
        col : int
            Column index of variable to get average.

        Returns
        -------
        Float
            Mean or np.nan if all divisions are empty.

        """
        tot_sum = 0
        count = 0
        count_empty = 0
        for i in range(0, len(df)):
            if str(df.iloc[i, col]) != "nan":
                tot_sum += df.iloc[i, col]
                count += 1
            else:
                count_empty += 1
        if count_empty == len(df):
            return np.nan
        else:
            return tot_sum / count   