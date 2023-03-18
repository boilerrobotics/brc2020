import time
import utils
import test_run
from odrive.enums import *

def dump_config(odrv, filename) -> None:
    '''
    Dump all config profile for comparision
    '''
    with open(filename, 'w+') as fp:
        print(str(odrv), file=fp)

def config_controler(controller) -> None:
    controller.config.control_mode = ControlMode.VELOCITY_CONTROL
    controller.config.vel_limit = 10

def config_motor(motor) -> None:
    motor.config.pole_pairs = 7
    motor.config.calibration_current = 20.0
    motor.config.motor_type = MotorType.HIGH_CURRENT
    motor.config.resistance_calib_max_voltage = 4.0
    motor.config.requested_current_range = 20.0
    motor.config.current_control_bandwidth = 100.0
    motor.config.torque_constant = 8.27/270
    motor.config.current_lim = 20

def config_encoder(encoder) -> None:
    encoder.config.mode = EncoderMode.HALL
    encoder.config.cpr = 42
    encoder.config.pre_calibrated = True
    encoder.config.bandwidth = 100
    encoder.config.calib_scan_distance = 300

odrvs = utils.find_odrvs()
for section, odrv in odrvs.items(): 
    utils.check_error(odrv, section) # Checking errors
    dump_config(odrv, filename=f'{section}-precal.txt')
    print(f'Calicating {section}...')    
    for axis in [odrv.axis0, odrv.axis1]:
        config_controler(axis.controller)
        config_motor(axis.motor)
        config_encoder(axis.encoder)
        axis.requested_state = AxisState.FULL_CALIBRATION_SEQUENCE
        while axis.current_state != AxisState.IDLE:
            utils.print_voltage_current(odrv)
            time.sleep(1)
        utils.check_error(odrv, section) # Check error again 
    dump_config(odrv, filename=f'{section}-postcal.txt')
    print(f'Section {section} calibration completed')
print('Test run ...')
test_run.test_run(odrvs, running_time=5, running_speed=3)
