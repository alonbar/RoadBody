
class TimeGrid(object):
    TIME_BUCKET = 10*60*1000 # 10 minutes
    TIME_FRAME = 7*24*60*60*1000
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
        timeAmount = self.TIME_FRAME / self.TIME_BUCKET + 1
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

    def getFriendsByLocation(self, location, radius, timeRadius, byExitTime):
        gridX = (location["longitude"] - self.gridStartX) / self.dx
        gridY = (location["latitude"] - self.gridStartY) / self.dy
        gridStartTime = self._normalizeTime(location["start_hour"]) / self.TIME_BUCKET
        gridEndTime = self._normalizeTime(location["end_hour"]) / self.TIME_BUCKET

        friends = set()
        for x in range(gridX - radius, gridX + radius):
            for y in range(gridY - radius, gridY + radius):
                for t in range(- timeRadius, timeRadius):
                    if byExitTime:
                        searchTime = (t + gridEndTime)%self.TIME_FRAME
                        if searchTime < 0:
                            searchTime += self.TIME_FRAME
                        friends |= self.usersEndMatrix[x][y][searchTime]
                    else:
                        searchTime = (t + gridStartTime)%self.TIME_FRAME
                        if searchTime < 0:
                            searchTime += self.TIME_FRAME
                        friends |= self.usersStartMatrix[x][y][searchTime]
        return friends


    def ouputCompatibility(self, alphaDistance, alphaTime):
        companions = {}
        for index in range(len(self.userData)-1):
            nextLocation = index + 1
            timeTraveled = self.userData[nextLocation]["start_time"] - self.userData[index]["end_time"]
            while timeTraveled < self.LIMIT:
                startCompanions = self.getFriendsByLocation(self.userData[index], int(timeTraveled*alphaDistance),
                                                            int(timeTraveled*alphaTime), True)
                endCompanions = self.getFriendsByLocation(self.userData[nextLocation], 1, 1, False)
                for trueCompanion in startCompanions & endCompanions:
                    companions.setdefault(trueCompanion, []).append((self.userData[index],
                                                                     self.userData[nextLocation]))
                nextLocation += 1
                timeTraveled = self.userData[nextLocation]["start_time"] - self.userData[index]["end_time"]
        return companions



