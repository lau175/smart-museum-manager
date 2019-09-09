# Author: Giuseppe Di Giacomo s263765
# Academic year: 2018/19

from lib.timeControl import TimeControl
from lib.peopleControl import PeopleControl
from lib.roomControl import RoomControl
import time
import requests
import json

# IP of room catalog
catalog_IP = '172.20.10.11'
# port of room catalog
catalog_port = '9090'
# URL of catalog 
broker_url = "http://" + catalog_IP + ":" + catalog_port + "/broker"
# the broker IP and port are requested to the room catalog
r = requests.get(broker_url)
print("Broker IP and port obtained from Room Catalog")
obj = json.loads(r.text)
broker_IP = obj["broker"]
broker_port = obj["port"]

# URL to get the interacquisition time: in the room catalog it is in minutes, so it must be multiplied by 60
interacquistion_url = "http://" + catalog_IP + ":" + catalog_port + "/interacquisition"
# request of the interacquisition value
print("Interacquisition time obtained from Room Catalog")
r = requests.get(interacquistion_url )
obj = json.loads(r.text)
interacquistion = obj["interacquisition"] * 60

# Time controller: initialization, start and subscription to the proper topics
time_controller = TimeControl("Time controller", broker_IP, broker_port, catalog_IP, catalog_port)
time_controller.run()
time_controller.myMqttClient.mySubscribe("measure/heat_stat")

# People controller: initialization, start and subscription to the proper topics
people_controller = PeopleControl("People controller", broker_IP, broker_port, catalog_IP, catalog_port)
people_controller.run()
people_controller.myMqttClient.mySubscribe("trigger/th")
people_controller.myMqttClient.mySubscribe("measure/people/detection")
people_controller.myMqttClient.mySubscribe("system")

# Room controller: initialization, start and subscription to the proper topics
room_controller = RoomControl("Room controller", broker_IP, broker_port, catalog_IP, catalog_port)
room_controller.run()
room_controller.myMqttClient.mySubscribe("trigger/th")
room_controller.myMqttClient.mySubscribe("measure/light_stat")
room_controller.myMqttClient.mySubscribe("measure/temperature")
room_controller.myMqttClient.mySubscribe("measure/humidity")
room_controller.myMqttClient.mySubscribe("measure/people/detection")
room_controller.myMqttClient.mySubscribe("measure/heat_stat")
tmp = 0

# room and people controllers status is set to 1(working) if the the musuem is open
if time_controller.isOpened():
    room_controller.setWorking(True)
    people_controller.setWorking(True)

# loop 
while 1:
    
    # the loop does nothing until synch is set to 0 and start working only if it becomes 1
    if people_controller.synch == 1:
        
        # check if the museum switches from closed to open: if true it sends a MQTT message to turn on the ligth and the heating system if they are off
        if time_controller.checkOpening():

            if time_controller.heatStatus == 0:
                time_controller.myMqttClient.myPublish("trigger/heat", '{"msg" : "void"}')
            room_controller.setWorking(True)
            people_controller.setWorking(True)

        # check if the museum switches from open to closed: if true it sends a MQTT message to turn off the ligth and the heating system if they are on
        elif time_controller.checkClosing():
            if time_controller.heatStatus == 1:
                time_controller.myMqttClient.myPublish("trigger/heat", '{"msg" : "void"}')
            room_controller.setWorking(False)
            people_controller.setWorking(False)

        
        if time_controller.isOpened():
            
            
            if room_controller.expiredTimeOut():
                room_controller.setLightStatus(0)
                room_controller.myMqttClient.myPublish("alert/light_down", '{"msg" : "void"}')
                time_controller.myMqttClient.myPublish("trigger/light", '{"msg" : "void"}')

            people_controller.updateArray()

            if tmp % interacquistion == interacquistion-1:

                people_controller.myMqttClient.myPublish("measure/people", '{"msg": %d}' % round(people_controller.getMeanPeople()))
                people_controller.clearArray()


        tmp += 1

    time.sleep(1)

time_controller.end()