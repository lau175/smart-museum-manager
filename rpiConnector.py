#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Author: Pietro Rando Mazzarino (s266498)
Academic year: 2018/19
"""

import Adafruit_DHT
import threading
import time
import paho.mqtt.client as mqtt
import json
import requests as req
import random

#Constants
SENSOR	= Adafruit_DHT.DHT11
PIN	   = 17
BROKER	= "localhost"
PORT	  = 1883
CLIENT_ID = "mainboard"
TS_DATA_UPDATE = "https://api.thingspeak.com/update?api_key=4M2QY10TRMJLXUX8"
BOARD_ID = 1
BOARD = "rpi"
SENSOR1 = "temperature"
SENSOR2 = "humidity"

def mqttJsonLoad(payload):
	"""
	function that parse the json mqtt message 
	
	Parameters
	------------
		payload : string
			payload of mqtt message

	Returns
	------------
		mqtt_payload : string
			the corresponding message associated to 'msg' key

	"""
	payload = payload.replace("'", "\"")
	
	mqtt_payload = json.loads(payload)
	
	return mqtt_payload["msg"]

def mqttJsonDump(payload):
	"""
	function that convert the payload into json format with the key: 'msg'
	
	Parameters
	------------
		payload: string 
			payload of mqtt message

	
	"""
	obj = {
		"msg":payload
	}
	return json.dumps(obj)


class Client():
	"""
	class implementing the mosquitto client

	Parameters
	-------------
		name : string
			client ID

	Methods
	-------------
		connect: starts the connection to the broker inside a loop
		
		subscribe: subscribe the client to a specific topic
		
		publish: publish in the specific topic a specific message
		
		on_connect: mqtt callback used to subscribe to the two interested topics 
		when connection begins
		
		on_disconnect: callback used to disconnect client from the broker
		
		on_message: callback used to insert data from mqtt message in the pending json
		
		on_subscribe: callback used to notify if subscription is done

	"""
	def __init__(self, name):
		self.name = name
		self.client = mqtt.Client(self.name)
		self.client.on_message=self.on_message
		self.client.on_connect=self.on_connect
		self.client.on_subscribe=self.on_subscribe
		self.client.on_disconnect=self.on_disconnect
		
	def connect(self):
		"""
		activates a looping 'forever' connection with the mosquitto broker

		"""
		self.printed_sub = False
		self.client.connect(BROKER)
		self.client.loop_forever()

	def subscribe(self, topic):
		"""
		subscribe the client to the specific topic, 
		which name is passed as a parameter

		Paramaters 
		------------
			topic : string
				name of the selected topic
		"""
		self.topic=topic
		self.client.subscribe(self.topic)
	
	def publish(self, topic, msg):
		"""
		publishes message in a specific topic, both the message 
		payload and the topic name are passed as parameters

		Paramaters
		------------
			topic : string
				name of the selected topic
			msg : string/int/float/binary
				message to be published in the topic
		"""
		self.topic = topic
		self.msg = msg 
		self.client.publish(self.topic, self.msg)
		

	def on_connect(self, client, userdata, flags, rc):
		"""
		callback that subscribe automatically, when conncetion starts, the client to topic 'measure/people'
		and to the topic 'system'. prints out a connection confirm.

		Parameteres
		-------------
			client :
				predefined phao mqtt library parameter
			userdata :
				predefined phao mqtt library parameter
			flags : 
				predefined phao mqtt library parameter
			rc :
				predefined phao mqtt library parameter

		"""

		self.subscribe("system")
		print ("[{}] Client connected".format(
			int(time.time())
		))

	def on_disconnect(self, client, userdata, rc):
		"""
		callback that disconnect the client from the broker, 	
		only modification wrt the predefined one is that is printing out
		a disconnection confirm.

		Parameteres
		-------------
			client :
				predefined phao mqtt library parameter
			userdata :
				predefined phao mqtt library parameter
			rc :
				predefined phao mqtt library parameter

		"""
		print ("[{}] Client disconnected".format(
			int(time.time())
		))

	def on_message(self, client, userdata, message):
		"""
		callback that when messages arrive on the topics calls the 'updatePendingJson' function
		to update the pending json in the data queue , with the payload of the mqtt message.
		it does this keeping attention to the right specific topic.

		Parameteres
		-------------
			client :
				predefined phao mqtt library parameters
			userdata :
				predefined phao mqtt library parameter
			message :
				mqtt message found in the topic
		"""
		self.message = message
		mqtt_msg = mqttJsonLoad(self.message.payload)
		
		print ("[{}] Message arrived:\n\t\tTopic: {}\n\t\tMessage: {}".format(
			int(time.time()), 
			message.topic, 
			message.payload
		))
		
		if self.message.topic == "measure/people":
			rpi.updatePendingJson("people_inside", mqtt_msg, "data")
		elif self.message.topic == "system":
			start()

	def on_subscribe(self, client, userdata, mid, granted_qos):
		"""
		callback funtion (precautional) used to notify subscription

		Parameteres
		-------------
			client :
				predefined phao mqtt library parameters
			userdata :
				predefined phao mqtt library parameter
			mid :
				predefined phao mqtt library parameters
			granted_qos :
				predefined phao mqtt library parameters

		"""
		print ("[{}] Client subscribed to {}".format(
			int(time.time()),
			self.topic
		))
		#the following lines are here and not in on_connect() only for printing purpose
		if not self.printed_sub:
			self.printed_sub = True
			self.subscribe("measure/people")

class Raspberry():
	"""
	class implementing the Raspberry functionalities, such as the managing of data queue,
	the acquisition of data from temperature/humidity sensor DHT11 locally connected and
	pinging the ESP in a while loop with a specific time interval

	
	Methods
	-------------
		createJson: creates new json object for storing data 
		
		updatePendingJson: manages the data queue of json objects
		
		fullJson: check if a json object storing a value for each data field is full and ready to be sent
		
		acquisition: mqtt callback used to subscribe to the two interested topics 
		when connection begins
		
		pingEsp: callback used to disconnect client from the broker
		
		registerDevice: register the device on the Room Catalog
		
	"""
	def __init__(self):
		self.queue = []
		self.dataQueue = []
		# init the json queue
		self.createJson("data")
		self.registerDevice()

	def createJson(self, channel):
		"""
		creates empty json object with 4 keys: 'temperature', 'humidity', 'light', 'people inside' 
		and None values for each one
		and appends to the queue the new created object and prints out that new json has been created

		Parameters
		-----------
			channel : string
				specify the channel chosen in this case 'data'
		"""
		self.channel = channel
		
		if self.channel == "data":
			self.queue = self.dataQueue
			self.json = {
					"temperature":None,
					"humidity":None,
					"people_inside":None,
			}
	
		self.json = json.dumps(self.json)
		self.queue.append(self.json)
		
		if self.channel == "data":
			self.dataQueue = self.queue
		
		print ("[{}] New json created".format(
			int(time.time()),
		))

	def updatePendingJson(self, param, data, channel):
		"""
		Updates the pending json files in the queue, creates a new empty json if the queue is initially empty, if not checks the pending jsons and inserts
		new data value where not already present, if already present saves that in successive freshly created pending json. When finds a full json file: with all non empty 
		values for each keys, create with those data a get request to ThingSpeak. Then delete the sent json from the queue and checks if the queue is emptied 
		if so creates a new empty json. 
		if first json in queue is not full is not ready to be sent, but if new data of an already full key arrives it saves it in a new pending json in position 2 and so on.
		this function uses functionalities of other functions of the class 'fullJson' 'createJson', and calls itself in a recursive fashion.
		Parameters
		------------
			param : string
				key of the json to be checked ('temperature' or 'humidity' or 'light' or 'person' or 'heat stat')
			data : depends
				is the actual value from the sensor to be inserted in the json empty space of corresponding key
			channel : string
				name of the channel

		Attributes
		-----------
			 found : boolean variable
			 	initially set to False becomes True when in the pending checked json  for the specific param there is no value
	
		"""
		self.channel = channel
		self.param = param
		self.data = data
		self.found = False
		
		if self.channel == "data":
			self.queue = self.dataQueue
		
		if len(self.queue) == 0:
				self.createJson(self.channel)
		else:
			for pending in self.queue:
				temp_json = json.loads(pending)

				if temp_json[self.param]==None:
					self.found = True
					temp_json[self.param] = self.data
					dumped_json = json.dumps(temp_json)

					if self.fullJson(temp_json, self.channel):
						if self.channel == "data":
							self.body = TS_DATA_UPDATE + "&"\
							+ "field1=" + str(temp_json["temperature"]) +"&"\
							+ "field2=" + str(temp_json["humidity"]) +"&"\
							+ "field3=" + str(temp_json["people_inside"])
							
						print ("[{}] Json message sent to ThingSpeak".format(
							int(time.time()),
						))
						
						index = self.queue.index(pending)
						self.queue.pop(index)
						if len(self.queue) == 0:
							self.createJson(self.channel)
							
						if self.channel == "data":
							self.dataQueue = self.queue
						break
						
					else:
						index = self.queue.index(pending)
						self.queue[index] = dumped_json
						
						if self.channel == "data":
							self.dataQueue = self.queue
						break
			if not self.found:
				new_json = self.createJson(self.channel)
				self.updatePendingJson(self.param, self.data, self.channel)
		
		print ("[{}] Queue updated:".format(
			int(time.time()),
		))
		
		for item in self.dataQueue:
			print "\t{}".format(item)
	
	def fullJson(self, obj, channel):
		"""
		this function checks if the chosen json is full or not, 
		in other words if there is a value for each one of the keys

		Parameters
		------------
			obj : json variable
				the json file to be checked
			channel : string
				name of the channel

		"""
		self.channel = channel
		self.obj = obj
		
		if self.channel == "data":
			cond_1 = self.obj["temperature"]!=None
			cond_2 = self.obj["humidity"]!=None
			cond_3 = self.obj["people_inside"]!=None
			
			if cond_1 and cond_2 and cond_3:
				return True
			else:
				return False
	
	def registerDevice(self):
		"""
		register the device on the Room Catalog by sending a post request to it.
		"""
		r = req.post("http://localhost:9090/devices?id={}&sensors={}_{}&board={}".format(
			BOARD_ID,
			SENSOR1,
			SENSOR2,
			BOARD
		))
		print ("[{}] Device Registered on Room Catalog".format(
			int(time.time()),
		))
				
	def acquisition(self):
		"""
		this function manages the data acquisition from the locally connected temperature/humidity sensor DHT11
		takes values from the sensor at given time intervals which are retrieved via get request from the room catalogue.
		It publish the data (in json format) in the corresponding topic.
		with the retrieved values updates the json data queue.
		"""
		while True:
			self.humidity, self.temperature = Adafruit_DHT.read_retry(SENSOR, PIN)
			print ("[{}] New measures from the Adafruit DHT:\n\tTemperature: {}C\n\tHumidity: {}%".format(
				int(time.time()),
				self.temperature,
				self.humidity
			))
			mqttCli.publish("measure/temperature", mqttJsonDump(self.temperature))
			mqttCli.publish("measure/humidity", mqttJsonDump(self.humidity))
			
			self.updatePendingJson("humidity", self.humidity, "data")
			self.updatePendingJson("temperature", self.temperature, "data")
			
			r=req.get('http://localhost:9090/interacquisition')
			r = r.content
			r = json.loads(r)
			delta_t = r["interacquisition"]*60
			
			print ("[{}] Interacquisition time retrieved from the Room Catalog".format(
				int(time.time()),
			))
			
			time.sleep(delta_t)
	
	def pingEsp(self):
		"""
		starts a while loop that with in defined time interval perform
		a ping to the ESP of arduinos to verify connection.
		"""
		while True:
			print ("[{}] Keeping alive the ESP8266 connection".format(
				int(time.time()),
			))
			mqttCli.publish("ping", mqttJsonDump('void'))
			time.sleep(180)

def start():
	"""
	function that starts the different threads in parallel:
	acquisition thread
	pinging thread
	"""
	print ("[{}] System started".format(
		int(time.time()),
	))
	t_acquisition = threading.Thread(name="Data", target=rpi.acquisition)
	t_ping = threading.Thread(name="ping", target=rpi.pingEsp)
	t_acquisition.start()
	t_ping.start()

global rpi
global mqttCli

rpi = Raspberry()
mqttCli = Client(CLIENT_ID)
t_client = threading.Thread(name="mqttClient", target=mqttCli.connect)
t_client.start()
