import cv2

from isolator import Isolator, IsolatorDirective, IsolatorMission, IsolatorWorldView

isolator = Isolator()

while True:
    # check from firmware if belts are still moving and depositor homed
    belt1_moving = False
    belt2_moving = False
    depositor_homed = True

    # Give isolator it's world view, i.e., external state of the world
    world = IsolatorWorldView(belt1_moving, belt2_moving, depositor_homed)

    # Give isolator it's mission, i.e., actively isolating or just idling
    mission = (
        IsolatorMission.ISOLATE
    )  # (or IsolatorMission.IDLE, if you want to suppress isolation rn)

    directive = isolator.spin(mission, world)

    print(directive.b1steps)
    print(directive.b2steps)
