
from getmac import get_mac_address
import serial.tools.list_ports
import yaml
import pandas as pd
# Change Accordingly  
mintsDefinitions          = yaml.load(open('mintsXU4/credentials/mintsDefinitions.yaml'),Loader=yaml.FullLoader)
dataFolder                = mintsDefinitions['dataFolder']
dataFolderReference       = mintsDefinitions['dataFolder'] + "/reference"
dataFolderMQTTReference   = mintsDefinitions['dataFolder'] + "/referenceMqtt"  # The path of your MQTT Reference Data 
dataFolderMQTT            = mintsDefinitions['dataFolder'] + "/rawMqtt"        # The path of your MQTT Raw Data 
tlsCert                   = mintsDefinitions['tlsCert']     # The path of your TLS cert

liveSpanSec               = mintsDefinitions['liveSpanSec']

latestOn                  = False

mqttOn                    = True
credentialsFile           = 'mintsXU4/credentials/credentials.yaml'
# credentials               = yaml.load(open(credentialsFile))

with open(credentialsFile, 'r') as file:
    credentials = yaml.load(file, Loader=yaml.SafeLoader)

sensorInfo                = pd.read_csv('https://raw.githubusercontent.com/mi3nts/mqttSubscribersV2/main/lists/sensorIDs.csv')
portInfo                  = pd.read_csv('https://raw.githubusercontent.com/mi3nts/mqttSubscribersV2/main/lists/portIDs.csv')

nodeInfo                  = pd.read_csv('https://raw.githubusercontent.com/mi3nts/mqttLiveV2/main/lists/sharedAirDFWSupport.csv') 
# nodeInfo                  = pd.read_csv('https://raw.githubusercontent.com/mi3nts/mqttLiveV3/main/lists/sharedAirDFWSupportTest.csv') # For Testing Purposes --> Different from the NODE ID LOOK UP


mqttBrokerDC              = "mqtt.circ.utdallas.edu"
mqttBrokerLoRa            = "mqtt.lora.trecis.cloud"

mqttPort                  = 8883  # Secure port
mqttPortLoRa              = 1883  # Secure port

timeSpan                  = mintsDefinitions['timeSpan']

liveFolder                = dataFolder    + "/liveUpdate/results"

modelFile                 = "mintsXU4/credentials/climateCorrectionModel.joblib"


def findMacAddress():
    macAddress= get_mac_address(interface="eth0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    macAddress= get_mac_address(interface="docker0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    macAddress= get_mac_address(interface="enp1s0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    return "xxxxxxxx"

macAddress                = findMacAddress()

print()
print("----- MQTT Subscriber V2 -----")
print(" ")
print("Node Info:")
print(nodeInfo)
print(" ")
print("Sensor Info:")
print(sensorInfo)
print(" ")
print("Port Info:")
print(portInfo)
