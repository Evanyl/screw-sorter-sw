 
from datetime import datetime
import serial
import json

class CoreComms:

    def __init__(self):
        self.id = "core_comms"
        self.connection = serial.Serial("/dev/ttyUSB0", 115200)
        self.out_data = \
        {
            "des_state": "idle",
            "corr_angle": 0.0,
        }
        self.in_data = \
        {
            "curr_state": "idle"
        }
        self.state_decode = \
        {
            0: "startup",
            1: "idle",
            2: "entering_deposited",
            3: "deposited",
            4: "entering_topdown",
            5: "topdown",
            6: "entering_sideon",
            7: "sideon",
            8: "entering_idle",
            9: "count"
        }

    def run50ms(self, scheduler):
        if scheduler.taskReleased(self.id):

            # Read in new serial data
            if self.connection.in_waiting() > 0:
                self.in_data.fromString(self.connection.read_until("\n"))
            else:
                # no new data, don't read from the serial buffer
                pass
            
            # Send an updated version of out_data
            self.connection.write(self.toString(self.out_data))

    def updateOutData(self, name, val):
        self.out_data[name] = val

    def toString(self):
        return "des-state " + self.outData["des_state"] + \
                f" corr-angle {self.outData["corr_angle"]}\n"
    
    def fromString(self, s):
        d = json.loads(s.strip("\n"))
        return {"curr_state": self.state_decode[d["system_state"]]}

