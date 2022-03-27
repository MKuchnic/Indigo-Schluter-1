#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2014, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo

import os
import sys
from schluter import Schluter

class Plugin(indigo.PluginBase):
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		self.login = ""
		self.password = ""
		self.schluter = Schluter()

	########################################
	# Actions defined in MenuItems.xml:
	####################
	def testMethod(self):
		indigo.server.log("Test Method Log")
		output = "Validate Prefs Config UI Method Log, login:" + self.login + " password:" + self.password
		indigo.server.log(output)
		
	def test_device_method(self):
		indigo.server.log("Test Device Method Log")

	def myListGenerator(self, filter="", valuesDict=None, typeId="", targetId=0):
		myArray = [("option1", "First Option"),("option2","Second Option")]
		
		response = schluter.get_session("mkuchnic@shaw.ca", "4G@mgTPU+)3A")
		output = response.json()
		sessionID = output['SessionId']
		
		thermostat_list = schluter.get_thermostats(sessionID)
		serial_numbers = []
		for thermostat in thermostat_list:
			tuple = (thermostat.serial_number, thermostat.serial_number)
			serial_numbers.append(tuple)
		
		return serial_numbers

	def validatePrefsConfigUi(self, valuesDict):
		self.login = valuesDict["login"]
		self.password = valuesDict["password"]
		output = "Validate Prefs Config UI Method Log, login:" + self.login + " password:" + self.password
		indigo.server.log(output)
		
		return True
