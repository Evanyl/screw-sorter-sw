import numpy as np
import cv2
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
    B1_MICRO_STEP = 10

    B2_CV = {
        "bbox-top-left": (98, 562),
        "bbox-bot-right": (2430, 1200),
        "background-lab-mask-lower": [0, 113, 113],
        "background-lab-mask-upper": [75, 139, 139],
        "background-mask-ksize": (10, 10),
        "fastener-contour-min-area": 250,
    }
    B2_MIN_SEP = 10
    B2_DEPOSITOR_DROP = B2_CV["bbox-bot-right"][0]
    B2_STEPS_PER_REV = 1000
    B2_STEPS_TO_CLEAR = B2_STEPS_PER_REV / 2
    B2_DEPOSITOR_CLOSE_DIST = 100
    B2_MICRO_STEP = 10

    def __init__(self):

        self.b1 = self.Locale("Belt 1", self.B1_CV)
        self.b2 = self.Locale("Belt 2", self.B2_CV)
        self.cam = Picamera2()
        camera_config = self.cam.create_still_configuration(
            main={"size": (self.FRAME_WIDTH, self.FRAME_HEIGHT)}
        )
        self.cam.configure(camera_config)
        self.cam.set_controls({"ExposureTime": 20000})
        self.cam.start()

        self.belts_command = IsolatorDirective(0,0,True)

    def spin(
        self, mission: IsolatorMission, world: IsolatorWorldView
    ) -> IsolatorDirective:

        if mission == IsolatorMission.IDLE:
            # TODO: update directive
            self.belts_command = IsolatorDirective(None, None, None)
            return IsolatorDirective(None, None, None)

        # sense the world
        self.frame = self.cam.capture_array("main")
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)
        # self.frame = cv2.imread("testing.jpg")

        # update state
        self.b1.spin(self.frame)
        self.b2.spin(self.frame)

        self.b2.fasteners.sort(key=lambda f: f.x2, reverse=True)
        b2_isolated = self._b2_is_isolated(right_sorted=True)
        #self.b2.show_fasteners([0,1])
        b2_dist_to_depositor = self._b2_dist_to_depositor(right_sorted=True)
        self.b1.fasteners.sort(key=lambda f: f.y1, reverse=False)
        b1_dist_to_drop = self._b1_dist_to_drop(top_sorted=True)

        print("SPIN")
        print("---")
        print(f"B2 ISOLATED: {b2_isolated}")
        print(f"B2 DIST: {b2_dist_to_depositor}")
        print(f"B1 DIST: {b1_dist_to_drop}")
        print("=====")

        if self.b2.last_N != None and self.b2.last_N > self.b2.N:

            return IsolatorDirective(0, 0, True)

        if self.b2.N > 0:

            """
            ASSUMPTIONS:
            * B2 has at least 1 fastener on board
            """
            # self.b2.fasteners.sort(key=lambda f: f.x2, reverse=True)
            # b2_isolated = self._b2_is_isolated(right_sorted=True)

            if not b2_isolated:

                """
                ASSUMPTIONS:
                * B2 has at least 1 fastener on board
                * B2 fasteners are NOT well-isolated
                """
                self.belts_command = IsolatorDirective(0, -self.B2_STEPS_TO_CLEAR, False)
                return IsolatorDirective(0, -self.B2_STEPS_TO_CLEAR, False)

            """
            ASSUMPTIONS:
            * B2 has at least 1 fastener on board
            * B2 fasteners are well-isolated
            """
            # b2_dist_to_depositor = self._b2_dist_to_depositor(right_sorted=True)
            if b2_dist_to_depositor < self.B2_DEPOSITOR_CLOSE_DIST:

                """
                ASSUMPTIONS:
                * B2 has at least 1 fastener on board
                * B2 fasteners are well-isolated
                * B2 rightmost fastener is very close to dropping on to depositor
                """
                self.belts_command = IsolatorDirective(0, self.B2_MICRO_STEP, False)
                return IsolatorDirective(0, self.B2_MICRO_STEP, False)

            """
            ASSUMPTIONS:
            * B2 has at least 1 fastener on board
            * B2 fasteners are well-isolated
            * B2 rightmost fastener is still far away from dropping on to depositor
            """
            self.belts_command = IsolatorDirective(0, max(b2_dist_to_depositor-self.B2_DEPOSITOR_CLOSE_DIST,self.B2_MICRO_STEP), False)
            return IsolatorDirective(
                0,
                max(
                    b2_dist_to_depositor - self.B2_DEPOSITOR_CLOSE_DIST,
                    self.B2_MICRO_STEP,
                ),
                False,
            )

        if self.b1.N > 0:

            """
            ASSUMPTIONS:
            * B1 has at least 1 fastener on board
            """

            # self.b1.fasteners.sort(key=lambda f: f.y1, reverse=False)
            # b1_dist_to_drop = self._b1_dist_to_drop(top_sorted=True)

            if b1_dist_to_drop < self.B1_DROP_CLOSE_DIST:

                """
                ASSUMPTIONS:
                * B1 has at least 1 fastener on board
                * B1 topmost fastener is very close to dropping on to B2
                """
                self.belts_command = IsolatorDirective(self.B1_MICRO_STEP, 0, False)
                return IsolatorDirective(self.B1_MICRO_STEP, 0, False)

            """
            ASSUMPTIONS:
            * B1 has at least 1 fastener on board
            * B1 topmost fastener is still far away from dropping on to depositor
            """
            self.belts_command = IsolatorDirective(
                max(
                    b1_dist_to_drop - self.B1_DROP_CLOSE_DIST,
                    self.B1_MICRO_STEP,
                ),
                0,
                False,
            )
            return IsolatorDirective(
                max(
                    b1_dist_to_drop - self.B1_DROP_CLOSE_DIST,
                    self.B1_MICRO_STEP,
                ),
                0,
                False,
            )

    def show(self):

        self.b1.show()
        self.b2.show()
        #cv2.imshow('sys', cv2.resize(self.frame, (0,0), fx=0.5, fy=0.5))
        #cv2.imwrite('testing.jpg', self.frame)

    def _b1_dist_to_drop(self, top_sorted=False):
        if not top_sorted:
            self.b1.fasteners.sort(key=lambda f: f.y1, reverse=False)
        if len(self.b1.fasteners) > 0:
            topmost = self.b1.fasteners[0]
            return topmost.y1 - self.B1_DROP
        else:
            return float('inf')

    def _b2_dist_to_depositor(self, right_sorted=False):

        if not right_sorted:
            self.b2.fasteners.sort(key=lambda f: f.x2, reverse=True)
        if len(self.b2.fasteners) > 0:
            rightmost = self.b2.fasteners[0]
            return self.B2_DEPOSITOR_DROP - rightmost.x2
        else:
            return float('inf')

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
            self.N = None

        def spin(self, img):

            self.last_N = self.N
            self.img = img.copy()[self.y1 : self.y2, self.x1 : self.x2, :]
            self.lab = cv2.cvtColor(self.img, cv2.COLOR_BGR2LAB)
            self.mask = self._generate_mask()
            self.fasteners = self._find_fasteners()
            self.N = len(self.fasteners)

        def show(self):

            show = self.img.copy()
            for i in range(self.N):
                f = self.fasteners[i]
                x1 = f.x1 - self.x1
                y1 = f.y1 - self.y1
                x4 = f.x4 - self.x1
                y4 = f.y4 - self.y1
                cv2.rectangle(show, (x1, y1), (x4, y4), (255, 0, 255), 3)
            # cv2.imshow(
            #     f"Fastener Isolation System - {self.name}",
            #     cv2.resize(show, (0, 0), fx=0.5, fy=0.5),
            # )

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
            # cv2.imshow(f"Fastener Isolation System - {self.name}", show)

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
