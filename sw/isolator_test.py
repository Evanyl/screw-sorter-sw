import cv2
import numpy as np
import time

from isolator import Isolator, IsolatorDirective, IsolatorMission, IsolatorWorldView

isolator = Isolator()
runtime = list()
while True:

    belt1_moving = False
    belt2_moving = False
    depositor_homed = True
    world = IsolatorWorldView(belt1_moving, belt2_moving, depositor_homed)
    mission = IsolatorMission.ISOLATE
    t2 = time.perf_counter()
    directive = isolator.spin(mission, world)
    t1 = time.perf_counter()
    isolator.show()
    runtime.append(t2 - t1)
    k = cv2.waitKey(0)
    if k == ord("q"):
        break

runtime = np.array(runtime)
print(f"N: {len(runtime)}")
print(f"Average Time: {np.mean(runtime)}")
print(f"Standard Deviation: {np.std(runtime)}")
cv2.destroyAllWindows()
