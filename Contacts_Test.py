from Controller import Controller
import time

c = Controller()

def head_check():
    c.neckVertiTo(4000)
    c.neckHoriTo(4000)


def relax_arm():
    c.R_WristTurn(4000)
    c.moveR_SholderH(8000)
    time.sleep(.2)
    c.moveR_SholderV(4000)
    c.moveR_Elbow(5000)
    #c.R_Grip(4000)
    c.moveR_WRIST_V(6000)

def arm_check():
    c.moveR_SholderV(7000)
    c.moveR_Elbow(8000)
    time.sleep(.2)
    c.moveR_SholderH(5000)
    c.R_WristTurn(5000)
    c.R_Grip(7000)
    c.moveR_WRIST_V(8000)

def test_all():
    for x in range(0, 18):
        print("Testing pin:", x)
        c.testPin(x)
        c.set_test_pin(x, 6000)
        time.sleep(2)
# print("Forward")
# c.burstForward()
# print("LEFR")
# c.burstLeft()
# print("RIGHT")
# c.burstRight()

# time.sleep(3)
# #head_check()
# relax_arm()
# print("Arm relaxed")
# time.sleep(3)
# arm_check()
# print("Arm Flexed")
# #c.moveR_Elbow(7000)
#
# time.sleep(2)
#
# c.extend_arm()
# print("Arm Extended")
#time.sleep(3)
#c.set_test_pin(8, 4000)
c.relax_arm()
print("arm relaxed")
time.sleep(2)
print("Arm Extended")
c.extend_arm()
time.sleep(2)
c.testPin(11)
time.sleep(2)
print("Arm checked")
c.arm_check()


