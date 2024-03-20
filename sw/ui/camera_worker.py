from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import time
import json

class CameraWorker(QtCore.QObject):
    action_finished = QtCore.pyqtSignal(str)

    def __init__(self, comms_path):
        super(CameraWorker, self).__init__()
        self.comms_path = comms_path

    @QtCore.pyqtSlot()
    def run_inference(self):
        print("Starting loop")
        with open(self.comms_path, 'w') as f:
            json.dump({'action': 'image'}, f)
        finished = False
        start = time.time()
        while not finished:
            time.sleep(1)
            with open(self.comms_path) as f:
                comms_in = json.load(f)
            #QtCore.QCoreApplication.processEvents()
            print(comms_in['action'])
            if comms_in['action'] == 'process_results':
                finished = True

        print("exit loop")
        self.action_finished.emit("inference")

    @QtCore.pyqtSlot()
    def run_labelling(self):
        print("Starting loop")
        with open(self.comms_path, 'w') as f:
            json.dump({'action': 'image'}, f)
        finished = False
        start = time.time()
        while not finished:
            #QtCore.QCoreApplication.processEvents()
            time.sleep(1)
            with open(self.comms_path) as f:
                comms_in = json.load(f)
            #QtCore.QCoreApplication.processEvents()
            if comms_in['action'] == 'process_results':
                finished = True

        print("exit loop")
        self.action_finished.emit("labelling")
