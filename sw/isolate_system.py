
from threading import Thread
from picamera2 import Picamera2
import time

class IsolateSystem:

    def __image_and_process_state_func(self):
        # take picture and process
        next_state = self.curr_state
        if self.thread.is_alive() == False:
            # populate data with results of imaging
            self.core_comms.updateOutData("top_belt_steps", 2000)
            self.core_comms.updateOutData("bottom_belt_steps", 2000)
            self.des_belt_state = "active"
            next_state = "idle"
        else:
            # do nothing, waiting for imaging and processing to finsh
            pass
        return next_state
    
    def __idle_state_func(self):
        next_state = self.curr_state
        # wait until belts_state is idle
        if self.belts_state == "idle":
            # create an imaging thread and switch states
            self.thread = Thread(target=time.sleep,
                                 args=[2])
            next_state = "image-and-process"
        else:
            # do nothing, wait for the belts to finish
            pass
        return next_state

    def __init__(self, core_comms):
        self.switch_dict = \
        {
            "idle":              self.__idle_state_func,
            "image-and-process": self.__image_and_process_state_func
        }
        self.core_comms = core_comms
        self.thread = Thread()
        self.belts_state = "idle"
        self.des_belt_state = "idle"
        self.curr_state = "idle"

    def run100ms(self, scheduler):
        if scheduler.taskReleased("isolate_system"):
            print(self.curr_state)
            # get last station_state
            self.belts_state = self.core_comms.getInData()["belts_curr_state"]
            # send next desired state
            self.core_comms.updateOutData("belts_des_state", self.des_belt_state)
            # call state updating function
            self.curr_state = self.switch_dict[self.curr_state]()
