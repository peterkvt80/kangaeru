# Kangaeru test host
# You must have a CAN bus in order to run this.
# For a virtual CAN port vcan0 (not Windows, sorry)
# Uncomment the socketcan option in kangaeru_io.py
# Bring the virtual can port up as follows
# sudo modprobe vcan
# sudo ip link add dev vcan0 type vcan
# sudo ip link set up vcan0
#
# For Windows you will need to go to a physical CAN port as socketcan is not an option
import os
import argparse
import tkinter as tk
from kangaeru_io import Kangaeru_io
window = tk.Tk()

def start_update(ca):
    # The UI components are updated here
    
    # gpo buttons
    GPOOnline=ca.isGPOOnline()
    for x in range(8):
        if GPOOnline:
            button[x].config(bg="blue")
        else:
            button[x].config(bg="grey")
    
    # yaw rate
    yaw = int(ca.get_yaw_rate())
    rot_number.config(text = str(yaw))
    
    # temperature
    temp_number.config(text = str(ca.get_temperature()))
    
    # pressure
    pressure = "{:.2f}".format(ca.get_pressure())
    pressure_number.config(text = (pressure))
    
    # humidity
    humidity = "{:.2f}".format(ca.get_humidity())
    humidity_number.config(text = (humidity))
    
    # this is how to run a timer function with a parameter
    command=lambda ca=ca: start_update(ca)
    
    window.after(1000, command) # This reads in values from the IO and displays them

def show_msg(n):
    ca.send(n)
    
parser = argparse.ArgumentParser(description="my argument parser")
parser.add_argument("serial_number", nargs="?", default="3456") # Serial number integer
parser.add_argument("port", nargs="?", default="vcan0") # usually vcan0 or can0
args = parser.parse_args()
print("port = " + args.port + " id = " + args.serial_number)

response = os.system("sudo ip link set "+args.port+" type can bitrate 250000")
if response!=0:
    print("Invalid CAN bus. " + str(response))
    exit() 

response = os.system("sudo ip link set "+args.port+" up")
if response!=0:
    print("Invalid CAN bus. " + str(response))
    exit() 
    
greeting = tk.Label(text="Kangaeru test ECU")
greeting.grid( row = 0, column = 0)

# GPO buttons
gpo_label = tk.Label(text="GPO", background="#34A2FE", width=14, anchor="w")
gpo_label.grid( row = 1, column = 0)
button = []
for x in range(8):
    button.append(tk.Button(
        text=str(x),
        width=8,
        height=2,
        bg="blue",
        fg="yellow",
        command=lambda x=x:show_msg(x)
    ))
    button[x].grid( row = 1, column = x+1)
    
# Yaw rate display
rot_label = tk.Label(text="Yaw deg/s", background="#34A2FE", width=14, anchor="w")
rot_label.grid(row = 2, column = 0)
rot_number = tk.Label(text="nnn.nn", background="#ffffff", height=2, width=22, anchor="w")
rot_number.grid(row = 2, column = 1, columnspan = 2)

# Temperature display
temp_label = tk.Label(text="Temp °C", background="#34A2FE", width=14, anchor="w")
temp_label.grid(row = 3, column = 0)
temp_number = tk.Label(text="nnn.nn", background="#ffffff", height=2, width=22, anchor="w")
temp_number.grid(row = 3, column = 1, columnspan = 2)

# Atmospheric pressure display
pressure_label = tk.Label(text="Pressure mBar", background="#34A2FE", width=14, anchor="w")
pressure_label.grid(row = 4, column = 0)		
pressure_number = tk.Label(text="nnn.nn", background="#ffffff", height=2, width=22, anchor="w")
pressure_number.grid(row = 4, column = 1, columnspan = 2)

# Humidity display
humidity_label = tk.Label(text="Humidity %", background="#34A2FE", width=14, anchor="w")
humidity_label.grid(row = 5, column = 0)
humidity_number = tk.Label(text="nnn.nn", background="#ffffff", height=2, width=22, anchor="w")
humidity_number.grid(row = 5, column = 1, columnspan = 2)

# controller application
ca = Kangaeru_io(args.serial_number, args.port) # default vcan0
ca.run()
start_update(ca)
window.mainloop()