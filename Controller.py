
import maestro


import socket, time


BODY = 0
MOTORS = 1
TURN = 2
HEADTURN = 3
HEADTILT = 4
R_SHOLDERS_V = 6
R_SHOLDERS_H = 7
R_ELBOW = 8
R_WRIST_V = 9
R_WRIST_TURN = 10
R_GRIP = 11

L_SHOLDERS_V = 14
L_SHOLDERS_H = 13
L_ELBOW = 13
L_WRIST_V = 15
L_WRIST_TURN = 16
L_GRIP = 17

class Controller:

    def __init__(self):
        self.tango = maestro.Controller()
        self.body = 6000
        self.headTurn = 6000
        self.headTilt = 6000
        self.motors = 6000
        self.turn = 6000

        self.servoSpeed = 150
        self.servoMAX = 8000
        self.servoMIN = 4000
        self.tango.setTarget(BODY, self.body)
        self.relax_arm()

    def relax_arm(self):
        self.R_WristTurn(4000)
        self.moveR_SholderH(8000)
        time.sleep(.2)
        self.moveR_SholderV(5000)
        self.moveR_Elbow(5000)
        self.R_Grip(4000)
        self.moveR_WRIST_V(6000)

    def extend_arm(self):
        self.moveR_SholderV(7000)
        self.moveR_Elbow(5000)
        self.R_WristTurn(6000)
        self.moveR_SholderH(6600)
        self.moveR_WRIST_V(6000)

    def arm_check(self):
        self.moveR_SholderV(7000)
        self.moveR_Elbow(8000)
        time.sleep(.2)
        self.moveR_SholderH(5000)
        self.R_WristTurn(5000)
        self.moveR_WRIST_V(8000)

    def testPin(self, val):
        for x in range(20, 50):
            self.tango.setTarget(val, (x*200))
            time.sleep(.1)
            print("The current value is:", x*200)

    def set_test_pin(self, val1, val2):
        self.tango.setTarget(val1, val2)

    def moveR_SholderH(self, val):
        self.tango.setTarget(R_SHOLDERS_H, val)
    
    def moveR_SholderV(self, val):
        self.tango.setTarget(R_SHOLDERS_V, val)

    def moveR_Elbow(self, val):
        self.tango.setTarget(R_ELBOW, val)

    def moveR_WRIST_V(self, val):
        self.tango.setTarget(R_WRIST_V, val)

    def R_WristTurn(self, val):
        self.tango.setTarget(R_WRIST_TURN, val)

    def R_Grip(self, val):
        self.tango.setTarget(R_GRIP, val)

    def moveL_SholderH(self, val):
        self.tango.setTarget(L_SHOLDERS_H, val)
    
    def moveL_SholderV(self, val):
        self.tango.setTarget(L_SHOLDERS_V, val)

    def moveL_Elbow(self, val):
        self.tango.setTarget(L_ELBOW, val)

    def moveL_WRIST_V(self, val):
        self.tango.setTarget(L_WRIST_V, val)

    def L_WristTurn(self, val):
        self.tango.setTarget(L_WRIST_TURN, val)

    def L_Grip(self, val):
        self.tango.setTarget(L_GRIP, val)

    def getServoPos(self):
        return self.headTurn, self.headTilt

    def getBodyPos(self):
        return self.body

    def burstLeft(self):
        self.turn = 7000
        self.tango.setTarget(TURN, self.turn)
        self.tango.setTarget(MOTORS, self.motors)
        time.sleep(.5)
        self.turn = 6000
        self.tango.setTarget(TURN, self.turn)
        self.tango.setTarget(MOTORS, self.motors)

    def burstRight(self):
        self.turn = 5000
        self.tango.setTarget(TURN, self.turn)
        self.tango.setTarget(MOTORS, self.motors)
        time.sleep(.5)
        self.turn = 6000
        self.tango.setTarget(TURN, self.turn)
        self.tango.setTarget(MOTORS, self.motors)

    def burstForward(self):
        self.motors = 5000
        self.tango.setTarget(MOTORS, self.motors)
        self.tango.setTarget(TURN, self.turn)
        time.sleep(1)
        self.motors = 6000
        self.tango.setTarget(MOTORS, self.motors)
        self.tango.setTarget(TURN, self.turn)


    def burstBackward(self):
        self.motors = 6900
        self.tango.setTarget(MOTORS, self.motors)
        self.tango.setTarget(TURN, self.turn)        

    def neckLeft(self):
        self.headTurn -= self.servoSpeed
        if self.headTurn < 0:
            self.headTurn = 0
        self.tango.setTarget(HEADTURN, self.headTurn)

    def neckRight(self):
        self.headTurn += self.servoSpeed
        if self.headTurn > self.servoMAX:
            self.headTurn = self.servoMAX
        self.tango.setTarget(HEADTURN, self.headTurn)

    def neckUp(self):
        self.headTilt += self.servoSpeed
        if self.headTilt > self.servoMAX:
            self.headTilt = self.servoMAX
        self.tango.setTarget(HEADTILT, self.headTilt)

    def neckDown(self):
        self.headTilt -= self.servoSpeed
        if self.headTilt < self.servoMIN:
            self.headTilt = self.servoMIN
        self.tango.setTarget(HEADTILT, self.headTilt)

    def stopNeck(self):
        self.headTurn = 6000
        self.headTilt = 6000
        self.tango.setTarget(HEADTURN, self.headTurn)
        self.tango.setTarget(HEADTILT, self.headTurn)

    def neckHoriTo(self, val):
        self.headTurn = val
        self.tango.setTarget(HEADTURN, self.headTurn)

    def neckVertiTo(self, val):
        self.headTilt = val
        self.tango.setTarget(HEADTILT, self.headTilt)

    def bodyTo(self, val):
        self.body = val
        self.tango.setTarget(BODY, self.body)

    def kill(self):
        self.motors = 6000
        self.turn = 6000
        self.body = 6000
        self.stopNeck()
        print("I HAVE CEASED MY ACTIONS MASTER.")
        self.tango.setTarget(MOTORS, self.motors)
        self.tango.setTarget(TURN, self.turn)
        self.tango.setTarget(BODY, self.body)
    
    def killMotors(self):
        print("Killed")
        self.motors = 6000
        self.turn = 6000
        self.tango.setTarget(MOTORS, self.motors)
        self.tango.setTarget(TURN, self.turn)