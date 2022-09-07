import datetime

class sensor:

    def __init__(self, sensor_id:str, temp:float,hudm:float, database="N/A"):
        self.temp = temp
        self.hudm = hudm
        self.lastActive = self.__getLastActive()
        self.sensor_id = sensor_id
        self.database = database
        self.highest = temp
        self.lowest = temp
        self.tempAvg = temp
        self.hudmAvg = hudm
        self.__dataCount = 1
        self.__tempSum = temp
        self.__hudmSum = hudm

    def __updateHighAndLowTemp(self):

        if self.highest < self.temp:
            self.highest = self.temp

        if self.lowest > self.temp:
            self.lowest = self.temp
    
    def __updateAvg(self):
        self.__hudmSum += self.hudm
        self.__tempSum += self.temp
        self.__dataCount += 1
        self.tempAvg = self.__tempSum / self.__dataCount
        self.hudmAvg = self.__hudmSum / self.__dataCount
        

    def __getLastActive(self):
        return datetime.datetime.now().strftime(
            "%Y/%m/%d %I:%M %p")

    def updateData(self, hud:int, temp:int):
        self.temp = temp
        self.hudm = hud
        self.lastActive = self.__getLastActive()
        self.__updateAvg()
        self.__updateHighAndLowTemp()

    def toString(self):
        return "temperature: " + str(self.temp) \
            + "\nhudmidity: " + str(self.hudm) \
            + "\nlast active: " + self.lastActive \
            + "\nlocation: " + str(self.sensor_id) \
            + "\nhigh: " + str(self.highest) \
            + "\nlow: " + str(self.lowest) \
            + "\ntemperature average: " + str(self.tempAvg) \
            + "\nhudmidity average: " + str(self.hudmAvg)

    def getDict(self):
        return {
            "temperature": self.temp,
            "hudmidity": self.hudm,
            "last active": self.lastActive,
            "location": self.sensor_id,
            "highest" : self.highest,
            "lowest" : self.lowest,
            "temperature average" : self.tempAvg,
            "hudmidity average" : self.hudmAvg
        }