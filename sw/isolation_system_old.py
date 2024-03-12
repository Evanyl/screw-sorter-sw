
from datetime import datetime
import sys
from threading import Thread
from picamera2 import Picamera2
from imaging import isolation_image_and_process


############################################################################
#              S T A T E    M A C H I N E   C O N S T A N T S             #
############################################################################
FIXED_DEPOSITOR_STEP_COUNT = 250
class IsolationSystem:

    ############################################################################
    #              S T A T E    M A C H I N E    F U N C T I O N S             #
    ############################################################################
    
    def __idle_state_func(self):
        next_state = self.curr_state
        if self.station_state == "idle":
            next_state = "attempt-isolated"
            self.des_station_state = "attempt-isolated"
        else:
            # do nothing, station still in startup
            pass
        return next_state
    
    def __attempt_isolated_state_func(self):
        next_state = self.curr_state
        if self.station_state == "idle" and self.thread.is_alive() == False:
            self.thread = Thread(target=isolation_image_and_process, args=[self.camera, self.thread_data])
            self.thread.start()
            next_state = "isolation-image-and-process"
        else:
            # do nothing, belts still in motion
            pass
        return next_state

    def __isolation_image_and_process_state_func(self):
        # camera is being queried, awaiting result
        next_state = self.curr_state
        if self.station_state == "idle" and self.thread.is_alive() == False:
            if self.thread_data["fastener_present"] == True:
                if self.thread_data["isolated"] == True:
                    self.des_station_state = "isolated"
                    next_state = "deliver"
                else:
                    self.des_station_state = "reject"
                    next_state = "reject"
            else:
                self.core_comms.updateOutData("belt_top_steps",
                                            self.thread_data["belt_top_steps"])
                self.core_comms.updateOutData("belt_bottom_steps",
                                            self.thread_data["belt_bottom_steps"])
                self.des_station_state = "attempt-isolated"
                next_state = "attempt-isolated"
        else:
            # waiting for processing to complete
            pass
        return next_state
    
    def __deliver_state_func(self):
        next_state = self.curr_state
        # TODO implement boolean check for if depositor is ready for fastener
        if self.station_state == "isolated":
            self.core_comms.updateOutData("belt_top_steps", 0)
            self.core_comms.updateOutData("belt_bottom_steps",
                                        FIXED_DEPOSITOR_STEP_COUNT)
            self.des_station_state = "delivered"
            next_state = "idle"
        else:
            pass # station has not updated its variable to isolated
        return next_state
    
    def __reject_state_func(self):
        next_state = self.curr_state
        if self.station_state == "reject":
            self.des_station_state == "idle"
            next_state = "idle"
        else:
            pass # station still in process of rejection
        return next_state
    
    ############################################################################
    #                 P U B L I C    C L A S S    M E T H O D S                #
    ############################################################################

    def __init__(self, core_comms):
        self.switch_dict = \
        {
            "idle":                             self.__idle_state_func,
            "isolation-image-and-process":      self.__isolation_image_and_process_state_func,
            "attempt-isolated":                 self.__attempt_isolated_state_func,
            "deliver":                          self.__deliver_state_func,
            "reject":                           self.__reject_state_func
        }

        self.thread_data = \
        {
            "fastener_present": False,
            "isolated": False,
            "belt_top_steps": 0.0,
            "belt_bottom_steps": 0.0
        }

        self.camera = Picamera2()
        camera_config = self.camera.create_preview_configuration()
        self.camera.configure(camera_config)

        self.curr_state = "idle"
        self.des_station_state = "idle"
        self.station_state = "startup"

        self.core_comms = core_comms
        self.thread = Thread()

    def run100ms(self, scheduler):
        if scheduler.taskReleased("isolation_system"):

            # get last station_state
            self.station_state = self.core_comms.getInData()["curr_isolation_state"]
            # send next desired state
            self.core_comms.updateOutData("des_state", self.des_station_state)

            # execute the state machine TODO fix this call here, causing fault?
            self.curr_state = self.switch_dict[self.curr_state]()
