import click
from pathlib import Path

from threading import Thread

import time

from ui.data_collection_backend import start_ui

from scheduler import Scheduler
from classify_system import ClassifySystem
from isolate_system import IsolateSystem
from core_comms import CoreComms

class SorterControl:
    def __init__(self, out_dir_path, model_path, decoder_path):
        self.task_periods = \
        {
            "scheduler":       10,
            "classify_system": 200,
            "isolate_system":  100,
            "core_comms":      50,
        }
        self.shared_data = \
        {
            "isolated": False,
        }
        self.scheduler = Scheduler(self.task_periods)
        self.core_comms = CoreComms(out_dir_path)
        self.isolate_system = IsolateSystem(self.core_comms, self.shared_data)
        self.classify_system = ClassifySystem(self.core_comms, out_dir_path, 
                                              model_path, decoder_path, 
                                              self.shared_data)

    def control(self):
        # execute the runXms functions of all task modules
        self.scheduler.run10ms()
        self.classify_system.run200ms(self.scheduler)
        self.isolate_system.run100ms(self.scheduler)
        self.core_comms.run50ms(self.scheduler)

def control_loop(s):
    sec_to_ms = 1000.0
    while True:
        time.sleep((s.task_periods['scheduler']/2.0)/sec_to_ms)
        s.control()

@click.command(help="Run comms for sorter")
@click.option("--out_dir_path", "out_dir_path", required=True, 
              help="Output path to save session info")
@click.option("--model_path", "model_path", required=True, 
              help="Quantized model path")
@click.option("--decoder_path", "decoder_path", required=True, 
              help="Model decoder json path")
@click.option("--operator_name", "operator_name", required=True, 
              help="Operator Name", default="herobrine")
def main(out_dir_path, model_path, decoder_path, operator_name):
    # get paths, make sure they exist
    out_dir_path = Path(out_dir_path)
    assert out_dir_path.exists(), f"{out_dir_path} does not exist"
    model_path = Path(model_path)
    assert model_path.exists(), f"{model_path} does not exist"
    decoder_path = Path(decoder_path)
    assert decoder_path.exists(), f"{decoder_path} does not exist"

    # start sorter control
    s = SorterControl(out_dir_path, model_path, decoder_path)
    control_thread = Thread(target=control_loop, args=[s])
    control_thread.start()

    # Pyqt needs to be on main thread... bruh moment
    start_ui(operator_name, out_dir_path, s.isolate_system)

        
if __name__ == "__main__":
    main()
