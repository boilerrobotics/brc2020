import math
from enums import EncoderError, Error, EncoderMode


class Encoder(Error):
    """
    ODrive encoder abstract class

    Full document:
    https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder

    This class is not included all configurations from the document
    """

    def __init__(self, encoder) -> None:
        self.encoder = encoder

    def get_errors(self) -> str:
        """
        Return encoder errors
        """
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder.Error
        errors = self.decode_errors(self.encoder.error)
        return " & ".join([EncoderError(error).name for error in errors])

    def has_errors(self) -> bool:
        """
        Return true if there are any errors
        """
        return self.encoder.error != 0
    
    def get_vel(self) -> float:
        return self.encoder.vel_estimate

    def is_ready(self) -> bool:
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder.is_ready
        return self.encoder.is_ready

    def index_found(self) -> bool:
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder.index_found
        return self.encoder.index_found

    def use_pre_calibrated(self) -> None:
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder.Config.pre_calibrated
        self.encoder.config.pre_calibrated = True

    def set_configs(self) -> bool:
        """
        Full document: https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder.Config
        Return true, if reboot is needed.
        """
        need_reset = False
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder.Mode
        self.encoder.config.mode = EncoderMode.HALL
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder.Config.cpr
        cpr = 42
        if self.encoder.config.cpr != cpr:
            need_reset = True
            self.encoder.config.cpr = 42
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder.Config.calib_scan_distance
        self.encoder.config.calib_scan_distance = (math.pi * 2) * 10
        # https://docs.odriverobotics.com/v/0.5.4/fibre_types/com_odriverobotics_ODrive.html#ODrive.Encoder.Config.bandwidth
        self.encoder.config.bandwidth = 100

        return need_reset
