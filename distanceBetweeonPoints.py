import math
from decimal import *
from math import radians, cos, sin, asin, sqrt
COORDINATE_RESOLUTION = math.pow(10,7)
def distanceOnUnitSphere(lat1, long1, lat2, long2):
        """

        :param lat1:
        :param long1:
        :param lat2:
        :param long2:
        :return:
        """
        #Convert latitude and longitude to
        #spherical coordinates in radians.

        lat1 = parseCoordinate(lat1)
        long1 = parseCoordinate(long1)
        lat2 = parseCoordinate(lat1)
        long2 = parseCoordinate(long2)
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
        arc = math.acos( cos )

        # Remember to multiply arc by the radius of the earth
        # in your favorite set of units to get length.
        return arc *6373


def parseCoordinate (num):
        num = float(num)
        while (num > 100):
                num = num/10
        return num

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    return km

print (distanceOnUnitSphere(317794440, 352103580, 317945578, 352414009)) # zofim
# print (distanceOnUnitSphere(31.7794440, 35.2103580, 31.7945578, 35.2414009)) # zofim
#4581.040229589153