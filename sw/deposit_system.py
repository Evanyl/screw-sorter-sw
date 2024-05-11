
import json
import random
from ui.screw_utils import process_decoded_predictions

WAIT_FOR_ACTIVE = 5

class DepositSystem:

    box_map = \
    {
        "name1": 0,
        "name2": 1,
        "name3": 2,
    }
    
    def __change_box_state_func(self):
        next_state = self.curr_state
        # wait for system to repond to active request
        if self.active_switch_counter >= WAIT_FOR_ACTIVE:
            # boxes are still moving, command that they should return to idle
            if self.boxes_curr_state == "active":
                self.boxes_des_state = "idle"
            # desired box achieved, return to idle
            elif self.boxes_curr_state == "idle":
                self.active_switch_counter = 0
                next_state = "idle"
        else:
            self.active_switch_counter += 1
        return next_state
    
    def __idle_state_func(self):
        next_state = self.curr_state
        if self.shared_data["start-deposit"] == True and \
           self.boxes_curr_state == "idle":
            # find desired box by processessing inference results.
            self.shared_data["start-deposit"] = False
            with open(self.core_comms.ui_comms_path) as f:
                processed_preds = process_decoded_predictions(
                    json.load(f)["inference_results"]
                )
                print(processed_preds)
            # just generate random box for now...
            self.boxes_des_box = random.randrange(0,16)
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
            self.boxes_curr_state = self.core_comms.getInData("deposit")["boxes_curr_state"]
            # send next desired state
            self.core_comms.updateOutData("boxes_des_state", self.boxes_des_state, "deposit")
            self.core_comms.updateOutData("boxes_des_box", self.boxes_des_box, "deposit")
            # call state updating function
            self.curr_state = self.switch_dict[self.curr_state]()
