#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2014, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo

import os
import sys
import logging
import time
import threading

from schluter import Schluter
from authenticator import Authenticator, Authentication

class Plugin(indigo.PluginBase):
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		self.schluter = Schluter()
	
	def startup(self):
		indigo.server.log("Starting Schluter")
	
	def shutdown(self):
		indigo.server.log("Stopping Schluter")
	
	########################################
	# Actions defined in MenuItems.xml:
	####################
	def testMethod(self):
		indigo.server.log("Test Method Log")
		output = "Test Method menu Item, login:" + self.pluginPrefs["login"] + " password:" + self.pluginPrefs["password"]
		indigo.server.log(output)
	
	def printPluginPrefs(self):
		output = "Login: " + self.pluginPrefs["login"] + " Password: " + self.pluginPrefs["password"]
		indigo.server.log(output)
	
	def test_device_method(self):
		indigo.server.log("Test Device Method Log")

	def myListGenerator(self, filter="", valuesDict=None, typeId="", targetId=0):
		authenticator = Authenticator(self.schluter, self.pluginPrefs["login"], self.pluginPrefs["password"])
		authentication = authenticator.authenticate()
		
		sessionID = authentication.session_id[0]
		
		thermostat_list = self.schluter.get_thermostats(sessionID)
		serial_numbers = []
		for thermostat in thermostat_list:
			# The UI uses a tuple for the list: (variable name, display name)
			tuple = (thermostat.serial_number, thermostat.name)
			serial_numbers.append(tuple)
		
		return serial_numbers

	def validatePrefsConfigUi(self, valuesDict):
		authenticator = Authenticator(self.schluter, valuesDict["login"], valuesDict["password"])
		authentication = authenticator.authenticate()
		
		#output = "Login:" + valuesDict["login"] + " Password:" + valuesDict["password"]
		#indigo.server.log(output)
		#output = "Authentication State: " + authentication.state.value
		#indigo.server.log(output)
		
		errorDict = indigo.Dict()
		errorDict["showAlertText"] = "Invalid Login or Password."
		
		if authentication.state.value != "authenticated":
			return (False, valuesDict, errorDict)
		
		#self.login = valuesDict["login"]
		#self.password = valuesDict["password"]
		#output = "Validate Prefs Config UI Method Log, login:" + self.login + " password:" + self.password
		#indigo.server.log(output)
		
		return True
