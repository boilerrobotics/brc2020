import yaml
import asyncio
import odrive
from enums import ODriveError, Error
from sensing import OdriveSensing
from axis import Axis


class Odrive(Error):
    """
    ODrive abstract class

    Full document:
    https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive

    This class is not included all configurations from the document
    """

    def __init__(self, odrv, section) -> None:
        self.odrv = odrv
        self.section = section
        self.serial_number: str = f"{odrv.serial_number:x}".upper()
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.hw_version_major
        self.hw_version = f"{odrv.hw_version_major}.{odrv.hw_version_minor} {odrv.hw_version_variant}V"
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.fw_version_major
        self.fw_version = f"{odrv.fw_version_major}.{odrv.fw_version_minor}.{odrv.fw_version_revision}"
        # check axis.py
        self.axis0 = Axis(odrv.axis0, 0)
        self.axis1 = Axis(odrv.axis1, 1)
        self.config = self.Config(odrv.config)

    def clear_errors(self) -> None:
        """
        Clear errors
        """
        self.odrv.clear_errors()

    def get_errors(self) -> str:
        """
        Return ODrive system errors
        """
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Error
        errors = self.decode_errors(self.odrv.error)
        return " & ".join([ODriveError(error).name for error in errors])

    def has_errors(self) -> bool:
        """
        Return true if there are any errors
        """
        return self.axis0.has_errors() or self.axis1.has_errors()

    def print_voltage_current(self, connection: OdriveSensing | None = None) -> None:
        """
        Print voltage and current for debugging.
        """
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.vbus_voltage
        vbus_voltage: float = self.odrv.vbus_voltage
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.ibus
        ibus: float = self.odrv.ibus
        print(f"  voltage = {vbus_voltage:5.2f} V" f"  current = {ibus:6.4f} A")
        if connection:
            connection.publish("brc/voltage", f"{vbus_voltage:5.2f}")
            connection.publish("brc/current", f"{ibus:7.5f}")

    def print_errors(self, component, name: str) -> str:
        """
        This function print part of the errors
        """
        if errors := component.get_errors():
            print(f"  {name} has {errors}")

    def check_errors(self) -> None:
        """
        This function will print the errors
        """
        print("-" * 100)
        print(f"{self.section} odrive status check...")
        self.print_voltage_current()
        self.print_errors(self, "system errors")
        print(f"Axis 0 current state: {self.axis0.get_state()}")
        print(
            f"Motor is{'' if self.axis0.motor.is_calibrated() else ' not'} calibrated"
        )
        print(f"Encoder is{'' if self.axis0.encoder.is_ready() else ' not'} ready")
        self.print_errors(self.axis0, "axis 0")
        self.print_errors(self.axis0.motor, "motor 0")
        self.print_errors(self.axis0.controller, "controller 0")
        self.print_errors(self.axis0.encoder, "encoder 0")
        print(f"Axis 1 current state: {self.axis1.get_state()}")
        print(
            f"Motor is{'' if self.axis1.motor.is_calibrated() else ' not'} calibrated"
        )
        print(f"Encoder is{'' if self.axis1.encoder.is_ready() else ' not'} ready")
        self.print_errors(self.axis1, "axis 1")
        self.print_errors(self.axis1.motor, "motor 1")
        self.print_errors(self.axis1.controller, "controller 1")
        self.print_errors(self.axis1.encoder, "encoder 1")

    def check_version(self) -> None:
        """
        Print out hardware version and firmware version.
        """
        print(
            f"Firmware version is {self.fw_version}"
            f'{" " * 3} Hardware version is {self.hw_version}'
        )

    async def reboot(self, save_config: bool = False) -> None:
        """
        Reboot Odrive then reconnect with 30 seconds timeout.
        Option to save config
        """
        try:
            if save_config:
                self.odrv.save_configuration()
            else:
                self.odrv.reboot()
        except Exception:
            print(
                f"rebooting {self.section} odrive..."
            )  # odrive will disappear. expect error will happen
        finally:
            # find odrive again
            try:
                odrv = await asyncio.wait_for(
                    odrive.find_any_async(serial_number=self.serial_number), timeout=30
                )
                self.odrv = odrv
                self.axis0 = Axis(odrv.axis0, 0)
                self.axis1 = Axis(odrv.axis1, 1)
            except asyncio.TimeoutError:
                print("Timeout: cannot reconnect with Odrive")
            except Exception as e:
                print(f"Unknown error: {e}")
            else:
                print(f"{self.section} odrive is online...")

    def set_configs(self) -> bool:
        """
        Set configurations (controller, motor, and encoder).
        Return true, if reboot is needed.
        """
        print(f"Applying configurations...")
        return True if (self.axis0.set_configs() | self.axis1.set_configs()) else False

    async def calibrate(self) -> None:
        """
        Run full calibration sequence
        """
        self.clear_errors()
        self.check_errors()
        # calibration can be done only one axis at a time
        for axis in [self.axis0, self.axis1]:
            name = f"Odrive {self.section} axis {axis.id}"
            if axis.motor.is_calibrated() and axis.encoder.is_ready():
                print(f"{name} is calibrated and ready. Calibration is not needed")
            elif axis.has_errors():
                print(f"{name} has error(s). Abort calibration")
            else:
                axis.request_full_calibration()
                await asyncio.sleep(1)
                while not axis.is_idle():
                    # check status every second
                    await asyncio.sleep(1)
                    self.check_errors()

                if axis.motor.is_calibrated() and axis.encoder.is_ready():
                    print(f"{name} is calibrated and ready. Calibration is completed")
                    axis.encoder.use_pre_calibrated()
                    axis.motor.use_pre_calibrated()

    async def test_run(self, speed: float, duration: int) -> None:
        """
        Test run for "duration" second with "speed" turn/second.
        Run both directions.
        """
        self.check_errors()
        await asyncio.gather(
            *[
                self.test_run_cycle(axis, speed, duration)
                for axis in [self.axis0, self.axis1]
            ]
        )
        self.check_errors()

    async def test_run_cycle(self, axis: Axis, speed: float, duration: int) -> None:
        """
        Test run for "duration" second with "speed" turn/second.
        """
        axis.request_close_loop_control()
        axis.controller.set_speed(speed)
        await asyncio.sleep(duration)
        axis.controller.set_speed(-speed)
        await asyncio.sleep(duration)
        axis.controller.stop()
        await asyncio.sleep(duration)
        axis.request_idle()

    class Config:
        """
        Odrive config class
        https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Config
        """

        def __init__(self, config) -> None:
            self.config = config
            # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Config.brake_resistance
            self.brake_resistance = 0.5
            # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Config.enable_brake_resistor
            self.enable_brake_resistor = True
            # set GPIO mode for hall sensor pins
            self.GPIO_MODE_DIGITAL = 0
            self.config.gpio9_mode = self.GPIO_MODE_DIGITAL
            self.config.gpio10_mode = self.GPIO_MODE_DIGITAL
            self.config.gpio11_mode = self.GPIO_MODE_DIGITAL
            self.config.gpio12_mode = self.GPIO_MODE_DIGITAL
            self.config.gpio13_mode = self.GPIO_MODE_DIGITAL
            self.config.gpio14_mode = self.GPIO_MODE_DIGITAL

        def set_break_resistor(self, brake_resistance: int | None = None) -> bool:
            """
            If break resistor is already enable, return False.
            The system won't reboot.
            """
            if brake_resistance:
                self.brake_resistance = brake_resistance
            self.config.brake_resistance = self.brake_resistance
            if self.config.enable_brake_resistor:
                return False
            else:
                self.config.enable_brake_resistor = self.enable_brake_resistor
                return True


async def find_odrvs_async(
    config_file="config.yml", timeout=3, section: str | None = None
) -> list[Odrive]:
    """
    This function will find all ODrives asynchronously.
    This function is not available on Odrive library version 0.5.4
    as `odrive.find_any_async()` function was introduced in version 0.6
    """
    with open(config_file) as fp:
        config = yaml.safe_load(fp)

    tasks = [
        asyncio.create_task(
            odrive.find_any_async(serial_number=serial),
            name=f"{section}",
        )
        for section, serial in config["serial"].items()
    ]
    print("finding ODrives...")
    done, pending = await asyncio.wait(
        tasks, timeout=timeout, return_when=asyncio.ALL_COMPLETED
    )

    odrvs = []
    for task in tasks:
        section = task.get_name()
        if task in pending:
            print(f"Warning! {section} ODrive not found")
            task.cancel()
        if task in done:
            odrv = Odrive(task.result(), section)
            odrvs.append(odrv)
            print(f"found {section} ODrive", end="")
            print(f"-> ", end="")
            odrv.check_version()

    return odrvs


def find_odrvs() -> dict[str, any]:
    """
    This function will find ODrive that serial numbers are list
    in the config.yml. This function needs to be changed to match
    expected output from `find_odrvs_async` function.
    """

    with open("config.yml") as fp:
        config = yaml.safe_load(fp)

    print("finding ODrives...")
    odrvs = {}  # Looking for available ODrive
    for section, serial in config["serial"].items():
        print(f"searching for serial number {serial}...")
        try:
            odrv = odrive.find_any(serial_number=serial, timeout=2)
            odrv = Odrive(odrv)
            odrvs[section] = odrv
            print(f"-> assign odrive {serial} to {section} section")
            print(f"-> ", end="")
            odrv.check_version()
        except TimeoutError as e:
            print(f"error: Cannot find serial {serial} !!")
    print("--------------------------------------")

    return odrvs
