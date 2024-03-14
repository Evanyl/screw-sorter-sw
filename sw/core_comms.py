 
from datetime import datetime
import serial
import json

class CoreComms:

    def __init__(self):
        self.id = "core_comms"
        self.connection = serial.Serial("/dev/ttyUSB0", 115200)
        self.out_data = \
        {
            "classify_des_state": "idle",
            "corr_angle": 0.0,
            "belts_des_state": "idle",
            "belt_top_steps": 0, 
            "belt_bottom_steps": 0
        } 
        self.in_data = \
        {
            "curr_imaging_state": "idle",
            "curr_isolation_state": "idle",
            "curr_depositor_state": "idle"
        }
        self.classify_state_decode = \
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
        self.belts_state_decode = \
        {
            0: "idle",
            1: "active",
            2: "count"
        }
        self.depositor_state_decode = \
        {
            0: "startup",
            1: "idle",
            2: "sweeping",
            3: "centering",
            4: "dropping",
            5: "entering-idle",
            6: "count"
        }
        self.last_time = datetime.now()

    def run50ms(self, scheduler):
        if scheduler.taskReleased(self.id):
            t = datetime.now()
            dt = int((t-self.last_time).total_seconds()*1000)
            self.last_time = t
            print(f"dt: {dt}")

            # Read in new serial data
            if self.connection.in_waiting > 0:
                s = self.connection.read_until(b"\n").decode('utf-8')
                # print(s)
                self.in_data = self.fromString(s)
            else:
                # no new data, don't read from the serial buffer
                pass
            
            # Send an updated version of out_data
            outstr = self.toString()
            print(outstr)
            self.connection.write(outstr)

    def updateOutData(self, name, val):
        self.out_data[name] = val

    def toString(self):
        angle = self.out_data["corr_angle"]
        classify_str = f"classify-des-state {self.out_data['classify_des_state']} " + \
                         f"corr-angle {angle} "
        # send a belt move command once.
        if self.in_data["curr_isolation_state"] == "active":
            self.out_data['belt_top_steps'] = 0
            self.out_data['belt_bottom_steps'] = 0
            belts_out_str = "belts-nop"
        else:
            belts_out_str = f"belts-des-state " + \
                f"{self.out_data['belt_top_steps']} " + \
                f"{self.out_data['belt_bottom_steps']}"

        return str.encode(classify_str + belts_out_str + "\n")

    def fromString(self, s):
        d = json.loads(s.strip("\n"))
        return {"curr_imaging_state": self.classify_state_decode[d["classify_system_state"]],
                "curr_isolation_state": self.belts_state_decode[d["belts_state"]],
                "curr_depositor_state": self.depositor_state_decode[d["depositor_state"]]}

    def getInData(self):
        return self.in_data

