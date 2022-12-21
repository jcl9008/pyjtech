import functools
import logging
import urllib.parse
import urllib.request
from functools import wraps
from threading import RLock

_LOGGER = logging.getLogger(__name__)

TIMEOUT = 2 # Number of seconds before operation timeout

class ZoneStatus(object):
    def __init__(self,
                 zone: int,
                 power: bool,
                 av: int):
        self.zone = zone
        self.power = power
        self.av = av

    # VidSta=O1ON&O2ON&O3ON&O4ON&O5ON&O6ON&O7ON&O8ON&O1I2&O2I7&O3I4&O4I8&O5I4&O6I8&O7I7&O8I4
    @classmethod
    def from_string(cls, zone: int, string: str):
        if not string:
            return None

        if not string.startswith("VidSta="):
            return None
        
        package = string[7:].split("&")

        #print(package)

        statusPower = [None]*9
        statusAV = [None]*9

        for key in package:
            i = int(key[1:][:1])
            if "I" in key:
                val = int(key[3:])
                statusAV[i] = val
            if "I" not in key:
                val = key[2:]
                if val == "ON":
                    statusPower[i] = True
                if val == "OFF":
                    statusPower[i] = False
        
        #print(statusAV)
        #print(statusPower)

        return ZoneStatus(zone, statusPower[zone], statusAV[zone])

class Jtech(object):
    """
    jtech matrix interface
    """

    def zone_status(self, zone: int):
        """
        Get the structure representing the status of the zone
        :param zone: zone 1..8
        :return: status of the zone or None
        """
        raise NotImplemented()

    def set_zone_power(self, zone: int, power: bool):
        """
        Turn zone on or off
        :param zone: Zone 1-8
        :param power: True to turn on, False to turn off
        """
        raise NotImplemented()

    def set_zone_source(self, zone: int, source: int):
        """
        Set source for zone
        :param zone: Zone 1-8
        :param source: integer from 1-8
        """
        raise NotImplemented()

    def set_all_zone_source(self, source: int):
        """
        Set source for all zones
        :param source: integer from 1-8
        """
        raise NotImplemented()

# Helpers

def _format_zone_status_request(zone: int) -> bytes:
    return 'Status{}.\r'.format(zone).encode()

def _format_set_zone_power(zone: int, power: bool) -> bytes:
    #http://10.0.0.7/TimSendCmd.CGI?button=O7OFF
    return '{}{}.\r'.format(zone, '@' if power else '$').encode()

def _format_set_zone_source(zone: int, source: int) -> bytes:
    #http://10.0.0.7/TimSendCmd.CGI?button=O1I1
    source = int(max(1, min(source,8)))
    return '{}B{}.\r'.format(source, zone).encode()

def _format_set_all_zone_source(source: int) -> bytes:
    source = int(max(1, min(source,8)))
    return '{}All.\r'.format(source).encode()

def get_jtech(url):
    """
    Return synchronous version of Jtech interface
    :param url: IP of the matrix, i.e. '10.0.0.7'
    :return: synchronous implementation of Jtech interface
    """
    lock = RLock()

    def synchronized(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return wrapper

    class JtechSync(Jtech):
        def __init__(self, url):
            """
            Initialize the client.
            """
            self.url = url

        def _process_request(self, request: bytes, zone=None, power=None, av=None):
            """
            Send data to socket
            :param request: request that is sent to the jtech
            :param skip: number of bytes to skip for end of transmission decoding
            :return: ascii string returned by jtech
            """
            _LOGGER.debug('Sending "%s"', self.url)

            #print(zone)
            #print(power)
            #print(av)

            values = {}

            url = 'http://' + self.url

            if zone is None:
                url += '/VIDDivSta.CGI'
            else:
                #http://10.0.0.7/TimSendCmd.CGI?button=O7ON
                if power is True:
                    values = {'button' : "O" + str(zone) + "ON"}
                #http://10.0.0.7/TimSendCmd.CGI?button=O7OFF
                if power is False:
                    values = {'button' : "O" + str(zone) + "OFF"}
                #http://10.0.0.7/TimSendCmd.CGI?button=O7I7
                if av is not None:
                    values = {'button' : "O" + str(zone) + "I" + str(av)}
                url += '/TimSendCmd.CGI'
            data = urllib.parse.urlencode(values)
            data = data.encode('ascii') # data should be bytes
            self.req = urllib.request.Request(url, data)

            #print('sending url', url)
            #print('sending values', values) 
            #print(data)
            response = ''

            with urllib.request.urlopen(self.req, timeout = TIMEOUT) as resp:
                response = resp.read()

            response = response.decode("utf-8") 

            #print('received', response)

            return response

        @synchronized
        def zone_status(self, zone: int):
            # Returns status of a zone
            return ZoneStatus.from_string(zone, self._process_request(_format_zone_status_request(zone), zone=None, power=None, av=None))

        @synchronized
        def set_zone_power(self, zone: int, power: bool):
            # Set zone power
            self._process_request(_format_set_zone_power(zone, power), zone=zone, power=power, av=None)

        @synchronized
        def set_zone_source(self, zone: int, source: int):
            # Set zone source
            self._process_request(_format_set_zone_source(zone, source), zone=zone, power=None, av=source)

        @synchronized
        def set_all_zone_source(self, source: int):
            for i in range(8):
                # Set all zones to one source
                self._process_request(_format_set_all_zone_source(source), zone=i+1, power=None, av=source)
        
    return JtechSync(url)

