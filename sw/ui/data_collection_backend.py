#!/usr/bin/env python3

from PyQt5 import QtCore, QtGui, QtWidgets

import cv2
import sys
import shutil
import json

from datetime import datetime

from ui.camera_worker import CameraWorker
from ui.data_collection_core_ui import DataCollectionCoreUi
from ui.screw_utils import create_label, process_decoded_predictions

from pathlib import Path

IMAGING_STATION_VERSION="1.0"
IMAGING_STATION_CONFIGURATION="A1"


class My_App(DataCollectionCoreUi):
    def __init__(self, operator_name, img_dir_path):
        super().__init__()
        # Set the date for this session
        self.session_date = datetime.now()
        self.operator_name = operator_name
        self.working_files_path = img_dir_path
        self.comms_path = self.working_files_path / "comms.json"
        self.comms_in = {}
        self.session_path = None
        self.workings_imgs_path = self.working_files_path / "imgs"
        self.setup_working_files_dir()

        self.setup_camera_worker()

        self.setup_labelling()

    def setup_camera_worker(self):
        self.camera_worker = CameraWorker(self.comms_path)
        self.camera_worker_thread = QtCore.QThread()
        self.camera_worker.moveToThread(self.camera_worker_thread)
        self.camera_worker_thread.start()

        self.camera_worker.action_finished.connect(self.handle_images)

        self.inference_button.clicked.connect(self.camera_worker.run_inference)
        self.labelling_button.clicked.connect(self.camera_worker.run_labelling)

    @QtCore.pyqtSlot(str)
    def handle_images(self, action_finished):
        with open(self.comms_path) as f:
            self.comms_in = json.load(f)
        if action_finished == "labelling":
            photo1 = self.pixmap_from_path(self.comms_in['raw_top_img_path']).scaled(800, 800, QtCore.Qt.KeepAspectRatio)
            photo2 = self.pixmap_from_path(self.comms_in['raw_side_img_path']).scaled(800, 800, QtCore.Qt.KeepAspectRatio)
            self.photo1.setPixmap(photo1)
            self.photo2.setPixmap(photo2)
            self.tabWidget.setCurrentIndex(1)
        elif action_finished == "inference":
            processed_preds = process_decoded_predictions(self.comms_in['inference_results'])
            self.display_inference_results(processed_preds)
            composed = self.pixmap_from_path(self.comms_in['composed_path']).scaled(800, 800, QtCore.Qt.KeepAspectRatio)
            self.photo1.setPixmap(composed)
            self.tabWidget.setCurrentIndex(2)
        else:
            print(f"{self.mode} should never be this")


    def setup_working_files_dir(self):
        # replace all potential bad filename characters with underscores
        filename_date = self.session_date.strftime("%y_%m_%d_%H_%M_%S")

        session_name = f"real_img_ses_v{IMAGING_STATION_VERSION}_c{IMAGING_STATION_CONFIGURATION}_{filename_date}_{self.operator_name}"

        self.session_path = self.working_files_path / "sessions" / session_name

        # Folder should not already exist!
        self.session_path.mkdir(parents=True)

        with open(self.comms_path, 'w') as f:
            json.dump({'action': 'idle'}, f)

    def setup_labelling(self):
        self.save_images_button.clicked.connect(self.save_images)
        self.redo_images_button.clicked.connect(self.redo_images)

    def save_images(self):
        label = create_label(self.filename_variables)
        uuid = label['uuid']
        images_dir = self.session_path / f"real_{self.fastener_filename.text()}_{uuid}"
        images_dir.mkdir()

        with open(images_dir / f"{uuid}.json", "w") as f:
            json.dump(label, f)

        shutil.copyfile(self.comms_in['top_img_path'], images_dir / f"0_{uuid}.tiff")
        shutil.copyfile(self.comms_in['side_img_path'], images_dir / f"1_{uuid}.tiff")

        self.tabWidget.setCurrentIndex(0)

    def redo_images(self):
        self.tabWidget.setCurrentIndex(0)

    def pixmap_from_path(self, img_path):
        cv_img = cv2.imread(img_path)
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        height, width, channel = cv_img.shape
        bytesPerLine = channel * width
        q_img = QtGui.QImage(cv_img.data, width, height,
                             bytesPerLine, QtGui.QImage.Format_RGB888)
        return QtGui.QPixmap.fromImage(q_img)


def start_ui(operator_name, img_dir_path):
    app = QtWidgets.QApplication([])
    myApp = My_App(operator_name, img_dir_path)
    myApp.show()
    app.exec_()
