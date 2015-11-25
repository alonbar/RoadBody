import math
class TimeGrid(object):
    TIME_BUCKET = 10*60*1000 # 10 minutes
    TOTAL_DAY = 24*60*60*1000
    LIMIT = 60*60*1000
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

        xAmount = (gridEndX - self.gridStartX) / self.dx + 1
        yAmount = (gridEndY - self.gridStartY) / self.dy + 1
        timeAmount = (self.endTime - self.startTime) / self.TIME_BUCKET + 1
        self.usersStartMatrix = [[[set()]*xAmount] * yAmount]*timeAmount
        self.usersEndMatrix = [[[set()]*xAmount] * yAmount]*timeAmount

    def _normalizeTime(self, timeTuple):
        day, hour, minute = timeTuple
        return (((hour)*60) + minute)*60*1000

    def distance_on_unit_sphere(lat1, long1, lat2, long2):
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
        gridX = (longitude - self.gridStartX) / self.dx
        gridY = (latitude - self.gridStartY) / self.dy
        gridStartTime = self._normalizeTime(startTime) / self.TIME_BUCKET
        gridEndTime = self._normalizeTime(endTime) / self.TIME_BUCKET

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
            self.enterUserToGrid(friendId, data["longitude"], data["latitude"], data["start_hour"], data["end_hour"])

    def getFriendsByLocation(self, location, radius):
        pass

    def ouputCompatibility(self, alpha):
        companions = {}
        coordinationResolution = math.pow(10,7)
        for index in range(len(self.userData)-1):
            nextLocation = index + 1
            timeTraveled = self.userData[nextLocation]["start_time"] - self.userData[index]["end_time"]
            while timeTraveled < self.LIMIT:
                distnaceFromNextLocation = self.distance_on_unit_sphere(self.userData[index]["latitude"]/coordinationResolution,
                                                                        self.userData[index]["longitude"]/coordinationResolution,
                                                                        self.userData[nextLocation]["latitude"]/coordinationResolution,
                                                                        self.userData[nextLocation]["longitude"]/coordinationResolution)
                # distanceTravel = self.userData[index]["latitude"] -
                startCompanions = self.getFriendsByLocation(self.userData[index], int(timeTraveled*alpha))
                endCompanions = self.getFriendsByLocation(self.userData[nextLocation], 1)
                for trueCompanion in startCompanions & endCompanions:
                    companions.setdefault(trueCompanion, []).append((self.userData[index],
                                                                     self.userData[nextLocation]))
                nextLocation += 1
                timeTraveled = self.userData[nextLocation]["start_time"] - self.userData[index]["end_time"]
        return companions



