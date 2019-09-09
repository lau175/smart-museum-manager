# Author: Giuseppe Di Giacomo s263765
# Academic year: 2018/19

import requests
import json
import numpy as np
from lib.MyMQTT import MyMQTT
# todo check system topic

class PeopleControl(object):
    """People threshold control algorithm: this algorithm acts as an MQTT subscriber to receive information about people
    detection (entering or leaving the room) from proximity sensors. The algorithm counts the number of people present
    in the room with information coming from proximity sensors and, if the threshold value (meant as maximum number of
    people allowed to stay in the monitored room and contained in the room catalogue) is reached, acts as an MQTT
    publisher to send a message to museum staff in charge of room control to stop allowing people to enter the room
    until the number of people inside is below the given threshold again. It also acts as an MQTT subscriber to verify
    if the threshold value has been changed or not.
    """

    def __init__(self, clientID, IP_broker, port_broker, IP_catalogue, port_catalogue):
    
        self.clientID = clientID
        self.myMqttClient = MyMQTT(self.clientID, IP_broker, port_broker, self)
        self.IP_catalogue = IP_catalogue
        self.port_catalogue = port_catalogue
        # threshold of maximum number of people allowed in the room
        self.people_threshold = int(self.getThreshold())
        # counter of present peoplein the room
        self.present_people = 0
        # status of th e museum: True if open, False if closed
        self.status = False
        self.synch = 0
        # array that each second it is updated with the value of present people: at the end of every minute, the mean of present 
        # people is computed and than the array is cleared
        self.array = []

    def run(self):
       
        print("running %s" % self.clientID)
        self.myMqttClient.start()

    def end(self):
 
        print("ending %s" % self.clientID)
        self.myMqttClient.stop()

    def notify(self, topic, msg):
        
        print("people controller received '%s' under topic '%s'" % (msg, topic))

        if topic == 'system':
            msg = str.replace(msg, "'", '"')
            if msg == "void":
                self.synch = 1

        if topic == "measure/people/detection":
            msg = str.replace(msg, "'", '"')
            try:
                json_mex = json.loads(msg)
            except:
                print "error json format"

            if json_mex["msg"] == "in":
                self.addPerson()

            if json_mex["msg"] == "out":
                self.removePerson()

        if topic == "trigger/th":
            self.people_threshold = int(self.getThreshold())
            if self.exceededThreshold():
                self.myMqttClient.myPublish("alert/people", '{"msg" : %d}' % self.present_people)

    def setWorking(self, state):
        """method to set the status of the museum, thta can be closed or open"""
       
        self.status = state

    def getThreshold(self):
        """method to get the threshold of maximum eople allowed"""
        
        try:
            threshold_URL = "http://" + self.IP_catalogue + ":" + self.port_catalogue + "/th"
            r = requests.get(threshold_URL)
            print("Maximum number of people allowed obtained from Room Catalog")
            threshold = r.text

            obj = json.loads(threshold)
            threshold = obj["threshold"]
            th_people = threshold["people_th"]
            
        # if connection to the catalog fails, the threshold is set to a default value 
        except requests.exceptions.RequestException as e: 
            print e
            th_people = 50
        return th_people

    def addPerson(self):
        """method to add a person and check if the number of present people exceeds the threshold of the maximum number allowed: in this case
        an MQTT alert message is published """
       
        self.present_people = self.present_people + 1
        print self.present_people
        if self.exceededThreshold():
            self.myMqttClient.myPublish("alert/people", '{"msg" : %d}'%self.present_people)

    def removePerson(self):
        """a person is removed: the counter of present people decreases by one
        it is check if the number of present people is greater than 0 just to avoid that the counter goes below 
        zero due to an error of the proximity sensor """
        
        if self.present_people > 0:
            self.present_people = self.present_people - 1
        elif self.present_people < 0:
            self.present_people = 0

        # if self.personAllowed():
        #     self.myMqttClient.myPublish("measure/people", '{"msg" : %d}'%self.present_people)

    def exceededThreshold(self):
        """method that returns true if the threshold of maximum people allowed has been exceeded """
        
        if self.present_people >= self.people_threshold:
            return True

    def personAllowed(self):
        """method that returns true if present people are below the threshold """
        
        if self.people_threshold != -1:
            if self.present_people < self.people_threshold:
                return True

    def getNumberPeople(self):
        """method that returns the number of present people"""
        
        return self.present_people

    def updateArray(self):
        """method to append to the array the number of present people; it is invoked each second """

        self.array.append(self.present_people)

    def clearArray(self):
        """method to clear the array the number of present people; it is invoked each minute """

        self.array = []

    def getMeanPeople(self):
        """method to get the mean of the array the number of present people; it is invoked each minute """
        
        return np.mean(self.array)