
from scheduler import Scheduler
from classify_system import ClassifySystem
from isolation_system import IsolationSystem
from core_comms import CoreComms

class SorterControl:

    def __init__(self):
        self.task_periods = \
        {
            "scheduler":       10,
            # "classify_system": 200,
            "isolation_system":  100,
            "core_comms":      50,
        }
        self.scheduler = Scheduler(self.task_periods)
        self.core_comms = CoreComms()
        # self.classify_system = ClassifySystem(self.core_comms)
        self.isolation_system = IsolationSystem(self.core_comms)

    def control(self):
        # execute the runXms functions of all task modules\
        self.scheduler.run10ms()
        # self.classify_system.run200ms(self.scheduler)
        self.isolation_system.run100ms(self.scheduler)
        self.core_comms.run50ms(self.scheduler)
        
if __name__ == "__main__":
    
    s = SorterControl()

    while True:
        s.control()
