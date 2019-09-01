#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""MQTT client which allows the communication between different software agents (Telegram 
Bots, external control system, etc.) in a smart museum room scenario.
It is part of the project requested by the 'Programming for IoT Applications' course at
Politecnico di Torino, IT.

Author: Luca Gioacchini (s257076)
Academic year: 2018/19
"""

from museum import MuseumBot
from artworks import ArtBot
import paho.mqtt.client as mqtt
import telepot
import emoji
import json
import time
import os

# MQTT constants
BROKER  	= 'localhost'

# Bot constants
TOKEN 		 = '661202308:AAE4rEptgYJqdVnP54f4-c3BNmpD2ZOxEQs'


class Client():
	"""Mqtt client. It connects to the local broker, subscribes to the 'alert/closing' topic.
	When the museum is closing a message is received at this topic and an alert is sent as
	a Telegram message to all the daily museum users.
	
	Parameters
	----------
		name : str
			mqtt client identification name
		bot_id : str
			bot identifier
			'art' for the artworks bot
			'museum' for the management bot
			
	Attributes
	----------
		bot_id : str
			bot identifier
			'art' for the artworks bot
			'museum' for the management bot
		bot : telepot.Bot
			Bot object of the telepot library
		client : paho.mqtt.client.Client
			Client object of the paho-mqtt library
		
	Methods
	-------
		connect()
			connect the mqtt client to the broker
		subscribe(topic)
			topics subscription management
		publish()
			message pubblication
		on_message(client, userdata, message)
			callback function called when a message arrives to a topic the client is 
			subscribed to
		on_connect(client, userdata, flags, rc)
			callback function called when the connection succeed
		on_disconnect(client, userdata, rc)
			callback function called when the client is disconnected
		on_publish(client, userdata, mid)
			callback function called when a message is published
		on_subscribe(client, userdata, mid, granted_qos)
			callback function called when the client is subscribed to a topic
		mqttJsonLoad(payload)
			when a json message arrives, it is loaded and the 'msg' value is returned
		mqttJsonDumps(payload)
			convert the message into a json one
	"""
	def __init__(self, name, bot_id):
		self.client = mqtt.Client(name)
		self.bot_id = bot_id
		if self.bot_id == 'art':
			self.bot = ArtBot()
		elif self.bot_id == 'museum':
			self.bot = MuseumBot()
		
		# Callbacks association
		self.client.on_message=self.on_message
		self.client.on_connect=self.on_connect
		self.client.on_publish=self.on_publish
		self.client.on_subscribe=self.on_subscribe
		self.client.on_disconnect=self.on_disconnect
	
	# Generic functions
	def connect(self):
		"""Connect the mqtt client to the broker
		
		"""
		self.client.connect(BROKER)
		self.client.loop_start()
		
		
	def subscribe(self, topic):
		"""Topic subscription management
		
		"""
		self.client.subscribe(topic)
	
	
	def publish(self, topic, msg):
		"""The message is converted into a json and it is published through mqtt
		
		Parameters
		----------
			topic : str
				topic the client wants to publish
			msg : str
				message payload
		
		Attributes
		----------
			topic : str
				topic the client wants to publish
			msg : str
				json converted message
		"""
		self.topic = topic
		self.msg = self.mqttJsonDump(msg)
		
		self.client.publish(topic, self.msg)
	
	
	# Callbacks definition
	def on_message(self, client, userdata, message):
		"""Paho-mqtt callback function called when a message arrives to a topic the client 
		is subscribed to. For more info	see the original paho-mqtt docstrings.
		
		Parameters
		----------
			client
    			the client instance for this callback
			userdata
				the private user data 
			message
				received message
		"""
		
		mqtt_msg = self.mqttJsonLoad(message.payload)
		
		print ("[{}] MQTT: Message arrived:\n\t\tTopic: {}\n\t\tMessage: {}".format(
			int(time.time()), 
			message.topic, 
			message.payload
		))
		# Notifications 
		if message.topic == "alert/temperature":
			with open ("jsons/museum_ids.json", "r") as file:
				json_list = json.loads(file.read())
				json_list = json_list["chat_ids"]
				
				for item in json_list:
					self.bot.sendAlerts('temperature', item, mqtt_msg)
		
		elif message.topic == "alert/humidity":
			with open ("jsons/museum_ids.json", "r") as file:
				json_list = json.loads(file.read())
				json_list = json_list["chat_ids"]

				for item in json_list:
					self.bot.sendAlerts('humidity', item, mqtt_msg)
		
		elif message.topic == "alert/people":
			with open ("jsons/museum_ids.json", "r") as file:
				json_list = json.loads(file.read())
				json_list = json_list["chat_ids"]
				
				for item in json_list:
					self.bot.sendAlerts('people', item, mqtt_msg)
		
		elif message.topic == "alert/light_down":
			with open ("jsons/museum_ids.json", "r") as file:
				json_list = json.loads(file.read())
				json_list = json_list["chat_ids"]
				
				for item in json_list:
					self.bot.sendAlerts('lights', item)
					
		elif message.topic == "alert/closing":	
			if self.bot_id == "museum":
				with open ("jsons/museum_ids.json", "r") as file:
					json_list = json.loads(file.read())
					json_list = json_list["chat_ids"]
					for item in json_list:
						self.bot.sendAlerts('closing', item, "")

			elif self.bot_id == "art":
				with open ("jsons/art_ids.json", "r") as file:
					json_list = json.loads(file.read())
					json_list = json_list["chat_ids"]
					for item in json_list:
						self.bot.sendAlerts('closing', item, "")
			
					os.remove("jsons/art_ids.json")				
			
					print("[{}] TBOT: Chatlist is empty".format(
							int(time.time())
						))	
						  
	def on_connect(self, client, userdata, flags, rc):
		"""Paho-mqtt callback function called when the connection succeed. For more info
		see the original paho-mqtt docstrings.
		
		Parameters
		----------	
			client
    			the client instance for this callback
			userdata
				the private user data 
			flags
				response flags sent by the broker
			rc
				the connection result
			flags 
				dict that contains response flags from the broker
		"""
		if self.bot_id == 'art':
			self.topic = "alert/closing"
		elif self.bot_id == 'museum':
			self.topic = "alert/#" 
		self.subscribe(self.topic)
		print ("[{}] MQTT: Client connected".format(
			int(time.time())
		))
	
	
	def on_disconnect(self, client, userdata, rc):
		"""Paho-mqtt callback function called when the client is disconnected. For more info
		see the original paho-mqtt docstrings.
		
		Parameters
		----------	
			client
    			the client instance for this callback
			userdata
				the private user data 
			flags
				response flags sent by the broker
			rc
				the disconnection result
		"""
		print ("[{}] MQTT: Client disconnected".format(
			int(time.time())
		))
	
	
	def on_publish(self, client, userdata, mid):
		"""Paho-mqtt callback function called when a message is published. For more info
		see the original paho-mqtt docstrings.
		
		Parameters
		----------	
			client
    			the client instance for this callback
			userdata
				the private user data 
			mid
				message ID for the publish request
		"""
		print ("[{}] MQTT: Message published:\n\t\tTopic: {}\n\t\tMessage: {}".format(
			int(time.time()), 
			self.topic, 
			self.msg
		))
		
		
	def on_subscribe(self, client, userdata, mid, granted_qos):
		"""Paho-mqtt callback function called when the client is subscribed to a topic. For 
		more info see the original paho-mqtt docstrings.
		
		Parameters
		----------	
			client
    			the client instance for this callback
			userdata
				the private user data 
			mid
				message ID for the publish request
			granted_qos
				QoS level the broker has granted for each of the different subscription 
				requests
		"""
		print ("[{}] MQTT: Subscribed to {}".format(
			int(time.time()),
			self.topic
		))
	
	
	def mqttJsonLoad(self, payload):
		"""When a json message arrives, it is loaded and the 'msg' value is returned
		
		Parameters
		----------
			payload : str
				json message
		
		Returns
		-------
			str
				value of the json 'msg' key
		"""
		payload = payload.replace("'", "\"")

		mqtt_payload = json.loads(payload)

		return mqtt_payload["msg"]
		
		
	def mqttJsonDump(self, payload):
		"""Convert the message into a json one
		
		Parameters
		----------
			payload : str
				message to be published
		
		Returns
		-------
			str
				json converted message
		"""
		obj = {
			"msg":payload
		}
		return json.dumps(obj)
