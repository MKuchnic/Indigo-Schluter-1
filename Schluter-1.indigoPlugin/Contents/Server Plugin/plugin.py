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
from datetime import datetime, timedelta
import threading

from schluter import Schluter
from schluter_thermo import Schluter_Thermo
from authenticator import Authenticator, Authentication, AuthenticationState

class Plugin(indigo.PluginBase):
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t[%(levelname)8s] %(name)20s.%(funcName)-25s%(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.plugin_file_handler.setFormatter(pfmt)

		self.logLevel = int(self.pluginPrefs.get(u"logLevel", logging.INFO))
		self.indigo_log_handler.setLevel(self.logLevel)
		self.logger.debug(u"logLevel = {}".format(self.logLevel))
		
		self.authentication_cache = Authentication(AuthenticationState.REQUIRES_AUTHENTICATION, None, None)
		
	def startup(self):
		self.logger.info(u"Starting Schluter")
		
		self.schluter = Schluter()
		
		self.updateFrequency = float(self.pluginPrefs.get('updateFrequency', "10")) *  60.0
		self.logger.debug(u"updateFrequency = {}".format(self.updateFrequency))
		self.next_update = time.time() + self.updateFrequency
		self.update_needed = False
		
		self.authenticator = Authenticator(self.schluter, self.pluginPrefs["login"], self.pluginPrefs["password"], self.authentication_cache)
		self.authentication = self.authenticator.authenticate()
		self.authentication_cache = self.authentication
		self.logger.debug("Startup Authentication = %s - %s",self.authentication.session_id,self.authentication.expires)

	
	def shutdown(self):
		self.logger.info(u"Stopping Schluter")
	
	def validatePrefsConfigUi(self, valuesDict):
		self.logger.debug(u"validatePrefsConfigUi called")
# 		do an authentication here to check entered values
		authenticator = Authenticator(self.schluter, valuesDict["login"], valuesDict["password"])
		authentication = authenticator.authenticate()
#		self.authentication_cache = authentication

		errorDict = indigo.Dict()

#		use authentication state to determine errors	
		if authentication.state.value == "bad_email":
			errorDict["login"] = "Login is invalid"
		
		if authentication.state.value == "bad_password":
			errorDict["password"] = "Password is invalid"

#		validate range for update interval
		updateFrequency = int(valuesDict['updateFrequency'])
		if (updateFrequency < 3) or (updateFrequency > 60):
			errorDict['updateFrequency'] = "Update frequency is invalid - enter a valid number (between 3 and 60)"

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
			
			self.authenticator = Authenticator(self.schluter, valuesDict["login"], valuesDict["password"])
			self.authentication = self.authenticator.authenticate()
			self.authentication_cache = self.authentication

			self.logger.debug(u"updating authentication")
			
	
	########################################
	
	def runConcurrentThread(self):
		self.logger.debug(u"runConcurrentThread starting")
		try:
			while True:
#				check  if we need to re-autheticate every loop
				self.logger.info(u"Re-authenticating")
				self.authenticator = Authenticator(self.schluter, self.pluginPrefs["login"], self.pluginPrefs["password"], self.authentication_cache)
				self.authentication = self.authenticator.authenticate()
				self.authentication_cache = self.authentication
				self.logger.debug("Periodic Authentication = %s - %s",self.authentication.session_id,self.authentication.expires)
				
#				check if the interval time has passed
				if (time.time() > self.next_update) or self.update_needed:
# 					update the schluter devices
					for dev in indigo.devices.iter("self"):
						if not dev.enabled or not dev.configured:
							continue
						self._refreshStatesFromHardware(dev, False, False)
					self.update_needed = False
					self.next_update = time.time() + self.updateFrequency

#				debug checking 
				tempthermo = self.schluter.get_temperature(self.authentication.session_id, 954095)
				self.logger.info(u"Current temp: %s %s",tempthermo.temperature, u"°C")
				self.logger.debug("runConcurrentThread loop iteration")

				self.sleep(60.0)
				
		except self.StopThread:
			pass
	
	########################################
	
	def _changeTempSensorValue(self, dev, index, value):
		stateKey = "temperatureInput" + str(index)
		uiValue = "%.1f °C" % (value)
		self.logger.debug("_changeTempSensorValue: value = {}, uiValue = {}".format(value, uiValue))
		dev.updateStateOnServer(stateKey, value, uiValue="%.1f °C" % (value), decimalPlaces=1)
	
	########################################
	
	def _refreshStatesFromHardware(self, dev, logRefresh, commJustStarted):
		self.logger.debug("_refreshStatesFromHardware called")
		
		thermostat = self.schluter.get_temperature(self.authentication.session_id, dev.pluginProps.get("serialNumbers", False))
		
		self._changeTempSensorValue(dev, 1, thermostat.temperature)
	
	########################################
	
	def deviceStartComm(self, dev):
		self._refreshStatesFromHardware(dev, True, True)
	
	def deviceStopComm(self, dev):
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
