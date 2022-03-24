#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2014, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo

import os
import sys

class Plugin(indigo.PluginBase):
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		self.login = ""
		self.password = ""

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
		return myArray

	def validatePrefsConfigUi(self, valuesDict):
		self.login = valuesDict["login"]
		self.password = valuesDict["password"]
		output = "Validate Prefs Config UI Method Log, login:" + self.login + " password:" + self.password
		indigo.server.log(output)
		
		return True
