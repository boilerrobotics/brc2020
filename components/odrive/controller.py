from enums import ControllerError, ControlMode, InputMode, Error


class Controller(Error):
    """
    ODrive controller abstract class

    Full document:
    https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller

    This class is not included all configurations from the document
    """

    def __init__(self, controller) -> None:
        self.controller = controller
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller.input_vel
        self.input_vel: float = controller.input_vel
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller.mechanical_power
        self.mechanical: float = controller.mechanical_power
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller.electrical_power
        self.electrical_power: float = controller.electrical_power

    def get_errors(self) -> str:
        """
        Return controller errors
        """
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller.Error
        errors = self.decode_errors(self.controller.error)
        return " & ".join([ControllerError(error).name for error in errors])

    def has_errors(self) -> bool:
        """
        Return true if there are any errors
        """
        return self.controller.error != 0

    def set_speed(self, speed: float) -> None:
        """
        Set speed in turn per second
        """
        self.controller.input_vel = speed

    def stop(self) -> None:
        """
        Set speed to 0
        """
        self.set_speed(0)

    def get_speed_limit(self) -> float:
        """
        Return speed limit in turn per second
        """
        return self.controller.config.vel_limit

    def set_speed_limit(self, speed: float) -> None:
        """
        Set speed limit in turn per second
        """
        self.controller.config.vel_limit = speed

    def set_configs(self, vel_limit=10) -> bool:
        """
        Full document: https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller.Config

        Use VELOCITY_CONTROL for control_mode:
        "
        Uses both the inner torque control loop and the velocity control loop.
        Use input_vel to command desired velocity, and input_torque.
        "

        Use VEL_RAMP for input_mode
        "
        Ramps a velocity command from the current value to the target value.
        "
        Return true, if reboot is needed.
        """
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller.ControlMode.VELOCITY_CONTROL
        self.controller.config.control_mode = ControlMode.VELOCITY_CONTROL
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller.Config.vel_limit
        self.controller.config.vel_limit = vel_limit
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller.InputMode.VEL_RAMP
        self.controller.config.input_mode = InputMode.VEL_RAMP
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Controller.Config.vel_ramp_rate
        self.controller.config.vel_ramp_rate = 3

        return False  # no need to reboot
