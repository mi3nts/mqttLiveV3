

# MQTT Client demo
# Continuously monitor two different MQTT topics for data,
# check if the received data matches two predefined 'commands'
 
# The headers on the csv which the current postgreysql converter reads 
# dateTime,nodeID,Latitude,Longitude,PM1,PM2_5,PM5_0,PM10,Temperature,Pressure,Humidity,DewPoint,nopGPS,nopPM,nopClimate
# Apply filters for PM2.5 >.0001 and  PM2.5 <5000
# Apple Sensor Based Calibration Values for Temperature 
# Do not have -1 --- Just use standard values
# ADD limits FOR TPH as well 



import paho.mqtt.client as mqtt
import ast
import datetime
import yaml
import collections
import json
import ssl
from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsLoRaReader as mLR
from mintsXU4 import mintsProcessing as mP
from mintsXU4 import mintsDefinitions as mD
from mintsXU4 import mintsLatest as mL
from mintsXU4 import mintsLiveNodes as mLN

import sys
import pandas as pd

mqttPort              = mD.mqttPort
mqttBroker            = mD.mqttBrokerDC
mqttCredentialsFile   = mD.credentials
tlsCert               = mD.tlsCert
nodeInfo              = mD.nodeInfo
sensorInfo            = mD.sensorInfo
credentials           = mD.credentials
liveSpanSec           = mD.liveSpanSec

connected             = False  # Stores the connection status
broker                = mqttBroker  
port                  = mqttPort  # Secure port
mqttUN                = credentials['mqtt']['username'] 
mqttPW                = credentials['mqtt']['password'] 

nodeIDs               = nodeInfo['nodeID']
sensorIDs             = sensorInfo['sensorID']

decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)

currentState = 0
nodeObjects  = []

    
def getNodeIndex(nodeIDRead):
    indexOut = 0
    for nodeID in nodeIDs:
        if (nodeIDRead == nodeID):
            return indexOut; 
        indexOut = indexOut +1
    return -1;

    
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
 
    # Subscribing in on_connect() - if we lose the connection and
    # reconnect then subscriptions will be renewed.
    for nodeID in nodeIDs:
        for sensorID in sensorIDs:
            topic = nodeID+"/"+ sensorID
            client.subscribe(topic)
            print("Subscrbing to Topic: "+ topic)

    # print(nodeInfo)
    # print(nodeInfo['pmSensor'])
    # print(nodeInfo['climateSensor'])
    # print(nodeInfo['gpsSensor'])

    print("Initializing Node Objects")
    for index, nodeInfoRow in nodeInfo.iterrows():
        print(nodeInfoRow)
        nodeObjects.append(mLN.node(nodeInfoRow))
        print("------------------------------------------------------")
        print("------------------------------------------------------")        

    
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global currentState
    
    try:
        [nodeID,sensorID] = msg.topic.split('/')
        sensorDictionary = decoder.decode(msg.payload.decode("utf-8","ignore"))
        nodeIndex = getNodeIndex(nodeID)
        dateTime = datetime.datetime.strptime(sensorDictionary["dateTime"], '%Y-%m-%d %H:%M:%S.%f')
        
        currentTimeInSec = dateTime.timestamp()
        liveState        = mP.getStateV2(currentTimeInSec)

        # Bird call data comes with a lag  
        if nodeIndex>=0 :   
            print() 
            print("==================================================================")
            print(" - - - ---------------- MINTS DATA RECEIVED ----------------- - - ")             
            print(" ------------------- Data for Live Node found ------------------- ")
            print("Node ID         : " + nodeID)
            print("Sensor ID       : " + sensorID)
            # print("Node Index      : " + str(nodeIndex))
            # print("Live State DC   : " + str(liveState))
            # print("LN Date Time    : " + str(dateTime))
            # print("Sensor Data     : " +  str(sensorDictionary))
            if currentState != liveState and sensorID != "MBC001":
                currentState = liveState
                print() 
                print(" - - - ==== - - - ======================== - - - ==== - - - ")
                print(" - - - ==== - - - ==== Status Changed ==== - - - ==== - - - ")
                for nodeObject in nodeObjects:
                    print() 
                    print("For Node Object" + str(nodeObject.nodeID))
                    nodeObject.changeStateV2()
   
            # print()
            # print(" - - - MINTS DATA RECEIVED - - - ")
            # print("Node ID   :" + nodeID)
            # print("Sensor ID :" + sensorID)
            # print("Node Index:" + str(nodeIndex))
            # print("Date Time :"  +str(dateTime))            
            # print("Data      :" + str(sensorDictionary))
            nodeObjects[nodeIndex].update(sensorID,sensorDictionary)



    except Exception as e:
        print("[ERROR] Could not publish data, error: {}".format(e))

# Create an MQTT client and attach our routines to it.
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(mqttUN,mqttPW)

client.tls_set(ca_certs=tlsCert, certfile=None,
                            keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                            tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)


client.tls_insecure_set(True)
client.connect(broker, port, 60)
client.loop_forever()
