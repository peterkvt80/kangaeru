# kangaeru
Can bus J1936 demonstration ECUs using a Raspberry Pi Sense Hat
J1939 is a CAN bus standard that is used for heavy machinery like buses, trucks and agricultural equipment. Kangaeru consists of three ECUs. The first is an eight bit GPO. The second returns various Sense Hat values. The third ECU hosts a GUI for the control and monitoring of the other ECUs.
You only need a Raspberry Pi and Sense Hat to run these ECUs if you use a virtual CAN bus. However, if you add CAN interfaces then you can connect them to a real CAN bus.
