import time
import sys

sys.path.append("./../lib/")
from image_transformer import transform_side_image
from image_transformer import transform_top_image

def setup_camera()

def image_and_process(shared_data, curr_state):
    print("imaging and processing...")

    file_name = ""
    exposure_time = 0
    # update imaging parameters based on what type of image is being taken
    if curr_state == "top-down":
        file_name = "0_top_down.tiff"
        exposure_time = 250000
    elif curr_state == "side-on":
        file_name = "1_side_on.tiff"
        exposure_time = 250000
    else:
        pass

    # take an image, store it locally, remember the name

    time.sleep(3)




#     # Retrieve our camera once, set exposure/white balance
#     with Vimba.get_instance() as vimba:
#         cams = vimba.get_all_cameras()
#         input_camera = cams[0]
#         with input_camera as cam:
#             setup_camera(cam)


#     from time import sleep
# import serial
# import json
# import os

# import cv2
# from vimba import *
# import time
# from datetime import datetime

# FOLDER_NAME = "imaging_test_{date}"
# FILE_NAME = "/pic_{n}.tiff"


# def setup_camera(cam: Camera):
#     with cam:
#         # set the camera exposure
#         try:
#             cam.ExposureAuto.set('Continuous')
#         except (AttributeError, VimbaFeatureError):
#             print("did not set exposure")
#         # set the camera white balance
#         try:
#             cam.BalanceWhiteAuto.set('Continuous')
#         except (AttributeError, VimbaFeatureError):
#             pass
#         # only for GigE cams, try removing this
#         try:
#             cam.GVSPAdjustPacketSize.run()
#             while not cam.GVSPAdjustPacketSize.is_done():
#                 pass
#         except (AttributeError, VimbaFeatureError):
#             pass
#         # Query available, open_cv compatible pixel formats
#         # prefer color formats over monochrome formats
#         cv_fmts = intersect_pixel_formats(cam.get_pixel_formats(),
#                                           OPENCV_PIXEL_FORMATS)
#         color_fmts = intersect_pixel_formats(cv_fmts, COLOR_PIXEL_FORMATS)

#         if color_fmts:
#             cam.set_pixel_format(color_fmts[0])
#         else:
#             mono_fmts = intersect_pixel_formats(cv_fmts, MONO_PIXEL_FORMATS)
#             if mono_fmts:
#                 cam.set_pixel_format(mono_fmts[0])
#             else:
#                 abort('Camera does not support a OpenCV compatible format')
