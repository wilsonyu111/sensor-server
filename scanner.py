from concurrent.futures import ThreadPoolExecutor
import requests

threadPool = {}
start = 20
last = 255
port = 3000
route = "/serverStat"
networkAdd = "192.168.1"
max_worker = 200
sensorFound = {}


def main():

    tp = ThreadPoolExecutor(max_workers=max_worker)

    for i in range(start, last+1):
        futureObj = tp.submit(sendReq, id=i)
        threadPool[i] = futureObj

    for id in threadPool:
        futureObj = threadPool[id]
        result, sensorHost = futureObj.result()
        if result != "":
            print(sensorFound[sensorHost])

    for i in sensorFound:
        print(sensorFound[i][0] + "\nresponse: " + sensorFound[i][1])
    print("done scanning")


def sendReq(id: int):
    tempNet = "http://"+networkAdd+"."+str(id)+":"+str(port)+route
    result = ""
    try:
        print("scanning " + tempNet + "...")
        req = requests.get(tempNet, timeout=15)
        result = id
        sensorFound[id] = (tempNet, req.text)
    except Exception as e:
        result = ""
    # except requests.ConnectTimeout:

    #     result = "timeout"
    # except requests.ConnectionError:
    #     result = "connection error"
    # except requests.ReadTimeout:
    #     result = "server response not received"

    return (result, id)


main()
