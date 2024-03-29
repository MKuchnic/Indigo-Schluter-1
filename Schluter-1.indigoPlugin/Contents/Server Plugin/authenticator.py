# -*- coding: utf-8 -*-
import os
import json
import logging
import indigo
from enum import Enum
from datetime import datetime, timedelta


class AuthenticationState(Enum):
    REQUIRES_AUTHENTICATION = "requires_authentication"
    AUTHENTICATED = "authenticated"
    BAD_EMAIL = "bad_email"
    BAD_PASSWORD = "bad_password"
    CONNECTION_ERROR = "connection_error"

class Authentication:
    def __init__(self, state, session_id = None, expires = None):
        self._state = state
        self._session_id = session_id,
        self._expires = expires
    
    @property
    def session_id(self):
        return self._session_id

    @property
    def expires(self):
        return self._expires

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

class Authenticator:

    def __init__(self, api, email, password, authentication_cache):
        self._api = api
        self._email = email
        self._password = password
        self._authentication = authentication_cache
        self.logger = logging.getLogger("Plugin.Authenticator")
        
        if self._authentication == None :
            self._authentication = Authentication(AuthenticationState.REQUIRES_AUTHENTICATION)
            return
        
        if self._authentication.state == AuthenticationState.AUTHENTICATED :
            token_expired = self._authentication.expires - datetime.utcnow()
            self.logger.debug("Checking token expiry")
            if token_expired < timedelta(minutes=5):
                self.logger.debug("Token has expired.")
                self._authentication = Authentication(AuthenticationState.REQUIRES_AUTHENTICATION)
            return

        self._authentication = Authentication(AuthenticationState.REQUIRES_AUTHENTICATION)

    def authenticate(self):
        self.logger.debug("authenticate called")
        if self._authentication.state == AuthenticationState.AUTHENTICATED:
            self.logger.debug("Exiting authenticate - authentication still valid")
            return self._authentication
        
        response = self._api.get_session(self._email, self._password)

        if response is not None:
            data = response.json()
            session_id = data["SessionId"]
            expires = datetime.utcnow() + timedelta(hours=1)

            if data["ErrorCode"] == 2:
                state = AuthenticationState.BAD_PASSWORD
                self.logger.error("Authenticate - Bad Password")
            elif data["ErrorCode"] == 1:
                state = AuthenticationState.BAD_EMAIL
                self.logger.error("Authenticate - Bad Email")
            else:
                state = AuthenticationState.AUTHENTICATED
                self.logger.info("Authentication Successful")
        
            self._authentication = Authentication(state, session_id, expires)
        else:
            self.logger.error("Authenticate - Connection Error")
            self._authentication = Authentication(AuthenticationState.CONNECTION_ERROR, None, None)

        return self._authentication
