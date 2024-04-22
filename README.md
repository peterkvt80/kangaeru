# kangaeru
Can bus J1936 demonstration ECUs using a Raspberry Pi Sense Hat.

J1939 is a CAN bus standard that is used for heavy machinery like buses, trucks and agricultural equipment. Kangaeru consists of three ECUs. The first is an eight bit GPO. The second returns various Sense Hat values. The third ECU hosts a GUI for the control and monitoring of the other ECUs.

You only need a Raspberry Pi and Sense Hat to run these ECUs if you use a virtual CAN bus. However, if you add CAN interfaces then you can connect them to a real CAN bus.
Due to changes in Raspberry Pi you should use a legacy OS version. Below is the Debian Bookworm version. Older versions are much simple and the instructions are on the Wiki.

# Running this demo on the latest Debian Bookworm
Clone the source code
```
cd ~
git clone https://github.com/peterkvt80/kangaeru.git
cd kangaeru
```

Install the libraries into a virtual environment
```
source ./environment.sh
```
.Create a virtual CAN port vcan0. Don't need to do the last line, the python also does this.
```
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```
Source the environment and run kangaeru GUI
Only need to source once per session.
```
source .venv/bin/activate
python3 kangaeru_gui.py
```
run GPO ECU
```
source .venv/bin/activate
python3 ecu_gpo.py
```
run Sense ECU
```
source .venv/bin/activate
python3 ecu_turn_sense.py
```

Install RTIMU Lib in the environment
```
cd ~/kangaeru
source .venv/bin/activate
git clone https://github.com/RPi-Distro/RTIMULib
cd ./RTIMULib/Linux/python/
python3 setup.py build
python3 setup.py install
```
=================
# If you are using an older Raspberry Pi OS such as Buster, then follow instructions below
Older systems do not need a virtual Python environment

Clone the code
```
cd ~
git clone https://github.com/peterkvt80/kangaeru.git
cd kangaeru
```
Install a library
```
pip3 install can-j1939
```
Run thonny

Press "Switch to regular mode" and restart

Go to "Manage packages...

Search on PyPi and install these packages.
```
can-j1939
python-can
```
Back on the command line...
```
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
```
Now you can run the three ECUs.

Run ecu_gpo.py in Thonny.

Start the sensors using another terminal and type
```
python3 ecu_turn_sense.py
```
Start the GUI by typing
```
python3 kangaeru_gui.py
```
This should bring up a GUI with sensor values and buttons hat will light LEDs on the Sense Hat.





