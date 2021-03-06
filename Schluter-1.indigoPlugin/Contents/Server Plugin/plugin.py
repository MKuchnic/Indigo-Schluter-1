#! /usr/bin/env python3.10
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2014, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo

import os
import sys
import logging
import time
import json # For debugging
from datetime import datetime, timedelta
import threading
import temperature_scale

from schluter import Schluter
from schluter_thermo import Schluter_Thermo
from authenticator import Authenticator, Authentication, AuthenticationState

################################################################################
TEMPERATURE_SCALE_PLUGIN_PREF='temperatureScale'
TEMP_CONVERTERS = {
	'F': temperature_scale.Fahrenheit(),
	'C': temperature_scale.Celsius(),
}

################################################################################
kHvacModeEnumToStrMap = {
	indigo.kHvacMode.Cool				: u"cool",
	indigo.kHvacMode.Heat				: u"heat",
	indigo.kHvacMode.HeatCool			: u"auto",
	indigo.kHvacMode.Off				: u"off",
	indigo.kHvacMode.ProgramHeat		: u"program heat",
	indigo.kHvacMode.ProgramCool		: u"program cool",
	indigo.kHvacMode.ProgramHeatCool	: u"program auto"
}


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
		
		self.current_setpoint = 0.0
		self.display_setpoint = 0
		
		scale = self.pluginPrefs.get(TEMPERATURE_SCALE_PLUGIN_PREF, 'C')
		self.logger.debug(u'setting temperature scale to {}'.format(scale))
		self.temperatureFormatter = TEMP_CONVERTERS[scale]
		
		self.authenticator = Authenticator(self.schluter, self.pluginPrefs["login"], self.pluginPrefs["password"], self.authentication_cache)
		self.authentication = self.authenticator.authenticate()
		if self.authentication.state is AuthenticationState.CONNECTION_ERROR:
			self.logger.error("Startup Authentication = Connection Error")
		else:
			self.authentication_cache = self.authentication
			self.logger.debug("Startup Authentication = %s - %s",self.authentication.session_id,self.authentication.expires)
		self.auth_next_update = time.time() + 300.0
		self.auth_update_needed =  False

	
	def shutdown(self):
		self.logger.info(u"Stopping Schluter")
	
	def validatePrefsConfigUi(self, valuesDict):
		self.logger.debug(u"validatePrefsConfigUi called")
# 		do an authentication here to check entered values
		authenticator = Authenticator(self.schluter, valuesDict["login"], valuesDict["password"])
		authentication = authenticator.authenticate()

		errorDict = indigo.Dict()

#		use authentication state to determine errors	
		if authentication.state.value == "bad_email":
			errorDict["login"] = "Login is invalid"
		
		if authentication.state.value == "bad_password":
			errorDict["password"] = "Password is invalid"
		
		if authentication.state.value == "connection_error":
			errorDict["showAlertText"] = "Server connection error"

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
			if self.authentication.state is AuthenticationState.CONNECTION_ERROR:
				self.logger.error("Authentication = Connection Error")
			else:
				self.authentication_cache = self.authentication
			self.auth_next_update = time.time() + 300.0
			self.auth_update_needed =  False

			self.temperatureFormatter = temperature_scale.Celsius()
			scale = valuesDict[TEMPERATURE_SCALE_PLUGIN_PREF]
			self.logger.debug(u'setting temperature scale to {}'.format(scale))
			self.temperatureFormatter = TEMP_CONVERTERS[scale]

			self.logger.debug(u"updating authentication")
			
	
	########################################
	
	def runConcurrentThread(self):
		self.logger.debug(u"runConcurrentThread starting")
		try:
			while True:
#				check  if we need to re-autheticate every loop
				if (time.time() > self.auth_next_update) or self.auth_update_needed:
					self.logger.info(u"Checking authentication")
					self.authenticator = Authenticator(self.schluter, self.pluginPrefs["login"], self.pluginPrefs["password"], self.authentication_cache)
					self.authentication = self.authenticator.authenticate()
					if self.authentication.state is AuthenticationState.CONNECTION_ERROR:
						self.logger.error("Periodic Authentication = Connection Error")
					else:
						self.authentication_cache = self.authentication
						self.logger.debug("Periodic Authentication = %s - %s",self.authentication.session_id,self.authentication.expires)
					self.auth_next_update = time.time() + 300.0
					self.auth_update_needed =  False
				
				# We shouldn't do any API calls unless server connection can be established
				# This could probably be more elegant
				if self.authentication.state is not AuthenticationState.CONNECTION_ERROR:
	#				check if the interval time has passed
					if (time.time() > self.next_update) or self.update_needed:
	# 					update the schluter devices
						for dev in indigo.devices.iter("self"):
							if not dev.enabled or not dev.configured:
								continue
							self._refreshStatesFromHardware(dev, False, False)
						self.update_needed = False
						self.next_update = time.time() + self.updateFrequency

				self.sleep(1.0)
				
		except self.StopThread:
			pass
	
	
	########################################
	
	def _updateDeviceStatesList(self, dev, thermostat):
		self.logger.debug("{}: Updating device".format(dev.name))
		self.logger.debug("Device Details: id = {}, name = {}, model = {}, enabled = {}, deviceTypeId = {}, displayStateId = {}".format(dev.id, dev.name, dev.model, dev.enabled, dev.deviceTypeId, dev.displayStateId))
		
		# These were only added to check values
		#pluginProps_dict = dev.pluginProps.to_dict()
		#self.logger.debug("pluginProps = {}".format(json.dumps(dev.pluginProps.to_dict())))
		
		#states_dict = dev.states.to_dict()
		#self.logger.debug("states = {}".format(json.dumps(dev.states.to_dict())))
		
		self.logger.debug("Thermostat values: vacation_enabled = {}, is_online = {}, early_start_of_heating = {}, error_code = {}, tzoffset = {}, kwh_charge = {}, load_measured_watt = {}, thermostat.regulation_mode = {}".format(thermostat.vacation_enabled, thermostat.is_online, thermostat.early_start_of_heating, thermostat.error_code, thermostat.tzoffset, thermostat.kwh_charge, thermostat.load_measured_watt, thermostat.regulation_mode))
		
		update_list = []
		
		value = bool(thermostat.vacation_enabled)
		update_list.append({'key' : "vacation_enabled", 'value' : value})
		
		value = bool(thermostat.is_online)
		update_list.append({'key' : "is_online", 'value' : value})
		
		value = bool(thermostat.early_start_of_heating)
		update_list.append({'key' : "early_start_of_heating", 'value' : value})
		
		value = thermostat.error_code
		update_list.append({'key' : "error_code", 'value' : value})
		
		value = thermostat.tzoffset
		update_list.append({'key' : "tzoffset", 'value' : value})
		
		value = thermostat.kwh_charge
		update_list.append({'key' : "kwh_charge", 'value' : value})
		
		value = thermostat.load_measured_watt
		update_list.append({'key' : "load_measured_watt", 'value' : value})
		
		value = thermostat.regulation_mode
		update_list.append({'key' : "regulation_mode", 'value' : value})

		# added to get the mode list
		update_list.append({'key' : "hvacOperationMode", 'value' : indigo.kHvacMode.Heat})
		
		value = bool(thermostat.is_heating)
		self.logger.debug("Heating is on: %s", value)
		update_list.append({'key' : "hvacHeaterIsOn", 'value' : value})

		# _changeTempSensorValue integrated into this method
		index = 1 # Not sure if this thermostat can even have more than 1 temp sensor
		stateKey = "temperatureInput" + str(index)
		self.logger.debug("_changeTempSensorValue: value = {}, uiValue = {}".format(self.temperatureFormatter.convertFromSchluter(thermostat.temperature), self.temperatureFormatter.format(thermostat.temperature).encode('utf-8')))
		update_list.append({'key' : stateKey, 'value' : self.temperatureFormatter.convertFromSchluter(thermostat.temperature), 'uiValue' : self.temperatureFormatter.format(thermostat.temperature), 'decimalPlaces' : 1})
		
		# _changeTempSetpoint integrated into this method
		value = self.temperatureFormatter.convertFromSchluter(thermostat.display_setpoint)
		self.logger.debug("_changeTempSetpoint: value = {}, uiValue = {}".format(self.temperatureFormatter.convertFromSchluter(thermostat.display_setpoint),self.temperatureFormatter.format(thermostat.display_setpoint).encode('utf-8')))
		update_list.append({'key' : "setpointHeat", 'value' : self.temperatureFormatter.convertFromSchluter(thermostat.display_setpoint), 'uiValue' : self.temperatureFormatter.format(thermostat.display_setpoint), 'decimalPlaces' : 1})

		dev.updateStatesOnServer(update_list)
	
	########################################
	
	def _refreshStatesFromHardware(self, dev, logRefresh, commJustStarted):
		self.logger.debug("_refreshStatesFromHardware called")
		
		# TODO: Setup catch for nonexistant response
		response = self.schluter.get_temperature(self.authentication.session_id, dev.pluginProps.get("serialNumbers", False))
		
		if response is not None:
			thermostat = Schluter_Thermo(response.json())
			
			# debugging 
			self.logger.info(u"Current temp: %s", self.temperatureFormatter.format(thermostat.temperature))
			self.logger.debug(u"Current temp unformatted: %s", thermostat.temperature)
			self.logger.debug(u"is_heating: %s", thermostat.is_heating)

			# Update current stored setpoint
			self.display_setpoint = thermostat.display_setpoint
			self.logger.debug(u"display_setpoint = {}".format(self.display_setpoint))

			self._updateDeviceStatesList(dev, thermostat)
		else:
			self.logger.error(u"Server Connection Error")

	########################################
	
	def getDeviceStateList(self, dev):
		stateList = indigo.PluginBase.getDeviceStateList(self, dev)
		
		# Type:
		#  52 = Boolean
		# 100 = Number
		# 150 = String
		
		stateList.append({  "Disabled"     : False, 
							"Key"          : "vacation_enabled", 
							"StateLabel"   : "Vacation Enabled",   
							"TriggerLabel" : "Vacation Enabled",   
							"Type"         : 52 })
		stateList.append({  "Disabled"     : False, 
							"Key"          : "is_online", 
							"StateLabel"   : "Online",   
							"TriggerLabel" : "Online",   
							"Type"         : 52 })
		stateList.append({  "Disabled"     : False, 
							"Key"          : "early_start_of_heating", 
							"StateLabel"   : "Early Start of Heating",   
							"TriggerLabel" : "Early Start of Heating",   
							"Type"         : 52 })
		stateList.append({  "Disabled"     : False, 
							"Key"          : "error_code", 
							"StateLabel"   : "Error Code",   
							"TriggerLabel" : "Error Code",   
							"Type"         : 100 })
		stateList.append({  "Disabled"     : False, 
							"Key"          : "tzoffset", 
							"StateLabel"   : "TZ Offset",   
							"TriggerLabel" : "TZ Offset",   
							"Type"         : 100 })
		stateList.append({  "Disabled"     : False, 
							"Key"          : "kwh_charge", 
							"StateLabel"   : "KWH Charge",   
							"TriggerLabel" : "KWH Charge",   
							"Type"         : 100 })
		stateList.append({  "Disabled"     : False, 
							"Key"          : "load_measured_watt", 
							"StateLabel"   : "Load Measured Watt",   
							"TriggerLabel" : "Load Measured Watt",   
							"Type"         : 100 })
		stateList.append({  "Disabled"     : False, 
							"Key"          : "regulation_mode", 
							"StateLabel"   : "Regulation Mode",   
							"TriggerLabel" : "Regulation Mode",   
							"Type"         : 100 })
				
		return stateList
	
	########################################
	def deviceStartComm(self, dev):
		self._refreshStatesFromHardware(dev, True, True)
	
	########################################
	def deviceStopComm(self, dev):
		pass
	
	########################################
	
	def serialNumberListGenerator(self, filter="", valuesDict=None, typeId="", targetId=0):
		self.logger.debug(u"get serial number called")
				
		sessionID = self.authentication.session_id[0]
		
		# TODO: Setup catch for nonexistant response
		thermostat_list = self.schluter.get_thermostats(sessionID)
		serial_numbers = []
		
		if thermostat_list is not None:
			for thermostat in thermostat_list:
				# The UI uses a tuple for the list: (variable name, display name)
				tuple = (thermostat.serial_number, thermostat.name)
				serial_numbers.append(tuple)
		else:
			tuple = (00000, "ERROR")
			serial_nubmers.append(tuple)
			
		return serial_numbers
	
	def serialNumberPicked(self, valuesDict, typeId, devId):
		self.logger.debug("serialNumberPicked called")
		self.logger.debug("valuesDict = {}".format(json.dumps(valuesDict.to_dict())))
		
		valuesDict["address"] = str(valuesDict["serialNumbers"])
		
		return valuesDict
	
	########################################
	# Actions defined in MenuItems.xml:
	########################################
	
	def menuResumeProgram(self, valuesDict, typeId):
		self.logger.debug("menuResumeProgram called")
		try:
			deviceId = int(valuesDict["targetDevice"])
		except:
			self.logger.error(u"Bad Device specified for Resume Program operation")
			return False

		serialNumber = indigo.devices[deviceId].address
		self.logger.info("Resume Program for thermostat: {}".format(indigo.devices[deviceId].name))

		# TODO: Setup catch for nonexistant response
		if self.schluter.return_to_schedule(self.authentication.session_id, serialNumber) is True:
			return True
		else:
			self.logger.error(u"Server Connection Error")
			return False
	
	def printPluginPrefs(self):
		self.logger.debug("printPluginPrefs values: login = {}, password = {}".format(self.pluginPrefs["login"], self.pluginPrefs["password"]))
	
	def test_device_method(self):
		self.logger.debug("test_device_method called")

    ########################################
    # Thermostat Action callbacks
    ########################################
    
    # Main thermostat action bottleneck called by Indigo Server.
   
	def actionControlThermostat(self, action, device):
		self.logger.debug(u"{}: action.thermostatAction: {}, action.actionValue: {}, setpointHeat: {}, setpointCool: {}".format(device.name, action.thermostatAction, 
		action.actionValue, device.heatSetpoint, device.coolSetpoint))

        ###### REQUEST STATE UPDATES ######
		if action.thermostatAction in [ indigo.kThermostatAction.RequestStatusAll,
										indigo.kThermostatAction.RequestMode,
										indigo.kThermostatAction.RequestEquipmentState,
										indigo.kThermostatAction.RequestTemperatures,
										indigo.kThermostatAction.RequestHumidities,
										indigo.kThermostatAction.RequestDeadbands,
										indigo.kThermostatAction.RequestSetpoints ]:
			self.update_needed = True
		
        ###### DECREASE/INCREASE HEAT SETPOINT ######
		if action.thermostatAction == indigo.kThermostatAction.IncreaseHeatSetpoint:
			self.logger.debug(u"IncreaseHeatSetpoint: actionValue = {}".format(action.actionValue))
			self.logger.debug(u"display_setpoint = {} tempStepSchluter = {}".format(self.display_setpoint, self.temperatureFormatter.tempStepSchluter()))
			self.logger.debug(u"new setpoint: {} + {} = {}".format(self.display_setpoint, self.temperatureFormatter.tempStepSchluter(), self.display_setpoint + self.temperatureFormatter.tempStepSchluter()))
			
#			self.logger.debug(u"current_setpoint = {}".format(self.current_setpoint))
#			self.logger.debug(u"tempStep = {}".format(self.temperatureFormatter.tempStep()))			
#			self.logger.debug(u"current_setpoint = {}".format(self.current_setpoint))
#			self.logger.debug(u"self.temperatureFormatter.convertToSchluter = {}".format(self.temperatureFormatter.convertToSchluter(self.current_setpoint)))
			
			# TODO: Setup catch for nonexistant response
			if self.schluter.set_temp_next_sched(self.authentication.session_id, device.pluginProps.get("serialNumbers", False), self.display_setpoint + self.temperatureFormatter.tempStepSchluter()) is True:
				self.update_needed = True
			else:
				self.logger.error(u"Server Connection Error")
		
		elif action.thermostatAction == indigo.kThermostatAction.DecreaseHeatSetpoint:
			self.logger.debug(u"DecreaseHeatSetpoint: actionValue = {}".format(action.actionValue))
			self.logger.debug(u"display_setpoint = {} tempStepSchluter = {}".format(self.display_setpoint, self.temperatureFormatter.tempStepSchluter()))
			self.logger.debug(u"new setpoint: {} - {} = {}".format(self.display_setpoint, self.temperatureFormatter.tempStepSchluter(), self.display_setpoint - self.temperatureFormatter.tempStepSchluter()))

#			self.logger.debug(u"current_setpoint = {}".format(self.current_setpoint))
#			self.logger.debug(u"tempStep = {}".format(self.temperatureFormatter.tempStep()))
#			self.logger.debug(u"current_setpoint = {}".format(self.current_setpoint))
#			self.logger.debug(u"self.temperatureFormatter.convertToSchluter = {}".format(self.temperatureFormatter.convertToSchluter(self.current_setpoint)))
			
			# TODO: Setup catch for nonexistant response
			if self.schluter.set_temp_next_sched(self.authentication.session_id, device.pluginProps.get("serialNumbers", False), self.display_setpoint - self.temperatureFormatter.tempStepSchluter()) is True:
				self.update_needed = True
			else:
				self.logger.error(u"Server Connection Error")

		###### SET HEAT SETPOINT ######
		elif action.thermostatAction == indigo.kThermostatAction.SetHeatSetpoint:
			self.logger.debug(u"SetHeatSetpoint: actionValue = {}".format(action.actionValue))
			self.logger.debug(u"new setpoint: {}".format(self.temperatureFormatter.convertToSchluter(action.actionValue)))
			
#			self.logger.debug(u"current_setpoint = {}".format(self.current_setpoint))
#			self.logger.debug(u"current_setpoint = {}".format(self.current_setpoint))
#			self.logger.debug(u"self.temperatureFormatter.convertToSchluter = {}".format(self.temperatureFormatter.convertToSchluter(self.current_setpoint)))

			# TODO: Setup catch for nonexistant response
			if self.schluter.set_temp_next_sched(self.authentication.session_id, device.pluginProps.get("serialNumbers", False), self.temperatureFormatter.convertToSchluter(action.actionValue)) is True:
				self.update_needed = True
			else:
				self.logger.error(u"Server Connection Error")

	########################################
	# Resume Program callbacks
	########################################

	def actionResumeProgram(self, action, device):
		self.logger.info(u"Resume Program for thermostat: {}".format(device.name))
		
		# TODO: Setup catch for nonexistant response
		if self.schluter.return_to_schedule(self.authentication.session_id, device.pluginProps.get("serialNumbers", False)) is False:
			self.logger.error(u"Server Connection Error")

	def pickThermostat(self, filter=None, valuesDict=None, typeId=0):
		self.logger.debug(u"pickThermostat")
		retList = []
		for device in indigo.devices.iter("self"):
			if device.deviceTypeId == 'SchluterThermostat':
				retList.append((device.id, device.name))
				self.logger.debug(u"device.id {}  device.name {}".format(device.id, device.name))
		retList.sort(key=lambda tup: tup[1])
		return retList

	def actionSetTemperature(self, action, device):
		self.logger.debug(u"{}: actionSetTemperature".format(device.name))
		tempValue = self.temperatureFormatter.convertToSchluter(int(action.props.get("temperatureValue")))
		holdType = action.props.get("holdType")
		self.logger.debug(u"tempValue {}  holdType {}".format(tempValue, holdType))

		if (tempValue < 500) or (tempValue > 4000):
				return False
		
		if holdType == "nextTransition":
			# TODO: Setup catch for nonexistant response
			if self.schluter.set_temp_next_sched(self.authentication.session_id, device.pluginProps.get("serialNumbers", False), tempValue) is False:
				self.logger.error(u"Server Connection Error")
				return False
		else:
			# TODO: Setup catch for nonexistant response
			if self.schluter.set_temp_permanently(self.authentication.session_id, device.pluginProps.get("serialNumbers", False), tempValue) is False:
				self.logger.error(u"Server Connection Error")
				return False
		return True

