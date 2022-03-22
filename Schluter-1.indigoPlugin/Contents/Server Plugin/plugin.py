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

	########################################
	# Actions defined in MenuItems.xml:
	####################
	def testMethod(self):
		indigo.server.log("Test Method Log")

	def validatePrefsConfigUi(self, valuesDict):
		#output = "Validate Prefs Config UI Method Log, Values:" + valuesDict
		indigo.server.log("Validate Prefs Config UI Method Log")
		#indigo.server.log(output)
		
		return True