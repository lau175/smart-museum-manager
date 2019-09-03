#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import cherrypy
import os
import json

HOST = "0.0.0.0"
PORT = 9090

class WebService():
	exposed = True
	
	def GET(self, *uri, **params):
		with open("jsons/room_catalog.json", "r") as jf:
			rc = json.load(jf) 
			rc = rc["roomcatalog"]
		if uri[0] == "broker":
			return json.dumps(rc[0])
		elif uri[0] == "interacquisition":
			return json.dumps(rc[1])
		elif uri[0] == "timetable":
			return json.dumps(rc[2])
		elif uri[0] == "th":
			return json.dumps(rc[3])
	
	def POST(self, *uri, **params):
		dev_in_rc = False
		sensor_list = []
		if uri[0] == "th":		
			with open("jsons/room_catalog.json", "r") as jf:
				rc = json.load(jf) 
			rc["roomcatalog"][3]["threshold"][params["type"]]=params["val"]

			with open("jsons/room_catalog.json", "w") as jf:
				jf.write(json.dumps(rc))
		
		elif uri[0] == "devices": 
			with open("jsons/room_catalog.json", "r") as jf:
				rc = json.load(jf)
			
			# get the sensor list from the query string
			if "_" in params["sensors"]:
				sensor_list = params["sensors"].split("_")
			else:
				sensor_list.append(params["sensors"])
			# load the devices list from the room catalog
			dev_list = rc["roomcatalog"][4]["devices"][params["board"]]
			# check if the new device is a new board
			for dev in dev_list:
				# if so, update the default board informations
				if dev["id"] == 0:
					dev["id"] = int(params["id"])
					dev["sensors"] = sensor_list
					dev_in_rc = True
					
			# if the system has already a similar board:
			if not dev_in_rc:
				# do nothing if the device has been already registered
				for dev in dev_list:
					if dev["id"] == int(params["id"]):
						dev_in_rc = True
						break
			# if the device is new:
			if not dev_in_rc:
				new_dev = {
					"id":int(params["id"]),
					"sensors":sensor_list
				}
				dev_list.append(new_dev)
			
			rc["roomcatalog"][4]["devices"][params["board"]] = dev_list
			
			with open("jsons/room_catalog.json", "w") as jf:
				jf.write(json.dumps(rc))
		
	def DELETE(self, *uri, **params):
		if uri[0] == "devices":
			with open("jsons/room_catalog.json", "r") as jf:
				rc = json.load(jf)
			
			dev_list = rc["roomcatalog"][4]["devices"][params["board"]]
			
			idx = 0
			for dev in dev_list:
				if dev["id"] == int(params["id"]):
					break
				idx+=1
					
			if len(dev_list) == 1:
				default = {
					"id":0,
					"sensors":[]
				}
				dev_list.append(default)
			dev_list.pop(idx)
			
			rc["roomcatalog"][4]["devices"][params["board"]] = dev_list
			
			with open("jsons/room_catalog.json", "w") as jf:
				jf.write(json.dumps(rc))
# __main__
conf={
	"/":{
		'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
		'tools.sessions.on': True,
	}
}

cherrypy.tree.mount(WebService(), "/", conf)
cherrypy.server.socket_host = HOST
cherrypy.server.socket_port = PORT
cherrypy.engine.start()
cherrypy.engine.block()
