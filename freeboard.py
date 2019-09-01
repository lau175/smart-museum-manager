#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Freeboard dashboard to perform an active and passive monitoring of environmental 
parameters of a smart museum room.
It is part of the project requested by the 'Programming for IoT Applications' course at
Politecnico di Torino, IT.

Author: Luca Gioacchini (s257076)
Academic year: 2018/19
"""

import cherrypy
import os
import json

FB_PATH = os.getcwd()
HOST = "0.0.0.0"

class WebService():
	"""WebService which exposes the freeboard dashboard. The cherrypy library provides a 
	request dispatcher. After having defined the HTTP requests methods, its body is executed
	whenever a user perform the request.
	
	Methods
	-------
	GET(*uri, **params)
		HTTP get request, it returns the freeboard page loaded from the index.html file
		stored in the freeboard/ directory
	POST(*uri, **params)
		HTTP post request, it allows to save the freeboard configuration in the 
		freeboard/dashboard/ directory
	"""
	exposed = True
	
	def GET(self, *uri, **params):
		"""When a GET HTTP request is sent from an internet browser to the IP of the device 
		hosting the webservice at the 8080 port, the freeboard html main page is displayed on
		the browser.
		
		Parameters
		----------
			*uri : tuple
				path of the HTTP ULR request
			**params : dict
				HTTP query string
		
		Returns
		-------
			str
				freeboard html page
		"""
		return open("lib/freeboard/index.html", "r").read()
	
	def POST(self, *uri, **params):
		"""When a POST HTTP request is sent to the IP of the device hosting the webservice 
		at the 8080 port, the freeboard configuration is saved in a json file stored in the
		freeboard/dashboard/ directory.
		
		Parameters
		----------
			*uri : tuple
				path of the HTTP ULR request
			**params : dict
				HTTP query string
		
		Returns
		-------
			str
				freeboard html page
		"""
		if uri[0] == "saveDashboard":
			path = "lib/freeboard/dashboard/"
			with open(path + "dashboard.json", "w") as file:
				file.write(params['json_string'])
		
#===============================
#			MAIN
#===============================

# Freeboard configuration
conf={
	# The freeboard main page is exposed at the "/" path
	"/":{
		# Method dispatcher of the cherrypy library. When an HTTP request is received
		# the dispatcher merges the request type (GET, POST, etc.) with the relative
		# method of the WebService() class.
		'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
		'tools.sessions.on': True,
		# The directory defined in the FB_PATH variable is taken as static and the
		# URI path "/" is associated to it
		'tools.staticdir.root': os.getcwd()
	},
	# The following lines are the static directories definitions associated to the relative
	# paths
	"/css":{
		'tools.staticdir.on':True,
		'tools.staticdir.dir':"lib/freeboard/css"
	},
	"/js":{
		'tools.staticdir.on':True,
		'tools.staticdir.dir':"lib/freeboard/js"
	},
	"/img":{
		'tools.staticdir.on':True,
		'tools.staticdir.dir':"lib/freeboard/img"
	},
	"/plugins":{
		'tools.staticdir.on':True,
		'tools.staticdir.dir':"lib/freeboard/plugins"
	},
	"/dashboard":{
		'tools.staticdir.on':True,
		'tools.staticdir.dir':"lib/freeboard/dashboard"
	}
}

# The WebService() class is exposed at the "/" URI path by using the configuration defined
# in the conf variable
cherrypy.tree.mount(WebService(), "/", conf)
# WebService() IP and port assignment
cherrypy.server.socket_host = HOST
cherrypy.server.socket_port = 8080
# WebService() starting
cherrypy.engine.start()
cherrypy.engine.block()
