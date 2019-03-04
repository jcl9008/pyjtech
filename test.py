from pyjtech import get_jtech

# Connect via IP
jtech = get_jtech('10.0.0.7')

# Valid zones are 1-8
zone_status = jtech.zone_status(1)

# Print zone status
print('Zone Number = {}'.format(zone_status.zone))
print('Zone Power is {}'.format('On' if zone_status.power else 'Off'))
print('AV Source = {}'.format(zone_status.av))
