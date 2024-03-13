
import time
from picamera2 import Picamera2


def image_and_process(thread_data):
    print("imaging and processing...")
    time.sleep(3)

def isolation_image_and_process(picamera_object, shared_data):
    print("Performing isolation imaging/processing...")
    # im = picamera_object.capture_array()
    
    fastener_isolated = True

    shared_data["isolated"] = fastener_isolated
    shared_data["belt_top_steps"] = 200
    shared_data["belt_bottom_steps"] = 200
    time.sleep(3)
    print("Done isolation imaging/processing")