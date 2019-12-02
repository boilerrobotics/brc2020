#!/usr/bin/env python

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist

class motor: 
    def __init__(self):
        self.speed = 0.5
        rospy.init_node('motor_listener', anonymous=True)
        rospy.Subscriber('/cmd_vel', Twist, self.callback)

    def callback(self, data):
        rospy.loginfo(data.linear.x)
        self.speed = self.pre_process_speed(data.linear.x)
        # print(self.speed)

    def pre_process_speed(self, speed):
        if abs(speed) > 1:
            speed = speed/abs(speed)
        return round(speed, 2)

    def drive_motor(self):
        print(self.speed)

if __name__ == '__main__':
    m = motor() 
    rospy.spin()
    try:
        while True:
            m.drive_motor()
    except KeyboardInterrupt:
        exit(0)
