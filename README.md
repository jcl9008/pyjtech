
# pyjtech
Python3 interface implementation for J-Tech Digital HDMI 2.0 Matrix JTECH-8X8-H20. Also sold by No Hassle AV as the 4K HDMI Matrix 8x8, HDCP2.2. Originally cloned from pyblackbird for the monoprice matrix.

## Notes
This is for use with [Home-Assistant](http://home-assistant.io)
Only supports IP communication with the matrix at this time (not serial).
May not be compatible with the new version of the No Hassle AV Matrix 8x8 that is 18GBPS HDR10 YUV 444 since the version developed against here is the standard 10.2GBPS 8x8 HDMI 4K MATRIX SWITCHER HDCP2.2 HDTV

## Usage
```python
from pyjtech import get_jtech

# Connect via IP
jtech = get_jtech('10.0.0.7')

# Valid zones are 1-8
zone_status = jtech.zone_status(1)

# Print zone status
print('Zone Number = {}'.format(zone_status.zone))
print('Zone Power is {}'.format('On' if zone_status.power else 'Off'))
print('AV Source = {}'.format(zone_status.av))

# Turn off zone #1
jtech.set_power(1, False)

# Set source 5 for zone #1
jtech.set_zone_source(1, 5)

# Set all zones to source 2
jtech.set_all_zone_source(2)

```
