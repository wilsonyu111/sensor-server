from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import json
import threading, time

tempRecords ={}
highestNum = 0
timeUp = False # keep track of if the time is up
COUNTDOWN = 10 # every 12 hours do a sensor check to see if any is offline
#app = Flask(__name__, static_folder = "/home/pi/esp_sensor_server/templates")
app = Flask(__name__)

# this is a temporary function used to test the servo
# take this offline or make it avaliable only in private network
# this function will send the servo testing html file
# that allows for the control of a servo
@app.route ("/fancontrol", methods=["GET"])
def fanController():

        return render_template ("fanControl.html", default_value = 20) # render fan control page

# This is an overloaded fanController function
# It takes a fanValue variable and update the html page with this value
# the default value is 20
def fanController(fanValue):
        return render_template ("fanControl.html", default_value=fanValue) # render fan control page

# This function is for updating/storing online fan controlling devices
# If a device has been inactive for 24 hour, it should be removed from
# the array (decide what data structure to use)
# 
@app.route ("/fanControllerOnline", methods=["PUT"])
def updateControllerProfile():

        # store the ip of each controller
        # store the time when it's online
        # store the location name
        # store mac or chip id??
        # if it already exist update these values
        return None


@app.route ("/fancontrol", methods=["POST"])
def fanControllerValue():
        sliderValue = request.form["fanSpeed"] # get the fan speed value from form request
        print (sliderValue) 
        return fanController(sliderValue) # return the original page, will change later

@app.route('/', methods=['GET']) # default home page
def sensors():

        return render_template ("main.html", temps= tempRecords, size= highestNum +1) # render html file in templates folder
        #return "hello!"

@app.route ('/sendtoserver', methods= ['POST']) #receive data from the sensors
def get_data ():

        data = request.get_json()
        tempF = data["temp"]
        hud = data["hud"]
        location = data["location"] # remember to update the controllers to send only numbers!!!!
        noSensor = ["no sensor","","","",""]
        global timeUp

        # to reference a global variable, you need to tell python this is a global variable
        # by doing the following and then you will be able to use this
        # I think for variables that are pass by reference you are not required to do this
        global highestNum 

        #how to read the dictionary of array
        #dictionary by location
        # each dictionary contain an array
        # [0] = room location
        # [1] = temp in F
        # [2] = hudmidity
        # [3] = last active
        #print ("length of records: " + str(len(tempRecords)))

        if int(location) > highestNum:
        #since the html need to loop through the dictionary using index
        #and all sensors are named based on numbers
        #This will give me the highest number that are connected
        #so I can loop through all these sensors up till the highest one
                
                highestNum = int(location)

        if (location in tempRecords): # if the key exist

                tempRecords[location][1] = tempF # update temp in F
                tempRecords[location][2] = hud # hudmidity
                tempRecords[location][3] = datetime.now().strftime("%Y/%m/%d %I:%M %p") # update time in 12 hour format
                
        else: # if a location does not exist in dictionary add it
                tempArr = ["room " + location, tempF, hud, datetime.now().strftime("%Y/%m/%d %I:%M %p")] # update time in 12 hour format
                tempRecords[location] = tempArr # add an array to the dictionary pair
        
        if timeUp:
                #check_sensor_down()
                timeUp = False
                startTimer()
        	
        return "received"

def countDown (): # this function does a countdown to however many seconds and set timeUp to True
        
        global COUNTDOWN
        global timeUp
        time.sleep(COUNTDOWN)
        timeUp = True

def startTimer():
        timer = threading.Thread(target=countDown)
        timer.start()

def lastActive(previousTime):
        diff = str(datetime.now() - previousTime)
        if "days," in diff: #if there exist days in the difference return how many days since last active
                day = diff.split("day")
                return day[0] + " day(s)"
        else: # if there only exist hours, minutes or seconds
                time = diff.split(":")

                if time[0] != "0": #return hours since last active
                        return time[0] + " hour(s) ago"
                elif time[1] != "00":
                        return time[1] + " minute(s) ago"# return minutes since last active
                else:
                        return time[2][0:2] + " second(s) ago"# return seconds since last active
        
if __name__ == "__main__": # in order to run it as main, it needs to be ran as python "file_name"

        startTimer() # to excute functions, you need to put it before app.run
	app.run(debug=True, host= '0.0.0.0', port= "5000") #allow the server to run in debug mode without setting it in console

