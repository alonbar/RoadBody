#adssd
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
        for index in range(len(self.userData)-1):
            nextLocation = index + 1
            timeTraveled = self.userData[nextLocation]["start_time"] - self.userData[index]["end_time"]
            while timeTraveled < self.LIMIT:
                startCompanions = self.getFriendsByLocation(self.userData[index], int(timeTraveled*alpha))
                endCompanions = self.getFriendsByLocation(self.userData[nextLocation], 1)
                for trueCompanion in startCompanions & endCompanions:
                    companions.setdefault(trueCompanion, []).append((self.userData[index],
                                                                     self.userData[nextLocation]))
                nextLocation += 1
        return companions



