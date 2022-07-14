# -*- coding: utf-8 -*-

from ensurepip import version
import json
import logging
import indigo
from requests import request, Session
import threading
import requests
import temperature_scale
from schluter_thermo import Schluter_Thermo

# URL Constants
API_BASE_URL = "https://ditra-heat-e-wifi.schluter.com"
API_AUTH_URL = API_BASE_URL + "/api/authenticate/user"
API_USERACCOUNT_URL = API_BASE_URL + "/api/useraccount?sessionid="
API_GET_THERMOSTATS_URL = API_BASE_URL + "/api/thermostats"
API_SET_TEMPERATURE_URL = API_BASE_URL + "/api/thermostat"
API_APPLICATION_ID = 7

class Schluter:

#    temperatureFormatter = temperature_scale.Celsius()
    
    def __init__(self, timeout=10, command_timeout=60):
        self._timeout = timeout
        self._command_timeout = command_timeout
        self._http_session = None
        self.logger = logging.getLogger("Plugin.Schluter")

    def get_session(self, email, password):
        self.logger.debug(u"get_session called")
        response = self._call_api(
            "post", 
            API_AUTH_URL,
            params = None,
            json = { 
                'Email': email, 
                'Password': password, 
                'Application': API_APPLICATION_ID
            })
        
        return response

    def get_thermostats(self, sessionId):
        self.logger.debug(u"get_thermostats called")
        params = { 'sessionId': sessionId }
        result = self._call_api("get", API_GET_THERMOSTATS_URL, params)
        
        if result is not None:
            thermostats = result.json()
            groups = thermostats["Groups"]

            thermostat_list = []
            for group in groups:
                for thermostat in group["Thermostats"]:
                    thermostat_list.append(Schluter_Thermo(thermostat))
            
            return thermostat_list
        else:
            return None
    
    def get_temperature(self, sessionId, serialNumber):
        self.logger.debug(u"get_temperature called")
        params = { 'sessionId': sessionId, 'serialnumber': serialNumber }
        result = self._call_api("get", API_SET_TEMPERATURE_URL, params = params)
        
        return result

    def return_to_schedule(self, sessionId, serialNumber):
        self.logger.debug(u"return_to_schedule called")
        params = { 'sessionId': sessionId, 'serialnumber': serialNumber }
        json = { "RegulationMode": 1, "VacationEnabled": False}
        result = self._call_api("post", API_SET_TEMPERATURE_URL, params = params, json = json)
        
        if result is not None:
            return True
        else:
            return False

    def set_temp_next_sched(self, sessionId, serialNumber, temperature):
        self.logger.debug(u"set_temp_next_sched called")
        params = { 'sessionId': sessionId, 'serialnumber': serialNumber }
        json = { "ComfortTemperature": temperature, "ComfortEndTime": "15/07/2022 04:30:00 +00:00", "RegulationMode": 2, "VacationEnabled": False}
        result = self._call_api("post", API_SET_TEMPERATURE_URL, params = params, json = json)
        
        if result is not None:
            return True
        else:
            return False

    def set_temp_permanently(self, sessionId, serialNumber, temperature):
        self.logger.debug(u"set_temp_permanently called")
        params = { 'sessionId': sessionId, 'serialnumber': serialNumber }
        json = { 'ManualTemperature': temperature, "RegulationMode": 3, "VacationEnabled": False}
        result = self._call_api("post", API_SET_TEMPERATURE_URL, params = params, json = json)
        
        if result is not None:
            return True
        else:
            return False

    # This method will return a None object if there is a connection error
    def _call_api(self, method, url, params, **kwargs):
        payload = kwargs.get("params") or kwargs.get("json")

        if "timeout" not in kwargs:
            kwargs["timeout"] = self._timeout
        
        self.logger.debug("Calling %s with params %s and payload=%s", url, params, payload)

        try:
            response = self._http_session.request(method, url, params = params, **kwargs) if\
                self._http_session is not None else\
                request(method, url, params = params, **kwargs)
        except requests.RequestException as error:
            self.logger.error("Connection Error - Unable to connect - {}".format(error))
            return None
            #response.raise_for_status()
        
        if response is not None:
            # These won't work if response doesn't exist
            if response.status_code == requests.codes.ok:
                self.logger.debug("Response OK")
            else:
                self.logger.error("Response Error: {}".format(response.status_code))
                return None
                #response.raise_for_status()

            self.logger.debug("API Response received: %s - %s", response.status_code, response.content)
        else:
            self.logger.error("No Response - Connection Error")
            return None

        return response
    