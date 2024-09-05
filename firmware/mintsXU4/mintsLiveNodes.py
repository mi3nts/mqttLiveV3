from cmath import nan
from datetime import datetime, timedelta
from os import name
import time
import random
import pandas as pd
#import pyqtgraph as pg
from collections import deque
#from pyqtgraph.Qt import QtGui, QtCore
from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsLoRaReader as mLR
from mintsXU4 import mintsDefinitions as mD
from mintsXU4 import mintsProcessing as mP
from mintsXU4 import mintsLatest as mL
# from mintsXU4 import mintsNow as mN
import math
from geopy.geocoders import Nominatim

# from dateutil import tz
import numpy as np
#from pyqtgraph import AxisItem
from time import mktime
import statistics
from collections import OrderedDict
# import pytz
import sys

liveSpanSec            = mD.mintsDefinitions['liveSpanSec']
liveFolder             = mD.liveFolder


# The humidity correction as well as the machine learning correction only 
# updates after the averaging has been done 
# On this version T will be in C 
# Next Few Steps - Try out the code and see if the GPS Stuff is working 
# Make sure I do not append climate data if they are not within bounds 
#  Add support for humidty corrections 


class node:
    def __init__(self,nodeInfoRow):
        self.nodeID = nodeInfoRow['nodeID']
        print("============MINTS============")
        print("NODE ID: " + self.nodeID)

        self.pmSensor      = nodeInfoRow['pmSensor']
        self.climateSensor = nodeInfoRow['climateSensor']
        self.gpsSensor     = nodeInfoRow['gpsSensor']
        
        self.latitudeHC    = nodeInfoRow['latitude']
        self.longitudeHC   = nodeInfoRow['longitude']
        self.altitudeHC    = nodeInfoRow['altitude']
        
        self.evenState       = True
        self.initRunPM       = True
        self.initRunClimate  = True
        self.initRunGPS      = True

        self.lastPMDateTime      = datetime(2010, 1, 1, 0, 0, 0, 0)
        self.lastClimateDateTime = datetime(2010, 1, 1, 0, 0, 0, 0)
        self.lastGPSDateTime     = datetime(2010, 1, 1, 0, 0, 0, 0)

 
        self.pc0_1          = []
        self.pc0_3          = []
        self.pc0_5          = []
        self.pc1_0          = []
        self.pc2_5          = []
        self.pc5_0          = []
        self.pc10_0         = []

        self.pm0_1          = []
        self.pm0_3          = []
        self.pm0_5          = []
        self.pm1_0          = []
        self.pm2_5          = []
        self.pm5_0          = []
        self.pm10_0         = []

        self.dateTimePM     = []


        # For Humidity Corrected Values 
        # Corrected PC Values 
        self.cor_pc0_1      = []
        self.cor_pc0_3      = []
        self.cor_pc0_5      = []
        self.cor_pc1_0      = []
        self.cor_pc2_5      = []
        self.cor_pc5_0      = []
        self.cor_pc10_0     = []

        #  Corrected PM Values 
        self.cor_pm0_1      = []
        self.cor_pm0_3      = []
        self.cor_pm0_5      = []
        self.cor_pm1_0      = []
        self.cor_pm2_5      = []
        self.cor_pm5_0      = []
        self.cor_pm10_0     = []

        # For ML Corrected 
        self.mlPM2_5        = []

        # if self.climateSensor  in {"BME280", "BME680", "BME688CNR"}:
        self.temperature         = []
        self.pressure            = []
        self.humidity            = []
        self.dewPoint            = []
        self.dateTimeClimate     = []

        # if self.gpsSensor  in {"GPGGAPL", "GPGGALR"}:
   
        self.latitude       = []
        self.longitude      = []
        self.altitude       = []
        self.dateTimeGPS    = []



        # For Validity checks 
        self.mlCorrected    = []
        
        # Validity Variables 
        self.temperatureValidity        = [] # Checks if temeperature readings are in range 
        self.humidityValidity           = []# Checks if humidity readings are in range 
        self.pressureValidity           = []
        self.momentaryValidity          = [] # Checks if climate readings are reasont 
        self.humidityLikelyhoodValidity = [] # Checks if humdity readings make sense for fog to be created 
        self.dewPointValidity           = [] # Checks if temperature and dew point is close enough to make sense for fog to be create
        
        self.climateRequirment          = [] # Climate  check 
        self.correctionRequirment       = [] # Master  check 





    def update(self,sensorID,sensorDictionary):
        if sensorID == self.pmSensor:
             self.nodeReaderPM(sensorDictionary)                
        if sensorID == self.climateSensor:
            self.nodeReaderClimate(sensorDictionary)
        if sensorID == self.gpsSensor:
             self.nodeReaderGPS(sensorDictionary)


    # For Particulate Matter  

    def nodeReaderPM(self,jsonData):
        # if (True):
        try:
            # print(jsonData)
            self.dataInPM       = jsonData
            self.ctNowPM        = datetime.strptime(self.dataInPM['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            # print(self.ctNowPM)

            if (self.ctNowPM>self.lastPMDateTime):
                self.currentUpdatePM()
        except Exception as e:
            print("[ERROR] Could not read JSON data, error: {}".format(e))
    
    def currentUpdatePM(self):

        if self.pmSensor  in {"IPS7100", "IPS7100CNR"}:
            self.pc0_1.append(float(self.dataInPM['pc0_1']))
            self.pc0_3.append(float(self.dataInPM['pc0_3']))
            self.pc0_5.append(float(self.dataInPM['pc0_5']))
            self.pc1_0.append(float(self.dataInPM['pc1_0']))
            self.pc2_5.append(float(self.dataInPM['pc2_5']))
            self.pc5_0.append(float(self.dataInPM['pc5_0']))
            self.pc10_0.append(float(self.dataInPM['pc10_0']))

            self.pm0_1.append(float(self.dataInPM['pm0_1']))
            self.pm0_3.append(float(self.dataInPM['pm0_3']))
            self.pm0_5.append(float(self.dataInPM['pm0_5']))
            self.pm1_0.append(float(self.dataInPM['pm1_0']))
            self.pm2_5.append(float(self.dataInPM['pm2_5']))
            self.pm5_0.append(float(self.dataInPM['pm5_0']))
            self.pm10_0.append(float(self.dataInPM['pm10_0']))

            timeIn = datetime.strptime(self.dataInPM['dateTime'],'%Y-%m-%d %H:%M:%S.%f')

            self.dateTimePM.append(timeIn)
            self.lastPMDateTime = timeIn


    # Taking care of climate data 
    
    def nodeReaderClimate(self,jsonData):
        try:
        # if (True):
            self.dataInClimate  = jsonData
            self.ctNowClimate   = datetime.strptime(self.dataInClimate['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            if (self.ctNowClimate>self.lastClimateDateTime):
                self.currentUpdateClimate()
        except Exception as e:
            print("[ERROR] Could not read JSON data, error: {}".format(e))
    
    def currentUpdateClimate(self):
         # Make sure to only append if climate data is valid 
        if self.climateSensor in {"BME280"}:        

            self.temperature.append(float(self.dataInClimate['temperature']))
            self.pressure.append(float(self.dataInClimate['pressure'])/100)
            self.humidity.append(float(self.dataInClimate['humidity']))
            self.dewPoint.append(float(self.calculateDewPointInC(self.temperature, self.humidity)))
            
            timeIn = datetime.strptime(self.dataInClimate['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            self.dateTimeClimate.append(timeIn)
            self.lastClimateDateTime = timeIn

        if self.climateSensor in {"BME280V2"}:        
            self.temperature.append(float(self.dataInClimate['temperature']))
            self.pressure.append(float(self.dataInClimate['pressure']))
            self.humidity.append(float(self.dataInClimate['humidity']))
            self.dewPoint.append(float(self.dataInClimate['dewPoint']))
            
            timeIn = datetime.strptime(self.dataInClimate['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            self.dateTimeClimate.append(timeIn)
            self.lastClimateDateTime = timeIn

        if self.climateSensor in {"BME688CNR"}:       
            self.temperature.append(float(self.dataInClimate['temperature']))
            self.pressure.append(float(self.dataInClimate['pressure']))
            self.humidity.append(float(self.dataInClimate['humidity']))
            self.dewPoint.append(float(self.calculateDewPointInC(self.temperature, self.humidity)))
            
            timeIn = datetime.strptime(self.dataInClimate['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            self.dateTimeClimate.append(timeIn)
            self.lastClimateDateTime = timeIn


        if self.climateSensor in {"BME680"}:       
            self.temperature.append(float(self.dataInClimate['temperature']))
            self.pressure.append(float(self.dataInClimate['pressure'])*10)
            self.humidity.append(float(self.dataInClimate['humidity']))
            self.dewPoint.append(float(self.calculateDewPointInC(self.temperature, self.humidity)))
            
            timeIn = datetime.strptime(self.dataInClimate['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            self.dateTimeClimate.append(timeIn)
            self.lastClimateDateTime = timeIn

        if self.climateSensor in {"WIMDA"}:       
            self.temperature.append(float(self.dataInClimate['airTemperature']))
            self.pressure.append(float(self.dataInClimate['barrometricPressureBars'])*1000)
            self.humidity.append(float(self.dataInClimate['relativeHumidity']))
            self.dewPoint.append(float(self.dataInClimate['dewPoint']))
            
            timeIn = datetime.strptime(self.dataInClimate['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            self.dateTimeClimate.append(timeIn)
            self.lastClimateDateTime = timeIn

    #  For  GPS Readings 
    def nodeReaderGPS(self,jsonData):
        try:
            self.dataInGPS  = jsonData
            self.ctNowGPS   = datetime.strptime(self.dataInGPS['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            if (self.ctNowGPS>self.lastGPSDateTime ):
                self.currentUpdateGPS()
        except Exception as e:
            print("[ERROR] Could not read JSON data, error: {}".format(e))

    def currentUpdateGPS(self):

            if self.gpsSensor in {"GPSGPGGA2","GPGGAPL","PA1010D"}:      
                self.latitude.append(float(self.dataInGPS['latitudeCoordinate']))
                self.longitude.append(float(self.dataInGPS['longitudeCoordinate']))
                self.altitude.append(float(self.dataInGPS['altitude']))
                timeIn  = datetime.strptime(self.dataInGPS['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
                self.dateTimeGPS.append(timeIn)
                self.lastGPSDateTime = timeIn

            if self.gpsSensor in {"GPGGA"}:      
                self.latitude.append(float(self.getLatitudeCords(self.dataInGPS['latitude'],self.dataInGPS['latDirection'])))
                self.longitude.append(float(self.getLongitudeCords(self.dataInGPS['longitude'],self.dataInGPS['lonDirection'])))
                self.altitude.append(float(self.dataInGPS['altitude']))
                timeIn  = datetime.strptime(self.dataInGPS['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
                self.dateTimeGPS.append(timeIn)
                self.lastGPSDateTime = timeIn

            if self.gpsSensor in {"GPGGALR"}:      
                self.latitude.append(float(self.dataInGPS['latitude']))
                self.longitude.append(float(self.dataInGPS['longitude']))
                self.altitude.append(float(self.dataInGPS['altitude']))
                timeIn  = datetime.strptime(self.dataInGPS['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
                self.dateTimeGPS.append(timeIn)
                self.lastGPSDateTime = timeIn

    def getLatitudeCords(self,latitudeStr,latitudeDirection):
        latitude = float(latitudeStr)
        latitudeCord      =  math.floor(latitude/100) +(latitude - 100*(math.floor(latitude/100)))/60
        if(latitudeDirection=="S"):
            latitudeCord = -1*latitudeCord
        return latitudeCord

    def getLongitudeCords(self,longitudeStr,longitudeDirection):
        longitude = float(longitudeStr)
        longitudeCord      =  math.floor(longitude/100) +(longitude - 100*(math.floor(longitude/100)))/60
        if(longitudeDirection=="W"):
            longitudeCord = -1*longitudeCord
        return longitudeCord


    def fahrenheitToCelsius(self,fahrenheit):
        return (fahrenheit - 32) / 1.8

    def celsiusToFahrenheit(self,celsius):
        return celsius * 9/5 + 32

    def calculateDewPointInF(self,temperature,humidity):
        # Convert Fahrenheit to Celsius
        temperatureCelsius = self.fahrenheitToCelsius(temperature)
        return self.celsiusToFahrenheit(self.calculateDewPointInC(temperatureCelsius, humidity))


    def calculateDewPointInC(self,temperature, humidity):
        dewPoint = 243.04 * (math.log(humidity/100.0) + ((17.625 * temperature)/(243.04 + temperature))) / (17.625 - math.log(humidity/100.0) - ((17.625 * temperature)/(243.04 + temperature)))
        return dewPoint



    def getTimeV2(self):
        checkTime = datetime.fromtimestamp(mP.getStateV2(self.dateTimePM[-1].timestamp())*liveSpanSec)
        self.dateTimeStrCSV = str(checkTime.year).zfill(4)+ \
                "-" + str(checkTime.month).zfill(2) + \
                "-" + str(checkTime.day).zfill(2) + \
                " " + str(checkTime.hour).zfill(2) + \
                ":" + str(checkTime.minute).zfill(2) + \
                ":" + str(checkTime.second).zfill(2) + '.000'
        # print(self.dateTimeStrCSV)    
        return ;

    
    def getValidity(self):
        # print("Getting Validity")     
        return len(self.pm0_1)>=1;



    def changeStateV2(self):
        # print("Change State V2")
        if self.getValidity():
            # print("Is Valid")
            self.getAverageAll()
            # self.getTimeV2()
            self.doCSV()
        # self.evenState = not(self.evenState)
        self.clearAll()      

    def clearAll(self):
        self.pc0_1      = []
        self.pc0_3      = []
        self.pc0_5      = []
        self.pc1_0      = []
        self.pc2_5      = []
        self.pc5_0      = []
        self.pc10_0     = []

        self.pm0_1      = []
        self.pm0_3      = []
        self.pm0_5      = []
        self.pm1_0      = []
        self.pm2_5      = []
        self.pm5_0      = []
        self.pm10_0     = []        
        self.dateTimePM = []

        self.temperature       = []
        self.pressure          = []
        self.humidity          = []
        self.dewPoint          = []
        self.dateTimeClimate   = []

        self.latitude          = []
        self.longitude         = []
        self.altitude          = []
        self.dateTimeGPS       = []


    def getAverageAll(self):
        if(len(self.pc0_1)>0):
            self.pc0_1Avg      = statistics.mean(self.pc0_1)
            self.pc0_3Avg      = statistics.mean(self.pc0_3)
            self.pc0_5Avg      = statistics.mean(self.pc0_5)
            self.pc1_0Avg      = statistics.mean(self.pc1_0)
            self.pc2_5Avg      = statistics.mean(self.pc2_5)
            self.pc5_0Avg      = statistics.mean(self.pc5_0)
            self.pc10_0Avg     = statistics.mean(self.pc10_0)

            self.pm0_1Avg      = statistics.mean(self.pm0_1)
            self.pm0_3Avg      = statistics.mean(self.pm0_3)
            self.pm0_5Avg      = statistics.mean(self.pm0_5)
            self.pm1_0Avg      = statistics.mean(self.pm1_0)
            self.pm2_5Avg      = statistics.mean(self.pm2_5)
            self.pm5_0Avg      = statistics.mean(self.pm5_0)
            self.pm10_0Avg     = statistics.mean(self.pm10_0)       
        
        if(len(self.temperature)>0):
            self.temperatureAvg  = statistics.mean(self.temperature)
            self.pressureAvg     = statistics.mean(self.pressure)
            self.humidityAvg     = statistics.mean(self.humidity)
            self.dewPointAvg     = statistics.mean(self.dewPoint)
        else:
            self.temperatureAvg  = 65.0
            self.pressureAvg     = 1013.25
            self.humidityAvg     = 50.0
            self.dewPointAvg     = 55.0
            
        if (len(self.latitude)>0):
            self.latitudeAvg  = statistics.mean(self.latitude)
            self.longitudeAvg = statistics.mean(self.longitude)
            self.altitudeAvg  = statistics.mean(self.altitude)
        else:
            self.longitudeAvg = self.longitudeHC
            self.latitudeAvg  = self.latitudeHC
            self.altitudeAvg  = self.altitudeHC

    def doCSV(self):
        self.getTimeV2()
        sensorDictionary = OrderedDict([
                ("dateTime"         ,self.dateTimeStrCSV),
                ("nodeID"           ,self.nodeID),
                ("climateSensor"    ,self.climateSensor),
                ("pmSensor"         ,self.pmSensor),                                
                ("Latitude"         ,self.latitudeAvg),                
                ("Longitude"        ,self.longitudeAvg),
                ("Altitude"         ,self.altitudeAvg),    
                ("PC0_1"            ,self.pc0_1Avg),
                ("PC0_3"            ,self.pc0_3Avg),
                ("PC0_5"            ,self.pc0_5Avg),
                ("PC1_0"            ,self.pc1_0Avg),
                ("PC2_5"            ,self.pc2_5Avg),
                ("PC5_0"            ,self.pc5_0Avg),
                ("PC10_0"           ,self.pc10_0Avg),
                ("PM0_1"            ,self.pm0_1Avg),
                ("PM0_3"            ,self.pm0_3Avg),
                ("PM0_5"            ,self.pm0_5Avg),
                ("PM1"              ,self.pm1_0Avg),
                ("PM2_5"            ,self.pm2_5Avg),
                ("PM5_0"            ,self.pm5_0Avg),
                ("PM10"             ,self.pm10_0Avg),
                ("Temperature"      ,self.temperatureAvg),
                ("Pressure"         ,self.pressureAvg),
                ("Humidity"         ,self.humidityAvg),
                ("DewPoint"         ,self.dewPointAvg),        
                ("nopGPS"           ,len(self.dateTimeGPS)),
                ("nopPM"            ,len(self.dateTimePM)),
                ("nopClimate"       ,len(self.dateTimeClimate)),       
                ("temperatureMDL"   ,"directDataUsed_noCalibrationDone"),
                ("pressureMDL"      ,"directDataUsed_noCalibrationDone"),
                ("humidityMDL"      ,"directDataUsed_noCalibrationDone"),
                ("dewPointMDL"      ,"directDataUsed_noCalibrationDone")                
               ])
        
        print()        
        print("===============MINTS===============")
        print(sensorDictionary)
        mP.writeCSV3( mP.getWritePathDateCSV(liveFolder,self.nodeID,\
            datetime.strptime(self.dateTimeStrCSV,'%Y-%m-%d %H:%M:%S.%f'),\
                "calibrated"),sensorDictionary)
        print("CSV Written")
        # mL.writeMQTTLatestRepublish(sensorDictionary,"mintsCalibrated",self.nodeID)

# from geopy.geocoders import Nominatim

    def getAltitudeFromGeopy(latitude, longitude):
        geolocator = Nominatim(user_agent="altitude_finder")
        location = geolocator.reverse((latitude, longitude), language="en")

        if location and "altitude" in location.raw:
            altitude = location.raw["altitude"]
            return altitude
        else:
            return None






