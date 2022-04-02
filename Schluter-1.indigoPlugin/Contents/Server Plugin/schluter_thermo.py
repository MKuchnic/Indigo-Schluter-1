class Schluter_Thermo():
    def __init__(self, data):
        self._serial_number = data["SerialNumber"]
        self._name = data["Room"]
        self._group_id = data["GroupId"]
        self._group_name = data["GroupName"]
        self._temperature = data["Temperature"]
        self._set_point_temp = data["SetPointTemp"]
        self._regulation_mode = data["RegulationMode"]
        self._vacation_enabled = data["VacationEnabled"]
        self._vacation_begin_day = data["VacationBeginDay"]
        self._vacation_end_day = data["VacationEndDay"]
        self._vacation_temperature = data["VacationTemperature"]
        self._comfort_temperature = data["ComfortTemperature"]
        self._comfort_end_time = data["ComfortEndTime"]
        self._manual_temp = data["ManualTemperature"]
        self._is_online = data["Online"]
        self._is_heating = data["Heating"]
        self._max_temp = data["MaxTemp"]
        self._min_temp = data["MinTemp"]
        self._temp_scale = "K"
        self._tzoffset = data["TZOffset"]
        self._kwh_charge = data["KwhCharge"]
        self._load_measured_watt = data["LoadMeasuredWatt"]
        self._sw_version = data["SWVersion"]
    
    @property
    def serial_number(self):
        return self._serial_number
        
    @property
    def name(self):
        return self._name
    
    @property
    def group_id(self):
        return self._group_id
    
    @property
    def group_name(self):
        return self._group_name
    
    @property
    def temperature(self):
        return round((self._temperature / 100.0) * 2.0) / 2.0 

    @property
    def set_point_temp(self):
        return round((self._set_point_temp / 100.0) * 2.0) / 2.0 
    
    @property
    def regulation_mode(self):
        return self._regulation_mode

    @property
    def vacation_enabled(self):
        return self._vacation_enabled
    
    @property
    def vacation_begin_day(self):
        return self._vacation_begin_day

    @property
    def vacation_end_day(self):
        return self._vacation_end_day

    @property
    def vacation_temperature(self):
        return round((self._vacation_temperature / 100) * 2.0) / 2.0

    @property
    def comfort_temperature(self):
        return round((self._comfort_temperature / 100) * 2.0) / 2.0

    @property
    def comfort_end_time(self):
        return self._comfort_end_time

    @property
    def manual_temp(self):
        return round((self._manual_temp / 100) * 2.0) / 2.0
    
    @property
    def is_online(self):
        return self._is_online
    
    @property
    def is_heating(self):
        return self._is_heating
    
    @property
    def max_temp(self):
        return round((self._max_temp / 100) * 2.0) / 2.0
    
	@property
	def min_temp(self):
		return round((self._min_temp / 100) * 2.0) / 2.0
    
    @property
    def temp_scale(self):
    	if self._max_temp == 4000 :
    		self._temp_scale = "C"
    	else :
    		self._temp_scale = "F"
    	return self._temp_scale

#	@property
#	def min_temp(self):
#		return round((self._min_temp / 100) * 2.0) / 2.0
#
#        
#	@property
#	def temp_scale(self):
#		if self._max_temp == 4000 :
#			self._temp_scale = "C"
#		else :
#			self._temp_scale = "F"
		return self._min_temp

    @property
    def tzoffset(self):
        return self._tzoffset

    @property
    def kwh_charge(self):
        return self._kwh_charge

    @property
    def load_measured_watt(self):
        return self._load_measured_watt

    @property
    def sw_version(self):
        return self._sw_version
