# name: ecu_gpo.py
# parameter 1: Serial ID number. A unique integer for this device. Default 1234567
# parameter 2: Socketcan port. The can bus to connect this ECU to. Default vcan0. Typically vcan0 or can0.
# Simple 8 bit GPO
# Sending a number 0..7 to pgn 0xfeed toggles that bit.
import os
import argparse
import logging
import time
import can
import j1939
from sense_hat import SenseHat

#logging.getLogger('j1939').setLevel(logging.DEBUG)
#logging.getLogger('can').setLevel(logging.DEBUG)

# compose the name descriptor for the new cap
name = j1939.Name(
    arbitrary_address_capable=0,
    industry_group=j1939.Name.IndustryGroup.Industrial,
    vehicle_system_instance=1,
    vehicle_system=1,
    function=1,
    function_instance=1,
    ecu_instance=1,
    manufacturer_code=64, # Spectra Physics
    # This number should make the name unique.
    # Initialisation is typically from from EPROM or command line    
    identity_number=1234567
    )

parser = argparse.ArgumentParser(description="my argument parser")
parser.add_argument("id", nargs="?", default="123456") # Each ECU of this type must have a unique serial number
parser.add_argument("port", nargs="?", default="vcan0") # usually vcan0 or can0

args = parser.parse_args()
name.identity_number = int(args.id)

# create the ControllerApplications
ca = j1939.ControllerApplication(name, 128)
state = 0 # state of the GPO

sense = SenseHat()
sense.clear()

# 0 is OK, 256 is already configured
response = os.system("sudo ip link set "+args.port+" up") 
if response!=0 and response!=256:
    print("Invalid CAN bus. " + str(response))
    exit()

def ca_receive(priority, pgn, source, timestamp, data):
    """Feed incoming message to this CA.
    (OVERLOADED function)
    :param int priority:
        Priority of the message
    :param int pgn:
        Parameter Group Number of the message
    :param int sa:
        Source Address of the message
    :param int timestamp:
        Timestamp of the message
    :param bytearray data:
        Data of the PDU
    """
    global state
    # print("PGN {} length {}".format(pgn, len(data))) # see what is being received
    if pgn==0xfeed:
        state = state ^ (1 << data[0])
        # print("got data. state="+str(state))
    # LED goes green if on
    sense.set_pixel(0,0,0,(state & 0x01>0)*255,0)
    sense.set_pixel(1,0,0,(state & 0x02>0)*255,0)
    sense.set_pixel(2,0,0,(state & 0x04>0)*255,0)
    sense.set_pixel(3,0,0,(state & 0x08>0)*255,0)
    sense.set_pixel(4,0,0,(state & 0x10>0)*255,0)
    sense.set_pixel(5,0,0,(state & 0x20>0)*255,0)
    sense.set_pixel(6,0,0,(state & 0x40>0)*255,0)
    sense.set_pixel(7,0,0,(state & 0x80>0)*255,0)    

def ca_timer_callback(cookie):
    """Callback for sending messages

    This callback is registered at the ECU timer event mechanism to be
    executed every 500ms.

    :param cookie:
        A cookie registered at 'add_timer'. May be None.
    """
    # wait until we have our device_address
    if ca.state != j1939.ControllerApplication.State.NORMAL:
        # returning true keeps the timer event active
        return True
    
    # Heartbeat
    data = [0xff, 0xff, 0x00, 0x00, 0x00, 0x00] # message to send
    ca.send_pgn(0, 0xfe, 0xca, 6, data) #DM1
    
    # returning true keeps the timer event active
    return True        

def main():
    print("Initializing")
    
    # create the ElectronicControlUnit (one ECU can hold multiple ControllerApplications)
    ecu = j1939.ElectronicControlUnit()

    # Connect to the CAN bus
    # Arguments are passed to python-can's can.interface.Bus() constructor
    # (see https://python-can.readthedocs.io/en/stable/bus.html).
    ecu.connect(bustype='socketcan', channel=args.port) # usually vcan0 or can0
    # ecu.connect(bustype='kvaser', channel=0, bitrate=250000)
    # ecu.connect(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000)
    # ecu.connect(bustype='ixxat', channel=0, bitrate=250000)
    # ecu.connect(bustype='vector', app_name='CANalyzer', channel=0, bitrate=250000)
    # ecu.connect(bustype='nican', channel='CAN0', bitrate=250000)
    # ecu.connect('testchannel_1', bustype='virtual')

    # add CA to the ECU
    ecu.add_ca(controller_application=ca)
    ca.subscribe(ca_receive)
    # callback every 1.0s
    ca.add_timer(1.000, ca_timer_callback)

    # by starting the CA it starts the address claiming procedure on the bus
    ca.start()
    
    # Run this forever
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted")
        
    print("Deinitializing")
    # Going offline? Switch off all outputs
    state = 0
    for i in range (0, 8):
        sense.set_pixel(i,0,0,0,0)

    ca.stop()
    ecu.disconnect()

if __name__ == '__main__':
    main()