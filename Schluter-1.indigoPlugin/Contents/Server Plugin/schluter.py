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
        self.logger = logging.getLogger(__name__)

    def get_session(self, email, password):
        self.logger.debug("get_session")
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
        self.logger.debug("get_thermostats")
        params = { 'sessionId': sessionId }
        thermostats = self._call_api("get", API_GET_THERMOSTATS_URL, params).json()
        groups = thermostats["Groups"]

        thermostat_list = []
        for group in groups:
            for thermostat in group["Thermostats"]:
                thermostat_list.append(Schluter_Thermo(thermostat))
         
        return thermostat_list
    
    def get_temperature(self, sessionId, serialNumber):
    	self.logger.debug("get_temperature")
        params = { 'sessionId': sessionId, 'serialnumber': serialNumber }
        result = self._call_api("get", API_SET_TEMPERATURE_URL, params = params).json()
        
        return result

    def set_temperature(self, sessionId, serialNumber, temperature):
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
        indigo.server.log("calling th payload")

        response = self._http_session.request(method, url, params = params, **kwargs) if\
            self._http_session is not None else\
            request(method, url, params = params, **kwargs)

        self.logger.debug("API Response received: %s - %s", response.status_code, response.content)
        indigo.server.log("API respons received")

        response.raise_for_status()
        return response
