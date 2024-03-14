import click
from pathlib import Path

import time
from scheduler import Scheduler
from classify_system import ClassifySystem
from isolation_system import IsolationSystem
from core_comms import CoreComms

class SorterControl:

    def __init__(self, out_dir_path, model_path, decoder_path):
        self.task_periods = \
        {
            "scheduler":       10,
            # "classify_system": 200,
            "isolation_system":  100,
            "core_comms":      50,
        }
        self.scheduler = Scheduler(self.task_periods)
        self.core_comms = CoreComms()
        self.isolate_system = IsolationSystem(self.core_comms)
        self.classify_system = ClassifySystem(self.core_comms, out_dir_path, 
                                              model_path, decoder_path)

    def control(self):
        # execute the runXms functions of all task modules
        self.scheduler.run10ms()
        # self.classify_system.run200ms(self.scheduler)
        self.isolation_system.run100ms(self.scheduler)
        self.core_comms.run50ms(self.scheduler)

@click.command(help="Run comms for sorter")
@click.option("--out_dir_path", "out_dir_path", required=True, 
              help="Output path to save session info")
@click.option("--model_path", "model_path", required=True, 
              help="Quantized model path")
@click.option("--decoder_path", "decoder_path", required=True, 
              help="Model decoder json path")
def main(out_dir_path, model_path, decoder_path):
    # get paths, make sure they exist
    out_dir_path = Path(out_dir_path)
    assert out_dir_path.exists(), f"{out_dir_path} does not exist"
    model_path = Path(model_path)
    assert model_path.exists(), f"{model_path} does not exist"
    decoder_path = Path(decoder_path)
    assert decoder_path.exists(), f"{decoder_path} does not exist"
    # start sorter control
    s = SorterControl(out_dir_path, model_path, decoder_path)
    sec_to_ms = 1000.0
    while True:
        time.sleep((s.task_periods['scheduler']/2.0)/sec_to_ms)
        s.control()
        
if __name__ == "__main__":
    main()
