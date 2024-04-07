import numpy as np
import cv2
import time
from math import floor
from enum import Enum

from picamera2 import Picamera2


class IsolatorMission(Enum):
    """
    enum class for isolator to set it's objective for the next spin cycle
    """

    IDLE = 0  # do nothing
    ISOLATE = 1  # keep track of the world and issue directives to isolate


class IsolatorWorldView:
    """
    incoming message-passing class that encodes the state of the world to the
    Isolator
    """

    def __init__(self, b1_moving: bool, b2_moving: bool, depositor_accepting: bool):

        self.b1_moving = b1_moving  # is belt 1 moving?
        self.b2_moving = b2_moving  # is belt 2 moving?
        self.depositor_accepting = (
            depositor_accepting  # is the depositor currently accepting fasteners?
        )


class IsolatorDirective:
    """
    outgoing message-passing class that encodes the Isolator's directive on how
    to change the world based on its WorldView and Mission
    """

    def __init__(self, b1steps: int, b2steps: int, start_imaging: bool):

        self.b1steps = b1steps  # how many steps to move belt 1
        self.b2steps = b2steps  # how many steps to move belt 2
        self.start_imaging = start_imaging  # should you start moving the depositor


class Isolator:

    FRAME_WIDTH = 4056
    FRAME_HEIGHT = 3040

    B1_CV = {
        "bbox-top-left": (229, 1273),
        "bbox-bot-right": (960, 2204),
        "background-lab-mask-lower": [0, 113, 113],
        "background-lab-mask-upper": [75, 139, 139],
        "background-mask-ksize": (10, 10),
        "fastener-contour-min-area": 250,
    }
    B1_DROP = B1_CV["bbox-top-left"][1]
    B1_DROP_CLOSE_DIST = 100
    B1_MICRO_STEP = 100

    B2_CV = {
        "bbox-top-left": (98, 585),  # 562
        "bbox-bot-right": (2430, 1200),  # 2430
        "background-lab-mask-lower": [0, 114, 114],
        "background-lab-mask-upper": [95, 139, 139],
        "background-mask-ksize": (10, 10),
        "fastener-contour-min-area": 250,
    }
    B2_MIN_SEP = 10
    B2_DEPOSITOR_DROP = B2_CV["bbox-bot-right"][0]
    B2_STEPS_PER_REV = 10000
    B2_STEPS_TO_CLEAR = B2_STEPS_PER_REV
    B2_DEPOSITOR_CLOSE_DIST = 100
    B2_MICRO_STEP = 100

    B21_CV = B2_CV.copy()
    B21_CV["bbox-top-left"] = (
        int(floor(B2_CV["bbox-bot-right"][0] - 75)),
        B2_CV["bbox-top-left"][1],
    )
    B21_CV["bbox-bot-right"] = (
        int(floor(B2_CV["bbox-bot-right"][0])),
        B2_CV["bbox-bot-right"][1],
    )

    def __init__(self):

        self.b1 = self.Locale("Belt 1", self.B1_CV)
        self.b2 = self.Locale("Belt 2", self.B2_CV)
        self.b21 = self.Locale("Belt 2 - Drop Zone", self.B21_CV)
        self.cam = Picamera2()
        camera_config = self.cam.create_still_configuration(
            main={"size": (self.FRAME_WIDTH, self.FRAME_HEIGHT)}
        )
        self.cam.configure(camera_config)
        self.cam.set_controls({"ExposureTime": 20000})
        self.cam.start()

        self._update_intention_command(Isolator.Intention.NULL)
        self.x = 0
        self.last_drop_count = None
        self.bdrop = None

    def spin(
        self, mission: IsolatorMission, world: IsolatorWorldView
    ) -> IsolatorDirective:
        print("SPIN")
        print("---")
        if mission == IsolatorMission.IDLE:
            print("IDLING")
            print("=====")
            self._update_intention_command(self.Intention.NULL)
            return

        # sense the world
        print("CAMERA_START")
        self.frame = self.cam.capture_array("main")
        print("CAMERA_END")
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)

        # update state
        self.b1.spin(self.frame)
        self.b2.spin(self.frame)
        self.b21.spin(self.frame)

        self.b2.fasteners.sort(key=lambda f: f.x2, reverse=True)
        b2_isolated = self._b2_is_isolated(right_sorted=True)
        b2_dist_to_depositor = self._b2_dist_to_depositor(right_sorted=True)
        self.b1.fasteners.sort(key=lambda f: f.y1, reverse=False)
        b1_dist_to_drop = self._b1_dist_to_drop(top_sorted=True)

        self.belts_command = self._intention_to_directive(self.Intention.NULL)

        print(f"B2 ISOLATED: {b2_isolated}")
        print(f"B2 DIST: {b2_dist_to_depositor}")
        print(f"B1 DIST: {b1_dist_to_drop}")
        print(f"ACCEPTING: {world.depositor_accepting}")
        print(f"LAST SPIN INTENTION: {self.last_intention}")
        print(f"21LAST: {self.b21.last_N}")
        print(f"21NOW: {self.b21.N}")
        print("=====")

        if self.last_intention == self.Intention.B2_ATTEMPT_DROP and self.bdrop != None:
            self.bdrop.spin(self.frame)
            if self.bdrop.N < self.bdrop.last_N:
                print("ISOLATED***********************************")
                self.bdrop = None
                self._update_intention_command(self.Intention.SIGNAL_START_IMAGING)
                return

        if self.b2.N > 0:
            """
            ASSUMPTIONS:
            * B2 has at least 1 fastener on board
            """
            if not b2_isolated:
                """
                ASSUMPTIONS:
                * B2 has at least 1 fastener on board
                * B2 fasteners are NOT well-isolated
                """
                self._update_intention_command(self.Intention.B2_REJECT_ALL)
                print("booting.....")
                return

            """
            ASSUMPTIONS:
            * B2 has at least 1 fastener on board
            * B2 fasteners are well-isolated
            """
            print(f"dist = {b2_dist_to_depositor}")
            if b2_dist_to_depositor < self.B2_DEPOSITOR_CLOSE_DIST:
                """
                ASSUMPTIONS:
                * B2 has at least 1 fastener on board
                * B2 fasteners are well-isolated
                * B2 rightmost fastener is very close to dropping on to depositor
                """
                cv = self.B2_CV.copy()
                idx = -1
                if self.b2.N > 1:
                    for i in range(self.b2.N - 1):
                        fl = self.b2.fasteners[i + 1]
                        fr = self.b2.fasteners[i]
                        disty = self.Fastener.xdist(fl, fr)
                        if disty > 50:
                            idx = i
                            break
                width = max(
                    25 + (self.B2_DEPOSITOR_DROP - self.b2.fasteners[idx].x1),
                    1.05 * (self.B2_DEPOSITOR_DROP - self.b2.fasteners[idx].x1),
                )
                cv["bbox-top-left"] = (
                    int(floor(self.B2_CV["bbox-bot-right"][0] - width)),
                    self.B2_CV["bbox-top-left"][1],
                )
                print(f"width = {width}")
                self.bdrop_cv = cv
                self.bdrop = self.Locale("Belt 2 - Drop", cv=cv)
                self.bdrop.spin(self.frame)
                if world.depositor_accepting == True:
                    # depositor is free, we can microstep
                    self._update_intention_command(self.Intention.B2_ATTEMPT_DROP)
                else:
                    # don't start micro-stepping until we can put fastner in depositor
                    self._update_intention_command(self.Intention.NULL)
                return

            """
            ASSUMPTIONS:
            * B2 has at least 1 fastener on board
            * B2 fasteners are well-isolated
            * B2 rightmost fastener is still far away from dropping on to depositor
            """
            self.last_intention = self.Intention.B2_ADVANCE_TO_DROP
            self.belts_command = IsolatorDirective(
                0,
                max(
                    b2_dist_to_depositor - self.B2_DEPOSITOR_CLOSE_DIST,
                    self.B2_MICRO_STEP,
                ),
                False,
            )
            return

        if self.b1.N > 0:
            """
            ASSUMPTIONS:
            * B1 has at least 1 fastener on board
            """
            if b1_dist_to_drop < self.B1_DROP_CLOSE_DIST:

                """
                ASSUMPTIONS:
                * B1 has at least 1 fastener on board
                * B1 topmost fastener is very close to dropping on to B2
                """
                self._update_intention_command(self.Intention.B1_ATTEMPT_DROP)
                return

            """
            ASSUMPTIONS:
            * B1 has at least 1 fastener on board
            * B1 topmost fastener is still far away from dropping on to depositor
            """
            self.last_intention = self.Intention.B1_ADVANCE_DROP
            self.belts_command = IsolatorDirective(
                max(
                    b1_dist_to_drop - self.B1_DROP_CLOSE_DIST,
                    self.B1_MICRO_STEP,
                ),
                0,
                False,
            )
            return

    def show(self):
        _1 = self.b1.show()
        _2 = self.b2.show()
        _3 = self.b21.show()
        if self.bdrop != None:
            cv2.imshow(self.bdrop.name, self.bdrop.show())

        cv2.imshow(self.b1.name, _1)
        cv2.imshow(self.b2.name, _2)
        # cv2.imshow(self.b21.name, _3)

    def _intention_to_directive(self, intention):

        if intention == self.Intention.NULL:
            return IsolatorDirective(0, 0, False)
        if intention == self.Intention.SIGNAL_START_IMAGING:
            return IsolatorDirective(0, 0, True)
        if intention == self.Intention.B2_REJECT_ALL:
            return IsolatorDirective(0, -self.B2_STEPS_TO_CLEAR, False)
        if intention == self.Intention.B2_ATTEMPT_DROP:
            return IsolatorDirective(0, self.B2_MICRO_STEP, False)
        if intention == self.Intention.B1_ATTEMPT_DROP:
            return IsolatorDirective(self.B1_MICRO_STEP, 0, False)

    def _update_intention_command(self, intention):

        self.last_intention = intention
        self.belts_command = self._intention_to_directive(intention)

    def _b1_dist_to_drop(self, top_sorted=False):
        if not top_sorted:
            self.b1.fasteners.sort(key=lambda f: f.y1, reverse=False)
        if len(self.b1.fasteners) > 0:
            topmost = self.b1.fasteners[0]
            return topmost.y1 - self.B1_DROP
        else:
            return float("inf")

    def _b2_dist_to_depositor(self, right_sorted=False):

        if not right_sorted:
            self.b2.fasteners.sort(key=lambda f: f.x2, reverse=True)
        if len(self.b2.fasteners) > 0:
            rightmost = self.b2.fasteners[0]
            return self.B2_DEPOSITOR_DROP - rightmost.x2
        else:
            return float("inf")

    def _b2_is_isolated(self, right_sorted=False):

        if not right_sorted:
            self.b2.fasteners.sort(key=lambda f: f.x2, reverse=True)
        iso = True
        for i in range(self.b2.N - 1):
            fright = self.b2.fasteners[i]
            fleft = self.b2.fasteners[i + 1]
            dist = Isolator.Fastener.xdist(fleft, fright)
            print(dist)
            if dist < self.B2_MIN_SEP:
                iso = False
                break
        return iso

    class Locale:

        def __init__(self, name: str, cv: dict):
            # unpack and set config
            self.name = name
            self.x1, self.y1 = cv["bbox-top-left"]
            self.x2, self.y2 = cv["bbox-bot-right"]
            self.lb = np.array(cv["background-lab-mask-lower"])
            self.ub = np.array(cv["background-lab-mask-upper"])
            self.ksize = cv["background-mask-ksize"]
            self.fastener_min_area = cv["fastener-contour-min-area"]
            self.bounded = None
            self.N = 0
            self.img = None

        def spin(self, img):
            self.last_N = self.N
            self.img = img.copy()[self.y1 : self.y2, self.x1 : self.x2, :]
            self.lab = cv2.cvtColor(self.img, cv2.COLOR_BGR2LAB)
            self.mask = self._generate_mask()
            self.fasteners = self._find_fasteners()
            self.N = len(self.fasteners)
            self.bounded = self._generate_show()

        def show(self):
            if self.bounded is None:
                return None
            else:
                return self.bounded.copy()

        def show_fasteners(self, indices):
            show = self.img.copy()
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255)]

            for i in indices:
                f = self.fasteners[i]
                x1 = f.x1 - self.x1
                y1 = f.y1 - self.y1
                x4 = f.x4 - self.x1
                y4 = f.y4 - self.y1
                cv2.rectangle(
                    show,
                    (x1, y1),
                    (x4, y4),
                    colors[indices.index(i) % len(colors)],
                    3,
                )

        def _generate_show(self):

            show = self.img.copy()
            for i in range(self.N):
                f = self.fasteners[i]
                x1 = f.x1 - self.x1
                y1 = f.y1 - self.y1
                x4 = f.x4 - self.x1
                y4 = f.y4 - self.y1
                cv2.rectangle(show, (x1, y1), (x4, y4), (255, 0, 255), 3)
            return show

        def _generate_mask(self):
            out = cv2.blur(self.lab, self.ksize)
            out = cv2.inRange(out, self.lb, self.ub)
            out = cv2.bitwise_not(out)
            return out

        def _find_fasteners(self):
            contours, _ = cv2.findContours(
                image=self.mask, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE
            )
            fasteners = list()
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.fastener_min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    x += self.x1
                    y += self.y1
                    bbox = (x, y, w, h)
                    fasteners.append(Isolator.Fastener(contour, bbox, area=area))
            return fasteners

    class Fastener:

        def __init__(self, contour, bbox, area=None):
            self.c = contour
            self.x1, self.y1, self.w, self.h = bbox
            self.x2 = self.x1 + self.w
            self.y2 = self.y1
            self.x3 = self.x1
            self.y3 = self.y1 + self.h
            self.x4 = self.x2
            self.y4 = self.y3
            self.area = cv2.contourArea(contour) if area is None else area

        @staticmethod
        def xdist(fleft, fright):
            return fright.x1 - fleft.x2

    class Intention(Enum):
        """
        enum class for isolator to track its internal intention with a directive
        """

        NULL = 0
        SIGNAL_START_IMAGING = 1
        B2_REJECT_ALL = 2
        B2_ATTEMPT_DROP = 3
        B2_ADVANCE_TO_DROP = 4
        B1_ATTEMPT_DROP = 5
        B1_ADVANCE_DROP = 6
