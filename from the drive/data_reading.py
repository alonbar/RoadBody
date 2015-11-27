# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 19:44:04 2015

@author: galyona
"""

import pandas as pd
import json
import datetime
import numpy as np
import math
import time

beg= time.time()
def printTime():
    print(time.time()-beg)

import warnings
warnings.simplefilter(action = "ignore", category = RuntimeWarning)

from sklearn.cluster import KMeans

import matplotlib.pyplot as plt


START_TIME = 'start_t'
END_TIME = 'end_t'
LONG = 'longitudeE7'
LAT = 'latitudeE7'
TIME = 'day_time'
SLOT = 'slot'
LOCATION = 'locate'


def combine_cols(df,a,b,to_col):
    df[to_col] = df.T.apply(lambda x: (x[a],x[b]))
    return df

def get_stats(df):
    long_avg = df[LONG].mean()
    lat_avg = df[LAT].mean()
    diff_squared = (df[LONG] - long_avg)**2 + (df[LAT] - lat_avg)**2
    loc_var = diff_squared.mean()
    size= df["NORM_TIME"].count()
    loc_var_norm = loc_var/size

    return pd.Series({START_TIME : df[TIME].min(),
                      END_TIME: df[TIME].max(),
                      LONG : long_avg,
                      LAT : lat_avg,
                      "var" : loc_var,
                      "norm_var": loc_var_norm,
                      "size" : size
                     })


def get_var_by_slot(df):
    return df

def get_timeslots(df):
    slot_length = 600000000 * 3
    df[SLOT] = df["OLD_TIME"].apply(lambda x: math.floor(x/slot_length))
    return df

# gets a path to the JSON file of a user and returns a data frame with data.
def parse_data(path):
    print("parsing")
    raw = pd.io.json.read_json(path)
    #raw= pd.DataFrame(json.load(open(path)))
    printTime()
    df = raw['locations'].apply(pd.Series)
    printTime()
    df['timestampMs'] = df['timestampMs'].map(lambda x:float(x)/1000)
    df['datetime'] = df.timestampMs.map(datetime.datetime.fromtimestamp)

    df[LAT] = df[LAT]/float(1e7)
    df[LONG] = df[LONG]/float(1e7)
#    print (df)
    return df

# builds an object which we append to UserTable
def build_dict(df):
    stop_points = find_stop_points(df)
    return points_to_dict(stop_points)

def points_to_dict(points):
    # needs to return a dict which we will append to UserTable[userID]
    res=[]
    for point in points:
        point_dict = {"start_miliseconds":point[START_TIME] ,
                  "end_miliseconds":point[END_TIME] ,
                  LAT: point[LAT],
                  LONG:point[LONG],
                  "from_last_coordinate":{
                                 "activity":"", "expected_velocity": 4,
                                 "max_velocity": 3, "is_endpoint":True
                                 },
                  "other":{"heading":"INT"}
                  }
        res.append(point_dict)
    return res

def prepare_dfs(dir):
    path = []
    dfs = []
    for cur,dirs,files in os.walk(dir):
        for file in files:
            dfs.append(parse_data(file))
    return dfs


def create_users_dict(dfs):
    result = {}
    for i, df in enumerate(dfs):
        result[i] = build_dict(df)
    return result

# receives a datetime object and returns milliseconds from (0,0) on monday
def date_converter(datetime):
    week_day = datetime.weekday() # monday is 0, sunday is 6
    elapsed_time = math.ceil(datetime.time().microsecond / 1000) +\
                   datetime.time().second * (10 ** 3) +\
                   datetime.time().minute * (60 * (10 ** 6)) +\
                   datetime.time().hour * (60 * 60 * (10 ** 6))

    return elapsed_time




# receives a data frame and returns a list of stop points for 1 week.
def find_stop_points(df):
    """ returns a vector with each position representating the
     stop point averaged (somehow) over the input period.    """

    # first remove old entries from df.
    starting_date_str = "2015-10-18 05:00:00"
    starting_date_object = datetime.datetime.strptime(starting_date_str, '%Y-%m-%d %H:%M:%S')
#    print(df)
#    print("+++")
    print("1")
    df = df[df['datetime'] > starting_date_object]
#    print (df)
    print("2")
    df[TIME] = df['datetime'].apply(date_converter)


    print("3")
    df_data = df[[TIME, LAT, LONG]]
    print (df_data)
    #normazlize the columns of df_data
    df_data['TIME_zscore'] = (df_data[TIME].copy()-df_data[TIME].copy().mean())/df_data[TIME].copy().std(ddof=0)

    df_data['LAT_zscore'] = (df_data[LAT].copy()-df_data[LAT].copy().mean())/df_data[LAT].copy().std(ddof=0)


    df_data['LONG_zscore'] = (df_data[LONG].copy()-df_data[LONG].copy().mean())/df_data[LONG].copy().std(ddof=0)



    df_data_normalized = df_data[['TIME_zscore','LAT_zscore','LONG_zscore',TIME,LAT,LONG]]
    df_data_normalized.columns = ['NORM_TIME', LAT,LONG, "OLD_TIME","OLD_LAT","OLD_LONG"]

    print(df_data_normalized)



    print("4")
    df_data_normalized = get_timeslots(df_data_normalized)
    #df_data = combine_cols(df,LAT,LONG,LOCATION)
    # calculate var and speed for each time
    print("5")
    print(df_data_normalized[SLOT])

    df_data_normalized = df_data_normalized.groupby(SLOT).apply(get_stats)
    df_data_normalized = df_data_normalized[(df_data_normalized["size"] > 3)].sort("norm_var").head(100)
    import csv
    w = csv.writer(open("to_check.txt", "w"))
    w.writerows(df_data_normalized.T.apply(lambda x: (x["OLD_LAT"],x["OLD_LONG"])).tolist())
    return df_data_normalized[[START_TIME,END_TIME,LAT,LONG]].T.to_dict().values()
    #df_data = get_var_by_slot(df_data)
#    print ("_-----------------------")
#    print(df_data)
#    print ("_-----------------------")


    #kmeans
    k = 70
    """
    estimator = KMeans(init='k-means++', n_clusters = k, n_init=10)

    clusters = estimator.fit_predict(df_data_normalized)
#    for item in clusters:
#        print(item)
    """

    # averaging the clusters
    lat_sums = np.zeros(k)
    long_sums= np.zeros(k)
    start_time_points = [float("inf") for i in range(k)]
    end_time_points = [-float("inf") for i in range(k)]

    for i in range(len(df)):
        lat_sums[clusters[i]] +=  df[LAT][i]
        long_sums[clusters[i]] +=  df[LONG][i]
        start_time_points[clusters[i]] = min(start_time_points[clusters[i]], df[TIME][i])
        end_time_points[clusters[i]] = max(end_time_points[clusters[i]], df[TIME][i])


    df['cluster'] = clusters

    for i in range(k):
        pass

    count_clusters = [sum([1 for cluster in clusters if cluster == i]) for i in range(k)]

    lat_averages = [lat_sums[i]/count_clusters[i] for i in range(k)]
    #print (lat_averages)

    long_averages = [long_sums[i]/count_clusters[i] for i in range(k)]
    #print (long_averages)

    final_list =[]

    for i in range(k):
        final_list.append({LAT:lat_averages[i], LONG:long_averages[i],
                           END_TIME:end_time_points[i],START_TIME:start_time_points[i]})
#    print (final_list)

    return final_list

# main

path = "C:\\Users\\borgr\\Google Drive\\chara\\gal_shorter.json"
#path = "C:\\Users\\borgr\\Google Drive\\chara\\gal"
output= {1:build_dict(parse_data(path))}
print(output)
with open('id1','w') as fil:
    fil.write(str(output))

