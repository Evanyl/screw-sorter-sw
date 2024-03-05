
from datetime import datetime
import sys
from threading import Thread
from imaging import image_and_process

class ClassifySystem:
    
    ############################################################################
    #              S T A T E    M A C H I N E    F U N C T I O N S             #
    ############################################################################
    
    def __idle_state_func(self):
        next_state = self.curr_state
        for line in sys.stdin:
            if line.rstrip() == "start":
                self.des_station_state = "top-down"
                next_state = "top-down"
            else:
                pass # no prompt to start control loop
        return next_state
    
    def __top_down_state_func(self):
        next_state = self.curr_state
        if self.station_state == "top-down" and \
           self.thread.thread_is_alive() == False:
            # branch off a thread to handle imaging, processing, storage...
            self.thread = Thread(image_and_process, self.thread_data)
            next_state = "image-and-process"
        else:
            # do nothing, station assuming top-down position
            pass
        return next_state
    
    def __image_and_process_state_func(self):
        
        if self.station_state == "top-down" and \
           self.thread.thread_is_alive() == False:
            # imaging and processing is finished, pass corr-angle to core_comms
            self.core_comms.sendDataself.thread_data["corr_angle"]
        else:
            # waiting for imaging and processing thread to finish
            pass          



    def __side_on_state_func(self):
        next_state = self.curr_state
        if self.station_state == "side-on" and not self.thread.is_alive():
            # break off a new thread for side-on imaging
            pass
    
    def __inference_state_func(self):
        pass

    ############################################################################
    #                 P U B L I C    C L A S S    M E T H O D S                #
    ############################################################################

    def __init__(self, core_comms):
        self.switch_dict = \
        {
            "idle":              self.__idle_state_func,
            "top-down":          self.__top_down_state_func,
            "image-and-process": self.__image_and_process_state_func,
            "side-on":           self.__side_on_state_func,
            "inference":         self.__inference_state_func,
        }
        self.thread_data = \
        {
            "corr_angle": 0.0,
            "pred":       ""
        }
        self.curr_state = "idle"
        self.des_station_state = "idle"

        self.core_comms = core_comms
        self.station_state = ""
        self.thread = Thread()
        self.last_time = datetime.now()

    def run200ms(self, scheduler):
        if scheduler.taskReleased("classify_system"):

            # get last station_state
            self.station_state = self.core_comms.getData("classify_system")
            # send next desired state
            self.core_comms.sendData(self.des_station_state)

            # execute the state machine
            self.curr_state = self.switch_dict[self.curr_state]()
