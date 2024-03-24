#from sw.imaging import image_and_process
import threading
from sw.inference import Predictor
#from sw.main import SorterControl
import time
from lib.image_transformer import transform_top_image
from pathlib import Path
import json
from threading import Thread

shared_data = {
    "corr_angle":    60.0,
    "pred":          "",
    "out_dir_path":  Path("/home/screwsorter/comms_05_03_2024"),
    "side-on_path": Path("/home/screwsorter/comms_05_03_2024/imgs/1_side_on.tiff"), 
    "top-down_path": Path("/home/screwsorter/comms_05_03_2024/imgs/0_top_down.tiffpreprocc.tiff"), 
    "final_file_path": Path("/home/screwsorter/comms_05_03_2024/imgs/composed.tiff"),
    #"final_file_path": Path("/home/screwsorter/comms_05_03_2024/imgs/final_sim.png"),
    "initialized": False,
}


model_path = Path("/home/screwsorter/v5_multihead_quant.tflite")
decoder_path = Path("/home/screwsorter/v5_multihead_decoding.json")

#image_and_process(shared_data, "top-down")


inf_run = Predictor(model_path, decoder_path)
inf_run.predict(shared_data["final_file_path"])

decoded = inf_run.decode(inf_run.predictions)

print(json.dumps(decoded, indent=4))


#transform_top_image(str(shared_data['top-down_path']))

#thread = Thread(target=image_and_process, args=[shared_data, "top-down"])



#s = SorterControl(shared_data['out_dir_path'], model_path, decoder_path)
#thread.start()
#while True:
#    time.sleep(s.task_periods['scheduler'] / 2 / 1000.0)
#    s.control()
