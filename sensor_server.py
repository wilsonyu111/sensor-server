from tkinter import W
from sensor_stat import sensor
from flask_cors import CORS
from flask import Flask, request, send_from_directory, make_response
import json
import datetime
import bcrypt
import secrets
import base64
import requests
from decouple import config
import time

tempRecords = {}
port = 8086
username = config('user')
password = config('password')
secretKey = config('secret_key')
database = {username: bcrypt.hashpw(password.encode(), bcrypt.gensalt())}
SESSION_ID_LENGTH = 60
session = {}
# to achieve "only one user can login at one time"
# one user account can only have one session id
# this is enforced by having session and userSessionMap
userSessionMap = {}

app = Flask(__name__, static_url_path='', static_folder='build')
app.secret_key = secretKey
CORS(app)

# ----------------------------------------------------------------------------------


@app.route("/",  methods=['GET'])
def sensors():
    return send_from_directory(app.static_folder, 'index.html')


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

    if (sensor_id in tempRecords):  # if the key exist

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


@app.route('/restartSensor', methods=['POST'])
def restartSensor():

    if not checkSessionID(request.get_json()["session_key"]):
        return "not authorized", 400
    (message, status_code) = sendHttpToSensor(req=request, URL_path="/restart")
    return message, status_code

# ----------------------------------------------------------------------------------
# update sensor configuration


def updateConfig(request):

    macadd = ""
    try:
        data = request.get_json()
        macadd = data["MAC_ADDRESS"]
        if macadd not in tempRecords:
            raise Exception("sensor not found")
    except:
        print(request)
        return ("bad request", 400)

    sensorInfo = tempRecords[macadd]

    httpURI = makeURI(sensorInfo.getConfig("sensor_ip"),
                      sensorInfo.getConfig("listen_port"), "/changeStat")

    data = removeEmptyDic(data)
    # add time stamp to this update
    data["modified_time"] = int(time.time())

    sensorInfo.updateConfig(data)

    # in general the timeout request should not happen
    # if it does, it means the sensor is down
    # wills need to implement extra logic to handle sensor alive check
    try:
        response = requests.post(url=httpURI, params=data)
    except:
        return ("sensor not avliable", 404)

    # if the response does not contain json response, return the text and status code
    # this can happen when the server returns an error code or other unknown code

    return (response.text, response.status_code)

# ----------------------------------------------------------------------------------
# check if sensor is online


def sensorHeartbeat(request):

    (message, status_code) = sendHttpToSensor(
        req=request, URL_path="/online")
    return (message, status_code)


@ app.route('/checkAction', methods=["POST"])
def actionAuthorization():

    # require mac address
    # requrie action type
    # require session key
    #

    data = request.get_json()

    # if not checkSessionID(data["session_key"]):
    #     return "not authorized", 401

    if "MAC_ADDRESS" not in data or "action" not in data:
        return "bad request", 400

    response = ("not found", 400)

    if data["action"] == "check_online":
        # call sensor heatbeat
        # not implemented yet
        print("sensor heartbeat")
        response = sensorHeartbeat(request=request)
    elif data["action"] == "change_stat":
        # update sensor config
        print("sensor update")
        response = updateConfig(request=request)
    elif data["action"] == "check_stat":
        # chekc sensor config
        print("sensor config")
        response = sensorConfig(request)

    return response[0], response[1]

# ----------------------------------------------------------------------------------
# require authorization
# request sensor config data
# check if data already exist, if it does send a request to verify timestamp
# if data does not exist or timestamp is not the same, the sensor will send back the correct configuration


# @ app.route('/sensorConfig', methods=['POST'])
def sensorConfig(request):

    result = timeStampCheck(req=request, URL_path="/timestampCheck")

    if result[1] == 304 or result[1] == 200:
        macadd = request.get_json()["MAC_ADDRESS"]
        sensorObj = tempRecords[macadd]

        if result[1] == 304:

            print("using cache")
            return json.dumps(sensorObj.getConfigDict(), indent=1), 200

        elif result[1] == 200:

            print("no cache")
            configDict = result[2]
            sensorObj.updateConfig(configDict)

            return (json.dumps(configDict,  indent=1), 200)

    return result

# -----------------------------------------------------------------------------------


@ app.route('/testSensorConfig', methods=['POST'])
def testSensorConfig():

    # sensorObj = getSensorObject(request.get_json())
    # if not sensorObj:
    #     return ("sensor not found", 404)

    # return json.dumps(sensorObj.getConfigDict(), indent=1), 200

    result = timeStampCheck(req=request, URL_path="/timestampCheck")

    if result[1] == 304 or result[1] == 200:
        macadd = request.get_json()["MAC_ADDRESS"]
        sensorObj = tempRecords[macadd]

        if result[1] == 304:

            print("using cache")
            return json.dumps(sensorObj.getConfigDict(), indent=1), 200

        elif result[1] == 200:

            print("no cache")
            configDict = result[2]
            sensorObj.updateConfig(configDict)

            return json.dumps(configDict,  indent=1), 200

    return result[0], result[1]
# -----------------------------------------------------------------------------------
# check if data is correct and if the sensor object exist, return the sensor object


def getSensorObject(data):

    keyName = "MAC_ADDRESS"
    if keyName in data:
        macadd = data[keyName]
        if macadd in tempRecords:
            return tempRecords[macadd]

    return None


# -----------------------------------------------------------------------------------
# helper function that takes the request from client and url path and returns the message
# and status code. If JSON data is returned, the data will be sent to client.


def sendHttpToSensor(req, URL_path):

    sensorObj = getSensorObject(req.get_json())
    if not sensorObj:
        return ("sensor not found", 404)

    httpURI = makeURI(sensorObj.getConfig("sensor_ip"),
                      sensorObj.getConfig("listen_port"), URL_path)

    # in general the timeout request should not happen
    # if it does, it means the sensor is down
    # wills need to implement extra logic to handle sensor alive check

    try:
        response = requests.get(url=httpURI)
    except:
        return "sensor not avliable", 404

    # either convert to 3 item tuple or 2 item tuple
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

    if macadd not in tempRecords:
        return ("sensor not found", 404)

    paramDict = {"time_stamp": tempRecords[macadd].getConfig(
        "modified_time")}

    sensorInfo = tempRecords[macadd]

    print(sensorInfo.getConfig("listen_port"))
    httpURI = makeURI(sensorInfo.getConfig("sensor_ip"),
                      sensorInfo.getConfig("listen_port"), URL_path)
    print(httpURI)

    # in general the timeout request should not happen
    # if it does, it means the sensor is down
    # wills need to implement extra logic to handle sensor alive check
    try:
        response = requests.post(url=httpURI, params=paramDict)
    except:
        return "sensor not avliable", 404

    # if the response does not contain json response, return the text and status code
    # this can happen when the server returns an error code or other unknown code
    try:
        return (response.text, response.status_code, response.json())
    except:
        return (response.text, response.status_code)

# ----------------------------------------------------------------------------------
# make full URI given ip address, port number and path


def makeURI(ip: str, port: int, path: str):
    return "http://" + ip + ":" + str(port) + path

# ----------------------------------------------------------------------------------
# function handles login


@ app.route('/login', methods=['POST'])  # login
def login():

    try:
        data = request.get_json()
        username = data["username"]
        password = data["password"].encode()
    except:
        return "bad request", 400

    if username in database and bcrypt.checkpw(password, database[username]):

        sessionID = generateSessionID(SESSION_ID_LENGTH, username)
        session[sessionID] = username
        userSessionMap[username] = sessionID

        resp = make_response()
        resp.set_cookie('sessionID', value=sessionID, max_age=300)
        return resp, 200

    elif username in database:
        return "wrong password", 401
    elif username not in database:
        return "user does not exist", 401
    else:
        return "server error", 500

# ----------------------------------------------------------------------------------
# function for handling logout


@ app.route('/logout', methods=['POST'])  # login
def logout():

    try:
        data = request.get_json()
        username = data["username"]
    except:
        return "user does not exist", 400

    if username in database and username in userSessionMap:
        sessionID = userSessionMap[username]
        userSessionMap.pop(username, None)
        session.pop(sessionID, None)
        return "logged out", 200
    elif username not in database:
        return "user does not exist", 400
    elif username not in userSessionMap:
        return "bad request", 400
    else:
        return "server error", 500

# ----------------------------------------------------------------------------------
# function handling signup


@ app.route('/signup', methods=['POST'])
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


@ app.route('/showdatabase', methods=['GET'])
def debugDatabase():

    debugData = {}
    for i in database:
        debugData[i] = str(database[i])

    return json.dumps(debugData, indent=4), 200

# ----------------------------------------------------------------------------------


@ app.route('/testCookie', methods=['POST'])
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


def removeEmptyDic(dic):
    newDic = {}

    for i in dic:
        if dic[i] != "":
            newDic[i] = dic[i]

    return newDic


def checkSessionID(sessionID):
    if sessionID in session:
        print(session[sessionID])
        for i in session:
            print(i)
        return True

    return False


if __name__ == "__main__":  # in order to run it as main, it needs to be ran as python "file_name"

    # allow the server to run in debug mode without setting it in console
    app.run(host='0.0.0.0', port="5000", debug=True)
