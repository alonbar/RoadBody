import math
class TimeGrid(object):
    """

    """
    TIME_BUCKET = 10*60*1000 # 10 minutes
    TIME_FRAME = 7*24*60*60*1000
    LIMIT = 10*60*60*1000
    COORDINATE_RESOLUTION = math.pow(10,7)
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
        self.gridStartX = min(location["longitude"] for location in userData) - self.dx
        self.gridStartY = min(location["latitude"] for location in userData) - self.dy
        gridEndX = max(location["longitude"] for location in userData) + self.dx
        gridEndY = max(location["latitude"] for location in userData) + self.dy

        xAmount = int((gridEndX - self.gridStartX) / self.dx + 1)
        yAmount = int((gridEndY - self.gridStartY) / self.dy + 1)
        timeAmount = int(self.TIME_FRAME / self.TIME_BUCKET + 1)
        print (xAmount, yAmount, timeAmount)
        self.usersStartMatrix = [[[set()]*timeAmount] * yAmount]*xAmount
        self.usersEndMatrix = [[[set()]*timeAmount] * yAmount]*xAmount


    def distanceOnUnitSphere(self, lat1, long1, lat2, long2):
        """

        :param lat1:
        :param long1:
        :param lat2:
        :param long2:
        :return:
        """
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
        arc = math.acos( cos )

        # Remember to multiply arc by the radius of the earth
        # in your favorite set of units to get length.
        return arc * 6373


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
        print("asd")
        self.usersStartMatrix[gridX][gridY][gridStartTime].add(userId)
        self.usersEndMatrix[gridX][gridY][gridEndTime].add(userId)

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

        friends = set()
        for x in range(gridX - radius, gridX + radius + 1):
            for y in range(gridY - radius, gridY + radius + 1):
                for t in range(- timeRadius, timeRadius + 1):
                    if byExitTime:
                        searchTime = (t + gridEndTime)%(int(self.TIME_FRAME/self.TIME_BUCKET))
                        friends |= self.usersEndMatrix[x][y][searchTime]
                    else:
                        searchTime = (t + gridStartTime)%self.TIME_FRAME
                        if searchTime < 0:
                            searchTime += self.TIME_FRAME
                        friends |= self.usersStartMatrix[x][y][searchTime]
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
            while timeTraveled < self.LIMIT and nextLocation < len(self.userData):
                distnaceTraveled = self.distanceOnUnitSphere(self.userData[index]["latitude"]/self.COORDINATE_RESOLUTION,
                                   self.userData[index]["longitude"]/self.COORDINATE_RESOLUTION,
                                   self.userData[nextLocation]["latitude"]/self.COORDINATE_RESOLUTION,
                                   self.userData[nextLocation]["longitude"]/self.COORDINATE_RESOLUTION)

                startCompanions = self.getFriendsByLocation(self.userData[index], int(distnaceTraveled*alphaDistance),
                                                            int(timeTraveled*alphaTime), True)
                endCompanions = self.getFriendsByLocation(self.userData[nextLocation], 1, 1, False)


                for trueCompanion in startCompanions & endCompanions:
                    companions.setdefault(trueCompanion, []).append((self.userData[index],
                                                                     self.userData[nextLocation]))
                nextLocation += 1
                if nextLocation < len(self.userData):
                    timeTraveled = self.userData[nextLocation]["start_hour"] - self.userData[index]["end_hour"]
        return companions


def getCompanions(data, user, dx, dy, alphaDistance, alphaTime):
    userData = data[user]
    friends = { friend : data[friend] for friend in data if friend != user }
    grid = TimeGrid(userData, dx, dy)
    grid.populateGrid(friends)
    return grid.ouputCompatibility(alphaDistance, alphaTime)

if __name__ == "__main__":
    import json
    data = json.load(open("resources/test.json"))
    user = "1"
    dx = 1
    dy = 1
    alphaDistance = 0.01
    alphaTime = 0.01
    print (getCompanions(data, user, dx, dy, alphaDistance, alphaTime))