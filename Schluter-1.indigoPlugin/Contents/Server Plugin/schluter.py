from ensurepip import version
import json
import logging
import indigo
from requests import request, Session
import requests
from schluter_thermo import Schluter_Thermo

# URL Constants
API_BASE_URL = "https://ditra-heat-e-wifi.schluter.com"
API_AUTH_URL = API_BASE_URL + "/api/authenticate/user"
API_USERACCOUNT_URL = API_BASE_URL + "/api/useraccount?sessionid="
API_GET_THERMOSTATS_URL = API_BASE_URL + "/api/thermostats"
API_SET_TEMPERATURE_URL = API_BASE_URL + "/api/thermostat"
API_APPLICATION_ID = 7


class Schluter:
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
        thermostats = self._call_api("get", API_GET_THERMOSTATS_URL, params).json()
        groups = thermostats["Groups"]

        thermostat_list = []
        for group in groups:
            for thermostat in group["Thermostats"]:
                thermostat_list.append(Schluter_Thermo(thermostat))
         
        return thermostat_list
    
    def get_temperature(self, sessionId, serialNumber):
        self.logger.debug(u"get_temperature called")
        params = { 'sessionId': sessionId, 'serialnumber': serialNumber }
        result = self._call_api("get", API_SET_TEMPERATURE_URL, params = params).json()
        
        return result

    def add_temp_scale(self, dict1):
#       adding tempscale to the object
        if dict1["MaxTemp"]/100 == 40:
            dict2 = {'TempScale':'C'}
        else:
            dict2 = {'TempScale':'F'}
        dict1 = dict1 | dict2
        return dict1

    def return_to_schedule(self, sessionId, serialNumber):
        params = { 'sessionId': sessionId, 'serialnumber': serialNumber }
        json = { "RegulationMode": 1, "VacationEnabled": False}
        result = self._call_api("post", API_SET_TEMPERATURE_URL, params = params, json = json).json()

        return result["Success"]

    def set_temp_next_sched(self, sessionId, serialNumber, temperature):
        modifiedTemp = int(temperature * 100)
        params = { 'sessionId': sessionId, 'serialnumber': serialNumber }
        json = { "ComfortTemperature": modifiedTemp, "RegulationMode": 2, "VacationEnabled": False}
        result = self._call_api("post", API_SET_TEMPERATURE_URL, params = params, json = json).json()

        return result["Success"]

    
    def set_temp_permanently(self, sessionId, serialNumber, temperature):
        modifiedTemp = int(temperature * 100)
        params = { 'sessionId': sessionId, 'serialnumber': serialNumber }
        json = { 'ManualTemperature': modifiedTemp, "RegulationMode": 3, "VacationEnabled": False}
        result = self._call_api("post", API_SET_TEMPERATURE_URL, params = params, json = json).json()
        
        return result["Success"]

    def _call_api(self, method, url, params, **kwargs):
        payload = kwargs.get("params") or kwargs.get("json")

        if "timeout" not in kwargs:
            kwargs["timeout"] = self._timeout
        
        self.logger.debug("Calling %s with payload=%s", url, payload)

        response = self._http_session.request(method, url, params = params, **kwargs) if\
            self._http_session is not None else\
            request(method, url, params = params, **kwargs)

        self.logger.debug("API Response received: %s - %s", response.status_code, response.content)

        response.raise_for_status()
        return response
