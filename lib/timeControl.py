# Author: Giuseppe Di Giacomo s263765
# Academic year: 2018/19

import json
import datetime
import calendar
import requests
from lib.MyMQTT import MyMQTT


class TimeControl(object):
    """Control strategy that makes heating and lighting system depending on museum timetable.
    It works as an MQTT publisher to switch on and off the cooling system according to the timing information coming via
    REST web services from the room catalogue.
    """

    def __init__(self, clientID, IP_broker, port_broker, IP_catalogue, port_catalogue):
        
        self.clientID = clientID
        self.myMqttClient = MyMQTT(self.clientID, IP_broker, port_broker, self)
        self.IP_catalogue = IP_catalogue
        self.port_catalogue = port_catalogue
        self.getTimeTables()
        self.checkStatus()
        self.heatStatus = 0
        self.lightStatus = 0

    def run(self):
    
        print("running %s" % self.clientID)
        self.myMqttClient.start()

    def end(self):
        
        print("ending %s" % self.clientID)
        self.myMqttClient.stop()

    def notify(self, topic, msg):

        # print("%s received '%s' under topic '%s'" % (self.clientID, msg, topic))

        if topic == "measure/heat_stat":
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            value = json_mex["msg"]
            self.heatStatus = int(value)
            
        if topic == "measure/light_stat":
            msg = str.replace(msg, "'", '"')
            json_mex = json.loads(msg)
            value = json_mex["msg"]
            self.lightStatus = int(value)

    def getTimeTables(self):
        """through requests library the function gets the opening and closing time of the museum"""
        
        try:
            timetable_URL = "http://" + self.IP_catalogue + ":" + self.port_catalogue + "/timetable"
            r = requests.get(timetable_URL)
            print("Museum timetable obtained from Room Catalog by " + self.clientID)
            timetable_txt = r.text

            obj = json.loads(timetable_txt)
            timetable_txt = obj["timetable"]

            self.openingTable = timetable_txt["opening_time"]
            self.closingTable = timetable_txt ["closing_time"]

        except requests.exceptions.RequestException as e:
            print e
            # if the request fails, the time table is built as follow
            opening = '{"opening_time": {"monday" : "00:00","tuesday" : "00:00","wednesday" : "00:00","thursday" : "00:00","friday" : "00:00","saturday" : "00:00","sunday" : "00:00"}}'
            obj = json.loads(opening)
            self.openingTable = obj["opening_time"]
            closing = '{"closing_time": {"monday" : "23:59","tuesday" : "23:59","wednesday" : "23:59","thursday" : "23:59","friday" : "23:59","saturday" : "23:59","sunday" : "23:59"}}'
            obj = json.loads(closing)
            self.closingTable = obj["closing_time"]

    def checkStatus(self):
        """"check the initial state of the museum, setting 'self.opened' properly"""
        
        # get current time
        currentWeekDay, currentHour, currentMinute = self.getCurrentTime()

        # get opening time
        openingHour, openingMinute = self.getOpeningTime(currentWeekDay)

        # get closing time
        closingHour, closingMinute = self.getClosingTime(currentWeekDay)
        self.opened = False
        
        if openingHour < currentHour < closingHour:
            self.opened = True

        elif currentHour == openingHour and currentHour < closingHour:
            if currentMinute >= openingMinute:
                self.opened = True

        elif currentHour > openingHour and currentHour == closingHour:
            if currentMinute < closingMinute:
                self.opened = True

        elif currentHour == openingHour and currentHour == closingHour:
            if openingMinute <= currentMinute < closingMinute:
                self.opened = True

    def getCurrentTime(self):
        """get the current time"""
        
        currentDate = datetime.datetime.now()
        currentWeekDay = currentDate.weekday()
        currentHour = currentDate.hour
        currentMinute = currentDate.minute
        return currentWeekDay, currentHour, currentMinute

    def getOpeningTime(self, currentWeekDay):
        """given the current day as parameter, the function returns the opening hour and minute of the current day"""
        
        weekDays = list(calendar.day_name)
        weekDays_low = [k.lower() for k in weekDays]
        openingHour = self.openingTable[weekDays_low[currentWeekDay]]
        openingHour, openingMinute = openingHour.split(':')
        openingHour = int(openingHour)
        openingMinute = int(openingMinute)
        return openingHour, openingMinute

    def getClosingTime(self, currentWeekDay):
        """given the current day as parameter, the function returns the closing hour and minute of the current day"""
        
        weekDays = list(calendar.day_name)
        weekDays_low = [k.lower() for k in weekDays]
        closingHour = self.closingTable[weekDays_low[currentWeekDay]]
        closingHour, closingMinute = closingHour.split(':')
        closingHour = int(closingHour)
        closingMinute = int(closingMinute)
        return closingHour, closingMinute

    def checkOpening(self):
        """returns true if museum switches from closed to opened"""

        if self.opened == False:

            # get current time
            currentWeekDay, currentHour, currentMinute = self.getCurrentTime()

            # get opening time
            openingHour, openingMinute = self.getOpeningTime(currentWeekDay)

            if currentHour == openingHour:
                if currentMinute == openingMinute:
                    self.opened = True
                    return True

        return False

    def checkClosing(self):
        """returns true if museum switches from opened to closed"""

        if self.opened == True:

            # get current time
            currentWeekDay, currentHour, currentMinute = self.getCurrentTime()

            # get closing time
            closingHour, closingMinute = self.getClosingTime(currentWeekDay)

            if currentHour == closingHour:
                if currentMinute == closingMinute:
                    self.opened = False
                    return True
        return False

    def isOpened(self):
        """return true if museum is opened, false otherwise"""

        return self.opened