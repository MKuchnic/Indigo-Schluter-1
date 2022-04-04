FORMAT_STRING = "{0:.1f}"

class TemperatureScale:

    def report(self, dev, stateKey, reading):
        dev.updateStateOnServer(key=stateKey, value=self.convertFromSchuter(reading), decimalPlaces=1, uiValue=self.format(reading))
        return txt

    def format(self, reading):
        return u"%s%s" % (FORMAT_STRING.format(self.convertFromSchluter(reading)), self.suffix())


class Fahrenheit(TemperatureScale):

    # convertFromSchluter() methods input the Schuter temperature value (convert to C x 100) and output the rounded to the nearest 0.5 converted value for the class
    def convertFromSchuter(self, reading):
        return round(((((reading / 100.0) * 9) / 5) + 32) * 2.0) / 2.0
        
    # convertToSchuter() methods input the temperature value in the current scale and output the Schluter value int(convert to C x 100)
    def convertToSchuter(self, reading):
        return int((((reading - 32) * 5) / 9) * 100)
        
    def suffix(self):
        return u"F"
        
class Celsius(TemperatureScale):

    # convertFromSchluter() methods input the Schuter temperature value (C x 100) and output the rounded to the nearest 0.5 converted value for the class
    def convertFromSchuter(self, reading):
        return round((reading / 100.0) * 2.0) / 2.0
        
    # convertToSchuter() methods input the temperature value in the current scale and output the Schluter value int(C x 100)
    def convertToSchuter(self, reading):
        return int(reading * 100)
        
    def suffix(self):
        return u"C"
        
