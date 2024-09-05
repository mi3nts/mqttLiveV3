# mqttLiveV3
Contains firmware for mints live sharedair updates with humidity and ML corrections


The Resulting .csv should have the following 
```
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
```
