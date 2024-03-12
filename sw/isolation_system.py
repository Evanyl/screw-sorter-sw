
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
    
    def __idle_state_func(self):
        next_state = self.curr_state
        if self.station_state == "idle" and self.thread.is_alive() == False:
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
            # update core_comms with newly populated variables
            # 
            # --insert some logic based off isolation_image_and_process() results--
            #
            if self.thread_data["isolated"] == True and self.depositor_state == "idle":
                # do xyz
                pass
            self.core_comms.updateOutData("belt_top_steps", self.thread_data["belt_top_steps"])
            self.core_comms.updateOutData("belt_top_dir", self.thread_data["belt_top_dir"])
            self.core_comms.updateOutData("belt_top_rate", self.thread_data["belt_top_rate"])
            self.core_comms.updateOutData("belt_top_ramp_rate", self.thread_data["belt_top_ramp_rate"])
            self.core_comms.updateOutData("belt_top_ramp_window", self.thread_data["belt_top_ramp_window"])
            self.core_comms.updateOutData("belt_bottom_steps", self.thread_data["belt_bottom_steps"])
            self.core_comms.updateOutData("belt_bottom_dir", self.thread_data["belt_bottom_dir"])
            self.core_comms.updateOutData("belt_bottom_rate", self.thread_data["belt_bottom_rate"])
            self.core_comms.updateOutData("belt_bottom_ramp_rate", self.thread_data["belt_bottom_ramp_rate"])
            self.core_comms.updateOutData("belt_bottom_ramp_window", self.thread_data["belt_bottom_ramp_window"])

            next_state = "idle"
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
            "idle":                             self.__idle_state_func,
            "isolation-image-and-process":      self.__isolation_image_and_process_state_func,
        }

        self.thread_data = \
        {
            "isolated": True,
            "belt_top_steps": 0,
            "belt_top_dir": BELT_TOP_FORWARD,
            "belt_top_rate": BELTS_NAV_RATE,
            "belt_top_ramp_rate": BELTS_STARTING_RATE,
            "belt_top_ramp_window": BELTS_RAMP_WINDOW,
            "belt_bottom_steps": 0,
            "belt_bottom_dir": BELT_BOTTOM_FORWARD,
            "belt_bottom_rate": BELTS_NAV_RATE,
            "belt_bottom_ramp_rate": BELTS_STARTING_RATE,
            "belt_bottom_ramp_window": BELTS_RAMP_WINDOW
        }

        self.camera = Picamera2()
        camera_config = self.camera.create_preview_configuration()
        self.camera.configure(camera_config)

        self.curr_state = "idle"
        self.des_station_state = "idle"
        self.station_state = "count"

        self.core_comms = core_comms
        self.thread = Thread()

    def run100ms(self, scheduler):
        if scheduler.taskReleased("isolation_system") and ISOLATION_ACTIVE:
            # get last station_state
            self.station_state = self.core_comms.getInData()["curr_isolation_state"]
            self.depositor_state = self.core_comms.getInData()["curr_depositor_state"]              
            
            # execute the state machine TODO fix this call here, causing fault?
            self.curr_state = self.switch_dict[self.curr_state]()
