
from threading import Thread
from picamera2 import Picamera2
import time
from imaging import IsolateImager

WAITING_LIMIT = 10

class IsolateSystem:

    def __image_and_process_state_func(self):
        # take picture and process
        next_state = self.curr_state
        if self.thread.is_alive() == False:
            # populate data with results of imaging
            self.fastener_isolated = self.imager.fastener_isolated
            self.fastener_ready = self.imager.fastener_ready
            self.top_belt_steps = self.imager.belt_top_steps
            self.bottom_belt_steps = self.imager.belt_bottom_steps
            self.des_belt_state = "active"
            self.count = 0
            next_state = "waiting-for-belts-to-start"
        else:
            # do nothing, waiting for imaging and processing to finsh
            pass
        return next_state
    
    def __idle_state_func(self):
        next_state = self.curr_state
        # wait until belts_state is idle
        if self.belts_state == "idle":
            # create an imaging thread and switch states
            self.thread = Thread(target=self.imager.isolation_image_and_process)
            self.thread.start()
            next_state = "image-and-process"
        return next_state
    
    def __waiting_for_belts_to_start_state_func(self):
        # dealing with belts taking multiple cycles to report "active" state
        self.des_belt_state = "idle"
        next_state = self.curr_state
        if self.belts_state == "idle" and self.count < WAITING_LIMIT:
            self.count += 1
        else:
            next_state = "idle"
        return next_state
    
    def __fastener_ready_state_func(self):
        next_state = self.curr_state
        # this state exits when classify_system calls dropping_fastener()
        return next_state
        

    def __init__(self, core_comms):
        self.switch_dict = \
        {
            "idle":              self.__idle_state_func,
            "image-and-process": self.__image_and_process_state_func,
            "waiting-for-belts-to-start": self.__waiting_for_belts_to_start_state_func,
            "fastener-ready": self.__fastener_ready_state_func
        }
        self.core_comms = core_comms
        self.thread = Thread()
        self.system_state = "startup"
        self.belts_state = "idle"
        self.des_belt_state = "idle"
        self.curr_state = "idle"

        self.top_belt_steps = 100
        self.bottom_belt_steps = 100
        self.imager = IsolateImager()
        self.fastener_isolated = False
        self.fastener_ready = False

    ############################################################################
    #                 P U B L I C    C L A S S    M E T H O D S                #
    ############################################################################ 
        
    def get_isolation_status(self):
        return self.fastener_isolated

    def reset_isolation_status(self):
        self.imager.fastener_isolated = False
        self.fastener_isolated = False

    def run100ms(self, scheduler):
        if scheduler.taskReleased("isolate_system"):
            print(self.curr_state)
            # get last station_state
            self.belts_state = self.core_comms.getInData()["belts_curr_state"]
            self.system_state = self.core_comms.getInData()["curr_state"]
            # send next desired state
            self.core_comms.updateOutData("top_belt_steps", self.top_belt_steps)
            self.core_comms.updateOutData("bottom_belt_steps", self.bottom_belt_steps)
            self.core_comms.updateOutData("belts_des_state", self.des_belt_state)
            # call state updating function
            self.curr_state = self.switch_dict[self.curr_state]()
