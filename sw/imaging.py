import time
import sys
import cv2
import numpy as np
from vimba import *

sys.path.append("./lib/")
from image_transformer import get_correction_angle, transform_top_image, transform_side_image

IMG_FOLDER = "imgs"

TOP_EXPOSURE = 18000
SIDE_EXPOSURE = 100000

def setup_camera():
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
            color_fmts = intersect_pixel_formats(cv_fmts, COLOR_PIXEL_FORMATS)
            cam.set_pixel_format(color_fmts[0])
    return input_camera

def image_and_process(shared_data, curr_state):
    print("imaging and processing...")
    print("########################")
    print("########################")
    print("########################")
    print("########################")
    print("########################")
    out_path = shared_data["out_dir_path"] / IMG_FOLDER
    out_path.mkdir(parents=True, exist_ok=True)

    if not shared_data['camera']:
        print("Initializing cam...")
        shared_data['camera'] = setup_camera()

    camera = shared_data['camera']
    file_name = ""
    exposure_time = 0
    # update imaging parameters based on what type of image is being taken
    if curr_state == "top-down":
        file_name = "0_top_down.tiff"
    elif curr_state == "side-on":
        file_name = "1_side_on.tiff"
    else:
        pass

    out_file = out_path / file_name

    # take an image, store it locally, remember the name
    take_image(camera, out_file, curr_state)

    start_time = time.time()
    if curr_state == "top-down":
        processed_img, corr_angle = transform_top_image(out_file)
        shared_data["corr_angle"] = -1 * corr_angle + 90
        print(f"Corr angle: {shared_data['corr_angle']}")
    elif curr_state == "side-on":
        processed_img = transform_side_image(out_file)

    cv2.imwrite(str(out_file), processed_img)
    print(f"Processed frame for {curr_state}, saved to mem")
    shared_data[f'{curr_state}_path'] = out_file
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Takes: {elapsed} to process for {curr_state}")

    if curr_state == "side-on":
        top_img = cv2.imread(str(shared_data['top-down_path']))
        side_img = cv2.imread(str(shared_data['side-on_path']))

        img_concat = np.concatenate([top_img, side_img], axis=0)
        final_file_path = out_path / "final.tiff"
        cv2.imwrite(str(final_file_path), img_concat)
        shared_data["final_file_path"] = final_file_path
        print(f"Ready for inference at {str(final_file_path)}")

def take_image(camera, out_file, curr_state):
    with Vimba.get_instance() as vimba:
        with camera as cam:
            # set frame capture timeout at max exposure time
            if curr_state == "top-down":
                cam.ExposureAuto.set("Off")
                cam.ExposureTime.set(TOP_EXPOSURE)
            elif curr_state == "side-on":
                cam.ExposureAuto.set("Off")
                cam.ExposureTime.set(SIDE_EXPOSURE)
            frame = cam.get_frame(timeout_ms=1000000)
            print("Got a frame")
            frame = frame.as_numpy_ndarray()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cv2.imwrite(str(out_file), frame)
            print("Frame saved to mem")

