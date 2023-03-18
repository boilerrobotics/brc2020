'''
Utility functions for ODrive calibration and test.
'''

import yaml
import odrive

def print_voltage_current(odrv) -> None:
    '''
    Print voltage and current for debugging.
    '''
    print(f'  voltage = {odrv.vbus_voltage:5.2f} V'
          f'  current = {odrv.ibus:5.2f} A')
    
def find_odrvs() -> dict:
    with open('config.yml') as fp:
        config = yaml.safe_load(fp) 

    print("finding odrives...")
    odrvs = {} # Looking for avaiable ODrive
    for section, serial in config['serial'].items():
        print(f'searching for serial number {serial}...')
        try: 
            odrv = odrive.find_any(serial_number=serial, timeout=1)
            odrvs[section] = odrv
            print(f'-> assign odrive {serial} to {section} section')
        except TimeoutError as e:
            print(f'error: Cannot find serial {serial} !!')
    print('--------------------------------------')

    return odrvs

def check_error(odrv, name: str | None = None) -> None:
    if name is not None: 
        print(f'{name} odrive checking...') 
    print_voltage_current(odrv)
    print(f'  {"error code:":<13}axis0{" "*10}axis1')
    # How can we get error code from enum
    print(f'  {"controller":<10}{odrv.axis0.controller.error:6}'
        f'{odrv.axis1.controller.error:15}')
    print(f'  {"encoder":<10}{odrv.axis0.encoder.error:6}'
        f'{odrv.axis1.encoder.error:15}')
    print(f'  {"motor":<10}{odrv.axis0.motor.error:6}'
        f'{odrv.axis1.motor.error:15}')
    print('--------------------------------------')