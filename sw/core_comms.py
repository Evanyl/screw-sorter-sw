 
from datetime import datetime
import serial
import json

class CoreComms:

    def __init__(self, out_dir_path, model_path, decoder_path):
        self.id = "core_comms"
        self.connection = serial.Serial("/dev/ttyUSB0", 115200)
        self.out_dir_path = out_dir_path
        self.model_path = model_path
        self.decoder_path = decoder_path
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
            2: "entering-deposited",
            3: "deposited",
            4: "entering-topdown",
            5: "top-down",
            6: "entering-sideon",
            7: "side-on",
            8: "entering-idle",
            9: "count"
        }

    def run50ms(self, scheduler):
        if scheduler.taskReleased(self.id):

            # Read in new serial data
            if self.connection.in_waiting > 0:
                s = self.connection.read_until(b"\n").decode('utf-8')
                self.in_data = self.fromString(s)
            else:
                # no new data, don't read from the serial buffer
                pass
            
            # Send an updated version of out_data
            self.connection.write(self.toString())

    def updateOutData(self, name, val):
        self.out_data[name] = val

    def toString(self):
        angle = self.out_data["corr_angle"]
        return  str.encode("des-state " + self.out_data["des_state"] + \
                f" corr-angle {angle}\n")
    
    def fromString(self, s):
        d = json.loads(s.strip("\n"))
        return {"curr_state": self.state_decode[d["system_state"]]}

    def getInData(self):
        return self.in_data

