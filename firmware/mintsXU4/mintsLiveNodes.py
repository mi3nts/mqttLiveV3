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
import traceback
# from dateutil import tz
import numpy as np
#from pyqtgraph import AxisItem
from time import mktime
import statistics
from collections import OrderedDict
# import pytz
import sys
import joblib


liveSpanSec            = mD.mintsDefinitions['liveSpanSec']
liveFolder             = mD.liveFolder

modelFile              = mD.modelFile
loadedPMModel          = joblib.load(modelFile)

# The humidity correction as well as the machine learning correction only 
# updates after the averaging has been done 
# On this version T will be in C 
# Next Few Steps - Try out the code and see if the GPS Stuff is working 
# Make sure I do not append climate data if they are not within bounds 
# Add support for humidty corrections 
# For climate data if there are no  data fill it up with fake data 

class node:
    def __init__(self,nodeInfoRow):
        self.nodeID = nodeInfoRow['nodeID']
        print("============MINTS============")
        print("NODE ID: " + self.nodeID)

        self.pmSensor      = nodeInfoRow['pmSensor']
        self.climateSensor = nodeInfoRow['climateSensor']
        self.gpsSensor     = nodeInfoRow['gpsSensor']

        self.jsonClimateData, self.jsonClimateDataRead = \
                            mL.readJSONLive(self.nodeID,self.climateSensor)
        
        self.jsonGPSData,     self.jsonGPSDataRead     = \
                            mL.readJSONLive(self.nodeID,self.gpsSensor)

        self.latitudeGit    = nodeInfoRow['latitude']
        self.longitudeGit   = nodeInfoRow['longitude']
        self.altitudeGit    = nodeInfoRow['altitude']
        
        self.evenState       = True
        self.initRunPM       = True
        self.initRunClimate  = True
        self.initRunGPS      = True

        self.lastPMDateTime      = datetime(2010, 1, 1, 0, 0, 0, 0)
        self.lastClimateDateTime = datetime(2010, 1, 1, 0, 0, 0, 0)
        self.lastGPSDateTime     = datetime(2010, 1, 1, 0, 0, 0, 0)

        self.latestPMAvgDateTime      = datetime(2010, 1, 1, 0, 0, 0, 0)
        self.latestClimateAvgDateTime = datetime(2010, 1, 1, 0, 0, 0, 0)
        self.latestGPSAvgDateTime     = datetime(2010, 1, 1, 0, 0, 0, 0)
 
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
        self.humidityValidity           = [] # Checks if humidity readings are in range 
        self.pressureValidity           = []
        self.momentaryValidity          = [] # Checks if climate readings are reasont 
        self.humidityLikelyhoodValidity = [] # Checks if humdity readings make sense for fog to be created 
        self.dewPointValidity           = [] # Checks if temperature and dew point is close enough to make sense for fog to be create
        
        self.climateRequirment          = [] # Climate  check 
        self.correctionRequirment       = [] # Master  check 



    def changeStateV2(self):
        # print("Change State V2")
        # if self.getPMValidity():
        print("Getting Time")
        if self.getPMValidity():
            self.getTimePM()

        if self.getClimateValidity():
            self.getTimeClimate()

        if self.getGPSValidity():
            self.getTimeGPS()

        print("Getting AverageAll")
        if self.dataAvailability():
            self.getAverageAll()

        if self.getPMValidity():
            self.applyCorrections()
            self.doCSV()

        self.clearAll()      

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
            traceback.print_exc()
    
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
            traceback.print_exc()
    
    def currentUpdateClimate(self):
         # Make sure to only append if climate data is valid 
        if self.climateSensor in {"BME280"}:        
            temperatureRead  = float(self.dataInClimate['temperature'])
            pressureRead     = float(self.dataInClimate['pressure'])/100
            humidityRead     = float(self.dataInClimate['humidity'])
            dewPointRead     = self.calculateDewPointInC(temperatureRead, humidityRead)

        if self.climateSensor in {"BME280V2"}:      
            temperatureRead  = float(self.dataInClimate['temperature'])
            pressureRead     = float(self.dataInClimate['pressure'])
            humidityRead     = float(self.dataInClimate['humidity'])
            dewPointRead     = float(self.dataInClimate['dewPoint'])

        if self.climateSensor in {"BME688CNR"}:       
            temperatureRead  = float(self.dataInClimate['temperature'])
            pressureRead     = float(self.dataInClimate['pressure'])
            humidityRead     = float(self.dataInClimate['humidity'])
            dewPointRead     = self.calculateDewPointInC(temperatureRead, humidityRead)

        if self.climateSensor in {"BME680"}:       
            temperatureRead  = float(self.dataInClimate['temperature'])
            pressureRead     = float(self.dataInClimate['pressure'])*10
            humidityRead     = float(self.dataInClimate['humidity'])
            dewPointRead     = self.calculateDewPointInC(temperatureRead, humidityRead)
            
        if self.climateSensor in {"WIMDA"}:      
            temperatureRead  = float(self.dataInClimate['airTemperature'])
            pressureRead     = float(self.dataInClimate['barrometricPressureBars'])*1000
            humidityRead     = float(self.dataInClimate['relativeHumidity'])
            dewPointRead     = float(self.dataInClimate['dewPoint'])
                                
        # At this point check for validity 
        if self.checkClimateValidity(temperatureRead,pressureRead,humidityRead):
            self.temperature.append(temperatureRead )
            self.pressure.append(pressureRead)
            self.humidity.append(humidityRead)
            self.dewPoint.append(dewPointRead)
            timeIn = datetime.strptime(self.dataInClimate['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            self.dateTimeClimate.append(timeIn)
            self.lastClimateDateTime = timeIn

    def is_valid_temperature(self,temp):
        return -20 <= temp <= 50  # Assuming temperature is in celsius

    def is_valid_pressure(self,pressure):
        return  950 <= pressure <= 1100  # Assuming pressure is in milibars

    def is_valid_humidity(self,humidity):
        return 0 <= humidity <= 100  # Assuming humidity is in percentage


    def checkClimateValidity(self,temperatureIn,pressureIn,humidityIn):
        return self.is_valid_temperature(temperatureIn) and\
                 self.is_valid_pressure(pressureIn) and\
                    self.is_valid_humidity(humidityIn) 


    #  For  GPS Readings 
    def nodeReaderGPS(self,jsonData):
        try:
            self.dataInGPS  = jsonData
            self.ctNowGPS   = datetime.strptime(self.dataInGPS['dateTime'],'%Y-%m-%d %H:%M:%S.%f')
            if (self.ctNowGPS>self.lastGPSDateTime ):
                self.currentUpdateGPS()
        except Exception as e:
            print("[ERROR] Could not read JSON data, error: {}".format(e))
            traceback.print_exc()

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

    # def getTimeV2(self):
    #     self.dateTimeCSV = datetime.fromtimestamp(mP.getStateV2(self.dateTimePM[-1].timestamp())*liveSpanSec)
    #     self.dateTimeStrCSV = str(self.dateTimeCSV.year).zfill(4)+ \
    #             "-" + str(self.dateTimeCSV.month).zfill(2) + \
    #             "-" + str(self.dateTimeCSV.day).zfill(2) + \
    #             " " + str(self.dateTimeCSV.hour).zfill(2) + \
    #             ":" + str(self.dateTimeCSV.minute).zfill(2) + \
    #             ":" + str(self.dateTimeCSV.second).zfill(2) + '.000'
    #     # print(self.dateTimeStrCSV)    
    #     return ;


    def getTimePM(self):
        self.dateTimePMCSV = datetime.fromtimestamp(mP.getStateV2(self.dateTimePM[-1].timestamp())*liveSpanSec)
        self.dateTimePMStrCSV = str(self.dateTimePMCSV.year).zfill(4)+ \
                "-" + str(self.dateTimePMCSV.month).zfill(2) + \
                "-" + str(self.dateTimePMCSV.day).zfill(2) + \
                " " + str(self.dateTimePMCSV.hour).zfill(2) + \
                ":" + str(self.dateTimePMCSV.minute).zfill(2) + \
                ":" + str(self.dateTimePMCSV.second).zfill(2) + '.000'
        # print(self.dateTimeStrCSV)    
        return ;
    
    def getTimeClimate(self):
        self.dateTimeClimateCSV = datetime.fromtimestamp(mP.getStateV2(self.dateTimeClimate[-1].timestamp())*liveSpanSec)
        self.dateTimeClimateStrCSV = str(self.dateTimeClimateCSV.year).zfill(4)+ \
                "-" + str(self.dateTimeClimateCSV.month).zfill(2) + \
                "-" + str(self.dateTimeClimateCSV.day).zfill(2) + \
                " " + str(self.dateTimeClimateCSV.hour).zfill(2) + \
                ":" + str(self.dateTimeClimateCSV.minute).zfill(2) + \
                ":" + str(self.dateTimeClimateCSV.second).zfill(2) + '.000'
        # print(self.dateTimeStrCSV)    
        return ;

    def getTimeGPS(self):
        self.dateTimeGPSCSV = datetime.fromtimestamp(mP.getStateV2(self.dateTimeGPS[-1].timestamp())*liveSpanSec)
        self.dateTimeGPSStrCSV = str(self.dateTimeGPSCSV.year).zfill(4)+ \
                "-" + str(self.dateTimeGPSCSV.month).zfill(2) + \
                "-" + str(self.dateTimeGPSCSV.day).zfill(2) + \
                " " + str(self.dateTimeGPSCSV.hour).zfill(2) + \
                ":" + str(self.dateTimeGPSCSV.minute).zfill(2) + \
                ":" + str(self.dateTimeGPSCSV.second).zfill(2) + '.000'
        # print(self.dateTimeStrCSV)    
        return ;



    def getPMValidity(self):
        # print("Getting PM Validity")     
        # print(self.pm0_1)
        # # print("validated")
        return len(self.pm0_1)>=1;

    def getClimateValidity(self):
        # print("Getting PM Validity")     
        # print(self.pm0_1)
        # # print("validated")
        return len(self.temperature)>=1;

    def getGPSValidity(self):
        # print("Getting PM Validity")     
        # print(self.pm0_1)
        # # print("validated")
        return len(self.latitude)>=1;


    def getAltitudeFromGeopy(latitude, longitude):
        geolocator = Nominatim(user_agent="altitude_finder")
        location = geolocator.reverse((latitude, longitude), language="en")

        if location and "altitude" in location.raw:
            altitude = location.raw["altitude"]
            return altitude
        else:
            return None



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

    def dataAvailability(self):
        return len(self.pc0_1)>0 or len(self.temperature)>0 or  len(self.latitude)>0

    def getAverageAll(self):
        # On this function it decides what data to use 

        # 1) Live data 
        # 2) Prev data recorded from the latest live data (Latest )
        # 3) Taken from Json data (Coined as JSON data )
        # These precursers apply only for Climate and GPS data 
        # And got to this about how this applies for the corrections 

        # The Relevant Flags 
            # climateConcurrent - Current Readings are used 
            # climateFirmware 
            # climateJSON  
            # climateDummy (This cannot be recent)
            # climateRecent (10 minutes) - Readings from the firmware or json 
            # fogLikelyhood

            # GPSConcurrent 
            # GPSFirmware 
            # GPSJson 
            # GPSFromGit
            # GPSRecent(Check if its from the last 10 minutes)
            
            # humidityCorrectionApplied
            # mlPM2_5CorrectionApplied  

        self.climateConcurrent = 0  
        self.climateFirmware   = 0  
        self.climateJSON       = 0  
        self.climateDummy      = 0  
        self.climateRecent     = 0  
        self.fogLikelyhood     = 0 

        self.GPSConcurrent     = 0  
        self.GPSFirmware       = 0  
        self.GPSJson           = 0  
        self.GPSFromGit        = 0  
        self.GPSRecent         = 0  

        self.humidityCorrectionApplied = 0 
        self.mlPM2_5CorrectionApplied  = 0 

        if(len(self.pc0_1)>0):
            # self.getTimeV2()
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
            
            self.latestClimateAvgDateTime = self.dateTimeClimateCSV
            self.latestTemperature        = self.temperatureAvg
            self.latestPressure           = self.pressureAvg
            self.latestHumidity           = self.humidityAvg
            self.latestDewPoint           = self.dewPointAvg
            
            climateDictionary = OrderedDict([
                ("dateTime"         ,self.dateTimeClimateStrCSV),
                ("nodeID"           ,self.nodeID),
                ("climateSensor"    ,self.climateSensor),
                ("Temperature"      ,self.temperatureAvg),
                ("Pressure"         ,self.pressureAvg),
                ("Humidity"         ,self.humidityAvg),
                ("DewPoint"         ,self.dewPointAvg),   
                ("nopClimate"       ,len(self.dateTimeClimate))
                   ])
            print(climateDictionary)
            mL.writeJSONLive(self.nodeID,self.climateSensor,climateDictionary)


            self.climateConcurrent = 1
            self.climateRecent     = 1

            
        elif self.getPMValidity():   
            if self.checkElapsedTime(self.dateTimePMCSV,\
                                     self.latestClimateAvgDateTime,\
                                        timedelta(minutes=10)):
                self.climateFirmware = 1
                self.climateRecent   = 1
                self.temperatureAvg  = self.latestTemperature
                self.pressureAvg     = self.latestPressure
                self.humidityAvg     = self.latestHumidity
                self.dewPointAvg     = self.latestDewPoint        

            elif self.checkElapsedTime( self.dateTimePMCSV,\
                                            self.latestClimateAvgDateTime,\
                                                timedelta(days=365*10)):
                self.climateFirmware = 1
                self.temperatureAvg  = self.latestTemperature
                self.pressureAvg     = self.latestPressure
                self.humidityAvg     = self.latestHumidity
                self.dewPointAvg     = self.latestDewPoint  
            
            else:
                if self.jsonClimateDataRead: 

                    print(self.jsonClimateData)
                    dateTimeJSON = datetime.strptime(\
                                        self.jsonClimateData['dateTime'],\
                                            '%Y-%m-%d %H:%M:%S.%f')
                    if self.checkElapsedTime(self.dateTimePMCSV,\
                                                dateTimeJSON,\
                                                    timedelta(minutes=10)):
                        self.climateRecent = 1
                        self.climateJSON   = 1  
                        self.temperatureAvg  = self.jsonClimateData['Temperature']
                        self.pressureAvg     = self.jsonClimateData['Pressure']
                        self.humidityAvg     = self.jsonClimateData['Humidity']
                        self.dewPointAvg     = self.jsonClimateData['DewPoint']

                    else: 
                        self.climateDummy    = 1
                        self.temperatureAvg  = 25.0
                        self.pressureAvg     = 1013.25
                        self.humidityAvg     = 50.0
                        self.dewPointAvg     = 55.0

                else:
                    self.climateDummy    = 1
                    self.temperatureAvg  = 25.0
                    self.pressureAvg     = 1013.25
                    self.humidityAvg     = 50.0
                    self.dewPointAvg     = 55.0
            
        if (len(self.latitude)>0):
            self.latitudeAvg   = statistics.mean(self.latitude)
            self.longitudeAvg  = statistics.mean(self.longitude)
            self.altitudeAvg   = statistics.mean(self.altitude)

            self.latestGPSAvgDateTime     = self.dateTimeGPSCSV
            self.latestLatitude           = self.latitudeAvg
            self.latestLongitude          = self.longitudeAvg
            self.latestAltitude           = self.altitudeAvg

            gpsDictionary = OrderedDict([
                ("dateTime"         ,self.dateTimeGPSStrCSV),
                ("nodeID"           ,self.nodeID),
                ("gpsSensor"        ,self.gpsSensor),                                
                ("Latitude"         ,self.latitudeAvg),                
                ("Longitude"        ,self.longitudeAvg),
                ("Altitude"         ,self.altitudeAvg),          
                ("nopGPS"           ,len(self.dateTimeGPS)),          
               ])
            print(gpsDictionary)
            mL.writeJSONLive(self.nodeID,self.gpsSensor,gpsDictionary)

            self.gpsConcurrent = 1
            self.gpsRecent     = 1

        elif self.getPMValidity():
            if self.checkElapsedTime(self.dateTimePMCSV,\
                                        self.latestGPSAvgDateTime,\
                                            timedelta(minutes=10)):
                self.latitudeAvg   = self.latestLatitude
                self.longitudeAvg  = self.latestLongitude
                self.altitudeAvg   = self.latestAltitude
                self.gpsRecent     = 1
                self.gpsFirmware   = 1

            elif self.checkElapsedTime( self.dateTimePMCSV,\
                                            self.latestGPSAvgDateTime,\
                                                timedelta(days=365*10)):
                self.gpsFirmware   = 1
                self.latitudeAvg   = self.latestLatitude
                self.longitudeAvg  = self.latestLongitude
                self.altitudeAvg   = self.latestAltitude

            else:
                if self.jsonGPSDataRead:
                    dateTimeJSON = datetime.strptime(\
                                        self.jsonGPSData['dateTime'],\
                                            '%Y-%m-%d %H:%M:%S.%f')
                    if self.checkElapsedTime(self.dateTimePMCSV,\
                                                dateTimeJSON,\
                                                    timedelta(minutes=10)):
                        self.GPSRecent = 1

                    self.GPSJSON   = 1  
                    self.latitudeAvg      = self.jsonGPSData['Latitude']
                    self.longitudeAvg     = self.jsonGPSData['Longitude']
                    self.altitudeAvg      = self.jsonGPSData['Altitude']
                else: 
                    self.gpsGit           = 1
                    self.latitudeAvg   = self.latitudeGit
                    self.longitudeAvg  = self.longitudeGit
                    self.altitudeAvg   = self.altitudeGit
                        
    def applyCorrections(self):

        self.pc0_1Cor, self.pc0_3Cor, self.pc0_5Cor, \
            self.pc1_0Cor, self.pc2_5Cor, self.pc5_0Cor,\
                self.pc10_0Cor \
                            =  self.pc0_1Avg, self.pc0_3Avg, self.pc0_5Avg,\
                                 self.pc1_0Avg, self.pc2_5Avg, self.pc5_0Avg, \
                                    self.pc10_0Avg        
            
        self.pm0_1Cor, self.pm0_3Cor, self.pm0_5Cor, \
            self.pm1_0Cor, self.pm2_5Cor, self.pm5_0Cor,\
                self.pm10_0Cor \
                            =  self.pm0_1Avg, self.pm0_3Avg, self.pm0_5Avg,\
                                self.pm1_0Avg, self.pm2_5Avg, self.pm5_0Avg, \
                                    self.pm10_0Avg 

        self.pm2_5ML =  self.pm2_5Cor

        self.setFogLikelyhood()
   
        if self.fogLikelyhood:
            print("Fog formation conditions are met") 
            self.humidityCorrectedPC()
            self.humidityCorrectedPM()
            self.humidityCorrectionApplied = 1

        if self.climateRecent:
            print("Applying ML")
            self.applyMLCorrections()


    def applyMLCorrections(self):
        try:
            foggy = float(self.temperatureAvg) - float(self.dewPointAvg)
            print("Foggyness:" + str(foggy))
            data = {'cor_pm2_5': [float(self.pm2_5ML)],\
                     'temperature': [float(self.temperatureAvg)],\
                       'pressure': [self.pressureAvg],\
                          'humidity':[self.humidityAvg], \
                            'dewPoint':[self.dewPointAvg],\
                                'temp_dew':[foggy]}
            dfInput = pd.DataFrame(data)
            print(dfInput)
            prediction = self.makePrediction(loadedPMModel, dfInput)
            self.pm2_5ML    =  prediction["Predictions"][0]
            self.mlPM2_5CorrectionApplied = 1

        except Exception as e:
            print("An error  occured")
            print(e)
            self.mlPM2_5     = self.pm2_5Cor
            traceback.print_exc()
            return 

    def makePrediction(self,modelName, est_df):
        prediction = pd.DataFrame(modelName.predict(est_df),columns=["Predictions"])
        return prediction   
    

    def setFogLikelyhood(self):

        self.fogLikelyhood = self.climateRecent and \
                                self.humidityAvg>40 and \
                                    self.temperatureAvg> -50 and \
                                        self.temperatureAvg - self.dewPointAvg < 2.5 


    def checkElapsedTime(self,dateTimeOne,dateTimeTwo,timeDeltaIn):
        time_difference = abs(dateTimeOne - dateTimeTwo)
        return time_difference <= timeDeltaIn

    def doCSV(self):
        print("DO CSV")
        sensorDictionary = OrderedDict([
            ("dateTime", self.dateTimePMStrCSV),
            ("nodeID", self.nodeID),
            ("pmSensor", self.pmSensor),       
            ("climateSensor", self.climateSensor),     
            ("gpsSensor", self.gpsSensor),                    
            ("Latitude", self.latitudeAvg),                
            ("Longitude", self.longitudeAvg),
            ("Altitude", self.altitudeAvg),    
            ("PC0_1", round(self.pc0_1Cor)),
            ("PC0_3", round(self.pc0_3Cor)),
            ("PC0_5", round(self.pc0_5Cor)),
            ("PC1",   round(self.pc1_0Cor)),
            ("PC2_5", round(self.pc2_5Cor)),
            ("PC5",   round(self.pc5_0Cor)),
            ("PC10",  round(self.pc10_0Cor)),
            ("PM0_1", self.pm0_1Cor),
            ("PM0_3", self.pm0_3Cor),
            ("PM0_5", self.pm0_5Cor),
            ("PM1",   self.pm1_0Cor),
            ("PM2_5", self.pm2_5Cor),
            ("PM5_0", self.pm5_0Cor),
            ("PM10",  self.pm10_0Cor),
            ("PM2_5ML", self.pm2_5Cor),                 
            ("Temperature", self.temperatureAvg),
            ("Pressure", self.pressureAvg),
            ("Humidity", self.humidityAvg),
            ("DewPoint", self.dewPointAvg),      
            ("PC0_1Raw", round(self.pc0_1Avg)),
            ("PC0_3Raw", round(self.pc0_3Avg)),
            ("PC0_5Raw", round(self.pc0_5Avg)),
            ("PC1_0Raw", round(self.pc1_0Avg)),
            ("PC2_5Raw", round(self.pc2_5Avg)),
            ("PC5_0Raw", round(self.pc5_0Avg)),
            ("PC10_0Raw",round(self.pc10_0Avg)),
            ("PM0_1Raw", self.pm0_1Avg),
            ("PM0_3Raw", self.pm0_3Avg),
            ("PM0_5Raw", self.pm0_5Avg),
            ("PM1Raw", self.pm1_0Avg),
            ("PM2_5Raw", self.pm2_5Avg),
            ("PM5_0Raw", self.pm5_0Avg),
            ("PM10Raw", self.pm10_0Avg),
            ("climateConcurrent", self.climateConcurrent), 
            ("climateFirmware", self.climateFirmware), 
            ("climateJSON", self.climateJSON), 
            ("climateDummy", self.climateDummy), 
            ("climateRecent", self.climateRecent), 
            ("fogLikelyhood", int(self.fogLikelyhood)),
            ("GPSConcurrent", self.GPSConcurrent), 
            ("GPSFirmware", self.GPSFirmware), 
            ("GPSJson", self.GPSJson), 
            ("GPSFromGit", self.GPSFromGit), 
            ("GPSRecent", self.GPSRecent), 
            ("humidityCorrectionApplied", self.humidityCorrectionApplied), 
            ("mlPM2_5CorrectionApplied", self.mlPM2_5CorrectionApplied), 
            ("nopGPS", len(self.dateTimeGPS)),
            ("nopPM", len(self.dateTimePM)),
            ("nopClimate", len(self.dateTimeClimate))              
        ])


        print()        
        print("===============MINTS===============")
        print(sensorDictionary)
        mP.writeCSV3( mP.getWritePathDateCSV(liveFolder,self.nodeID,\
            datetime.strptime(self.dateTimePMStrCSV,'%Y-%m-%d %H:%M:%S.%f'),\
                "calibrated"),sensorDictionary)
        print("CSV Written")
        # mL.writeMQTTLatestRepublish(sensorDictionary,"mintsCalibrated",self.nodeID)



    def humidityCorrectedPC(self):

            pc0_1  = float(self.pc0_1Avg)
            pc0_3  = float(self.pc0_3Avg)
            pc0_5  = float(self.pc0_5Avg)
            pc1_0  = float(self.pc1_0Avg)
            pc2_5  = float(self.pc2_5Avg)
            pc5_0  = float(self.pc5_0Avg)
            pc10_0 = float(self.pc10_0Avg)

            hum = float(self.humidityAvg)


            print('Condition is satisfied')
            data = {'count': [pc0_1, None, pc0_3, pc0_5, pc1_0, pc2_5, pc5_0, pc10_0, None],
                    'D_range': [50, 20, 200, 200, 500, 1500, 2500, 5000, None],
                    'D_point': [50, 80, 100, 300, 500, 1000, 2500, 5000, 10000]}
            df1 = pd.DataFrame(data)
            df1['N/D'] = df1['count']/df1['D_range']

            df1['height_ini'] = 0
            df1.loc[7, 'height_ini'] = (2*df1.loc[7, 'count'])/5000
            df1.loc[6, 'height_ini'] = (2*df1.loc[6, 'count'])/2500 - df1.loc[7, 'height_ini']
            df1.loc[5, 'height_ini'] = (2*df1.loc[5, 'count'])/1500 - df1.loc[6, 'height_ini']
            df1.loc[4, 'height_ini'] = (2*df1.loc[4, 'count'])/500 - df1.loc[5, 'height_ini']
            df1.loc[3, 'height_ini'] = (2*df1.loc[3, 'count'])/200 - df1.loc[4, 'height_ini']
            df1.loc[2, 'height_ini'] = (2*df1.loc[2, 'count'])/200 - df1.loc[3, 'height_ini']
            df1.loc[0, 'height_ini'] = (2*df1.loc[0, 'count'])/50 - df1.loc[2, 'height_ini']
            df1.loc[1, 'height_ini'] = (20*(df1.loc[0, 'height_ini']-df1.loc[2, 'height_ini'])/50) + df1.loc[2, 'height_ini']
            df1.loc[1, 'count'] = 0.5*(df1.loc[1, 'height_ini']+df1.loc[2, 'height_ini'])*20

            RH = (hum) * 0.7
            RH = 98 if RH >= 99 else RH
            k = 0.62
            df1['D_dry_point'] = df1['D_point']/((1 + k*(RH/(100-RH)))**(1/3))

            df1['D_dry_range'] = df1['D_dry_point'].diff().shift(-1)

            df1['fit_height_ini'] = 0

            df1.loc[7, 'fit_height_ini'] = (2*df1.loc[7, 'count'])/df1.loc[7, 'D_dry_range']
            df1.loc[6, 'fit_height_ini'] = (2*df1.loc[6, 'count'])/df1.loc[6, 'D_dry_range'] - df1.loc[7, 'fit_height_ini']
            df1.loc[5, 'fit_height_ini'] = (2*df1.loc[5, 'count'])/df1.loc[5, 'D_dry_range'] - df1.loc[6, 'fit_height_ini']
            df1.loc[4, 'fit_height_ini'] = (2*df1.loc[4, 'count'])/df1.loc[4, 'D_dry_range'] - df1.loc[5, 'fit_height_ini']
            df1.loc[3, 'fit_height_ini'] = (2*df1.loc[3, 'count'])/df1.loc[3, 'D_dry_range'] - df1.loc[4, 'fit_height_ini']
            df1.loc[2, 'fit_height_ini'] = (2*df1.loc[2, 'count'])/df1.loc[2, 'D_dry_range'] - df1.loc[3, 'fit_height_ini']
            df1.loc[1, 'fit_height_ini'] = (2*df1.loc[1, 'count'])/df1.loc[1, 'D_dry_range'] - df1.loc[2, 'fit_height_ini']

            df1['slope'] = (df1['fit_height_ini'].shift(-1) - df1['fit_height_ini']) / df1['D_dry_range']
            df1['interc'] = df1['fit_height_ini'] - df1['slope'] * df1['D_dry_point']

            df1['cor_height'] = None
            df1['cor_count'] = 0

            if df1.loc[8, 'D_dry_point'] > 5000:
                df1.loc[7, 'cor_height'] = df1.loc[7, 'slope']*5000 + df1.loc[7, 'interc']
                df1.loc[7, 'cor_count'] = 0.5*df1.loc[7, 'cor_height']*(df1.loc[8, 'D_dry_point']-5000)
            else:
                df1.loc[7, 'cor_height'] = 0
                df1.loc[7, 'cor_count'] = 0
            
            if (2500<df1.loc[7, 'D_dry_point']<=5000)&(df1.loc[8, 'D_dry_point']>5000):
                df1.loc[6, 'cor_height'] = df1.loc[6, 'slope']*2500 + df1.loc[6, 'interc']
                df1.loc[6, 'cor_count'] = (0.5*(df1.loc[7, 'cor_height']+df1.loc[7, 'fit_height_ini'])*(5000-df1.loc[7, 'D_dry_point'])) + (0.5*(df1.loc[6, 'cor_height']+df1.loc[7, 'fit_height_ini'])*(df1.loc[7, 'D_dry_point']-2500))
            elif (2500<df1.loc[7, 'D_dry_point']<5000)&(df1.loc[8, 'D_dry_point']<5000):
                df1.loc[6, 'cor_height'] = df1.loc[6, 'slope']*2500 + df1.loc[6, 'interc']
                df1.loc[6, 'cor_count'] = (0.5*(df1.loc[6, 'cor_height']+df1.loc[7, 'fit_height_ini'])*(df1.loc[7, 'D_dry_point']-2500)) + (0.5*df1.loc[7, 'fit_height_ini']*(df1.loc[8, 'D_dry_point']-df1.loc[7, 'D_dry_point']))
            elif (df1.loc[7, 'D_dry_point']<2500)&(df1.loc[8, 'D_dry_point']<5000):
                df1.loc[6, 'cor_height'] = df1.loc[7, 'slope']*2500 + df1.loc[7, 'interc']
                df1.loc[6, 'cor_count'] = (0.5*df1.loc[6, 'cor_height'])*(df1.loc[8, 'D_dry_point']-2500)
            else:
                df1.loc[6, 'cor_height'] = df1.loc[7, 'slope']*2500 + df1.loc[7, 'interc']
                df1.loc[6, 'cor_count'] = 0.5*(df1.loc[7, 'cor_height']+df1.loc[6, 'cor_height'])*2500
            
            if (1000<df1.loc[6, 'D_dry_point']<=2500)&(df1.loc[7, 'D_dry_point']>2500):
                df1.loc[5, 'cor_height'] = df1.loc[5, 'slope']*1000 + df1.loc[5, 'interc']
                df1.loc[5, 'cor_count'] = (0.5*(df1.loc[6, 'cor_height']+df1.loc[6, 'fit_height_ini'])*(2500-df1.loc[6, 'D_dry_point'])) + (0.5*(df1.loc[5, 'cor_height']+df1.loc[6, 'fit_height_ini'])*(df1.loc[6, 'D_dry_point']-1000))
            elif (1000<df1.loc[6, 'D_dry_point']<2500)&(df1.loc[7, 'D_dry_point']<2500):
                df1.loc[5, 'cor_height'] = df1.loc[5, 'slope']*1000 + df1.loc[5, 'interc']
                df1.loc[5, 'cor_count'] = (0.5*(df1.loc[5, 'cor_height']+df1.loc[6, 'fit_height_ini'])*(df1.loc[6, 'D_dry_point']-1000)) + (0.5*(df1.loc[6,'fit_height_ini']+df1.loc[7,'fit_height_ini'])*(df1.loc[7,'D_dry_point']-df1.loc[6,'D_dry_point'])) + (0.5*(df1.loc[7,'fit_height_ini']+df1.loc[6,'cor_height'])*(2500-df1.loc[7,'D_dry_point']))
            elif (df1.loc[6,'D_dry_point']<1000)&(df1.loc[7,'D_dry_point']<2500):
                df1.loc[5,'cor_height'] = df1.loc[6,'slope']*1000 + df1.loc[6,'interc']
                df1.loc[5,'cor_count'] = (0.5*(df1.loc[6,'cor_height']+df1.loc[7,'fit_height_ini'])*(2500-df1.loc[7,'D_dry_point'])) + (0.5*(df1.loc[5,'cor_height']+df1.loc[7,'fit_height_ini'])*(df1.loc[7,'D_dry_point']-1000))
            else:
                df1.loc[5,'cor_height'] = df1.loc[6,'slope']*1000 + df1.loc[6,'interc']
                df1.loc[5,'cor_count'] = 0.5*(df1.loc[6,'cor_height']+df1.loc[5,'cor_height'])*1500

            if (500<df1.loc[5,'D_dry_point']<=1000)&(df1.loc[6,'D_dry_point']>1000):
                df1.loc[4,'cor_height'] = df1.loc[4,'slope']*500 + df1.loc[4,'interc']
                df1.loc[4,'cor_count'] = (0.5*(df1.loc[5,'cor_height']+df1.loc[5,'fit_height_ini'])*(1000-df1.loc[5,'D_dry_point'])) + (0.5*(df1.loc[4,'cor_height']+df1.loc[5,'fit_height_ini'])*(df1.loc[5,'D_dry_point']-500))
            elif (500<df1.loc[5,'D_dry_point']<1000)&(df1.loc[6,'D_dry_point']<1000):
                df1.loc[4,'cor_height'] = df1.loc[4,'slope']*500 + df1.loc[4,'interc']
                df1.loc[4,'cor_count'] = (0.5*(df1.loc[4,'cor_height']+df1.loc[5,'fit_height_ini'])*(df1.loc[5,'D_dry_point']-500)) + (0.5*(df1.loc[5,'fit_height_ini']+df1.loc[6,'fit_height_ini'])*(df1.loc[6,'D_dry_point']-df1.loc[5,'D_dry_point'])) + (0.5*(df1.loc[6,'fit_height_ini']+df1.loc[5,'cor_height'])*(1000-df1.loc[6,'D_dry_point']))
            elif (df1.loc[5,'D_dry_point']<500)&(df1.loc[6,'D_dry_point']<1000):
                df1.loc[4,'cor_height'] = df1.loc[5,'slope']*500 + df1.loc[5,'interc']
                df1.loc[4,'cor_count'] = (0.5*(df1.loc[5,'cor_height']+df1.loc[6,'fit_height_ini'])*(1000-df1.loc[6,'D_dry_point'])) + (0.5*(df1.loc[4,'cor_height']+df1.loc[6,'fit_height_ini'])*(df1.loc[6,'D_dry_point']-500))
            else:
                df1.loc[4,'cor_height'] = df1.loc[5,'slope']*500 + df1.loc[5,'interc']
                df1.loc[4,'cor_count'] = 0.5*(df1.loc[5,'cor_height']+df1.loc[4,'cor_height'])*500

            if (300<df1.loc[4,'D_dry_point']<=500)&(df1.loc[5,'D_dry_point']>500):
                df1.loc[3,'cor_height'] = df1.loc[3,'slope']*300 + df1.loc[3,'interc']
                df1.loc[3,'cor_count'] = (0.5*(df1.loc[4,'cor_height']+df1.loc[4,'fit_height_ini'])*(500-df1.loc[4,'D_dry_point'])) + (0.5*(df1.loc[3,'cor_height']+df1.loc[4,'fit_height_ini'])*(df1.loc[4,'D_dry_point']-300))
            elif (300<df1.loc[4,'D_dry_point']<500)&(df1.loc[5,'D_dry_point']<500):
                df1.loc[3,'cor_height'] = df1.loc[3,'slope']*300 + df1.loc[3,'interc']
                df1.loc[3,'cor_count'] = (0.5*(df1.loc[3,'cor_height']+df1.loc[4,'fit_height_ini'])*(df1.loc[4,'D_dry_point']-300)) + (0.5*(df1.loc[4,'fit_height_ini']+df1.loc[5,'fit_height_ini'])*(df1.loc[5,'D_dry_point']-df1.loc[4,'D_dry_point'])) + (0.5*(df1.loc[5,'fit_height_ini']+df1.loc[4,'cor_height'])*(500-df1.loc[5,'D_dry_point']))
            elif (df1.loc[4,'D_dry_point']<300)&(df1.loc[5,'D_dry_point']<500):
                df1.loc[3,'cor_height'] = df1.loc[4,'slope']*300 + df1.loc[4,'interc']
                df1.loc[3,'cor_count'] = (0.5*(df1.loc[4,'cor_height']+df1.loc[5,'fit_height_ini'])*(500-df1.loc[5,'D_dry_point'])) + (0.5*(df1.loc[3,'cor_height']+df1.loc[5,'fit_height_ini'])*(df1.loc[5,'D_dry_point']-300))
            else:
                df1.loc[3,'cor_height'] = df1.loc[4,'slope']*300 + df1.loc[4,'interc']
                df1.loc[3,'cor_count'] = 0.5*(df1.loc[4,'cor_height']+df1.loc[3,'cor_height'])*200

            if (100<df1.loc[3,'D_dry_point']<=300)&(df1.loc[4,'D_dry_point']>300):
                df1.loc[2,'cor_height'] = df1.loc[2,'slope']*100 + df1.loc[2,'interc']
                df1.loc[2,'cor_count'] = (0.5*(df1.loc[3,'cor_height']+df1.loc[3,'fit_height_ini'])*(300-df1.loc[3,'D_dry_point'])) + (0.5*(df1.loc[2,'cor_height']+df1.loc[3,'fit_height_ini'])*(df1.loc[3,'D_dry_point']-100))
            elif (100<df1.loc[3,'D_dry_point']<300)&(df1.loc[4,'D_dry_point']<300):
                df1.loc[2,'cor_height'] = df1.loc[2,'slope']*100 + df1.loc[2,'interc']
                df1.loc[2,'cor_count'] = (0.5*(df1.loc[2,'cor_height']+df1.loc[3,'fit_height_ini'])*(df1.loc[3,'D_dry_point']-100)) + (0.5*(df1.loc[3,'fit_height_ini']+df1.loc[4,'fit_height_ini'])*(df1.loc[4,'D_dry_point']-df1.loc[3,'D_dry_point'])) + (0.5*(df1.loc[4,'fit_height_ini']+df1.loc[3,'cor_height'])*(300-df1.loc[4,'D_dry_point']))
            elif (df1.loc[3,'D_dry_point']<100)&(df1.loc[4,'D_dry_point']<300):
                df1.loc[2,'cor_height'] = df1.loc[3,'slope']*100 + df1.loc[3,'interc']
                df1.loc[2,'cor_count'] = (0.5*(df1.loc[3,'cor_height']+df1.loc[4,'fit_height_ini'])*(300-df1.loc[4,'D_dry_point'])) + (0.5*(df1.loc[2,'cor_height']+df1.loc[4,'fit_height_ini'])*(df1.loc[4,'D_dry_point']-100))
            else:
                df1.loc[2,'cor_height'] = df1.loc[3,'slope']*100 + df1.loc[3,'interc']
                df1.loc[2,'cor_count'] = 0.5*(df1.loc[3,'cor_height']+df1.loc[2,'cor_height'])*200

            if (50<df1.loc[2,'D_dry_point']<=100)&(df1.loc[3,'D_dry_point']>100):
                df1.loc[0,'cor_height'] = df1.loc[1,'slope']*50 + df1.loc[1,'interc']
                df1.loc[0,'cor_count'] = (0.5*(df1.loc[2,'cor_height']+df1.loc[2,'fit_height_ini'])*(100-df1.loc[2,'D_dry_point'])) + (0.5*(df1.loc[0,'cor_height']+df1.loc[2,'fit_height_ini'])*(df1.loc[2,'D_dry_point']-50))
            elif (50<df1.loc[2,'D_dry_point']<100)&(df1.loc[3,'D_dry_point']>100):
                df1.loc[0,'cor_height'] = df1.loc[1,'slope']*50 + df1.loc[1,'interc']
                df1.loc[0,'cor_count'] = (0.5*(df1.loc[0,'cor_height']+df1.loc[2,'fit_height_ini'])*(df1.loc[2,'D_dry_point']-50)) + (0.5*(df1.loc[2,'fit_height_ini']+df1.loc[3,'fit_height_ini'])*(df1.loc[3,'D_dry_point']-df1.loc[2,'D_dry_point'])) + (0.5*(df1.loc[3,'fit_height_ini']+df1.loc[2,'cor_height'])*(100-df1.loc[3,'D_dry_point']))
            elif (df1.loc[2,'D_dry_point']<50)&(df1.loc[3,'D_dry_point']>100):
                df1.loc[0,'cor_height'] = df1.loc[2,'slope']*50 + df1.loc[2,'interc']
                df1.loc[0,'cor_count'] = (0.5*(df1.loc[2,'cor_height']+df1.loc[3,'fit_height_ini'])*(100-df1.loc[3,'D_dry_point'])) + (0.5*(df1.loc[0,'cor_height']+df1.loc[3,'fit_height_ini'])*(df1.loc[3,'D_dry_point']-50))
            else:
                df1.loc[0,'cor_height'] = df1.loc[2,'slope']*50 + df1.loc[2,'interc']
                df1.loc[0,'cor_count'] = 0.5*(df1.loc[2,'cor_height']+df1.loc[0,'cor_height'])*50
                
            
            self.pc0_1Cor, self.pc0_3Cor, self.pc0_5Cor, self.pc1_0Cor, self.pc2_5Cor, self.pc5_0Cor, self.pc10_0Cor = \
                df1.loc[0,'cor_count'], df1.loc[2,'cor_count'], df1.loc[3,'cor_count'], df1.loc[4,'cor_count'], df1.loc[5,'cor_count'], df1.loc[6,'cor_count'], df1.loc[7,'cor_count']
            

            
    def humidityCorrectedPM(self):

        m0_1 = 8.355696123812269e-07
        m0_3 = 2.2560825222215327e-05
        m0_5 = 0.00010446111749483851
        m1_0 = 0.0008397941861044865
        m2_5 = 0.013925696906339288
        m5_0 = 0.12597702778750686
        m10_0 = 1.0472

        self.pm0_1Cor   = m0_1*self.pc0_1Cor
        self.pm0_3Cor   = self.pm0_1Cor + m0_3*self.pc0_3Cor
        self.pm0_5Cor   = self.pm0_3Cor + m0_5*self.pc0_5Cor
        self.pm1_0Cor   = self.pm0_5Cor + m1_0*self.pc1_0Cor
        self.pm2_5Cor   = self.pm1_0Cor + m2_5*self.pc2_5Cor
        self.pm5_0Cor   = self.pm2_5Cor + m5_0*self.pc5_0Cor
        self.pm10_0Cor  = self.pm5_0Cor + m10_0*self.pc10_0Cor

        self.pm2_5ML =  self.pm2_5Cor
        
        print("Humidity Corrected PM")





