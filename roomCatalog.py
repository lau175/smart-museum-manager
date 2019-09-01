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
		if uri[0] == "th":		
			with open("jsons/room_catalog.json", "r") as jf:
				rc = json.load(jf) 
			rc["roomcatalog"][3]["threshold"][params["type"]]=params["val"]

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
