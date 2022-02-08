#!/usr/bin/env python3
from math import pi, cos, sin

import diagnostic_msgs
import diagnostic_updater
from roboclaw_3 import Roboclaw
import rospy
import tf
from roboclaw_node.msg import MotorPosition, EncoderValues
from roboclaw_node.srv import HomeArm

__author__ = "bwbazemore@uga.edu (Brad Bazemore)"


class Node:
    def __init__(self):

        self.ERRORS = {0x0000: (diagnostic_msgs.msg.DiagnosticStatus.OK, "Normal"),
                       0x0001: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "M1 over current"),
                       0x0002: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "M2 over current"),
                       0x0004: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Emergency Stop"),
                       0x0008: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Temperature1"),
                       0x0010: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Temperature2"),
                       0x0020: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Main batt voltage high"),
                       0x0040: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Logic batt voltage high"),
                       0x0080: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Logic batt voltage low"),
                       0x0100: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "M1 driver fault"),
                       0x0200: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "M2 driver fault"),
                       0x0400: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "Main batt voltage high"),
                       0x0800: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "Main batt voltage low"),
                       0x1000: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "Temperature1"),
                       0x2000: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "Temperature2"),
                       0x4000: (diagnostic_msgs.msg.DiagnosticStatus.OK, "M1 home"),
                       0x8000: (diagnostic_msgs.msg.DiagnosticStatus.OK, "M2 home")}

        rospy.init_node("roboclaw_node")
        rospy.on_shutdown(self.shutdown)
        rospy.loginfo("Connecting to roboclaw")
        dev_name = rospy.get_param("~dev", "/dev/ttyACM0")
        baud_rate = int(rospy.get_param("~baud", "115200"))
        self.roboclaw = Roboclaw(dev_name,baud_rate)

        self.address = int(rospy.get_param("~address", "128"))
        if self.address > 0x87 or self.address < 0x80:
            rospy.logfatal("Address out of range")
            rospy.signal_shutdown("Address out of range")

        # TODO need someway to check if address is correct
        try:
            self.roboclaw.Open()
        except Exception as e:
            rospy.logfatal("Could not connect to Roboclaw")
            rospy.logdebug(e)
            rospy.signal_shutdown("Could not connect to Roboclaw")

        self.updater = diagnostic_updater.Updater()
        self.updater.setHardwareID("Roboclaw")
        self.updater.add(diagnostic_updater.
                         FunctionDiagnosticTask("Vitals", self.check_vitals))

        try:
            version = self.roboclaw.ReadVersion(self.address)
        except AttributeError as e:
            rospy.logfatal("Could not connect to Roboclaw")
            rospy.logdebug(e)
            rospy.signal_shutdown("Could not connect to Roboclaw")
            return
        except Exception as e:
            rospy.logerr(type(e).__name__)
            rospy.logwarn("Problem getting roboclaw version")
            rospy.logdebug(e)
            pass

        if not version[0]:
            rospy.logwarn("Could not get version from roboclaw")
        else:
            rospy.logdebug(repr(version[1]))

        rospy.loginfo("Connected to Roboclaw at %d", self.address)
        
        # BAD
        self.roboclaw.SpeedM1M2(self.address, 0, 0)
        self.roboclaw.ResetEncoders(self.address)

        self.joint1 = int(rospy.get_param("~joint1", "0"))
        self.joint2 = int(rospy.get_param("~joint2", "1"))
        self.reduction1 = float(rospy.get_param("~reduction1", "5281.1"))
        self.reduction2 = float(rospy.get_param("~reduction2", "5281.1"))

        self.last_command_time = rospy.get_rostime()

        self.pub = rospy.Publisher('/brc_arm/motor_positions',EncoderValues, queue_size=10)
        rospy.Subscriber("/brc_arm/motor_commands", MotorPosition, self.cmd_pos_callback)
        self.homeArm = rospy.Service('/brc_arm/home_arm', HomeArm, self.handle_home_arm)

        rospy.sleep(1)

        rospy.logdebug("dev %s", dev_name)
        rospy.logdebug("baud %d", baud_rate)
        rospy.logdebug("address %d", self.address)
        rospy.logdebug("joint1 %d", self.joint1)
        rospy.logdebug("joint2 %d", self.joint2)
        rospy.logdebug("reduction1 %d", self.reduction1)
        rospy.logdebug("reduction2 %d", self.reduction2)

    def run(self):
        if not rospy.is_shutdown():
            rospy.loginfo("Starting motor drive")
            r_time = rospy.Rate(10)

            # Jank way to "home"
            self.roboclaw.SetEncM1(self.address, 0)
            self.roboclaw.SetEncM2(self.address, 0)

            while not rospy.is_shutdown():
                if (rospy.get_rostime() - self.last_command_time).to_sec() > 1:
                    rospy.loginfo("Did not get command for 1 second, stopping")
                    try:
                        self.roboclaw.ForwardM1(self.address, 0)
                        self.roboclaw.ForwardM2(self.address, 0)
                    except OSError as e:
                        rospy.logerr("Could not stop")
                        rospy.logdebug(e)

                r_time.sleep()
    
    # Only homes two motors right now and is likely broken
    def handle_home_arm(self, req):
        r_time = rospy.Rate(10)
        status = [0] * len(req.motor_number)
        for i in range(0, len(req.motor_number)):
            rospy.loginfo("Homing joint: %d", i)
            if req.motor_number[i] == 1:
                if i == self.joint1:
                    self.roboclaw.BackwardM1(self.address, 63)
                    while self.roboclaw.ReadError != 4194304:
                        r_time.sleep()
                elif i == self.joint2:
                    self.roboclaw.BackwardM2(self.address, 63)
                    while self.roboclaw.ReadError != 4194304:
                        r_time.sleep()
                status[i] = req.motor_number[i]
        return [status]

    def publish_encoder(self, angles):
        # TODO need find solution to the OSError11 looks like sync problem with serial
        status1, enc1, crc1 = None, None, None
        status2, enc2, crc2 = None, None, None

        try:
            status1, enc1, crc1 = self.roboclaw.ReadEncM1(self.address)
            rospy.logwarn("EncM1 Reading: %d",enc1)
        except ValueError:
            pass
        except OSError as e:
            rospy.logwarn("ReadEncM1 OSError: %d", e.errno)
            rospy.logdebug(e)

        try:
            status2, enc2, crc2 = self.roboclaw.ReadEncM2(self.address)
        except ValueError:
            pass
        except OSError as e:
            rospy.logwarn("ReadEncM2 OSError: %d", e.errno)
            rospy.logdebug(e)

        if ('enc1' in vars()) and ('enc2' in vars()):
            rospy.loginfo(" Encoders %d %d" % (enc1, enc2))
            self.updater.update()

            angles[self.joint1] = enc1 / self.reduction1 * 6.28
            angles[self.joint2] = enc2 / self.reduction2 * 6.28
        
        self.pub.publish(angles)
    
    def cmd_pos_callback(self, data):
        self.last_command_time = rospy.get_rostime()

        pos1Raw = data.angle[self.joint1]
        pos1Motor = int(pos1Raw/6.28 * self.reduction1) # not actual reduction
        pos2Raw = data.angle[self.joint2]
        pos2Motor = int(pos2Raw/6.28 * self.reduction2) # not actual reduction

        # rospy.logdebug("Joint %d raw:%f, Joint %d motor: %d", self.joint1, pos1Raw, self.joint1, pos1Motor)
        # rospy.logdebug("Joint %d raw:%f, Joint %d motor: %d", self.joint2, pos2Raw, self.joint2, pos2Motor)

        try:
            self.roboclaw.SpeedAccelDeccelPositionM1(self.address, 100, 10000, 100, pos1Motor, 0)
            rospy.loginfo("Joint %d command sent, posraw: %d", self.joint1, pos1Motor)
        except OSError as e:
            rospy.logwarn("SpeedAccelDeccelPositionM1 OSError: %d", e.errno)
            rospy.logdebug(e)

        try:
            self.roboclaw.SpeedAccelDeccelPositionM2(self.address, 100, 10000, 100, pos2Motor, 0)
            rospy.loginfo("Joint %d command sent, posraw: %d", self.joint2, pos2Motor)
        except OSError as e:
            rospy.logwarn("SpeedAccelDeccelPositionM2 OSError: %d", e.errno)
            rospy.logdebug(e)

        self.publish_encoder(data.angles)

    # TODO: Need to make this work when more than one error is raised
    def check_vitals(self, stat):
        try:
            status = self.roboclaw.ReadError(self.address)[1]
        except OSError as e:
            rospy.logwarn("Diagnostics OSError: %d", e.errno)
            rospy.logdebug(e)
            return
        state, message = self.ERRORS[status]
        stat.summary(state, message)
        try:
            stat.add("Main Batt V:", float(self.roboclaw.ReadMainBatteryVoltage(self.address)[1] / 10))
            stat.add("Logic Batt V:", float(self.roboclaw.ReadLogicBatteryVoltage(self.address)[1] / 10))
            stat.add("Temp1 C:", float(self.roboclaw.ReadTemp(self.address)[1] / 10))
            stat.add("Temp2 C:", float(self.roboclaw.ReadTemp2(self.address)[1] / 10))
        except OSError as e:
            rospy.logwarn("Diagnostics OSError: %d", e.errno)
            rospy.logdebug(e)
        return stat

    # TODO: need clean shutdown so motors stop even if new msgs are arriving
    def shutdown(self):
        rospy.loginfo("Shutting down")
        try:
            self.roboclaw.ForwardM1(self.address, 0)
            self.roboclaw.ForwardM2(self.address, 0)
        except Exception as e:
            rospy.logerr("Shutdown did not work trying again")
            try:
                self.roboclaw.ForwardM1(self.address, 0)
                self.roboclaw.ForwardM2(self.address, 0)
            except Exception as e:
                rospy.logerr("Could not shutdown motors!!!!")
                rospy.logdebug(e)


if __name__ == "__main__":
    try:
        node = Node()
        node.run()
    except rospy.ROSInterruptException:
        pass
    rospy.loginfo("Exiting")
