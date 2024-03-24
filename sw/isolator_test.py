import cv2

from isolator import Isolator, IsolatorDirective, IsolatorMission, IsolatorWorldView

x = Isolator()
x.spin(IsolatorMission.ISOLATE, IsolatorWorldView(True, True, True))
# x.show()
cv2.waitKey(0)
cv2.destroyAllWindows()
