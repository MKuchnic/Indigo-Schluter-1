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
		pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t[%(levelname)8s] %(name)20s.%(funcName)-25s%(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.plugin_file_handler.setFormatter(pfmt)

		self.logLevel = int(self.pluginPrefs.get(u"logLevel", logging.INFO))
		self.indigo_log_handler.setLevel(self.logLevel)
		self.logger.debug(u"logLevel = {}".format(self.logLevel))
		
	def startup(self):
		indigo.server.log("Starting Schluter")
		
		self.schluter = Schluter()
		
		self.updateFrequency = float(self.pluginPrefs.get('updateFrequency', "15")) *  60.0
		self.next_update = time.time() + self.updateFrequency
		
		self.update_needed = False
	
	def shutdown(self):
		indigo.server.log("Stopping Schluter")
	
	def validatePrefsConfigUi(self, valuesDict):
		authenticator = Authenticator(self.schluter, valuesDict["login"], valuesDict["password"])
		authentication = authenticator.authenticate()
		self.logger.debug(u"validatePrefsConfigUi called")
		errorDict = indigo.Dict()
		
		errorDict = indigo.Dict()
		errorDict["showAlertText"] = "Invalid Login or Password."
		
		if authentication.state.value != "authenticated":
			errorDict["showAlertText"] = "Invalid Login or Password."

		updateFrequency = int(valuesDict['updateFrequency'])
		if (updateFrequency < 3) or (updateFrequency > 60):
			errorDict['updateFrequency'] = u"Update frequency is invalid - enter a valid number (between 3 and 60)"

		if len(errorDict) > 0 :
			return (False, valuesDict, errorDict)
		
		return True
	
	########################################
	
	def runConcurrentThread(self):
		try:
			while True:
				if (time.time() > self.next_update) or self.update_needed:
					self.update_needed = False
					self.next_update = time.time() + self.updateFrequency
					
					indigo.server.log("Schluter - Periodic Update")

				self.sleep(60.0)
				
		except self.StopThread:
			pass
	
	########################################
	
	def serialNumberListGenerator(self, filter="", valuesDict=None, typeId="", targetId=0):
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
	
	########################################
	# Actions defined in MenuItems.xml:
	########################################
	
	def testMethod(self):
		indigo.server.log("Test Method Log")
		output = "Test Method menu Item, login:" + self.pluginPrefs["login"] + " password:" + self.pluginPrefs["password"]
		indigo.server.log(output)
	
	def printPluginPrefs(self):
		output = "Login: " + self.pluginPrefs["login"] + " Password: " + self.pluginPrefs["password"]
		indigo.server.log(output)
	
	def test_device_method(self):
		indigo.server.log("Test Device Method Log")