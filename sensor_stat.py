import datetime
import time


class sensor:

    def __init__(self, data, config):

        self.collectionDict = {
            "data": {
                "temperature": 0.0,
                "humidity": 0,
                "last_active": self.__getLastActive(),
                "light_status": "n/a"
            },
            "config": {
                "sensor_id": "",
                "location_name": "",
                "sensor_ip": "",
                "server_ip": "",
                "listen_port": -1,
                "modified_time": -1,
                "ssid": "",
                "installed_light": 0,
                "dest_port": -1,
                "sleep_timer": -1
            }
        }
        # self.collectionDict = {
        #     "data" : {}, "config" : {}
        # }

        self.updateData(data)
        self.updateConfig(config)

    def __updateCollectionDict(self, data, type: str):

        for i in data:
            if i in self.collectionDict[type]:
                self.collectionDict[type][i] = data[i]

    def __getLastActive(self):
        return datetime.datetime.now().strftime(
            "%Y/%m/%d %I:%M %p")

    def updateData(self, data):
        self.__updateCollectionDict(data, "data")
        self.collectionDict["data"]["last_active"] = self.__getLastActive()

    def updateConfig(self, config):
        self.__updateCollectionDict(config, "config")

    def getData(self, valName: str):
        return self.collectionDict["data"][valName]

    def getConfig(self, valName: str):
        return self.collectionDict["config"][valName]

    def toString(self):
        return "temperature: " + str(self.getValue("temperature")) \
            + "\nhumidity: " + str(self.getValue("humidity")) \
            + "\nlight status: " + self.getValue("light_status") \
            + "\nlast active: " + self.getValue("last_active") \
            + "\nlocation: " + self.getValue("location_name") \
            + "\nmac address: " + self.getValue("sensor_id") \
            + "\nip address: " + self.getValue("ip_address")\
            + "\nlistening port: " + str(self.getValue("listen_port"))

    def getDataDict(self):
        return self.collectionDict["data"]

    def getConfigDict(self):
        return self.collectionDict["config"]

    def getCollectionDict(self):
        return self.collectionDict
