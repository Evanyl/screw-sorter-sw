
from datetime import datetime
import json
from threading import Thread
# import threading
# from imaging import image_and_process
from inference import Predictor
from imaging import Imager

class ClassifySystem:
    
    ############################################################################
    #              S T A T E    M A C H I N E    F U N C T I O N S             #
    ############################################################################
    
    def __idle_state_func(self):
        next_state = self.curr_state
        if self.station_state == "idle" and self.shared_data["start-imaging"] == True:
            # indicate that we are processing the isolated fastener
            self.shared_data["start-imaging"] = False
            next_state = "top-down"
            self.des_station_state = "top-down"
        else:
            # do nothing, the station is homing still...
            pass
        return next_state
    
    def __top_down_state_func(self):
        next_state = self.curr_state
        if self.station_state == "top-down" and self.thread.is_alive() == False:
            # branch off a thread to handle imaging, processing, storage...
            self.thread = Thread(target=self.imager.image_and_process,
                                 args=[self.curr_state])
            self.shared_data["classifying"] = True
            self.thread.start()
            next_state = "image-and-process"
        else:
            # do nothing, station assuming top-down position
            pass
        return next_state
    
    def __image_and_process_state_func(self):
        next_state = self.curr_state
        if self.station_state == "top-down" and self.thread.is_alive() == False:
            # imaging and processing is finished, pass corr-angle to core_comms
            self.shared_data["classifying"] = False
            self.core_comms.updateOutData("corr_angle", self.imager.corr_angle)
            self.des_station_state = "side-on"
            next_state = "side-on"
        if self.station_state == "side-on" and self.thread.is_alive() == False:
            self.shared_data["classifying"] = False
            self.thread = Thread(target=self.predictor.predict, 
                                 args=[self.imager.composed_path])
            self.thread.start()
            self.des_station_state = "idle"
            next_state = "inference"
        else:
            # waiting for imaging and processing thread to finish
            pass 
        return next_state         
    
    def __side_on_state_func(self):
        next_state = self.curr_state
        if self.station_state == "side-on" and self.thread.is_alive() == False:
            # break off a new thread for side-on imaging
            self.thread = Thread(target=self.imager.image_and_process, 
                                 args=[self.curr_state])
            self.shared_data["classifying"] = True
            self.thread.start()
            next_state = "image-and-process"
        else:
            # do nothing, station assuming side-on position
            pass
        return next_state

    def __inference_state_func(self):
        next_state = self.curr_state
        if self.station_state == "idle" and self.thread.is_alive() == False:
            # finished inference, print it out for now
            preds = self.predictor.decode(self.predictor.predictions)
            next_state = "idle"

            self.run_number += 1

            ui_comms_out = {
                "action": "process_results",
                "top_img_path": str(self.imager.top_down_path),
                "raw_top_img_path": str(self.imager.raw_top_down_path),
                "side_img_path": str(self.imager.side_on_path),
                "raw_side_img_path": str(self.imager.raw_side_on_path),
                "composed_path": str(self.imager.composed_path),
                "inference_results": preds,
                "run_number": self.run_number,
            }

            with open(self.core_comms.ui_comms_path, 'w') as f:
                json.dump(ui_comms_out, f)

        else:
            # performing inference, wait for thread to finish
            pass
        return next_state
    
    ############################################################################
    #                 P U B L I C    C L A S S    M E T H O D S                #
    ############################################################################

    def __init__(self, core_comms, out_dir_path, model_path, decoder_path, shared_data):
        # state machine definition
        self.switch_dict = \
        {
            "idle":              self.__idle_state_func,
            "top-down":          self.__top_down_state_func,
            "image-and-process": self.__image_and_process_state_func,
            "side-on":           self.__side_on_state_func,
            "inference":         self.__inference_state_func,
        }
        # instance variables
        self.shared_data = shared_data
        self.curr_state = "idle"
        self.des_station_state = "idle"
        self.station_state = "startup"
        self.core_comms = core_comms
        self.thread = Thread()
        self.imager = Imager(out_dir_path)
        self.predictor = Predictor(model_path, decoder_path) 

        self.run_number = 0

    def run200ms(self, scheduler):
        if scheduler.taskReleased("classify_system"):
            # print(self.curr_state)
            # get last station_state
            self.station_state = self.core_comms.getInData()["curr_state"]
            # send next desired state
            self.core_comms.updateOutData("des_state", self.des_station_state)
            # call state updating function
            self.curr_state = self.switch_dict[self.curr_state]()
