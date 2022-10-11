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

tempRecords = {}
port = 8086
test_Uname = "wilson"
test_Pwd="password"
database = {test_Uname:bcrypt.hashpw(test_Pwd.encode(), bcrypt.gensalt())}
SESSION_ID_LENGTH = 50

app = Flask(__name__, static_url_path='', static_folder='build')
CORS(app)
app.secret_key = "testsession"

# ----------------------------------------------------------------------------------

@app.route("/",  methods=['GET'])
def sensors():
    return send_from_directory(app.static_folder,'index.html')


# ----------------------------------------------------------------------------------
# return a dictionary containing all sensor object's data
@app.route('/getData', methods=['GET'])
def getData():

        debug = {}
        for i in tempRecords:
                dictionary = tempRecords[i].getDict()
                debug[i] = dictionary
                
        return json.dumps(debug, indent=4)

# ----------------------------------------------------------------------------------

@app.route('/sendtoserver', methods=['POST'])  # receive data from the sensors
def receiveData():

        data = request.get_json()
        tempF = float(data["temperature"])
        hud = float(data["humidity"])
        sensor_id = data["MAC_ADDRESS"]
        location_name = data["location_name"]
        lightStat=data["light_status"]
        ipadd=data["sensor_IP"]
        sensor_port=data["sensor_listen_port"]

        if (sensor_id in tempRecords):  # if the key exist

            updateSesnor = tempRecords[sensor_id]  # get the sensor object
            # updates temp, hud and last active
            updateSesnor.updateData(hud=hud, temp=tempF, lightStat=lightStat, ipadd=ipadd, listen_port=sensor_port)

        else:  # if a location does not exist in dictionary add it

            # create a new sensor object for holding sensor informations
            tempRecords[sensor_id] = sensor(
                sensor_id=sensor_id, temp=tempF, hud=hud, location_name=location_name, lightStat=lightStat, ipadd=ipadd, listen_port=sensor_port)

        return "received", 200
    


# ----------------------------------------------------------------------------------
    
@app.route('/restartSensor', methods=['GET'])
def restartSensor():
    
    (message, status_code) = sendHttpToSensor(req=request, URL_path="/restart")
    return message, status_code

# ----------------------------------------------------------------------------------

@app.route('/sensorOnline', methods=['GET'])
def sensorHeartBeat():
    
    (message, status_code) = sendHttpToSensor(req=request, URL_path="/online")
    return message, status_code

# ----------------------------------------------------------------------------------
@app.route('/sensorConfig', methods=['GET'])
def sensorConfig():
    
    (message, status_code, jsonBody) = sendHttpToSensor(req=request, URL_path="/serverStat")
    return json.dumps(jsonBody,  indent=1), status_code

# ----------------------------------------------------------------------------------
    
def sendHttpToSensor(req, URL_path):
    macadd = ""    
    try:
        data = req.get_json()
        macadd = data["macadd"]
    except:
        return ("bad request", 400)
    
    if macadd == "" or macadd not in tempRecords:
        return ("Not Found", 404)
    
    
    sensorInfo = tempRecords[macadd]
    httpURI = makeURI(sensorInfo.ipadd, sensorInfo.listen_port, URL_path)
    
    response = requests.get(url = httpURI)
    
    try:
        return (response.text, response.status_code, response.json())
    except:
        return (response.text, response.status_code)

# ----------------------------------------------------------------------------------

def makeURI(ip:str, port:int, path:str):
    return "http://" + ip +":" + str(port) + path          

# ----------------------------------------------------------------------------------

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
        print(sessionID)
        # sessionCookie = "sessionId="+sessionID+"; Max-Age="+str(300)+";"
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

@app.route('/logout', methods=['POST'])  # login
def logout():
    
    try:
        data = request.get_json()
        username = data["username"]
    except:
        return "bad request", 400
    
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
    app.run(debug=True, host='0.0.0.0', port="5000")
    