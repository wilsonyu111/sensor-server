import datetime
from http import server
from time import sleep

class sensor:

    def __init__(self, sensor_id:str, location_name:str, temp:float,hud:float, lightStat:str, ipadd:str, listen_port:int):
        self.temp = temp
        self.hud = hud
        self.lastActive = self.__getLastActive()
        self.highest = temp
        self.lowest = temp
        self.tempAvg = temp
        self.hudAvg = hud
        self.__dataCount = 1
        self.__tempSum = temp
        self.__hudSum = hud
        self.lightStatus = lightStat
        self.sensor_id = sensor_id
        self.location_name = location_name
        self.ipadd = ipadd
        self.listen_port = listen_port # sesnor listening port
        self.configTime = -1
        self.ssid = ""
        self.installed_light = False
        self.destPort = -1 # raspberry pi's listening port, the port sensor will send data to
        self.sleepTimer = -1
        

    def __updateHighAndLowTemp(self):


        if self.highest < self.temp:
            self.highest = self.temp

        if self.lowest > self.temp:
            self.lowest = self.temp
    
    def updateDeviceConfig(self, ipadd:str, ssid:str, locationName:str , configTime:int, sensor_port:int, destPort:int, sleepTimer: int, installed_light:bool,):
        self.configTime = configTime
        self.ipadd = ipadd
        self.ssid = ssid
        self.installed_light = installed_light
        self.destPort = destPort
        self.sleepTimer = sleepTimer
        self.listen_port = sensor_port
        self.location_name = locationName
    
    def compareTime(self, serverTime:int, sensorTime:int):
        return serverTime == sensorTime

    
    def __updateAvg(self):
        self.__hudSum += self.hud
        self.__tempSum += self.temp
        self.__dataCount += 1
        self.tempAvg = self.__tempSum / self.__dataCount
        self.hudAvg = self.__hudSum / self.__dataCount
        

    def __getLastActive(self):
        return datetime.datetime.now().strftime(
            "%Y/%m/%d %I:%M %p")

    def updateData(self, hud:int, temp:int, lightStat:str, ipadd:str, listen_port:int):
        self.temp = temp
        self.hud = hud
        self.lightStatus = lightStat
        self.ipadd = ipadd
        self.listen_port = listen_port
        self.lastActive = self.__getLastActive()
        self.__updateAvg()
        self.__updateHighAndLowTemp()

    def toString(self):
        return "temperature: " + str(self.temp) \
            + "\nhumidity: " + str(self.hud) \
            + "\nlight status: " + self.lightStatus \
            + "\nlast active: " + self.lastActive \
            + "\nlocation: " + self.location_name \
            + "\nmac address: " + self.sensor_id \
            + "\nip address: " + self.ipadd\
            + "\nlistening port: " + self.listen_port\
            + "\nhigh: " + str(self.highest) \
            + "\nlow: " + str(self.lowest) \
            + "\ntemperature average: " + str(self.tempAvg) \
            + "\nhumidity average: " + str(self.hudAvg)

    def getDict(self):
        return {
            "temperature": self.temp,
            "humidity": self.hud,
            "light_status":self.lightStatus,
            "last_active": self.lastActive,
            "location": self.location_name,
            "mac_address": self.sensor_id,
            "ip_address": self.ipadd,
            "port": self.listen_port,
            "highest" : self.highest,
            "lowest" : self.lowest,
            "temperature average" : self.tempAvg,
            "humidity average" : self.hudAvg
        }
    
    def getConfigDict(self):
        return {
            "configured_time": self.configTime,
            "mac_address": self.sensor_id,
            "location": self.location_name,
            "ip_address": self.ipadd,                        
            "ssid": self.ssid,
            "sensor_listening_port": self.listen_port,
            "installed_light_sensor": self.installed_light,
            "sleep_timer": self.sleepTimer,
            "pi_server_port": self.destPort
        }