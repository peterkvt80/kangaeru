import os
import logging
import time
import can
import j1939

# Example copied from https://github.com/juergenH87/python-can-j1939/tree/master
# and placed in a class wrapper so we can call it from a GUI.
#
#enable these if you want to see how the interface is doing
#logging.getLogger('j1939').setLevel(logging.DEBUG)
#logging.getLogger('can').setLevel(logging.DEBUG)

class Kangaeru_io():
    def __init__(self, id, can_port):
        super().__init__()
        self.init(id, can_port)

    def init(self, id, can_port):
        self.id=id
        self.can_port=can_port
        self.heartbeat=False
        self.GPOOnline=False
        self.timeoutCounter=3
        
        response = os.system("sudo ip link set up "+can_port)        
        if response!=0 and response!=512:
            print("Invalid CAN bus... " + str(response))
            exit() 

        # compose the name descriptor for the kangaeru ca
        self.name = j1939.Name(
            arbitrary_address_capable=1,
            industry_group=j1939.Name.IndustryGroup.AgriculturalAndForestry,
            vehicle_system_instance=1,
            vehicle_system=0,
            function=0,
            function_instance=0,
            ecu_instance=0,
            manufacturer_code=64, # Spectra Physics
            # This number should make the name unique.
            # Normally get the serial number from an EPROM or initialisation.
            identity_number=3456 
            )

        # create the ControllerApplications
        self.ca = j1939.ControllerApplication(self.name, 16) # Pinch 16 as the default port
        
        # These are the values that this controller application deals with
        self.yaw_rate = 0
        self.temperature = 0.0
        self.pressure = 0.0
        self.humidity = 0.0

    def ca_receive(self, priority, pgn, source, timestamp, data):
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
        # print("PGN {} length {}".format(pgn, len(data)))
        
        if pgn == 0Xfeca:
            # print("Got heartbeat from "+str(source))
            # TODO: we should be able to take the source and get the name from the system.
            # "notify" handles the other ecu names so it should be possible
            
            self.heartbeat=True
            self.GPOOnline=True
            self.timeoutCounter=3 # Three timeouts means offline
            #print(self.ca.__dir__())
            
            # Pathetic fixed address scheme. Should replace this with a proper address claim
            # if source==128: # turn
                # print("Got a GPO signal")
            #if source==130: # turn
            #    print("Got a turn signal")
        if pgn == 0xfecb: # yeah. Probably ought to get a different pgn
            # print("Got a turn signal"+str(data[1]*0x100+data[0]))
            self.yaw_rate = data[1] * 0x100 + data[0]
            self.temperature = data[2] - 40
            self.pressure = 260 + ((data[3] * 0x100 + data[4]) / 10)
            self.humidity = (data[5] * 0x100 + data[6]) / 100.0
            print(str(data[2])+" "+str(data[5]) + " " + str(data[6]))
            
    def get_yaw_rate(self):
        # return the yaw rate in degrees per second
        yaw = self.yaw_rate
        yaw = yaw / 0x80
        yaw = yaw - 250
        return yaw

    def get_temperature(self):
        # return the temperature in range -40 to +250 degrees C
        return self.temperature

    def get_pressure(self):
        # return the pressure in range 260 to 1260mb
        return self.pressure

    def get_humidity(self):
        # return the humidity from 0% to 100%
        return self.humidity

    def ca_timer_callback1(self, cookie):
        """Callback for sending messages

        This callback is registered at the ECU timer event mechanism to be
        executed every 500ms.

        :param cookie:
            A cookie registered at 'add_timer'. May be None.
        """
        # wait until we have our device_address
        if self.ca.state != j1939.ControllerApplication.State.NORMAL:
            # returning true keeps the timer event active
            return True

        # create data with 8 bytes
        data = [j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_8] * 8

        # sending normal broadcast message
        #self.ca.send_pgn(0, 0xFD, 0xED, 6, data)

        # sending normal peer-to-peer message, destination address is 0x80
        self.ca.send_pgn(0, 0xE0, 0x80, 6, data)

        # returning true keeps the timer event active
        return True

    def ca_timer_callback2(self, cookie):
        """Callback for sending messages

        This callback is registered at the ECU timer event mechanism to be
        executed every 500ms.

        :param cookie:
            A cookie registered at 'add_timer'. May be None.
        """
        # wait until we have our device_address
        if self.ca.state != j1939.ControllerApplication.State.NORMAL:
            # returning true keeps the timer event active
            return True

        # create data with 100 bytes
        # data = [j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_8] * 100

        # sending multipacket message with TP-BAM
        #self.ca.send_pgn(0, 0xFE, 0xF6, 6, data)

        # sending multipacket message with TP-CMDT, destination address is 0x05
        # self.ca.send_pgn(0, 0xD0, 0x05, 6, data)

        # returning true keeps the timer event active
        return True
    
    def heartbeatTimeout(self, cookie):
        if self.timeoutCounter<=0:
            print("timed out")
            self.GPOOnline=False
            return True
        if self.heartbeat==False:
            self.timeoutCounter=self.timeoutCounter-1
            print("counting down")
        self.heartbeat=False
        return True
    
    def isGPOOnline(self):
        return self.GPOOnline
    
    def send(self, gpo):
        data=[]
        data.append(gpo)
        self.ca.send_pgn(0, 0xfe, 0xed, 1, data)

    def run(self):
        print("Initializing")

        # create the ElectronicControlUnit (one ECU can hold multiple ControllerApplications)
        ecu = j1939.ElectronicControlUnit()

        # Connect to the CAN bus
        # Arguments are passed to python-can's can.interface.Bus() constructor
        # (see https://python-can.readthedocs.io/en/stable/bus.html).
        ecu.connect(bustype='socketcan', channel=self.can_port)
        # ecu.connect(bustype='kvaser', channel=0, bitrate=250000)
        # ecu.connect(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000)
        # ecu.connect(bustype='ixxat', channel=0, bitrate=250000)
        # ecu.connect(bustype='vector', app_name='CANalyzer', channel=0, bitrate=250000)
        # ecu.connect(bustype='nican', channel='CAN0', bitrate=250000)
        # ecu.connect('testchannel_1', bustype='virtual')

        # add CA to the ECU
        ecu.add_ca(controller_application=self.ca)
        self.ca.subscribe(self.ca_receive)
        # callback every 0.5s
        self.ca.add_timer(0.500, self.ca_timer_callback1)
        # callback every 5s
        self.ca.add_timer(5, self.ca_timer_callback2)
        # by starting the CA it starts the address claiming procedure on the bus
        self.ca.add_timer(1.0, self.heartbeatTimeout)
        self.ca.start()

    def __del__(self):
        print("Deinitializing")
        self.ca.stop()
        ecu.disconnect()

#if __name__ == '__main__':
#    main()