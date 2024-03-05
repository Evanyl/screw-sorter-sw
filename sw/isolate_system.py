
from datetime import datetime
import sys
from threading import Thread
from picamera2 import Picamera2
from imaging import isolation_image_and_process


############################################################################
#              S T A T E    M A C H I N E   C O N S T A N T S             #
############################################################################
REGION_ONE_BOX = ((20,10),(60,100)) # Corrsponds to direct output of belt 1 
                                    # top-left corner to bottom-right corner
REGION_TWO_BOX = ((80,220),(300,400)) # direct output of belt 2, just before chute
class IsolateSystem:

    ############################################################################
    #              S T A T E    M A C H I N E    F U N C T I O N S             #
    ############################################################################
    
    def __idle_state_func(self):
        next_state = self.curr_state
        for line in sys.stdin:
            if line.rstrip() == "start-isolate":
                self.thread = Thread(target=isolation_image_and_process, args=(self.camera, self.thread_data))
                next_state = "isolation-image-and-process"
            else:
                pass
        return next_state
    
    def __isolation_image_and_process_state_func(self):
        # camera is being queried, awaiting result
        next_state = self.curr_state
        if self.station_state == "move-belt-one" and self.thread.is_alive() == False:
            self.core_comms.updateOutData("belt_one_distance",
                                            self.thread_data["belt_one_distance"])
            self.des_station_state = "move-belt-one"
            next_state = "move-belt-one"
        if self.station_state == "move-belt-two" and self.thread.is_alive() == False:
            self.core_comms.updateOutData("belt_two_distance",
                                            self.thread_data["belt_two_distance"])
            self.des_station_state = "move-belt-two"
            next_state = "move-belt-two"
        else:
            # waiting for processing to complete
            pass
        
        return next_state
    
    def __move_belt_one_state_func(self):
        next_state = self.curr_state
        if self.station_state == "move-belt-one" and self.thread.is_alive() == False:
            # completed motion
            self.thread = Thread(target=isolation_image_and_process, args=(self.camera, self.thread_data))
            next_state = "isolation-image-and-process"
        else:
            # wait for belt to finish movement
            pass
        return next_state

    def __move_belt_two_state_func(self):  
        next_state = self.curr_state  
        if self.station_state == "move-belt-two" and self.thread.is_alive() == False:
            # completed motion
            self.thread = Thread(target=isolation_image_and_process, args=(self.camera, self.thread_data))
            next_state = "isolation-image-and-process"
        else:
            # wait for belt to finish movement
            pass
        return next_state
    
    def __move_chute(self):
        # TODO think of how to integrate this fcn into code
        # required for accept/reject.
        next_state = self.curr_state
        return next_state

    ############################################################################
    #                 P U B L I C    C L A S S    M E T H O D S                #
    ############################################################################

    def __init__(self, core_comms):
        self.switch_dict = \
        {
            "idle":                             self.__idle_state_func,
            "isolation-image-and-process":      self.__isolation_image_and_process_state_func,
            "move-belt-one":                    self.__move_belt_one_state_func,
            "move-belt-two":                    self.__move_belt_two_state_func,
        }

        self.thread_data = \
        {
            "belt-one-distance": 0.0,
            "belt-two-distance": 0.0
        }

        self.camera = Picamera2()

        self.curr_state = "idle"
        self.des_station_state = "idle"
        self.station_state = "startup"

        self.core_comms = core_comms
        self.thread = Thread()

    def run100ms(self, scheduler):
        if scheduler.taskReleased("isolate_system"):

            # get last station_state
            self.station_state = self.core_comms.getInData()["curr_isolation_state"]
            # send next desired state
            self.core_comms.updateOutData("des_state", self.des_station_state)

            # execute the state machine TODO fix this call here, causing fault?
            self.curr_state = self.switch_dict[self.curr_state]()
