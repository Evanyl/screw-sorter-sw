import time
from picamera2 import Picamera2
import sys
import cv2
import numpy as np
from vimba import *

sys.path.append("./../lib/")
from image_transformer import transform_top_image, \
                              transform_side_image

class Imager:
    def __init__(self, out_dir_path):
        self.out_dir_path = out_dir_path
        self.corr_angle = 0.0
        self.camera = None
        self.side_exposure = 100000
        self.top_exposure = 18000
        self.temp_img_folder = "imgs"
        self.side_on_path = ""
        self.top_down_path = ""
        self.composed_path = ""

    ############################################################################
    #                P R I V A T E    C L A S S    M E T H O D S               #
    ############################################################################ 

    def __setup_camera(self):
            # Retrieve our camera once, set exposure/white balance
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras()
            input_camera = cams[0]
            with input_camera as cam:
                # set the camera exposure
                try:
                    cam.ExposureAuto.set('Continuous')
                except (AttributeError, VimbaFeatureError):
                    print("did not set exposure")
                # set the camera white balance
                try:
                    cam.BalanceWhiteAuto.set('Continuous')
                except (AttributeError, VimbaFeatureError):
                    pass
                # only for GigE cams, try removing this
                try:
                    cam.GVSPAdjustPacketSize.run()
                    while not cam.GVSPAdjustPacketSize.is_done():
                        pass
                except (AttributeError, VimbaFeatureError):
                    pass
                # Query available, open_cv compatible pixel formats
                # prefer color formats over monochrome formats
                cv_fmts = intersect_pixel_formats(cam.get_pixel_formats(),
                                                  OPENCV_PIXEL_FORMATS)
                color_fmts = intersect_pixel_formats(cv_fmts, 
                                                     COLOR_PIXEL_FORMATS)
                cam.set_pixel_format(color_fmts[0])
        self.camera = input_camera

    def __take_image(self, out_file, curr_state):
        with Vimba.get_instance() as vimba:
            with self.camera as cam:
                # set frame capture timeout at max exposure time
                if curr_state == "top-down":
                    cam.ExposureAuto.set("Off")
                    cam.ExposureTime.set(self.top_exposure)
                elif curr_state == "side-on":
                    cam.ExposureAuto.set("Off")
                    cam.ExposureTime.set(self.side_exposure)
                frame = cam.get_frame(timeout_ms=1000000)
                frame = frame.as_numpy_ndarray()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                cv2.imwrite(str(out_file), frame)

    ############################################################################
    #                 P U B L I C    C L A S S    M E T H O D S                #
    ############################################################################ 

    def image_and_process(self, curr_state):
        out_path = self.out_dir_path / self.temp_img_folder
        out_path.mkdir(parents=True, exist_ok=True)

        if not self.camera:
            print("Initializing cam...")
            self.__setup_camera()

        # update imaging parameters based on what type of image is being taken
        file_name = ""
        if curr_state == "top-down":
            file_name = "0_top_down.tiff"
        elif curr_state == "side-on":
            file_name = "1_side_on.tiff"
        else:
            pass
        out_file = out_path / file_name

        # take an image, store it locally, remember the name
        self.__take_image(out_file, curr_state)
        if curr_state == "top-down":
            processed_img, corr_angle = transform_top_image(out_file)
            self.corr_angle = corr_angle
            self.top_down_path = out_file
        elif curr_state == "side-on":
            processed_img = transform_side_image(out_file)
            self.side_on_path = out_file
        else:
            pass
        cv2.imwrite(str(out_file), processed_img)
        # if this is he second image (side-on), form a composed image and save
        if curr_state == "side-on":
            top_img = cv2.imread(str(self.top_down_path))
            side_img = cv2.imread(str(self.side_on_path))
            img_concat = np.concatenate([top_img, side_img], axis=0)
            
            self.composed_path = out_path / "composed.tiff"
            cv2.imwrite(str(self.composed_path), img_concat)
            print(f"Ready for inference at {str(self.composed_path)}")

class IsolationImager:
    def __init__(self):
        self.cam = Picamera2()
        camera_config = self.cam.create_preview_configuration()
        self.cam.configure(camera_config)
        self.cam.start()
        self.belt_top_steps = 0
        self.belt_bottom_steps = 0
        self.isolated = False

    def isolation_image_and_process(self):
        print("Performing isolation imaging/processing...")
        im = self.cam.capture_array(wait=True)
        print("Done getting obj")
        
        fastener_isolated = True

        self.isolated = fastener_isolated
        self.belt_top_steps = 499
        self.belt_bottom_steps = 1000
        time.sleep(3)
        print("Done isolation imaging/processing")