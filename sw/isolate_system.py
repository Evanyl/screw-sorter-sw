
from threading import Thread

from isolator import Isolator, IsolatorMission, IsolatorWorldView

BELT_WAITING_COUNT = 10
IDLE_WAITING_COUNT = 10

class IsolateSystem:

    def __image_and_process_state_func(self):
        # take picture and process
        next_state = self.curr_state
        if self.thread.is_alive() == False:
            # populate data with results of imaging
            self.top_belt_steps = self.isolator.belts_command.b2steps
            self.bottom_belt_steps = self.isolator.belts_command.b1steps
            if self.shared_data["start-imaging"] == False:
                # only update start-imaging flag if prev consumed
                self.shared_data["start-imaging"] = self.isolator.belts_command.start_imaging
            else:
                # prev flag hasn't been consumed
                pass
            # self.start_imaging = self.isolator.belts_command.start_imaging
            self.des_belt_state = "active"
            self.belt_count = 0
            next_state = "waiting-for-belts"
        else:
            # do nothing, waiting for imaging and processing to finsh
            pass
        return next_state
    
    def __idle_state_func(self):
        next_state = self.curr_state
        self.idle_count += 1
        # wait until belts_state is idle
        if self.belts_state == "idle" and self.idle_count >= IDLE_WAITING_COUNT:
            # reset the idle counter, don't check the camera too quick after
            #     belt movement.
            self.idle_counter = 0
            # create an imaging thread and switch states
            accepting = self.depositor_state=="idle" and \
                        self.shared_data["start-imaging"] == False
            self.thread = \
                Thread(target=self.isolator.spin,
                       args=[
                           IsolatorMission.ISOLATE,
                           IsolatorWorldView(b1_moving=False,
                                             b2_moving=False,
                                             depositor_accepting=accepting)
                           ]
                )
            self.thread.start()
            next_state = "image-and-process"
        return next_state
    
    def __waiting_for_belts_state_func(self):
        # dealing with belts taking multiple cycles to report "active" state
        self.des_belt_state = "idle"
        next_state = self.curr_state
        if self.belts_state == "idle" and self.belt_count < BELT_WAITING_COUNT:
            self.belt_count += 1
        else:
            next_state = "idle"
        return next_state
        

    def __init__(self, core_comms, shared_data):
        self.switch_dict = \
        {
            "idle":              self.__idle_state_func,
            "image-and-process": self.__image_and_process_state_func,
            "waiting-for-belts": self.__waiting_for_belts_state_func
        }
        self.shared_data = shared_data
        self.isolator = Isolator()
        self.core_comms = core_comms
        self.thread = Thread()
        self.belts_state = "idle"
        self.des_belt_state = "idle"
        self.curr_state = "idle"
        self.idle_count = 0
        self.belt_count = 0 
        self.depositor_state = "startup"
        # self.start_imaging = False

        self.top_belt_steps = 0
        self.bottom_belt_steps = 0

    def run100ms(self, scheduler):
        if scheduler.taskReleased("isolate_system"):
            a = self.shared_data["start-imaging"]
            print(f"start-imaging (shared): {a}")
            # get last station_state and depositor state
            self.belts_state = self.core_comms.getInData()["belts_curr_state"]
            self.depositor_state = self.core_comms.getInData()["depositor_curr_state"]
            print(f"depositor_state: {self.depositor_state}")
            # send next desired state
            self.core_comms.updateOutData("top_belt_steps", self.top_belt_steps)
            self.core_comms.updateOutData("bottom_belt_steps", self.bottom_belt_steps)
            self.core_comms.updateOutData("belts_des_state", self.des_belt_state)
            # update shared data between controller modules
            # if self.shared_data["start-imaging"] == False:
            #     self.shared_data["start-imaging"] = self.start_imaging
            # else:
            #     pass
            # print(f"start_imaging (machine): {self.start_imaging}")
            print(f"start_imaging (belts): {self.isolator.belts_command.start_imaging}")
            # call state updating function
            self.curr_state = self.switch_dict[self.curr_state]()
