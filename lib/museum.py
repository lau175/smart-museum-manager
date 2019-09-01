#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Telegram Bot developed for an active and passive monitoring of a museum room.
It is part of the project requested by the 'Programming for IoT Applications' course at
Politecnico di Torino, IT.

Author: Luca Gioacchini (s257076)
Academic year: 2018/19
"""

from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.loop import MessageLoop
import requests as req
import telepot
import emoji
import json
import time
import os

# Bot constants
TOKEN 			= '656937907:AAH06cLicJwrPelYqfiRji6LnXnV8wCeg_M'

# Thingspeak
TS_DATA 		= 'https://api.thingspeak.com/channels/699095/feeds.json?'+\
				  'api_key=U17R0YH2YW9OBOZJ&results=1'
RC_TH			= 'http://localhost:9090/th'
# Telegram Inline Keyboards
K1 = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text='Yes', callback_data='Yes'),
		InlineKeyboardButton(text='No', callback_data='No')]
	])
	
K2 = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text='Get Last Data', callback_data='data'),
		InlineKeyboardButton(text='Display Threshold', callback_data='act_th')],
		[InlineKeyboardButton(text='Set New Threshold', callback_data='set_th'),
		InlineKeyboardButton(text='Device Interaction', callback_data='dev')]
	])
	
K3 = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text='Max Temperature', callback_data='max_temp'),
		InlineKeyboardButton(text='Min Temperature', callback_data='min_temp')],
		[InlineKeyboardButton(text='Humidity', callback_data='hum'),
		InlineKeyboardButton(text='People', callback_data='peop')],
		[InlineKeyboardButton(text='Light Timer', callback_data='light_t'),
		InlineKeyboardButton(text='Cancel', callback_data='cancel')]
	])

K4 = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text='Light', callback_data='onoff_light'),
		InlineKeyboardButton(text='Heating', callback_data='onoff_heat')],
		[InlineKeyboardButton(text='Cancel', callback_data='cancel')]
	])	


class MuseumBot():
	"""Telegram Bot which servers the museum employees. It is based on three main functions:
	1) Get the environmental parameters from ThingSpeak. The parameters are the room
	   temperature, the room humidity and the average number of people inside the room
	2) Retrieve the threshold set and change them. The thresholds are stored in the Room
	   Catalog. By considering that they can be changed also trough the Freeboard dashboard
	   from an internet browser, the thresholds set can be also displayed as an additional 
	   check
	3) Interact with devices (lights and heating) by turning them ON or OFF.
	
	When a new user joins the Bot it is asked if he wants to receive notification. If he
	wants, its Telegram chat ID is appended to a json storing all the active users' chat ID
	
	Moreover, when the external control system detect that an environmental parameter value
	exceeds the threshold, an alert is sent to the users through the bot.
	The alerts are:
	1) Critical temperature value
	2) Critical humidity value
	3) Critical number of people inside the room
	4) Lighs shutting down notification
	5) Museum closing notification
	
	The communication between the control system and the Telegram bot is based on the MQTT 
	protocol.
	
	Parameters
	----------
		mqtt_client : tuple
			paho.mqtt client
	
	Attributes
	----------
		bot : telepot.Bot
			Bot object of the telepot library
		client : instance
			instance of the mqtt.paho.client.Client class
		min_temp_flag : bool
			True if the minimum temperature threshold is changing
			False otherwise
		max_temp_flag : bool
			True if the maximum temperature threshold is changing
			False otherwise
		hum_flag : bool
			True if the humidity threshold is changing
			False otherwise
		people_flag : bool
			True if the maximum people threshold is changing
			False otherwise
		timer_flag : bool
			True if the light timer threshold is changing
			False otherwise
		
	Methods
	-------
		start()	
			start the bot loop
		handle(msg)
			message reception and replying handling function
		supportedMsg(msg)
			check if the message is a number or is a word
		updateRc(field, val)
			update the thresholds in the Room Catalog
		getData(target)
			retrieve data from ThingSpeak and hresholds from the Room Catalog
		updateChatList(ch_id)
			when a new user join the bot its chat identifier is appended at the end of
			the chatlist. If there is no chatlist, it is initialized as empty
		startRes(ch_id)
			ask for notification
		notificationManager(ch_id, msg)
			manage the chatlist if the user wants to receive notification
		mainOptions(op_id, ch_id)
			manage the bot main operations
		changeStat(dev, ch_id)
			change the devices status
		queries(msg)
			manage the queries associated to the inline keyboard buttons
		sendAlerts(key, ch_id, *msg)
			send the alerts to the users if an environmental parameter value exceed a 
			threshold
	"""
	def __init__(self, *mqtt_client):
		self.bot = telepot.Bot(TOKEN)
		
		if len(mqtt_client)>0:
			self.client = mqtt_client[0]
			self.client.connect()
					
		self.min_temp_flag 	= False
		self.max_temp_flag 	= False
		self.hum_flag 		= False
		self.people_flag 	= False
		self.timer_flag 	= False
	
	
	def start(self):
		"""Start the telegram bot loop.
		
		"""
		print("[{}] TBOT: Telegram Bot started".format(
			int(time.time())
		))	
		MessageLoop(
			self.bot,{
				"chat":self.handle,
				"callback_query":self.queries
			}
		).run_as_thread()
	
	
	def handle(self, msg):
		"""Main function and configuration of the Telegram bot.
		The bot waits for the photo and sends back the description of the artwork relative
		artwork.
	
		Parameters
		----------
			msg : dict 
				received message from the user 
		"""
		content_type, chat_type, chat_id = telepot.glance(msg)
		
		# Bot Start
		if msg["text"] == "/start":
			print ("[{}] TBOT: New Bot user with id {}".format(
				int(time.time()),
				chat_id
			))
			self.startRes(chat_id)	
		
		# Set new threshold
		# Max Temperature
		elif self.max_temp_flag:
			if self.supportedMsg(msg["text"]):
				self.max_temp_flag = False
				self.updateRc("max_temperature_th", msg["text"])
				
				self.bot.sendMessage(chat_id, 
					'New Maximum temperature threshold set as ' + msg["text"] + " C",
					reply_markup=K2
				)
				
				print ("[{}] TBOT: New max temperature threshold set: {}C".format(
					int(time.time()),
					msg["text"]
				))
				
			else:
				self.bot.sendMessage(
					chat_id, "Invalid Input: The value must be a number.\nTry Again."
				)
		
		# Max Temperature
		elif self.min_temp_flag:
			if self.supportedMsg(msg["text"]):
				self.min_temp_flag = False
				self.updateRc("min_temperature_th", msg["text"])
				
				self.bot.sendMessage(
					chat_id, 
					'New Minimum temperature threshold set as ' + msg["text"] + " C",
					reply_markup=K2
				)
				
				print ("[{}] TBOT: New min temperature threshold set: {}C".format(
					int(time.time()),
					msg["text"]
				))
				
			else:
				self.bot.sendMessage(
					chat_id, "Invalid Input: The value must be a number.\nTry Again."
				)
		
		# Humidity
		elif self.hum_flag:
			if self.supportedMsg(msg["text"]):
				self.hum_flag = False
				self.updateRc("humidity_th", msg["text"])

				self.bot.sendMessage(
					chat_id, 
					'New humidity threshold set as ' + msg["text"] + "%",
					reply_markup=K2
				)
				
				print ("[{}] TBOT: New humidity threshold set: {}%".format(
					int(time.time()),
					msg["text"]
				))
				
			else:
				self.bot.sendMessage(
					chat_id, "Invalid Input: The value must be a number.\nTry Again."
				)
		
		# People
		elif self.people_flag:
			if self.supportedMsg(msg["text"]):
				self.people_flag = False
				self.updateRc("people_th", msg["text"])

				self.bot.sendMessage(
					chat_id, 
					'New people threshold set as ' + msg["text"] + " people",
					reply_markup=K2
				)
				
				print ("[{}] TBOT: New people threshold set: {}".format(
					int(time.time()),
					msg["text"]
				))
				
			else:
				self.bot.sendMessage(
					chat_id, "Invalid Input: The value must be a number.\nTry Again."
				)
		
		# Light Timer
		elif self.timer_flag:
			if self.supportedMsg(msg["text"]):
				self.timer_flag = False
				self.updateRc("light_timer", msg["text"])

				self.bot.sendMessage(
					chat_id, 
					'New light timer set as ' + msg["text"] + " seconds",
					reply_markup=K2
				)
				
				print ("[{}] TBOT: New light timer set: {} min".format(
					int(time.time()),
					msg["text"]
				))
				
			else:
				self.bot.sendMessage(
					chat_id, "Invalid Input: The value must be a number.\nTry Again."
				)
		
		# Unsupported Messages	
		else:	
			self.bot.sendMessage(chat_id, "Message type not supported. Try again")

	
	def supportedMsg(self, msg):
		"""Check if the message is a number or is a word.
		
		Parameters
		----------
			msg : str
				message to check
		
		Returns
		-------
			True : bool
				if the message is a number
			False : bool
				if the message is a word
		"""
		letter_count = 0
		
		for letter in msg:
			if not letter.isnumeric():
				letter_count += 1
		
		if letter_count != 0:
			return False
		
		else:
			return True
	
	
	def updateRc(self, field, val):
		"""Update the thresholds stored in the Room Catalog with a HTTP post request.
		Publish an mqtt message to notify the threshold updating.
		
		Parameters
		----------
			field : str
				threshold quantity
			val : int
				new threshold value
		
		Attributes
		----------
			set : dict
				thresholds set retrieved from the Room Catalog
		"""
		self.set = threshold_set
		
		self.set[field] = val
		r = req.post(RC_TH + "?type=" + field + "&val=" + self.set[field])
		print ("[{}] TBOT: Room Catalog updated with new thresholds".format(
			int(time.time())
		))
		
		self.client.publish("trigger/th", "void")
	
	
	def getData(self, target):
		"""Retrieve environmental parameters from ThingSpeak and thresholds set from the
		Room Catalog thanks to a HTTP get request.
		
		Parameters
		----------
			target : str
				'data' if the environmental parameters are nedded
				'thresholds' if the thresholds set is needed
				
		Returns
		-------
			feeds : dict
				json message containing the requested values
		"""
		if target == "data":
			r = req.get(TS_DATA)
			ts_res = json.loads(r.content)
			feeds = ts_res["feeds"]
			feeds = feeds[0]
			print ("[{}] TBOT: Data obtained from ThingSpeak".format(
				int(time.time())
			))
			
		elif target == "thresholds":
			r = req.get(RC_TH)
			r = json.loads(r.content)
			feeds = r["threshold"]
			print ("[{}] TBOT: Thresholds obtained from Room Catalog".format(
				int(time.time())
			))	
		
		return feeds
	
	
	def updateChatList(self, ch_id):
		"""When a new user join the bot its chat identifier is appended at the end of
		the chatlist. If there is no chatlist, it is initialized as empty.
		
		Parameters
		----------
			ch_id : int
				Telegram user's identification number
		"""
		# Create a new json list if it is not present
		if "museum_ids.json" not in os.listdir("jsons/"):
			json_obj = {"chat_ids":[]}
			json_obj = json.dumps(json_obj)
			
			with open("jsons/museum_ids.json", "w") as file:
				file.write(json_obj)
			
			print ("[{}] TBOT: Chatlist created".format(
				int(time.time())
			))
			
		# List update		
		with open("jsons/museum_ids.json", "r+") as file:
			chat_list = json.loads(file.read())
			
			if ch_id not in chat_list["chat_ids"]:
				chat_list["chat_ids"].append(ch_id)
				chat_list=json.dumps(chat_list)
				file.seek(0)
				file.write(chat_list)
			
			print ("[{}] TBOT: Chatlist updated".format(
				int(time.time())
			))


	def startRes(self, ch_id):
		"""When a new user join the bot he can choose to receive notifications or not.
		
		Parameters
		----------
			ch_id : int
				Telegram user's identification number
		"""
		self.bot.sendMessage(ch_id, 
			'Do you want to receive alert notifications?',
			reply_markup = K1,
		)
 
 
	def notificationManager(self, ch_id, msg):
		"""If the new user wants to receive notifications, his chat ID is appended to the
		chat list.
		
		Parameters
		----------
			ch_id : int
				Telegram user's identification number
			msg : str
				user's message
		"""
		if msg == "No":
			self.bot.sendMessage(ch_id, 
				'Choose an option:',
				reply_markup=K2
			)
			
		else:
			self.updateChatList(ch_id)
			self.bot.sendMessage(ch_id, 
				'Now you will receive alert notifications.\n\nChoose an option:',
				reply_markup=K2
			)
	
	
	def mainOptions(self, op_id, ch_id):
		"""Manage the main options of the bot: 
		1) Retrieve the environmental parameters from ThingSpeak
		2) Retrieve the thresholds set from the Room Catalog
		3) Change the devices (lights and heating) status
		
		Parameters
		----------
			op_id : int
				main operation identification number
			ch_id : int
				Telegram user's identification number
		"""
		global threshold_set
		global device_status
		
		# Display data
		if op_id == 0:
			feeds = self.getData("data")
			date, hour = feeds["created_at"].split("T")
			hour = hour.replace("Z", "")
			hour, min_, sec = hour.split(":")
			hour = int(hour) + 2
			min_ = int(min_)
			sec = int(sec)
					
			# Message Creation
			msg = """Last Data Acquisition:

Temperature: {}C
Humidity: {}%
People Inside: {}

Last Update:
{}
{}:{}:{}""".format(
				feeds["field1"],
				feeds["field2"],
				feeds["field3"],
				date,
				hour,
				min_,
				sec
			) 
							
			# Reply	
			self.bot.sendMessage(ch_id, 
				msg,
				reply_markup=K2
			)
		
		# Change Threshold	
		elif op_id == 1:
			feeds = self.getData("thresholds")
			threshold_set = feeds
			
			# Message Creation
			msg ="""Actual thresholds:

Max temperature: {}C
Min temperature: {}C
Max humidity: {}%
Max people inside: {}
Light timer: {} min

Choose threshold quantity.""".format(
				feeds["max_temperature_th"],
				feeds["min_temperature_th"],
				feeds["humidity_th"],
				feeds["people_th"],
				feeds["light_timer"]			
			) 
			
			self.bot.sendMessage(ch_id, 
				msg,
				reply_markup=K3
			)
			
		# Change Devices Status
		elif op_id == 2:
			self.bot.sendMessage(ch_id, 
				"Choose a device:",
				reply_markup=K4
			)
		
		# Change Threshold	
		elif op_id == 3:
			feeds = self.getData("thresholds")
			threshold_set = feeds
		
			# Message Creation
			msg ="""Actual thresholds:

Max temperature: {}C
Min temperature: {}C
Max humidity: {}%
Max people inside: {}
Light timer: {} min

Choose threshold quantity.""".format(
				feeds["max_temperature_th"],
				feeds["min_temperature_th"],
				feeds["humidity_th"],
				feeds["people_th"],
				feeds["light_timer"]			
			) 
			
			self.bot.sendMessage(ch_id, 
				msg,
				reply_markup=K2
			)

	
	def changeStat(self, dev, ch_id):
		"""Change the devices status by triggering an event through an mqtt message.
		
		Parameters
		----------
			dev : str
				"Light" if the user wants to change the lights status
				"Heat" if the user wants to change the heating status
			ch_id : int
				Telegram user's identification number
		"""
		# Light Switch
		if dev == "Light":
			self.client.publish("trigger/light", "void")
			self.bot.sendMessage(
				ch_id, 
				"Light status changed.",
				reply_markup=K2
			)
			print ("[{}] TBOT: Light status changed".format(
				int(time.time())
			))
			
		# Heating Switch
		else:
			self.client.publish("trigger/heat", "void")
			self.bot.sendMessage(
				ch_id, 
				"Heating status changed.",
				reply_markup=K2
			)
			print ("[{}] TBOT: Heat status changed".format(
				int(time.time())
			))


	def queries(self, msg):
		"""Manages the queries associated to each inline keyboard buttons. This exploit the
		functions of the telepot library.
		
		Parameter
		---------
			msg : dict
				received message from the user
		"""
		query_id, ch_id, query = telepot.glance(msg, flavor = 'callback_query')
		
		# ask for notification
		if query == "Yes" or query == "No":
			self.notificationManager(ch_id, query)
		# display data
		elif query == "data":
			self.mainOptions(0, ch_id)
		# set new threshold
		elif query == 'set_th':		
			self.mainOptions(1, ch_id)
		# devices interaction
		elif query == 'dev':		
			self.mainOptions(2, ch_id)
		# display thresholds
		elif query == 'act_th':		
			self.mainOptions(3, ch_id)
		elif query == "max_temp":
			self.max_temp_flag = True
			self.bot.sendMessage(
				ch_id, 
				"Insert the new maximum temperature threshold."
			)
		elif query == "min_temp":
			self.min_temp_flag = True
			self.bot.sendMessage(
				ch_id, 
				"Insert the new minimum temperature threshold."
			)
		elif query == "hum":
			self.hum_flag = True
			self.bot.sendMessage(
				ch_id, 
				"Insert the new humidity threshold."
			)
		elif query == "peop":
			self.people_flag = True
			self.bot.sendMessage(
				ch_id, 
				"Insert the new people threshold."
			)
		elif query == "light_t":
			self.timer_flag = True
			self.bot.sendMessage(
				ch_id, 
				"Insert the new light timer."
			)
		elif query == "onoff_light":
			self.changeStat("Light", ch_id)
		elif query == "onoff_heat":
			self.changeStat("Heat", ch_id)
		elif query == "cancel":
			self.bot.sendMessage(
				ch_id, 
				"Operation aborted.\n\nChoose an option.",
				reply_markup = K2
			)


	def sendAlerts(self, key, ch_id, *msg):
		"""Send the alerts when an environmental parameter value exceed a treshold.
		This function is triggered by the mqtt client.
		
		Parameters
		----------
			key : str
				type of alert
			ch_id : int
				Telegram user's identification number
			msg : tuple
				message to be sent
		"""
		if key == 'temperature':
			self.bot.sendMessage(
				ch_id, 
				emoji.emojize(
					':warning: ALERT :warning:', 
					use_aliases=True
				)+\
				'\nCritical temperature value:\n{}C'.format(msg[0]),
				reply_markup=K2
			)
			print ("[{}] TBOT: Temperature alert sent to users".format(
				int(time.time())
			))
			
		elif key == 'humidity':
			self.bot.sendMessage(
				ch_id, 
				emoji.emojize(
					':warning: ALERT :warning:', 
					use_aliases=True
				)+\
				'\nCritical humidity value:\n{}%'.format(msg[0]),
				reply_markup=K2
			)
			print ("[{}] TBOT: Humidity alert sent to users".format(
				int(time.time())
			))
			
		elif key == 'people':
			self.bot.sendMessage(
				ch_id, 
				emoji.emojize(
					':warning: ALERT :warning:', 
					use_aliases=True
				)+\
				'\nCritical number of people inside:\n{} perole'.format(msg[0]),
				reply_markup=K2
			)
			print ("[{}] TBOT: People alert sent to users".format(
				int(time.time())
			))
			
		elif key == 'lights':
			self.bot.sendMessage(
				ch_id, 
				emoji.emojize(
					':warning: ALERT :warning:', 
					use_aliases=True
				)+\
				'\nLights are OFF',
				reply_markup=K2
			)
			print ("[{}] TBOT: Lights shutting down alert sent to users".format(
				int(time.time())
			))
			
		elif key == 'closing':
			self.bot.sendMessage(
				ch_id, 
				emoji.emojize(
					':warning: ALERT :warning:', 
					use_aliases=True
					)+\
					'\nMuseum is closed. Shutting down lights and heating.',
				reply_markup=K2
			)
			print ("[{}] TBOT: Closing alert sent to users".format(
				int(time.time())
			))
