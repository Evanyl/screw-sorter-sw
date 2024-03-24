import cv2

from isolator import Isolator, IsolatorDirective, IsolatorMission, IsolatorWorldView

isolator = Isolator()

while True:

    belt1_moving = False
    belt2_moving = False
    depositor_homed = True
    world = IsolatorWorldView(belt1_moving, belt2_moving, depositor_homed)
    mission = IsolatorMission.ISOLATE
    directive = isolator.spin(mission, world)
    isolator.show()
    k = cv2.waitKey(0)
    if k == ord("q"):
        break

cv2.destroyAllWindows()
