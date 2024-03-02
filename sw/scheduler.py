
from datetime import datetime

class Scheduler:

    def __init__(self, task_periods):
        self.period = task_periods["scheduler"]
        del task_periods["scheduler"]
        self.last_time = datetime.now()
        self.tick_count = 1
        self.task_periods = task_periods
        self.task_flags = {k:False for k in task_periods.keys()}
        self.max_period = max(self.task_periods.values())

    def run10ms(self):
        t = datetime.now()
        if int((t - self.last_time).total_seconds() * 1000) >= self.period:
            # increment or reset counter
            if self.tick_count < self.max_period / self.period:
                self.tick_count += 1
            else:
                self.tick_count = 1
            # update last time
            self.last_time = t
            # update task flags
            for task in self.task_periods.keys():
                if (self.tick_count) % \
                    int(self.task_periods[task] / self.period) == 0:
                    self.task_flags[task] = True
                else:
                    pass # task period has not yet elapsed

    def taskReleased(self, task_id):
        ret = False
        if self.task_flags[task_id] == True:
            self.task_flags[task_id] = False
            ret = True
        return ret
