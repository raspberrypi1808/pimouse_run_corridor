#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger, TriggerResponse
from pimouse_ros.msg import LightSensorValues

class WallStopAccel():
    def __init__(self,freq=10,accel=0.2,min_speed=0.2,max_speed=0.8):
        self.cmd_vel = rospy.Publisher('/cmd_vel',Twist,queue_size=1)
        rospy.Subscriber('/lightsensors', LightSensorValues, self.callback_sensors)
        self.sensors = LightSensorValues()

        self.freq = freq #[Hz]
        self.accel_once = accel/freq #[m/(s*one cycle)]
        self.min_speed = min_speed #[m/s]
        self.max_speed = max_speed #[m/s]

    def callback_sensors(self,messages):
        self.sensors = messages

    def behavior_stop(self):
            return 0.0, 0.0

    def behavior_go(self,prev):
        linear = prev.linear.x + self.accel_once
        if   linear < self.min_speed: linear = self.min_speed
        elif linear > self.max_speed: linear = self.max_speed
        return linear, 0.0

    def decision(self,sensors,prev):
        if sensors.sum_all >= 50:
            return self.behavior_stop()
        else:
            return self.behavior_go(prev)
    
    def run(self):
        rate = rospy.Rate(self.freq)
        d = Twist()
        d.linear.x, d.angular.z = 0.0, 0.0
        while not rospy.is_shutdown():
            d.linear.x, d.angular.z = self.decision(self.sensors,d)
            self.cmd_vel.publish(d)
            rate.sleep()

if __name__ == '__main__':
    rospy.init_node('wall_trace')
    rospy.wait_for_service('/motor_on')
    rospy.wait_for_service('/motor_off')

    rospy.on_shutdown(rospy.ServiceProxy('/motor_off',Trigger).call)
    if not rospy.ServiceProxy('/motor_on',Trigger).call().success:
        rospy.logerr("motors are not empowered")
        sys.exit(1)

    WallStopAccel().run()
