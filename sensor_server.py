from tkinter import W
from sensor_stat import sensor
from flask_cors import CORS 
from flask import Flask, request, send_from_directory, session, make_response
import json
import datetime
import bcrypt
import secrets
import base64
from http import cookies
import requests
from decouple import config

tempRecords = {}
port = 8086
username = config('user')
password = config('password')
secretKey = config('secret_key')
database = {username:bcrypt.hashpw(password.encode(), bcrypt.gensalt())}
SESSION_ID_LENGTH = 60


app = Flask(__name__, static_url_path='', static_folder='build')
app.secret_key = secretKey

# ----------------------------------------------------------------------------------

@app.route("/",  methods=['GET'])
def sensors():
    return send_from_directory(app.static_folder,'index.html')


# ----------------------------------------------------------------------------------
# return a dictionary containing all sensor object's data
@app.route('/debugData', methods=['GET'])
def getDebugData():
        debug = {}
        for i in tempRecords:
                dictionary = tempRecords[i].getCollectionDict()
                debug[i] = dictionary
                
        return json.dumps(debug, indent=2)
    
# ----------------------------------------------------------------------------------
# return a dictionary containing all sensor object's data
@app.route('/getData', methods=['GET'])
def getData():
        data = {}
        for i in tempRecords:
                dictionary = tempRecords[i].getDataDict()
                dictionary["location"] = tempRecords[i].getConfig("location_name")
                data[i] = dictionary
                
        return json.dumps(data, indent=2)

# ----------------------------------------------------------------------------------

@app.route('/sendtoserver', methods=['POST'])  # receive data from the sensors
def receiveData():

        data = request.get_json()
        dataDict = data["data"]
        configDict = data["config"]
        sensor_id = configDict["sensor_id"]

        if ( sensor_id in tempRecords):  # if the key exist

            updateSensor = tempRecords[sensor_id]  # get the sensor object
            # updates temp, hud and last active
            updateSensor.updateData(dataDict)
            updateSensor.updateConfig(configDict)

        else:  # if a location does not exist in dictionary add it

            # create a new sensor object for holding sensor informations
            tempRecords[sensor_id] = sensor(dataDict, configDict)

        return "received", 200
    


# ----------------------------------------------------------------------------------
# restart sensor
    
@app.route('/restartSensor', methods=['GET'])
def restartSensor():
    
    (message, status_code) = sendHttpToSensor(req=request, URL_path="/restart")
    return message, status_code

# ----------------------------------------------------------------------------------

# @app.route('/updateConfig', methods=['POST'])
# def updateConfig():
#     return None

# ----------------------------------------------------------------------------------
# check if sensor is online

@app.route('/sensorOnline', methods=['GET'])
def sensorHeartbeat():
    
    (message, status_code) = sendHttpToSensor(req=request, URL_path="/online")
    return message, status_code

# ----------------------------------------------------------------------------------
# request sensor config data
# check if data already exist, if it does send a request to verify timestamp
# if data does not exist or timestamp is not the same, request the data to be sent

@app.route('/sensorConfig', methods=['POST'])
def sensorConfig():
    
    result = timeStampCheck(req=request, URL_path="/timestampCheck")
    
    if result[1] == 304 or result [1] == 200:
        macadd = request.get_json()["MAC_ADDRESS"]
        sensorObj = tempRecords[macadd]
    
        if result[1] == 304:
            
            print("using cache")
            return json.dumps( sensorObj.getConfigDict(), indent=1), 200
        
        elif result[1] == 200:
            
            print("no cache")
            configDict = result[2] 
            sensorObj.updateConfig(configDict)
            
            return json.dumps(configDict,  indent=1), 200
        
    return result[0], result[1]

#-----------------------------------------------------------------------------------

@app.route('/testSensorConfig', methods=['POST'])
def testSensorConfig():
    
    sensorObj = getSensorObject(request.get_json())
    if not sensorObj:
        return ("sensor not found", 404)
    
    return json.dumps(sensorObj.getConfigDict(), indent=1), 200
#-----------------------------------------------------------------------------------
# check if data is correct and if the sensor object exist, return the sensor object

def getSensorObject(data):
    
    keyName = "MAC_ADDRESS"
    if keyName in data:
        macadd = data[keyName]
        if macadd in tempRecords:
            return tempRecords[macadd]
    
    return None


#-----------------------------------------------------------------------------------
# helper function that takes the request from client and url path and returns the message
# and status code. If JSON data is returned, the data will be sent to client.

    
def sendHttpToSensor(req, URL_path):
    
    sensorObj = getSensorObject(req.get_json())
    if not sensorObj:
        return ("sensor not found", 404)
        
    httpURI = makeURI(sensorObj.getConfig("sensor_ip"), sensorObj.getConfig("listen_port"), URL_path)
    
    # in general the timeout request should not happen
    # if it does, it means the sensor is down
    # wills need to implement extra logic to handle sensor alive check
    try:    
        response = requests.get(url = httpURI)
    except:
        return "sensor not avliable", 404        
    
    #either convert to 3 item tuple or 2 item tuple
    try:
        return (response.text, response.status_code, response.json())
    except:
        return (response.text, response.status_code)
    
def timeStampCheck(req, URL_path):
    
    macadd = ""
    try:
        data = req.get_json()
        macadd = data["MAC_ADDRESS"]
    except:
        print(request)
        return ("bad request", 400)
    
    paramDict = {"time_stamp": tempRecords[macadd].getConfig("config_timestamp")}
    
    sensorInfo = tempRecords[macadd]
    httpURI = makeURI(sensorInfo.getConfig("sensor_ip"), sensorInfo.getConfig("listen_port"), URL_path)
    
    # in general the timeout request should not happen
    # if it does, it means the sensor is down
    # wills need to implement extra logic to handle sensor alive check
    try:
        response = requests.get(url = httpURI, params=paramDict)
    except:
        return "sensor not avliable", 404
    
    
    try:
        return (response.text, response.status_code, response.json())
    except:
        return (response.text, response.status_code)

# ----------------------------------------------------------------------------------

# @app.route('/updateConfig', methods=['POST'])
# def processConfigUpdate():
    

# ----------------------------------------------------------------------------------
# make full URI given ip address, port number and path

def makeURI(ip:str, port:int, path:str):
    return "http://" + ip +":" + str(port) + path          

# ----------------------------------------------------------------------------------
# function handles login

@app.route('/login', methods=['POST'])  # login
def login():
    
    try:
        data = request.get_json()
        username = data["username"]
        password = data["password"].encode()
    except:
        return "bad request", 400
    
    if username in database and bcrypt.checkpw(password, database[username]):
        
        sessionID = generateSessionID(SESSION_ID_LENGTH, username)
        session[username] = sessionID
            
        resp = make_response()
        resp.set_cookie('sessionID', value=session[username], max_age=300)
        return resp, 200
        
    elif username in database:
        return "wrong password", 401
    elif username not in database:
        return "user does not exist", 401
    else:
        return "server error", 500
    
# ----------------------------------------------------------------------------------
# function for handling logout

@app.route('/logout', methods=['POST'])  # login
def logout():
    
    try:
        data = request.get_json()
        username = data["username"]
    except:
        return "user does not exist", 400
    
    if username in database and username in session:
        session.pop(username, None)
        return "logged out", 200
    elif username not in database:
        return "user does not exist", 400
    elif username not in session:
        return "bad request", 400
    else:
        return "server error", 500

# ----------------------------------------------------------------------------------        
#function handling signup

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    try:        
        username = data["username"]
        password = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
    except:
        return "bad request", 400
    
    if username in database:
            return "username already exist", 200
    else:
        database[username] = password
        return "user created", 201 

# ----------------------------------------------------------------------------------

@app.route('/showdatabase', methods=['GET'])
def debugDatabase():
    
    debugData = {}
    for i in database:
        debugData[i] = str(database[i])
        
    
    return json.dumps(debugData, indent=4), 200

# ----------------------------------------------------------------------------------

@app.route('/testCookie', methods=['POST'])
def testCookie():
    resp = make_response()
    resp.set_cookie('username', 'the username')
    return resp

# ----------------------------------------------------------------------------------

def generateSessionID(bstrSize, username):
    data = secrets.token_bytes(nbytes=bstrSize)
    sessionID = base64.b64encode(data).decode('utf-8')
    session[sessionID] = username
    return sessionID  

def getTimeStamp():
    # returns the current time in military time (UTC) format
    return datetime.datetime.now().replace(microsecond=0).isoformat()+"Z"


def getMonth():
    # Return the current month as a string
    return datetime.datetime.now().strftime("%B")


def getYear():
    # Return the current year as a string
    return datetime.datetime.now().strftime("%Y")


if __name__ == "__main__":  # in order to run it as main, it needs to be ran as python "file_name"

    # allow the server to run in debug mode without setting it in console
    app.run(host='0.0.0.0', port="5000")
    