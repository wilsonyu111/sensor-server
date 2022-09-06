from sensor_stat import sensor
from logging import exception
from flask_cors import CORS 
from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import datetime
import json

tempRecords = {}
port = 8086

# app = Flask(__name__)
app = Flask(__name__, static_url_path='', static_folder='frontend/build')
CORS(app)

# @app.route('/', methods=['GET'])  # default home page
# def sensors():

#     # render html file in templates folder
#     return render_template("build/index.html")
#     # return send_from_directory(app.static_folder, 'index.html')
@app.route("/",  methods=['GET'])
def sensors():
    return send_from_directory(app.static_folder,'index.html')

# return a dictionary containing all sensor object's data
@app.route('/getData', methods=['GET'])
def getData():

        debug = {}
        for i in tempRecords:
                dictionary = tempRecords[i].getDict()
                debug[i] = dictionary
                
        return json.dumps(debug, indent=4)


@app.route('/sendtoserver', methods=['POST'])  # receive data from the sensors
def receiveData():

        data = request.get_json()
        tempF = int(data["temp"])
        hud = int(data["hud"])
        sensor_id = data["sensor_id"]

        if (sensor_id in tempRecords):  # if the key exist

            updateSesnor = tempRecords[sensor_id]  # get the sensor object
            # updates temp, hud and last active
            updateSesnor.updateData(hud, tempF)
            print(updateSesnor.toString())

        else:  # if a location does not exist in dictionary add it

            # create a new sensor object for holding sensor informations
            tempRecords[sensor_id] = sensor(
                sensor_id=sensor_id, temp=tempF, hudm=hud)

        return "received", 200

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