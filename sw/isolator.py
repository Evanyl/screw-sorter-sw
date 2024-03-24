import numpy as np
import cv2
from enum import Enum


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

    def __init__(self, b1steps: int, b2steps: int):

        self.b1steps = b1steps  # how many steps to move belt 1
        self.b2steps = b2steps  # how many steps to move belt 2


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


class Isolator:

    FRAME_WIDTH = 4056
    FRAME_HEIGHT = 3040

    B1_CV = {
        "bbox-top-left": (229, 1273),
        "bbox-bot-right": (960, 2204),
        "background-lab-mask-lower": [0, 120, 120],
        "background-lab-mask-upper": [75, 131, 131],
        "background-mask-ksize": (10, 10),
        "fastener-contour-min-area": 250,
    }
    B1_DROP = B1_CV["bbox-top-left"][1]
    B1_DROP_CLOSE_DIST = 50
    B1_MICRO_STEP = 10

    B2_CV = {
        "bbox-top-left": (98, 562),
        "bbox-bot-right": (2430, 1200),
        "background-lab-mask-lower": [0, 120, 120],
        "background-lab-mask-upper": [75, 131, 131],
        "background-mask-ksize": (10, 10),
        "fastener-contour-min-area": 250,
    }
    B2_MIN_SEP = 10
    B2_DEPOSITOR_DROP = B2_CV["bbox-bot-right"][0]
    B2_STEPS_PER_REV = 1000
    B2_STEPS_TO_CLEAR = B2_STEPS_PER_REV / 2
    B2_DEPOSITOR_CLOSE_DIST = 25
    B2_MICRO_STEP = 10

    def __init__(self):

        self.b1 = self.Locale("Belt 1", self.B1_CV)
        self.b2 = self.Locale("Belt 2", self.B2_CV)
        self.frame = None

    def spin(
        self, mission: IsolatorMission, world: IsolatorWorldView
    ) -> IsolatorDirective:

        if mission == IsolatorMission.IDLE:
            return IsolatorDirective(None, None)

        # sense the world
        self.frame = cv2.imread("black-felt-1.jpg")  # get image from camera

        # update state
        self.b1.spin(self.frame)
        self.b2.spin(self.frame)

        if self.b2.N > 0:

            """
            ASSUMPTIONS:
            * B2 has at least 1 fastener on board
            """
            self.b2.fasteners.sort(key=lambda f: f.x2, reverse=True)
            b2_isolated = self._b2_is_isolated(right_sorted=True)

            if not b2_isolated:

                """
                ASSUMPTIONS:
                * B2 has at least 1 fastener on board
                * B2 fasteners are NOT well-isolated
                """
                return IsolatorDirective(0, -self.B2_STEPS_TO_CLEAR)

            """
            ASSUMPTIONS:
            * B2 has at least 1 fastener on board
            * B2 fasteners are well-isolated
            """
            b2_dist_to_depositor = self._b2_dist_to_depositor(right_sorted=True)
            if b2_dist_to_depositor < self.B2_DEPOSITOR_CLOSE_DIST:

                """
                ASSUMPTIONS:
                * B2 has at least 1 fastener on board
                * B2 fasteners are well-isolated
                * B2 rightmost fastener is very close to dropping on to depositor
                """
                return IsolatorDirective(0, self.B2_MICRO_STEP)

            """
            ASSUMPTIONS:
            * B2 has at least 1 fastener on board
            * B2 fasteners are well-isolated
            * B2 rightmost fastener is still far away from dropping on to depositor
            """

            return IsolatorDirective(
                0,
                max(
                    b2_dist_to_depositor - self.B2_DEPOSITOR_CLOSE_DIST,
                    self.B2_MICRO_STEP,
                ),
            )

        if self.b1.N > 0:

            """
            ASSUMPTIONS:
            * B1 has at least 1 fastener on board
            """

            self.b1.fasteners.sort(key=lambda f: f.y1, reverse=False)
            b1_dist_to_drop = self._b1_dist_to_drop(top_sorted=True)

            if b1_dist_to_drop < self.B1_DROP_CLOSE_DIST:

                """
                ASSUMPTIONS:
                * B1 has at least 1 fastener on board
                * B1 topmost fastener is very close to dropping on to B2
                """
                return IsolatorDirective(self.B1_MICRO_STEP, 0)

            """
            ASSUMPTIONS:
            * B1 has at least 1 fastener on board
            * B1 topmost fastener is still far away from dropping on to depositor
            """

            return IsolatorDirective(
                max(
                    b1_dist_to_drop - self.B1_DROP_CLOSE_DIST,
                    self.B1_MICRO_STEP,
                ),
                0,
            )

    def show(self):

        self.b1.show()
        self.b2.show()

    def _b1_dist_to_drop(self, top_sorted=False):
        if not top_sorted:
            self.b1.fasteners.sort(key=lambda f: f.y1, reverse=False)
        topmost = self.b1.fasteners[0]
        return topmost.y1 - self.B1_DROP

    def _b2_dist_to_depositor(self, right_sorted=False):

        if not right_sorted:
            self.b2.fasteners.sort(key=lambda f: f.x2, reverse=True)
        rightmost = self.b2.fasteners[0]
        return self.B2_DEPOSITOR_DROP - rightmost.x2

    def _b2_is_isolated(self, right_sorted=False):

        if not right_sorted:
            self.b2.fasteners.sort(key=lambda f: f.x2, reverse=True)
        iso = True
        for i in range(self.b2.N - 1):
            fright = self.b2.fasteners[i]
            fleft = self.b2.fasteners[i + 1]
            dist = Fastener.xdist(fleft, fright)
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

        def spin(self, img):

            self.img = img.copy()[self.y1 : self.y2, self.x1 : self.x2, :]
            self.lab = cv2.cvtColor(self.img, cv2.COLOR_BGR2LAB)
            self.mask = self._generate_mask()
            self.fasteners = self._find_fasteners()
            self.N = len(self.fasteners)

        def show(self):

            show = self.img.copy()
            for i in range(self.N):
                f = self.fasteners[i]
                cv2.rectangle(show, (f.x1, f.y1), (f.x4, f.y4), (255, 0, 255), 3)
            cv2.imshow(f"Fastener Isolation System - {self.name}", show)

        def show_fasteners(self, indices):

            show = self.img.copy()
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255)]

            for i in indices:
                f = self.fasteners[i]
                cv2.rectangle(
                    show,
                    (f.x1, f.y1),
                    (f.x4, f.y4),
                    colors[indices.index(i) % len(colors)],
                    3,
                )
            cv2.imshow(f"Fastener Isolation System - {self.name}", show)

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
                    fasteners.append(Fastener(contour, bbox, area=area))
            return fasteners
