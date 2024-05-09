# Rate of turn (yaw)
# Sending a number 0..7 to pgn 0xfeed toggles that bit.
# This requires the CAN port to be already UP
# ip link set up can0

import logging
import time
import can
import j1939

#logging.getLogger('j1939').setLevel(logging.DEBUG)
#logging.getLogger('can').setLevel(logging.DEBUG)

class ECU_Turn_io():
    def __init__(self, id, can_port):
        super().__init__()
        self.init(id, can_port)

    def init(self, id, _can_port):
        self.can_port = _can_port
        print("id = "+id+" can_port = "+_can_port)
        #response = os.system("sudo ip link set up "+can_port) 
        #if response!=0:
        #    print("Invalid CAN bus. " + str(response))
        #    exit()
            
        # compose the name descriptor for the new ca
        self.name = j1939.Name(
            arbitrary_address_capable=1,
            industry_group=j1939.Name.IndustryGroup.AgriculturalAndForestry,
            vehicle_system_instance=0,
            vehicle_system=0,
            function=0,
            function_instance=2, # Rate of turn ECU
            ecu_instance=0,
            manufacturer_code=64, # Spectra Physics
            identity_number=555 # Init this from non volatile memory. Each unit should be unique.
            )
        self.name.identity_number = int(id)
        # create the ControllerApplications
        self.ca = j1939.ControllerApplication(self.name, 130)
        self.state = 0 # state of the GPO
        
        self.yaw_rate = 0 # yaw is 16 bit value
        self.temperature = 0.0
        
    def set_yaw_rate(self, _yaw_rate):
        self.yaw_rate = _yaw_rate

    def set_temperature(self, _temperature):
        self.temperature = _temperature

    def set_pressure(self, _pressure):
        self.pressure = _pressure

    def set_humidity(self, _humidity):
        self.humidity = _humidity

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
        # global state
        # print("PGN {} length {}".format(pgn, len(data)))
        # Could react to other PGNs here if needed for configuration etc.
        # This picks up GPO signals but we don't actually use them here.
        if pgn==0xfeed:
            self.state = self.state ^ (1 << data[0])
            # print("got data. state="+str(self.state))    
          
    def ca_timer_callback(self, cookie):
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
        #data = [j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_8] * 8

        # sending multipacket message with TP-BAM
        #self.ca.send_pgn(0, 0xFE, 0xF6, 6, data)

        # sending multipacket message with TP-CMDT, destination address is 0x05
        #self.ca.send_pgn(0, 0xD0, 0x05, 6, data)

        data = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07] # message to send
        # yaw
        data[1] = self.yaw_rate >> 8
        data[0] = self.yaw_rate & 0xff
        # temperature. 1 byte. 1 bit per degree, offset -40
        t = int(self.temperature)
        if t < -40:
            t = -40
        if t > 250:
            t = 250
        t = t + 40        
        data[2] = t
        #pressure
        # 2 bytes, offset 260mb, mb per bit 0.1mb
        p = self.pressure
        p = p - 260 # offset
        if p<0:
            p = 0
        p = int(p * 10) # 0.1mb)
        if p>10000:
            p=10000
        data[3] = p >> 8
        data[4] = p & 0xff
        #print(str(data[3])+" "+str(data[4]))
        
        # humidity 2 bytes, no offset, 0.01% per bit
        h = int(self.humidity * 100)
        if h < 0:
            h = 0
        if h>10000:
            h = 10000
        data[5] = h >> 8
        data[6] = h & 0xff
        

        self.ca.send_pgn(0, 0xfe, 0xcb, 7, data) #our custom pgn

        # returning true keeps the timer event active
        return True

    def run(self):
        print("Initializing")

        # create the ElectronicControlUnit (one ECU can hold multiple ControllerApplications)
        self.ecu = j1939.ElectronicControlUnit()

        # Connect to the CAN bus
        # Arguments are passed to python-can's can.interface.Bus() constructor
        # (see https://python-can.readthedocs.io/en/stable/bus.html).
        print("Connecting to can bus "+self.can_port)
        self.ecu.connect(bustype='socketcan', channel=self.can_port)
        # ecu.connect(bustype='kvaser', channel=0, bitrate=250000)
        # ecu.connect(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000)
        # ecu.connect(bustype='ixxat', channel=0, bitrate=250000)
        # ecu.connect(bustype='vector', app_name='CANalyzer', channel=0, bitrate=250000)
        # ecu.connect(bustype='nican', channel='CAN0', bitrate=250000)
        # ecu.connect('testchannel_1', bustype='virtual')

        # add CA to the ECU
        self.ecu.add_ca(controller_application=self.ca)
        self.ca.subscribe(self.ca_receive)
        # send five turn updates per second
        self.ca.add_timer(0.2, self.ca_timer_callback)
        # by starting the CA it starts the address claiming procedure on the bus
        self.ca.start()

    def __del__(self):
        print("Deinitializing")
        self.ca.stop()
        self.ecu.disconnect()
