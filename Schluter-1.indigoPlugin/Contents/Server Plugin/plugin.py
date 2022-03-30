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
import datetime, delta
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
		self.logger.info(u"Starting Schluter")
		
		self.schluter = Schluter()
		
		self.updateFrequency = float(self.pluginPrefs.get('updateFrequency', "10")) *  60.0
		self.logger.debug(u"updateFrequency = {}".format(self.updateFrequency))
		self.next_update = time.time() + self.updateFrequency
		self.update_needed = False
		
		self.authenticator = Authenticator(self.schluter, self.pluginPrefs["login"], self.pluginPrefs["password"])
		self.authentication = authenticator.authenticate()
		self.logger.debug(u"Startup authentication")

	
	def shutdown(self):
		self.logger.info(u"Stopping Schluter")
	
	def validatePrefsConfigUi(self, valuesDict):
		self.logger.debug(u"validatePrefsConfigUi called")
		authenticator = Authenticator(self.schluter, valuesDict["login"], valuesDict["password"])
		authentication = authenticator.authenticate()

		errorDict = indigo.Dict()
		
		if authentication.state.value == "bad_email":
			errorDict["login"] = "Login is invalid"
		
		if authentication.state.value == "bad_password":
			errorDict["password"] = "Password is invalid"

		updateFrequency = int(valuesDict['updateFrequency'])
		if (updateFrequency < 3) or (updateFrequency > 30):
			errorDict['updateFrequency'] = u"Update frequency is invalid - enter a valid number (between 3 and 30)"

		if len(errorDict) > 0 :
			return (False, valuesDict, errorDict)
		
		return True

	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		self.logger.debug(u"closedPrefsConfigUi called")
		if not userCancelled:
			try:
				self.logLevel = int(valuesDict[u"logLevel"])
			except:
				self.logLevel = logging.INFO
			self.indigo_log_handler.setLevel(self.logLevel)
			self.logger.debug(u"logLevel = " + str(self.logLevel))
			
			self.updateFrequency = float(valuesDict['updateFrequency']) * 60.0
			self.logger.debug(u"updateFrequency = {}".format(self.updateFrequency))
			self.next_update = time.time()
			
			self.update_needed = True
	
	########################################
	
	def runConcurrentThread(self):
		self.logger.debug(u"runConcurrentThread starting")
		try:
			while True:
				if (time.time() > self.next_update) or self.update_needed:
					self.update_needed = False
					self.next_update = time.time() + self.updateFrequency
					if self.authenticate.expires <= datetime.utcnow():
						self.authetication = authenticator.authenticate()
						self.logger.debug(u"Re-authenticating NOW"")
					
					self.logger.debug("runConcurrentThread loop iteration")

				self.sleep(60.0)
				
		except self.StopThread:
			pass
	
	########################################
	
	def serialNumberListGenerator(self, filter="", valuesDict=None, typeId="", targetId=0):
#		authenticator = Authenticator(self.schluter, self.pluginPrefs["login"], self.pluginPrefs["password"])
#		authentication = authenticator.authenticate()
		self.logger.debug(u"get serial number called")
				
		sessionID = self.authentication.session_id[0]
		
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
		self.logger.debug("testMethod called: login = {}, password = {}".format(self.pluginPrefs["login"], self.pluginPrefs["password"]))
	
	def printPluginPrefs(self):
		self.logger.debug("printPluginPrefs values: login = {}, password = {}".format(self.pluginPrefs["login"], self.pluginPrefs["password"]))
	
	def test_device_method(self):
		self.logger.debug("test_device_method called")
