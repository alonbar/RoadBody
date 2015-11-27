import math
import sys
import json
# from bokeh.sampledata import us_states, us_counties, unemployment
# from bokeh.plotting import *
COORDINATE_RESOLUTION = math.pow(10,7)
class TimeGrid(object):
    """

    """
    TIME_BUCKET = 10*60*1000 # 10 minutes
    TIME_FRAME = 7*24*60*60*1000
    LIMIT = 2*60*60*1000

    def __init__(self, userData, dx, dy):
        """

        :param userData: The data for the user of the grid
        :type userData: list[dict]]
        :param dx: resolution on x axis
        :type dx: int
        :param dy: resolution on y axis
        :type dy: int
        """
        self.userData = userData
        self.dx = dx
        self.dy = dy
        self.gridStartX = float("inf")
        self.gridStartY = float("inf")
        for location in userData:
            if location["longitude"] < self.gridStartX:
                self.gridStartX = location["longitude"]
            if location["latitude"] <  self.gridStartY:
                self.gridStartY = location["latitude"]
        self.gridStartX = self.gridStartX - 100
        self.gridStartY =  self.gridStartY - 100
        self.gridEndX = -float("inf")
        self.gridEndY = -float("inf")
        for location in userData:
            if location["longitude"] > self.gridEndX:
                self.gridEndX = location["longitude"]
            if location["latitude"] > self.gridEndY:
                self.gridEndY = location["latitude"]
        self.gridEndX = self.gridEndX - 100
        self.gridEndY = self.gridEndY - 100
        self.xAmount = int(((self.gridEndX - self.gridStartX) / (self.dx)) + 1)
        self.yAmount = int(((self.gridEndY - self.gridStartY) / (self.dy)) + 1)

        self.timeAmount = int(self.TIME_FRAME / self.TIME_BUCKET + 1)
        print (self.xAmount, self.yAmount, self.timeAmount)
        self.usersStartMatrix = []
        self.usersEndMatrix = []
        for x in range(self.xAmount):
            self.usersStartMatrix.append([])
            self.usersEndMatrix.append([])
            for y in range(self.yAmount):
                self.usersStartMatrix[x].append([])
                self.usersEndMatrix[x].append([])
                for t in range(self.timeAmount):

                    self.usersStartMatrix[x][y].append({})
                    self.usersEndMatrix[x][y].append({})

    def enterUserToGrid(self, userId, longitude, latitude, startTime, endTime):
        """

        :param userId:
        :param longitude:
        :param latitude:
        :param startTime:
        :param endTime:
        :return:
        """
        gridX = int((longitude - self.gridStartX) / self.dx)
        gridY = int((latitude - self.gridStartY) / self.dy)
        gridStartTime = int(startTime / self.TIME_BUCKET)
        gridEndTime = int(endTime / self.TIME_BUCKET)
        if ((gridX >= 0)  & (gridX < self.xAmount) & (gridY >= 0) & (gridY < self.yAmount) & (gridStartTime < self.timeAmount) & (gridEndTime < self.timeAmount)& (gridStartTime >= 0)):
            if userId not in self.usersStartMatrix[gridX][gridY][gridStartTime]:
                self.usersStartMatrix[gridX][gridY][gridStartTime][userId] = set()
            self.usersStartMatrix[gridX][gridY][gridStartTime][userId].add((latitude,longitude))
            if userId not in self.usersEndMatrix[gridX][gridY][gridEndTime]:
                self.usersEndMatrix[gridX][gridY][gridEndTime][userId] = set()
            self.usersEndMatrix[gridX][gridY][gridEndTime][userId].add((latitude,longitude))

    def populateGrid(self, friendsData):
        """

        :param friendsData:
        :type friendsData: dict[str|list[dict]]
        :return:
        """
        for friendId, data in friendsData.items():
            # TODO: check if we need to filter by day
            for location in data:
                self.enterUserToGrid(friendId, location["longitude"], location["latitude"], location["start_hour"], location["end_hour"])



    def getFriendsByLocation(self, location, radius, timeRadius, byExitTime):
        """

        :param location:
        :param radius:
        :param timeRadius:
        :param byExitTime:
        :return:
        """
        gridX = int((location["longitude"] - self.gridStartX) / self.dx)
        gridY = int((location["latitude"] - self.gridStartY) / self.dy)
        gridStartTime = int(location["start_hour"] / self.TIME_BUCKET)
        gridEndTime = int(location["end_hour"] / self.TIME_BUCKET)

        friends = {}
        cnt = 0
        for x in range(gridX - radius, gridX + radius + 1):
            for y in range(gridY - radius, gridY + radius + 1):
                for t in range(- 4, timeRadius +1 ):
                    cnt +=1
                    if byExitTime:
                        searchTime = (t + gridEndTime)%(int(self.TIME_FRAME/self.TIME_BUCKET))
                        if ((x >= 0)  & (x < self.xAmount) & (y >= 0) & (y < self.yAmount) & (searchTime < self.timeAmount) & (searchTime >= 0)):
                            friends.update(self.usersEndMatrix[x][y][searchTime])
                    else:
                        searchTime = (t + gridStartTime)%self.TIME_FRAME
                        if searchTime < 0:
                            searchTime += self.TIME_FRAME
                        if ((x >= 0)  & (x < self.xAmount) & (y >= 0) & (y < self.yAmount) & (searchTime < self.timeAmount) & (searchTime >= 0)):
                            friends.update(self.usersStartMatrix[x][y][searchTime])
        return friends


    def ouputCompatibility(self, alphaDistance, alphaTime):
        """
        Calculates the
        :param alphaDistance:
        :param alphaTime:
        :return:
        """
        companions = {}
        for index in range(len(self.userData)-1):
            nextLocation = index+1
            timeTraveled = self.userData[nextLocation]["start_hour"] - self.userData[index]["end_hour"]
            cnt = 0
            while timeTraveled < self.LIMIT and nextLocation < len(self.userData):
                cnt+=1
                distnaceTraveled = distanceOnUnitSphere(self.userData[index]["latitude"],
                                   self.userData[index]["longitude"],
                                   self.userData[nextLocation]["latitude"],
                                   self.userData[nextLocation]["longitude"])

                startCompanions = self.getFriendsByLocation(self.userData[index], int(distnaceTraveled*alphaDistance),
                                                            int(timeTraveled*alphaTime), True)
                endCompanions = self.getFriendsByLocation(self.userData[nextLocation], int(distnaceTraveled*alphaDistance),  int(timeTraveled*alphaTime), False)

                for trueCompanion in (startCompanions.keys() & endCompanions.keys()):
                    companions.setdefault(trueCompanion, []).append(((self.userData[index],
                                                                     startCompanions[trueCompanion]),
                                                                     (self.userData[nextLocation],
                                                                     endCompanions[trueCompanion])))
                nextLocation += 1
                if nextLocation < len(self.userData):
                    timeTraveled = self.userData[nextLocation]["start_hour"] - self.userData[index]["end_hour"]
        return self.outputRecommendation(companions)

    def outputRecommendation(self, companions):
        suggestedCompanionPerLocation = {}
        compnionsWithDistance = {}
        for companion in companions:
            for matching in companions[companion]:
                startLocation, endLocation = matching
                maxEndLocation = float("inf")
                maxEndCoordination = ()
                maxStartLocation = float("inf")
                maxStartCoordination = ()
                for locations in startLocation[1]:
                    distance =  distanceOnUnitSphere(startLocation[0]["latitude"], startLocation[0]["longitude"], locations[0],locations[1])
                    if (distance < maxStartLocation):
                        maxStartLocation = distance
                        maxStartCoordination = locations;

                for locations in endLocation[1]:
                    distance =  distanceOnUnitSphere(endLocation[0]["latitude"], endLocation[0]["longitude"], locations[0],locations[1])
                    if (distance < maxEndLocation):
                        maxEndLocation = distance
                        maxEndCoordination = locations
                    candidateDistance = min(maxStartLocation, maxEndLocation)
                    locationCandidate = {
                                        "maxStartLocation" : maxStartLocation,
                                        "maxStartCoordination" : maxStartCoordination,
                                        "maxEndLocation" : maxEndLocation,
                                        "maxEndCoordination" : maxEndCoordination,
                                        "companion" : companion,
                                        "candidateDistance": candidateDistance}

                    suggestedCompanionPerLocation.setdefault((startLocation[0]["latitude"], startLocation[0]["longitude"],endLocation[0]["latitude"], endLocation[0]["longitude"]) , []).append(locationCandidate)

                # locationWithDistance = (startLocation, latitude, longitude, distance)
                # if companion not in compnionsWithDistance:
                #     compnionsWithDistance[companion] = []
                # compnionsWithDistance[companion].append(locationWithDistance)

        keys = suggestedCompanionPerLocation.keys();
        for key in keys:
            suggestedCompanionPerLocation[key].sort(key=lambda x:x["candidateDistance"])
        # print (companions)
        print("---------------")
        # print (compnionsWithDistance)
        print("---------------")
        # print(suggestedCompanionPerLocation)
        print("---------------")
        # print (json.dumps(suggestedCompanionPerLocation))
        print(suggestedCompanionPerLocation)
        print("------")
        return suggestedCompanionPerLocation


def getCompanions(data, user, dx, dy, alphaDistance, alphaTime):
    userData = data[user]
    friends = { friend : data[friend] for friend in data if friend != user }
    grid = TimeGrid(userData, dx, dy)
    grid.populateGrid(friends)
    # companions = grid.ouputCompatibility(alphaDistance, alphaTime)

    return grid.ouputCompatibility(alphaDistance, alphaTime)

def parseCoordinate (num):
        num = float(num)
        while (num > 100):
                num = num/10
        return num

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
        lat2 = parseCoordinate(lat2)
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
        return arc * 6373

class Coordination(object):
    def __init__(self,long, lat):
        self.lat = lat
        self.long = long

if __name__ == "__main__":
    import json
    data = json.load(open("resources/test2.json"))
    user = "alon"
    dx = 100000
    dy = 100000
    alphaDistance = 0.0000001
    alphaTime = 0.00001
    getCompanions(data, user, dx, dy, alphaDistance, alphaTime)