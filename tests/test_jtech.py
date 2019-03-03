import unittest

from pyjtech import (get_jtech, get_async_jtech, ZoneStatus)
from tests import (create_dummy_port, create_dummy_socket)
import asyncio


class TestZoneStatus(unittest.TestCase):

    def test_zone_status_broken(self):
        self.assertIsNone(ZoneStatus.from_string(None, None))
        self.assertIsNone(ZoneStatus.from_string(1, 'VA: 09-<01\r'))
        self.assertIsNone(ZoneStatus.from_string(10, '\r\n\r\n'))

class TestJtech(unittest.TestCase):
    def setUp(self):
        self.responses = {}
        self.jtech = get_jtech(create_dummy_port(self.responses))

    def test_zone_status(self):
        self.responses[b'Status1.\r'] = b'AV: 02->01\r\nIR: 02->01\r'
        status = self.jtech.zone_status(1)
        self.assertEqual(1, status.zone)
        self.assertTrue(status.power)
        self.assertEqual(2, status.av)
        self.assertEqual(2, status.ir)
        self.assertEqual(0, len(self.responses))


    def test_set_zone_power(self):
        self.responses[b'1@.\r'] = b'01 Open.\r'
        self.jtech.set_zone_power(1, True)
        self.responses[b'1@.\r'] = b'01 Open.\r'
        self.jtech.set_zone_power(1, 'True')
        self.responses[b'1@.\r'] = b'01 Open.\r'
        self.jtech.set_zone_power(1, 1)
        self.responses[b'1$.\r'] = b'01 Closed.\r'
        self.jtech.set_zone_power(1, False)
        self.responses[b'1$.\r'] = b'01 Closed.\r'
        self.jtech.set_zone_power(1, None)
        self.responses[b'1$.\r'] = b'01 Closed.\r'
        self.jtech.set_zone_power(1, 0)
        self.responses[b'1$.\r'] = b'01 Closed.\r'
        self.jtech.set_zone_power(1, '')
        self.assertEqual(0, len(self.responses))

    def test_set_zone_source(self):
        self.responses[b'1B1.\r'] = b'AV:01->01\r'
        self.jtech.set_zone_source(1,1)
        self.responses[b'8B1.\r'] = b'AV:08->05\r'
        self.jtech.set_zone_source(1,100)
        self.responses[b'1B1.\r'] = b'AV:01->01\r'
        self.jtech.set_zone_source(1,-100)
        self.responses[b'2B2.\r'] = b'AV:02->02\r'
        self.jtech.set_zone_source(2,2)
        self.assertEqual(0, len(self.responses))

    def test_set_all_zone_source(self):
        self.responses[b'1All.\r'] = b'01 To All.\r'
        self.jtech.set_all_zone_source(1)
        self.assertEqual(0, len(self.responses))

    def test_timeout(self):
        with self.assertRaises(serial.SerialTimeoutException):
           self.jtech.set_zone_source(6,6)

class TestAsyncJtech(TestJtech):

    def setUp(self):
        self.responses = {}
        loop = asyncio.get_event_loop()
        jtech = loop.run_until_complete(get_async_jtech(create_dummy_port(self.responses), loop))

        # Dummy jtech that converts async to sync
        class DummyJtech():
            def __getattribute__(self, item):
                def f(*args, **kwargs):
                    return loop.run_until_complete(jtech.__getattribute__(item)(*args, **kwargs))
                return f
        self.jtech = DummyJtech()

    def test_timeout(self):
        with self.assertRaises(asyncio.TimeoutError):
            self.jtech.set_zone_source(6, 6)

if __name__ == '__main__':
   unittest.main()
