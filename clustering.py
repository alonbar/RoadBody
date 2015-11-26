import json
import pandas as pd
import datetime
import math
from sklearn.cluster import KMeans

def distance_on_unit_sphere(row):
        lat1 = row["latitudeE7"]*1.0/pow(10,7)
        long1 = row["longitudeE7"]*1.0/pow(10,7)
        lat2 = row["otherLatitudeE7"]*1.0/pow(10,7)
        long2 = row["otherLongitudeE7"]*1.0/pow(10,7)
        if lat1 == lat2 and long1 == long2:
            return 0.0
        #Convert latitude and longitude to
        #spherical coordinates in radians.
        degrees_to_radians = math.pi/180.0
         # phi = 90 - latitude
        phi1 = (90.0 - lat1)*degrees_to_radians
        phi2 = (90.0 - lat2)*degrees_to_radians

        # theta = longitude
        theta1 = long1*degrees_to_radians
        theta2 = long2*degrees_to_radians

        # Compute spherical distance from spherical coordinates.

        # For two locations in spherical coordinates
        # (1, theta, phi) and (1, theta', phi')
        # cosine( arc length ) =
        #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
        # distance = rho * arc length

        cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
               math.cos(phi1)*math.cos(phi2))
        if cos > 1.0:
            return 0
        arc = math.acos( cos )

        # Remember to multiply arc by the radius of the earth
        # in your favorite set of units to get length.
        return arc * 6373


def date_converter(datetime):
    week_day = datetime.weekday() # monday is 0, sunday is 6
    elapsed_time = math.ceil(datetime.time().microsecond / 1000) +\
               datetime.time().second * (10 ** 3) +\
               datetime.time().minute * (60 * (10 ** 6)) +\
               datetime.time().hour * (60 * 60 * (10 ** 6) + 
               week_day * (24 *60 * 60 * (10**6)))

    return elapsed_time

def group_by_location(df):
    s = pd.Series({
            "start_miliseconds" : df["weekly_miliseconds"].min(),    
            "end_miliseconds" : df["weekly_miliseconds"].max(),        
        })
    return s

def create(path):
    data = json.load(open(path))
    df = pd.DataFrame(data["locations"])

    df["weekly_miliseconds"] = df["timestampMs"].map(lambda x:float(x)/1000).map(datetime.datetime.fromtimestamp).apply(date_converter)
    return df

def clean(df , window=10, limit=0):
    df = df[df["latitudeE7"].notnull() & df["longitudeE7"].notnull() ].copy()
    def get_speed(idx):
        d = df.loc[idx:idx+window]
        return sum(d["distance"])/(max(d["otherTimestampMs"]) - min(d["timestampMs"]))

    df["timestampMs"] = df["timestampMs"].apply(float)
    df = df.sort("timestampMs")
    df.index = range(len(df.index))
    df['ii'] = df.index
    shifted = df[["latitudeE7", "longitudeE7", "timestampMs"]].shift()
    df["otherLatitudeE7"] = shifted["latitudeE7"]
    df["otherLongitudeE7"] = shifted["longitudeE7"]
    print ("2")
    df["otherTimestampMs"] = shifted["timestampMs"]
    df["distance"] = df.T.apply(distance_on_unit_sphere)
    df["speed"] = df.ii.apply(get_speed)
    #df["distance"]  = 0
    #df["speed"] = 1
    #df["speed"][0:100] = 0
    df = df[df["speed"] <= limit]
    print ("1")

    df = df.groupby(["latitudeE7", "longitudeE7"]).apply(group_by_location)
    df["weekday"] = df["start_miliseconds"].map(lambda x:float(x)/1000).map(datetime.datetime.fromtimestamp).apply(lambda x: x.weekday())
    print("3")
    return df.reset_index()


def cluster(df, max_clusters=10):
    means = (df["latitudeE7"].mean(), df["longitudeE7"].mean())
    stds = (df["latitudeE7"].copy().std(ddof=0), df["longitudeE7"].copy().std(ddof=0))
    #df['TIME_zscore'] = (df["weekly_miliseconds"].copy()-means[0])/stds[0]
    df['LAT_zscore'] = (df["latitudeE7"].copy()-means[0])/stds[0]
    df['LONG_zscore'] = (df["longitudeE7"].copy()-means[1])/stds[1]

    #old = df[["latitudeE7", "longitudeE7", "weekly_miliseconds"]].values
    X = df[["LAT_zscore", "LONG_zscore"]].values
    clf = KMeans(max_clusters)
    #print (X)
    clf.fit(X)
    clusters = clf.predict(X)

    centers = [(row[0]*stds[0]+means[0], row[1]*stds[1]+means[1]) for row in clf.cluster_centers_]
    df["center_lat"] = [centers[c][0] for c in clusters]
    df["center_long"] = [centers[c][1] for c in clusters]

    #center_test = df.groupby(["center_lat","center_long", "weekday"]).apply(lambda cluster: cluster["start_miliseconds"].var(ddof=0) > 100)
    #df[df[["center_lat", "center_long", "weekday"]].T.apply(lambda x: x.loc[x])]
    return df


def output(df, path, name, location_fields):
    df = df[["start_miliseconds", "end_miliseconds"]+location_fields]
    df.columns = ["start_miliseconds", "end_miliseconds","latitudeE7", "longitudeE7"]
    df["latitudeE7"] = df["latitudeE7"]/pow(10,7)
    df["longitudeE7"] = df["longitudeE7"]/pow(10,7)
    json.dump({ name : list(df.T.to_dict().values())}, open(path,"w"))

if __name__ == "__main__":
    print("Opening Data")
    df = create(r"C:\Users\user\Google Drive\chara\data\takeout2\Location History\LocationHistory.json")
    print("CLean Data")
    df = clean(df,5)
    output(df,r"C:\Users\user\Google Drive\chara\second_cleaned.json", "2", ["latitudeE7", "longitudeE7"])
    print("CLusetering")
    df = cluster(df,3)
    output(df, r"C:\Users\user\Google Drive\chara\second_clusters.json","2", ["center_lat", "center_long"])