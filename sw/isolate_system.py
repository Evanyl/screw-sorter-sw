
from datetime import datetime

class IsolateSystem:

    def __init__(self):
        self.last_time = datetime.now()

    def run100ms(self, scheduler):
        if scheduler.taskReleased("isolate_system"):
            t = datetime.now()
            dt = int((t - self.last_time).total_seconds() * 1000)
            self.last_time = t
            print(f"isolate dt: {dt}")
