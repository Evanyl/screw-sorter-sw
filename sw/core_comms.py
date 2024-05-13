from datetime import datetime
import serial
import json

class CoreComms:

    def __init__(self, out_dir_path):
        self.id = "core_comms"

        self.connection0 = serial.Serial("/dev/ttyUSB0", 115200)
        self.connection1 = serial.Serial("/dev/ttyUSB1", 115200)
        self.serial0_calib = False
        self.serial1_calib = False

        self.isolate_classify_connection = None
        self.deposit_connection = None

        # outgoing/ingoing data for isolate_classify
        self.out_data_isolate_classify = \
        {
            "des_state": "idle",
            "corr_angle": 0.0,

            "belts_des_state": "idle",
            "top_belt_steps": 100,
            "bottom_belt_steps": 100
        }
        self.in_data_isolate_classify = \
        {
            "curr_state": "idle",
            "belts_curr_state": "idle",
            "depositor_curr_state": "idle"
        # outgoing/ingoing data for deposit
        self.in_data_deposit = \
        {
            "boxes_curr_state": "startup"
        }
        self.out_data_deposit = \
        {
            "boxes_des_state": "idle",
            "boxes_des_box": 0,
        }
        # state decoding dictionaries
        self.belts_state_decode = \
        {
            0: "idle",
            1: "active"
        }
        self.system_state_decode = \
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
        self.depositor_state_decode = \
        {
            0: "homing",
            1: "idle",
            2: "sweeping",
            3: "centering",
            4: "dropping",
            5: "entering_idle",
            6: "count"
        }
        self.boxes_state_decode = \
        {
            0: "startup",
            1: "idle",
            2: "active"
        }

        self.out_dir_path = out_dir_path
        self.ui_comms_path = self.out_dir_path / "comms.json"

    def run50ms(self, scheduler):
        if scheduler.taskReleased(self.id):
            # read in new serial data
            if not self.serial0_calib and not self.serial1_calib:
                # calibrate the serial connections, monitor just one of two
                if self.connection0.in_waiting > 0:
                    try:
                        s = self.connection0.read_until(b"\n").decode('utf-8')
                        self.in_data_isolate_classify = \
                            self.fromString(s, "isolate_classify")
                        self.isolate_classify_connection = self.connection0
                        self.deposit_connection = self.connection1
                        self.serial0_calib = True
                        self.serial1_calib = True
                    except Exception:
                        self.isolate_classify_connection = self.connection1
                        self.deposit_connection = self.connection0
                        self.serial0_calib = True
                        self.serial1_calib = True
                self.connection0.write(str.encode("calib-serial\n"))
                self.connection1.write(str.encode("calib-serial\n"))
                print("Calibrating Serial Connections")
            else:
                # process commands in a regular fashion
                if self.isolate_classify_connection.in_waiting > 0:
                    s = self.isolate_classify_connection.\
                        read_until(b"\n").decode('utf-8')
                    self.in_data_isolate_classify = \
                        self.fromString(s, "isolate_classify")
                else:
                    pass # no new data, don't read from serial buffer

                if self.deposit_connection.in_waiting > 0:
                    s = self.deposit_connection.read_until(b"\n").\
                        decode('utf-8')
                    self.in_data_deposit = \
                        self.fromString(s, "deposit")
                else:
                    pass # no new data don't read from serial buffer

                # send an updated version of out_data to both connections
                out_str_isolate_classify = self.toString("isolate_classify")
                out_str_deposit = self.toString("deposit")
                self.isolate_classify_connection.write(out_str_isolate_classify)
                self.deposit_connection.write(out_str_deposit)

    def updateOutData(self, name, val, id):
        if id == "isolate_classify":
            self.out_data_isolate_classify[name] = val
        elif id == "deposit":
            self.out_data_deposit[name] = val
        else:
            pass # invalid id, don't update out_data

    def toString(self, id):
        ret = ""
        if id == "isolate_classify":
            # numerical values
            angle = self.out_data_isolate_classify["corr_angle"]
            top_belt_steps = self.out_data_isolate_classify["top_belt_steps"]
            bottom_belt_steps = \
                self.out_data_isolate_classify["bottom_belt_steps"]
            # message string
            ret = str.encode(                                                  \
                "des-state " + self.out_data_isolate_classify["des_state"] +   \
                f" corr-angle {angle:.2f} " +                                  \
                "belts-des-state " + self.out_data_isolate_classify            \
                                     ["belts_des_state"] +                     \
                f" belts-steps {top_belt_steps} {bottom_belt_steps}\n"         \
            )
        elif id == "deposit":
            des_box = self.out_data_deposit["boxes_des_box"]
            ret = str.encode(
                "boxes-des-state " + self.out_data_deposit["boxes_des_state"] +\
                f" boxes-box {des_box}\n"
            )
        else:
            pass # not a valid id, return empty string
        return ret

    def fromString(self, s, id):
        d = json.loads(s.strip("\n"))
        if id == "isolate_classify":
            ret = {
                "curr_state":                                                  \
                    self.system_state_decode[d["system_state"]],
                "belts_curr_state":                                            \
                    self.belts_state_decode[d["belts_state"]],
                "depositor_curr_state":                                        \
                    self.depositor_state_decode[d["depositor_state"]]
            }
        elif id == "deposit":
            ret = {
                "boxes_curr_state": self.boxes_state_decode[d["boxes_state"]],
            }
        else:
            pass # invalid id, don't process string
        return ret

    def getInData(self, id):
        ret = None
        if id == "isolate_classify":
            ret = self.in_data_isolate_classify
        elif id == "deposit":
            ret = self.in_data_deposit
        else:
            pass # invalid id, return None
        return ret

