#!/usr/bin/python

#Angular Rate Data Packet

#The following table describes the Angular Rate Data Packet:

#Angular Rate Data Packet Payload
#Byte Number	Parameter	Range	Resolution	Offset
#0:1	Angular Rate X	-250 to +252 deg/s	1/128 deg/second/bit	-250 deg
#2:3	Angular Rate Y	-250 to +252 deg/s	1/128 deg/second/bit	-250 deg
#4:5	Angular Rate Z	-250 to +252 deg/s	1/128 deg/second/bit	-250 deg

import os
import argparse
from sense_hat import SenseHat
import time
from ecu_turn import ECU_Turn_io

# scale yaw rate to a 16 bit payload
def payload(value): 
    # clip 
    if value < -250:
        value = -250
    if value > 252:
        value = 252
    value = int((value + 250) * 128)
    return value

sense = SenseHat()
sense.set_imu_config(False, True, True)  # no compass. Use 6 axis only.
# Note that this will compensate for orientation. The yaw axis does not depend on the IMU orientation.

last_time = time.time()
last_yaw = 0.0
last_roll = 0.0
last_pitch = 0.0

parser = argparse.ArgumentParser(description="my argument parser")
parser.add_argument("id", nargs="?", default="123456") # Each ECU of this type must have a unique serial number
parser.add_argument("port", nargs="?", default="vcan0") # usually vcan0 or can0

args = parser.parse_args()

can_ecu = ECU_Turn_io(id=args.id, can_port=args.port)
can_ecu.run()

while True:
    # Call this often to keep the Kalman filter fresh
    orientation_deg = sense.get_orientation_degrees()
    now = time.time()
    delta_time = now-last_time
    last_time = now
    yaw = orientation_deg["yaw"]
    delta_yaw = yaw - last_yaw
    last_yaw = yaw
    roll = orientation_deg["roll"]
    delta_roll = roll - last_roll
    last_roll = roll
    pitch = orientation_deg["pitch"]
    delta_pitch = pitch - last_pitch
    last_pitch = pitch

    #print(str(yaw)+" "+str(delta_time))
    angular_velocity_yaw = delta_yaw / delta_time
    angular_velocity_roll = delta_roll / delta_time # we don't use these values in this application
    angular_velocity_pitch = delta_pitch / delta_time
    #print(int(payload(angular_velocity_yaw
    
    temperature = sense.get_temperature()
    
    pressure = sense.get_pressure()
    
    humidity = sense.get_humidity()
    
    can_ecu.set_yaw_rate(payload(angular_velocity_yaw))
    can_ecu.set_temperature(temperature)
    can_ecu.set_pressure(pressure)
    can_ecu.set_humidity(humidity)
    time.sleep(0.1) # be nice to other processes
