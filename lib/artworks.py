#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Museum-visitor-side Telegram Bot developed to provide the artworks description of a 
Museum Room.
It is part of the project requested by the 'Programming for IoT Applications' course at
Politecnico di Torino, IT.

Author: Luca Gioacchini (s257076)
Academic year: 2018/19
"""

from pyzbar.pyzbar import decode
from qrcode import QRCode
from PIL import Image
import telepot
import emoji
import json
import time
import os

# Bot constants
TOKEN 		= '661202308:AAE4rEptgYJqdVnP54f4-c3BNmpD2ZOxEQs'


class ArtBot():
	"""Telegram Bot which servers the museum visitors. Each artwork is associated to a QR 
	code. The artwork information and description are stored in a local database.
	When a user join the Bot, its Telegram identification number is stored in a chatlist.
	If the user send to the Bot a picture containing the QR code of an artwork, this is 
	decoded (the QR code contains an identification number) and its description is provided
	to the user as a message and a picture of the relative artwork. 
	When the museum closing all the daily users receive a message and the chatlist is
	emptied.
	
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
	
	Methods
	-------
		start()
			start the bot loop
		getDb(art_id)
			database management. Once got the artworks id, the database is scanned and the
			infos are provided
		readQrcodes(msg)
			telegram bot downloads the QR code photo, and decodes the message
		handle(msg)
			message reception and replying handling function
		addChatId(ch_id)
			when a new user join the bot its chat identifier is appended at the end of
			the chatlist. If there is no chatlist, it is initialized as empty
		sendAlerts(key, ch_id, msg)
			send an alert to the museum visitors when the museum is closing
	"""
	def __init__(self, *mqtt_client):
		self.bot = telepot.Bot(TOKEN)

		if len(mqtt_client)>0:
			self.client = mqtt_client[0]
			self.client.connect()
		
		
	def start(self):
		"""Start the bot loop.
		
		"""
		print("[{}] TBOT: Telegram Bot started".format(
					int(time.time())
		))	
		self.bot.message_loop(self.handle)
		
		
	def getDb(self, art_id):
		"""Database management. Once got the artworks id, the database is scanned and the
		infos are provided.
	
		Parameters
		----------
			art_id : int 
				artwork id encoded in the QR code
	
		Returns
		-------
			msg : str 
				artwork infos
			pic : str 
				wikipedia artwork url
		"""
		with open("jsons/database.json") as file:
			json_data = json.load(file)
			for item in json_data["database"]:
				if str(art_id) == item["id"]:
					msg = ("*Title:* " + item["title"] + 
						   "\n*Author:* " + item["author"] + 
						   "\n\n*Year:* " + item["year"] +
						   "\n*Size:* " + item["size"] +
						   "\n\n" + item["description"] 
					)
					pic = item['thumbnail']
		
		return msg, pic


	def readQrcodes(self, msg):
		"""Telegram bot downloads the QR code photo, and decodes the message.
	
		Parameters
		----------
			msg : dict 
				message encoded in QR code
	
		Returns
		-------
			qrcodes : dict 
				decoded message
		"""
		self.bot.download_file(
			msg['photo'][-1]['file_id'], 
			"media/file.png"
		)
		img = Image.open("media/file.png")
		qrcodes = decode(img)
		print ("[{}] TBOT: QR code decoded: {}".format(
			int(time.time()),
			qrcodes[0].data
		))
	
		return qrcodes
	
	 
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
		
		if content_type == 'photo':
			qrcodes = self.readQrcodes(msg)

			if len(qrcodes) > 0:
				for code in qrcodes:
					msg, pic = self.getDb(code.data)
					self.bot.sendPhoto(chat_id, pic, caption = msg, parse_mode='Markdown')
			else:
				self.bot.sendMessage(chat_id, "No QR code found. Try again")

		else:
			if msg['text'] == "/start":
				print ("[{}] TBOT: New Bot user with id {}".format(
					int(time.time()),
					chat_id
				))
				self.addChatId(chat_id)
				self.bot.sendMessage(chat_id, 
					'Send a phtoto of the artwork QR code.',
					)
			else:	
				self.bot.sendMessage(chat_id, "Message type not supported. Try again")


	def addChatId(self, ch_id):
		"""When a new user join the bot its chat identifier is appended at the end of
		the chatlist. If there is no chatlist, it is initialized as empty.
		
		Parameters
		----------
			ch_id : int
				Telegram user's identification number
		"""
		# Chatlist creation
		if "art_ids.json" not in os.listdir("jsons/"):
			json_obj = {"chat_ids":[]}
			json_obj = json.dumps(json_obj)
			
			with open("jsons/art_ids.json", "w") as file:
				file.write(json_obj)
			
			print ("[{}] TBOT: Chatlist created".format(
				int(time.time())
			))
			
		# Chatlist updating		
		with open("jsons/art_ids.json", "r+") as file:
			chat_list = json.loads(file.read())
			
			if ch_id not in chat_list["chat_ids"]:
				chat_list["chat_ids"].append(ch_id)
				chat_list=json.dumps(chat_list)
				file.seek(0)
				file.write(chat_list)
			
			print ("[{}] TBOT: Chatlist updated".format(
				int(time.time())
			))
	
	def sendAlerts(self, key, ch_id, *msg):
		"""Send an alert to the museum visitors when the museum is closing.
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
		if key == 'closing':
			self.bot.sendMessage(
				ch_id, 
				emoji.emojize(
					':warning: ALERT :warning:', 
					use_aliases=True
				)+\
				'\nMuseum is closing. Please head to the main exit.'
			)
			print ("[{}] TBOT: Closing alert sent to users".format(
				int(time.time())
			))


