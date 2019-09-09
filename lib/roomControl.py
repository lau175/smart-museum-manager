# Author: Giuseppe Di Giacomo s263765
# Academic year: 2018/19

import json
import time
import requests
from lib.MyMQTT import MyMQTT

class RoomControl(object):
    """Room parameter control algorithm: this algorithm acts as an MQTT subscriber to receive information about temperature
    and humidity from a proper sensor and about detection of people from the proximity ones. Information received about
    temperature and humidity is used to control if a certain threshold (upper or lower bound with the aim of maintaining
    the temperature at a comfortable level  value contained in the Room Catalogue) is exceeded. If it happens, the
    algorithm acts as an MQTT publisher to control the relay able to switch on and off the cooling system and to send a
    notification to the museum staff. Using information about people detection, the algorithm counts for how much time
    the room remains empty and, if this time exceeds a certain threshold (also this one contained in the room catalogue),
    it works as an MQTT publisher to switch off the lighting system and to send a notification to the museum staff.
    On the other side, the algorithm switches on the lights again if a new detection occurs after that the lights have
    been switched off (in this case it works again an MQTT publisher to control the proper relay)."""

    def __init__(self, clientID, IP_broker, port_broker, IP_catalogue, port_catalogue):
    
        self.clientID = clientID
        self.myMqttClient = MyMQTT(self.clientID, IP_broker, port_broker, self)
        self.IP_catalogue = IP_catalogue
        self.port_catalogue = port_catalogue
        self.minTemperature = self.getMinTemperatureThreshold()
        self.maxTemperature = self.getMaxTemperatureThreshold()
        self.maxHumidity = self.getMaxHumidityThreshold()
        self.timeOut = self.getTimeOut()
        self.present_people = 0
        self.timeEmpty = time.time()
        self.status = False
        self.lightStatus = 0
        self.coolStatus = 0

    def run(self):
        
        print("running %s" % self.clientID)
        self.myMqttClient.start()

    def end(self):
        
        print("ending %s" % self.clientID)
        self.myMqttClient.stop()

    def notify(self, topic, msg):
       
        print("roomControl received '%s' under topic '%s'" % (msg, topic))

        if topic == "trigger/th":
            #update of thresholds contained in the room catalog
            
            # if json_mex["msg"] == "timeout":
                self.timeOut = self.getTimeOut()
            # if json_mex["msg"] == "max_temp":
                self.maxTemperature = self.getMaxTemperatureThreshold()
            # if json_mex["msg"] == "min_temp":
                self.minTemperature = self.getMinTemperatureThreshold()
                self.maxHumidity = self.getMaxHumidityThreshold()
                self.controlHeating()

        if topic == "measure/temperature":
            
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            value = json_mex["msg"]
            # the received value of temperature is saved
            self.currentTemperature = value
            # check of cooling system: basing on the current temperature it is turned on or off
            self.controlHeating()

        if topic == "measure/heat_stat":
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            value = json_mex["msg"]
            # the received value of the cooling system status is saved
            self.coolStatus = int(value)

        if topic == "measure/humidity":
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            value = json_mex["msg"]
            # the received value of humidity is saved
            self.currentHumidity = int(value)
            # check of cooling system: basing on the current temperature it is turned on or off
            self.controlHeating()

        if topic == "measure/light_stat":
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            value = json_mex["msg"]
            # the received value of the light status is saved
            self.lightStatus = int(value)

        if topic == "measure/people/detection":
            
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            
            if json_mex["msg"] == "in": # a person entered in the room
                self.addPerson()
            if json_mex["msg"] == "out": # a person leaved the room
                self.removePerson()

    def setWorking(self, state):
        """method to set the status of the museum, thta can be closed or open"""
        
        self.status = state

    def getMaxTemperatureThreshold(self):
        """through requests library the function gets and returns the maximum temperature allowed in the museum"""
        try:
            threshold_URL = "http://" + self.IP_catalogue + ":" + self.port_catalogue + "/th"
            r = requests.get(threshold_URL)
            print("Maximum temperature allowed obtained from Room Catalog")
            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["threshold"]
            maxTemperature= threshold["max_temperature_th"]

        except requests.exceptions.RequestException as e:
            print e
            # if connection to the catalog fails, the max temperature allowed is set to a default value 
            maxTemperature = 25

        return int(maxTemperature)

    def getMaxHumidityThreshold(self):
        """through requests library the function gets and returns the maximum humidity allowed in the museum"""
        try:
            threshold_URL = "http://" + self.IP_catalogue + ":" + self.port_catalogue + "/th"
            r = requests.get(threshold_URL)
            print("Minimum humidity allowed obtained from Room Catalog")
            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["threshold"]
            humidity = threshold["humidity_th"]
            
        # if connection to the catalog fails, the max humidity allowed is set to a default value 
        except requests.exceptions.RequestException as e:
            print e
            humidity = 50

        return int(humidity)

    def getMinTemperatureThreshold(self):
        """through requests library the function gets and returns the minimum temperature allowed in the museum"""
        
        try:
            threshold_URL = "http://" + self.IP_catalogue + ":" + self.port_catalogue + "/th"
            r = requests.get(threshold_URL)
            print("Minimum temperature allowed obtained from Room Catalog")

            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["threshold"]
            minTemperature = threshold["min_temperature_th"]

        except requests.exceptions.RequestException as e:
            print e
            # if connection to the catalog fails, the minimum humidity allowed is set to a default value 

            minTemperature = 15

        return int(minTemperature)

    def getTimeOut(self):
        """through requests library the function gets and returns the light timeout"""
        
        try:
            threshold_URL = "http://" + self.IP_catalogue + ":" + self.port_catalogue + "/th"
            r = requests.get(threshold_URL)
            print("Light timeout obtained from Room Catalog")
            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["threshold"]
            timeOut = threshold["light_timer"]

        except requests.exceptions.RequestException as e:
            print e
            # if connection to the catalog fails, the light timeout is set to a default value 
            timeOut = 60

        return int(timeOut)

    def expiredTimeOut(self):
        """method that returns true if the time past from the moment in which the room becomes empty exceeds the timeout,
         false otherwise"""
         
        if self.present_people == 0 and self.getLightStatus() == 1:
            if (time.time() - self.timeEmpty) > int(self.timeOut):
                return True
        else:
            return False

    def setLightStatus(self, value):
        """method to set the status of the lights: if 1 they are on, 0 if they are off"""
        
        self.lightStatus = int(value)

    def addPerson(self):
        """method that adds a person and turns on the lights if they are off"""
    
        if self.lightStatus == 0:
            self.lightStatus = 1
            self.myMqttClient.myPublish("trigger/light", '{"msg" : "void"}')
        self.present_people = self.present_people + 1

    def removePerson(self):
        """method that removes a person and if thre is no people inside the room the current time is saved"""
        if self.present_people > 0:
            self.present_people = self.present_people - 1
        elif self.present_people < 0:
            self.present_people = 0
        if self.present_people == 0:
            self.timeEmpty = time.time()

    # def turnOffHeating(self):
    #
    #     diff = self.maxTemperature - self.minTemperature
    #     mean = (self.maxTemperature + self.minTemperature)/2
    #     lowerBound = mean - diff/2
    #     upperBound = mean + diff/2
    #     if lowerBound < self.currentTemperature() < upperBound:
    #         return True
    #     else:
    #         return False

    def isTemperatureValid(self):
        """method that checks if current temperature is valid: if it is, the method returns True, False otherwise"""
        if int(self.minTemperature) < self.currentTemperature < int(self.maxTemperature):
            return True
        else:
            return False

    def isHumidityValid(self):
        """method that checks if current humidity is valid: if it is, the method returns True, False otherwise"""
        if self.currentHumidity < self.maxHumidity:
            return True
        else:
            return False

    def complementCooling(self):
        """method that turns on the cooling system if the actual temperature is above the max allowed one and if the cooling system is off;
           moreover it turns off the cooling system if the actual temperature is below the max allowed one and if the cooling system is on. 
           It returns true each time the cooling system status changes."""
        
        if self.currentTemperature >= int(self.maxTemperature) and self.coolStatus == 0:
            self.coolStatus = 1
            return True
        elif self.currentTemperature < int(self.maxTemperature) and self.coolStatus == 1:
            self.coolStatus = 0
            return True
        else:
            return False


    def controlHeating(self):
        """method that, basing on the current temperature or humidity, sends alerts or complement tha status of the cooling system"""
        if self.status:
            if not(self.isTemperatureValid()):
                self.myMqttClient.myPublish("alert/temperature", '{"msg" : %d}'% self.currentTemperature)

            if self.complementCooling():
                self.myMqttClient.myPublish("trigger/heat", '{"msg" : "void"}')

            if not(self.isHumidityValid()):
                self.myMqttClient.myPublish("alert/humidity", '{"msg" : %d}'% self.currentHumidity)

    def getLightStatus(self):
        """method that returns the status of the light"""
        
        return int(self.lightStatus)

    def getCurrentTemperature(self):
        """method that returns the current temperature"""
        
        return  int(self.currentTemperature)