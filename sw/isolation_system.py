
from datetime import datetime
import sys
from threading import Thread
from picamera2 import Picamera2
from imaging import IsolationImager



############################################################################
#              S T A T E    M A C H I N E   C O N S T A N T S             #
############################################################################
BELTS_NAV_RATE = 750
BELTS_STARTING_RATE = 50
BELTS_RAMP_WINDOW = 250
BELT_TOP_FORWARD = 1
BELT_TOP_BACKWARD = 0
BELT_BOTTOM_FORWARD = 1
BELT_BOTTOM_BACKWARD = 0
ISOLATION_ACTIVE = True
WAIT_LIMIT = 10

class IsolationSystem:

    def set_photo_to_ready(self):
        self.photo_done = True

    ############################################################################
    #              S T A T E    M A C H I N E    F U N C T I O N S             #
    ############################################################################
    
    def __ready_to_take_photo_state_func(self):
        next_state = self.curr_state
        if self.isolation_system_state == "idle" and self.thread.is_alive() == False:
            self.photo_done = False
            print("Getting photo")
            # self.photo = self.camera.capture_array(signal_function=self.set_photo_to_ready)
            self.thread = Thread(target=self.imager.isolation_image_and_process)
            self.thread.start()
            next_state = "isolation-image-and-process"
            print("Photo function is done")
            # next_state = "wait-for-photo"
        else:
            # do nothing, station still in motion
            pass
        return next_state

    def __wait_for_photo_to_finish_state_func(self):
        print("Waiting for photo to arrive")
        next_state = self.curr_state
        if self.photo_done:
            print("Photo obtained!")
            next_state = "isolation-image-and-process"
        else:
            pass # photo capture is multithreaded, waiting on its arrival
        return next_state
    
    def __isolation_image_and_process_state_func(self):
        next_state = self.curr_state
        if self.thread.is_alive() == False:
            # image processing is complete
            # 
            # --insert some logic based off isolation_image_and_process() results--
            # for example, this if-statement
            if self.imager.isolated == True:
                # do xyz delivery
                pass
            self.core_comms.updateOutData("belt_top_steps", self.imager.belt_top_steps)
            self.core_comms.updateOutData("belt_bottom_steps", self.imager.belt_bottom_steps)
            next_state = "wait"
            self.wait_counter = 0
        else:
            # do nothing, still processing
            pass
        return next_state

    def __wait_for_belts_to_turn_on_state_func(self):
        # Belts take a few loops to activate, intermediate waiting state
        next_state = self.curr_state
        if self.isolation_system_state == "active":
            next_state = "photo"
        elif self.wait_counter > WAIT_LIMIT:
            # the belts somehow returned to idle while we were waiting
            # so, we reset to "photo" state because belts are ready now
            next_state = "photo"
        else:
            # do nothing, the belts haven't moved yet
            pass

        self.wait_counter += 1

        return next_state

    
    
    ############################################################################
    #                 P U B L I C    C L A S S    M E T H O D S                #
    ############################################################################

    def __init__(self, core_comms):
        self.switch_dict = \
        {
            "photo":                             self.__ready_to_take_photo_state_func,
            "isolation-image-and-process":       self.__isolation_image_and_process_state_func,
            "wait":                              self.__wait_for_belts_to_turn_on_state_func,
            "wait-for-photo":                    self.__wait_for_photo_to_finish_state_func
        }

        self.imager = IsolationImager()

        self.curr_state = "photo"
        self.isolation_system_state = "idle"
        self.depositor_system_state = "startup"

        self.core_comms = core_comms
        self.thread = Thread()
        self.wait_counter = 0

        self.photo = None
        self.photo_done = False

    def run100ms(self, scheduler):
        if scheduler.taskReleased("isolation_system") and ISOLATION_ACTIVE:
            # get last station_state
            self.isolation_system_state = self.core_comms.getInData()["curr_isolation_state"]
            self.depositor_system_state = self.core_comms.getInData()["curr_depositor_state"]              
            
            # execute the state machine
            # print(f"{self.curr_state} {self.isolation_system_state}")
            self.curr_state = self.switch_dict[self.curr_state]()
