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

liveSpanSec            = mD.mintsDefinitions['liveSpanSec']
liveFolder             = mD.liveFolder


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
        self.humidityValidity           = [] # Checks if humidity readings are in range 
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
        self.dateTimeCSV = datetime.fromtimestamp(mP.getStateV2(self.dateTimePM[-1].timestamp())*liveSpanSec)
        self.dateTimeStrCSV = str(self.dateTimeCSV.year).zfill(4)+ \
                "-" + str(self.dateTimeCSV.month).zfill(2) + \
                "-" + str(self.dateTimeCSV.day).zfill(2) + \
                " " + str(self.dateTimeCSV.hour).zfill(2) + \
                ":" + str(self.dateTimeCSV.minute).zfill(2) + \
                ":" + str(self.dateTimeCSV.second).zfill(2) + '.000'
        # print(self.dateTimeStrCSV)    
        return ;

    def getPMValidity(self):
        # print("Getting PM Validity")     
        # print(self.pm0_1)
        # # print("validated")
        return len(self.pm0_1)>=1;


    def getAltitudeFromGeopy(latitude, longitude):
        geolocator = Nominatim(user_agent="altitude_finder")
        location = geolocator.reverse((latitude, longitude), language="en")

        if location and "altitude" in location.raw:
            altitude = location.raw["altitude"]
            return altitude
        else:
            return None


    def changeStateV2(self):
        # print("Change State V2")
        if self.getPMValidity():
            # print("Is Valid")
            self.getTimeV2()
            self.getAverageAll()
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
            
            self.latestClimateAvgDateTime = self.dateTimeCSV
            self.latestTemperature        = self.temperatureAvg
            self.latestPressure           = self.pressureAvg
            self.latestHumidity           = self.humidityAvg
            self.latestDewPoint           = self.dewPointAvg
            
            climateDictionary = OrderedDict([
                ("dateTime"         ,self.dateTimeStrCSV),
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

            
        else:   
            if self.checkElapsedTime(self.dateTimeCSV,\
                                     self.latestClimateAvgDateTime,\
                                        timedelta(minutes=10)):
                self.climateFirmware = 1
                self.climateRecent   = 1
                self.temperatureAvg  = self.latestTemperature
                self.pressureAvg     = self.latestPressure
                self.humidityAvg     = self.latestHumidity
                self.dewPointAvg     = self.latestDewPoint        

            elif self.checkElapsedTime( self.dateTimeCSV,\
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
                    if self.checkElapsedTime(dateTimeJSON,\
                        self.dateTimeCSV,\
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

            self.latestGPSAvgDateTime     = self.dateTimeCSV
            self.latestLatitude           = self.latitudeAvg
            self.latestLongitude          = self.longitudeAvg
            self.latestAltitude           = self.altitudeAvg

            gpsDictionary = OrderedDict([
                ("dateTime"         ,self.dateTimeStrCSV),
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

        else:
            if self.checkElapsedTime(self.dateTimeCSV,\
                                     self.latestGPSAvgDateTime,\
                                        timedelta(minutes=10)):
                self.latitudeAvg   = self.latestLatitude
                self.longitudeAvg  = self.latestLongitude
                self.altitudeAvg   = self.latestAltitude
                self.gpsRecent     = 1
                self.gpsFirmware   = 1

            elif self.checkElapsedTime( self.dateTimeCSV,\
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
                    if self.checkElapsedTime(dateTimeJSON,\
                        self.dateTimeCSV,\
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
                        

                

    def checkElapsedTime(self,dateTimeOne,dateTimeTwo,timeDeltaIn):
        time_difference = abs(dateTimeOne - dateTimeTwo)
        return time_difference <= timeDeltaIn

    def doCSV(self):
        sensorDictionary = OrderedDict([
            ("dateTime", self.dateTimeStrCSV),
            ("nodeID", self.nodeID),
            ("pmSensor", self.pmSensor),       
            ("climateSensor", self.climateSensor),     
            ("gpsSensor", self.gpsSensor),                    
            ("Latitude", self.latitudeAvg),                
            ("Longitude", self.longitudeAvg),
            ("Altitude", self.altitudeAvg),    
            ("PC0_1", self.pc0_1Avg),
            ("PC0_3", self.pc0_3Avg),
            ("PC0_5", self.pc0_5Avg),
            ("PC1", self.pc1_0Avg),
            ("PC2_5", self.pc2_5Avg),
            ("PC5", self.pc5_0Avg),
            ("PC10", self.pc10_0Avg),
            ("PM0_1", self.pm0_1Avg),
            ("PM0_3", self.pm0_3Avg),
            ("PM0_5", self.pm0_5Avg),
            ("PM1", self.pm1_0Avg),
            ("PM2_5", self.pm2_5Avg),
            ("PM5_0", self.pm5_0Avg),
            ("PM10", self.pm10_0Avg),
            ("Temperature", self.temperatureAvg),
            ("Pressure", self.pressureAvg),
            ("Humidity", self.humidityAvg),
            ("DewPoint", self.dewPointAvg),      
            ("PC0_1Raw", self.pc0_1Avg),
            ("PC0_3Raw", self.pc0_3Avg),
            ("PC0_5Raw", self.pc0_5Avg),
            ("PC1_0Raw", self.pc1_0Avg),
            ("PC2_5Raw", self.pc2_5Avg),
            ("PC5_0Raw", self.pc5_0Avg),
            ("PC10_0Raw", self.pc10_0Avg),
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
            ("fogLikelyhood", self.fogLikelyhood),
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
            datetime.strptime(self.dateTimeStrCSV,'%Y-%m-%d %H:%M:%S.%f'),\
                "calibrated"),sensorDictionary)
        print("CSV Written")
        # mL.writeMQTTLatestRepublish(sensorDictionary,"mintsCalibrated",self.nodeID)







