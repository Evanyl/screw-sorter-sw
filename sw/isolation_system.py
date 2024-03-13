
from datetime import datetime
import sys
from threading import Thread
from picamera2 import Picamera2
from imaging import isolation_image_and_process


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

class IsolationSystem:

    ############################################################################
    #              S T A T E    M A C H I N E    F U N C T I O N S             #
    ############################################################################
    
    def __ready_to_take_photo_state_func(self):
        next_state = self.curr_state
        if self.isolation_system_state == "idle" and self.thread.is_alive() == False:
            self.thread = Thread(target=isolation_image_and_process, args=[self.camera, self.thread_data])
            self.thread.start()
            next_state = "isolation-image-and-process"
        else:
            # do nothing, station still in motion
            pass
        return next_state
    
    def __isolation_image_and_process_state_func(self):
        next_state = self.curr_state
        if self.thread.is_alive() == False:
            # image processing is complete
            # 
            # --insert some logic based off isolation_image_and_process() results--
            # for example, this if-statement
            if self.thread_data["isolated"] == True and self.depositor_system_state == "idle":
                # do xyz delivery
                pass
            self.core_comms.updateOutData("belt_top_steps", self.thread_data["belt_top_steps"])
            self.core_comms.updateOutData("belt_bottom_steps", self.thread_data["belt_bottom_steps"])
            next_state = "photo"
        else:
            # do nothing, still processing
            pass
        return next_state
    
    
    ############################################################################
    #                 P U B L I C    C L A S S    M E T H O D S                #
    ############################################################################

    def __init__(self, core_comms):
        self.switch_dict = \
        {
            "photo":                             self.__ready_to_take_photo_state_func,
            "isolation-image-and-process":       self.__isolation_image_and_process_state_func,
        }

        self.thread_data = \
        {
            "isolated": True,
            "belt_top_steps": 0,
            "belt_bottom_steps": 0,
        }

        self.camera = Picamera2()
        camera_config = self.camera.create_preview_configuration()
        self.camera.configure(camera_config)

        self.curr_state = "photo"
        self.isolation_system_state = "idle"
        self.depositor_system_state = "startup"

        self.core_comms = core_comms
        self.thread = Thread()

    def run100ms(self, scheduler):
        if scheduler.taskReleased("isolation_system") and ISOLATION_ACTIVE:
            # get last station_state
            self.isolation_system_state = self.core_comms.getInData()["curr_isolation_state"]
            self.depositor_system_state = self.core_comms.getInData()["curr_depositor_state"]              
            
            # execute the state machine
            self.curr_state = self.switch_dict[self.curr_state]()
