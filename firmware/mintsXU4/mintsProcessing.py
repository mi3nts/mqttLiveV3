# // # ***************************************************************************
# // #   MQTT Subscribers V2
# // #   ---------------------------------
# // #   Written by: Lakitha Omal Harindha Wijeratne
# // #   - for -
# // #   MINTS:  Multi-scale Integrated Sensing and Simulation
# // #   &  
# // #   TRECIS: Texas Research and Education Cyberinfrastructure Services
# // #   ---------------------------------
# // #   Date: October 30th, 2023
# // #   ---------------------------------
# // #   This module is written for generic implimentation of LoRaWAN MINTS projects
# // #   --------------------------------------------------------------------------
# // #   https://github.com/mi3nts
# // #   https://mints.utdallas.edu/
# // #   https://trecis.cyberinfrastructure.org/
# // #  ***************************************************************************


import serial
import datetime
from datetime import timedelta
import os
import csv
#import deepdish as dd
from mintsXU4 import mintsLatest as mL
from mintsXU4 import mintsDefinitions as mD
from mintsXU4 import mintsSensorReader as mSR
from getmac import get_mac_address
import time
import serial
import pynmea2
from collections import OrderedDict
import netifaces as ni
import math
import base64
import json
import struct

macAddress              = mD.macAddress
dataFolder              = mD.dataFolder
dataFolderMQTT          = mD.dataFolderMQTT
dataFolderMQTTReference = mD.dataFolderMQTTReference
latestOn                = mD.latestOn
mqttOn                  = mD.mqttOn
decoder                 = json.JSONDecoder(object_pairs_hook=OrderedDict)
liveSpanSec             = mD.liveSpanSec

def getStateV2(timeIn):
    stateOut = int((timeIn + liveSpanSec/2)/liveSpanSec);
    # print("Current State")
    # print(stateOut)
    return stateOut;

def writeCSV3(writePath,sensorDictionary):
    exists = mSR.directoryCheck(writePath)
    keys =  list(sensorDictionary.keys())
    with open(writePath, 'a') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)
        if(not(exists)):
            # directoryCheck(writePath)
            writer.writeheader()
        writer.writerow(sensorDictionary)


def getWritePathDateCSV(folderIn,nodeID,dateTime,labelIn):
     
    writePath = folderIn+"/"+nodeID+"/"+ \
     str(dateTime.year).zfill(4)  + "/" + str(dateTime.month).zfill(2)+ "/"+str(dateTime.day).zfill(2)+"/"+ \
         "MINTS_"+ nodeID + "_" +labelIn + "_" +\
             str(dateTime.year).zfill(4) + "_" +str(dateTime.month).zfill(2) + "_" +str(dateTime.day).zfill(2) +".csv"
    return writePath;