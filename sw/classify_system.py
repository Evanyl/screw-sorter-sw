
from datetime import datetime
# from serial import Serial
import sys
import threading

class ClassifySystem:

    def __idle_state_func(self, curr_state):
        next_state = curr_state
        for line in sys.stdin:
            if line.rstrip() == "start": # replace with input from isolate
                next_state = "top-down"
            else:
                pass # no prompt to start control loop
        return next_state
    
    def __top_down_state_func(self, curr_state):
        next_state = curr_state
        if self.response == "top-down" and self.thread is None:
            # create a new thread and start it to handle imaging
            pass
        elif self.response == "top-down" and self.thread_is_alive():
            # performing the imaging, stay static
            pass
        else:
            # create a new thread and start it to handle processing + storage
            self.desired_state = "side-on"
            self.next_state = "side-on"
        return next_state

    def __side_on_state_func(self, curr_state):
        next_state = curr_state
        if self.response == "side-on" and not self.thread.is_alive():
            # break off a new thread for side-on imaging
            pass

    def __init__(self, core_comms):
        self.switch_dict = \
        {
            "idle": self.__idle_state_func, # wait for a prompt from isolation
            "entering-top-down": self.__entering_top_down_state_func, # prompt the fw to enter top-down, wait
            "top-down": self.__top_down_state_func, # take image, process it, store it
            "entering-side-on": self.__entering_side_on_state_func, # prompt the fw to enter side-on,
            "side-on": self.__side_on_state_func, # take image, process it, store it
            "inference": self.__inference_state_func, # prompt fw to enter idle, combine the images and predict
        }
        self.curr_state = "idle"
        self.core_comms = core_comms
        self.desired_state = "idle"
        self.response = ""
        self.thread = None
        self.last_time = datetime.now()

    def run200ms(self, scheduler):
        if scheduler.taskReleased("classify_system"):

            # get last response
            self.response = self.core_comms.getData("classify_system")
            # send next desired state
            self.core_comms.sendData(self.desired_state)

            # execute the state machine
            self.curr_state = self.switch_dict[self.curr_state]
