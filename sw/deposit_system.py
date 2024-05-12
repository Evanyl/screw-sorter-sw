
import json
from ui.screw_utils import process_decoded_predictions

WAIT_FOR_ACTIVE = 5

class DepositSystem:

    box_map = \
    {
        "M2:0.40mm:hex:socket:6.00mm":                  0,
        "M2:0.40mm:hex:socket:8.00mm":                  1,
        "M2:0.40mm:hex:socket:10.00mm":                 2,
        "M2:0.40mm:hex:socket:12.00mm":                 3,
        "No. 2:56 threads per inch:hex:socket:1/4 in.": 4,
        "No. 2:56 threads per inch:hex:socket:3/8 in.": 5,
        "No. 2:56 threads per inch:hex:socket:1/2 in.": 6,
        "M2.5:0.45mm:hex:socket:6.00mm":                7,
        "M2.5:0.45mm:hex:socket:8.00mm":                8,
        "M2.5:0.45mm:hex:socket:10.00mm":               9,
        "No. 4:40 threads per inch:hex:socket:1/4 in.": 10,
        "No. 4:40 threads per inch:hex:socket:3/8 in.": 11,
        "No. 4:40 threads per inch:hex:socket:1/2 in.": 12,
        "M3:0.50mm:hex:socket:6.00mm":                  13,
        "M3:0.50mm:hex:socket:8.00mm":                  14,
    }
    
    def __change_box_state_func(self):
        next_state = self.curr_state
        # wait for system to repond to active request
        if self.active_switch_counter >= WAIT_FOR_ACTIVE:
            # boxes are still moving, command next state is "idle"
            if self.boxes_curr_state == "active":
                self.boxes_des_state = "idle"
            # desired box achieved, return SW state to "idle"
            elif self.boxes_curr_state == "idle":
                self.active_switch_counter = 0
                next_state = "idle"
                self.shared_data["start-deposit"] = False
        else:
            self.active_switch_counter += 1
        return next_state
    
    def __idle_state_func(self):
        next_state = self.curr_state
        if self.shared_data["start-deposit"] == True and \
           self.boxes_curr_state == "idle":
            # find desired box by processessing inference results.
            with open(self.core_comms.ui_comms_path) as f:
                processed_preds = process_decoded_predictions(
                    json.load(f)["inference_results"]
                )
                # create prediction string
                d = processed_preds
                pred = d["width"][0] + ":" + \
                       d["pitch"][0] + ":" + \
                       d["drive"][0] + ":" + \
                       d["head"][0]  + ":" + \
                       d["length"][0]
                # map prediction to box number
                try:
                    self.boxes_des_box = self.box_map[pred]
                except Exception:
                    self.boxes_des_box = 15

            self.boxes_des_state = "active"
            next_state = "change-box"
        else:
            pass # no prediction yet, wait on a prediction
        return next_state
        
    def __init__(self, core_comms, shared_data):
        self.switch_dict = \
        {
            "idle":       self.__idle_state_func,
            "change-box": self.__change_box_state_func
        }
        # shared objects
        self.shared_data = shared_data
        self.core_comms = core_comms
        # boxes firmware vars
        self.boxes_curr_state = "idle"
        self.boxes_des_state = "idle"
        self.boxes_des_box = 0
        # state machine variables
        self.curr_state = "idle"
        self.active_switch_counter = 0

    def run200ms(self, scheduler):
        if scheduler.taskReleased("deposit"):
            # get new data from firmware side
            self.boxes_curr_state = self.core_comms.getInData("deposit")\
                                                    ["boxes_curr_state"]
            # send next desired state
            self.core_comms.updateOutData("boxes_des_state", 
                                          self.boxes_des_state, "deposit")
            self.core_comms.updateOutData("boxes_des_box", 
                                          self.boxes_des_box, "deposit")
            # call state updating function
            self.curr_state = self.switch_dict[self.curr_state]()
