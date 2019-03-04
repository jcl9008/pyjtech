import functools
import logging
import re
import socket
from functools import wraps
from threading import RLock

_LOGGER = logging.getLogger(__name__)
ZONE_PATTERN_ON = re.compile('\D\D\D\s(\d\d)\D\D\d\d\s\s\D\D\D\s(\d\d)\D\D\d\d\s')
ZONE_PATTERN_OFF = re.compile('\D\D\DOFF\D\D\d\d\s\s\D\D\D\D\D\D\D\D\d\d\s')
EOL = b'\r'
LEN_EOL = len(EOL)
TIMEOUT = 2 # Number of seconds before operation timeout
SOCKET_RECV = 2048

class ZoneStatus(object):
    def __init__(self,
                 zone: int,
                 power: bool,
                 av: int,
                 ir: int):
        self.zone = zone
        self.power = power
        self.av = av
        self.ir = ir

    @classmethod
    def from_string(cls, zone: int, string: str):
        if not string:
            return None
        match_on = re.search (ZONE_PATTERN_ON, string)
        if not match_on:
            match_off = re.search (ZONE_PATTERN_OFF, string)
            if not match_off:
                return None
            return ZoneStatus(zone,0,None,None)
        return ZoneStatus(zone,1,*[int(m) for m in match_on.groups()])

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
    return '{}{}.\r'.format(zone, '@' if power else '$').encode()

def _format_set_zone_source(zone: int, source: int) -> bytes:
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
            self.host = url
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(TIMEOUT)
            self.socket.connect((self.host, 80))

            # Clear login message
            self.socket.recv(SOCKET_RECV)

        def _process_request(self, request: bytes, skip=0):
            """
            Send data to socket
            :param request: request that is sent to the jtech
            :param skip: number of bytes to skip for end of transmission decoding
            :return: ascii string returned by jtech
            """
            _LOGGER.debug('Sending "%s"', request)

            self.socket.send(request)

            response = ''

            while True:

                data = self.socket.recv(SOCKET_RECV)
                response += data.decode('ascii')
                
                if EOL in data and len(response) > skip:
                    break

            return response

        @synchronized
        def zone_status(self, zone: int):
            # Returns status of a zone
            return ZoneStatus.from_string(zone, self._process_request(_format_zone_status_request(zone), skip=20))

        @synchronized
        def set_zone_power(self, zone: int, power: bool):
            # Set zone power
            self._process_request(_format_set_zone_power(zone, power))

        @synchronized
        def set_zone_source(self, zone: int, source: int):
            # Set zone source
            self._process_request(_format_set_zone_source(zone, source))

        @synchronized
        def set_all_zone_source(self, source: int):
            # Set all zones to one source
            self._process_request(_format_set_all_zone_source(source))

    return JtechSync(url)

