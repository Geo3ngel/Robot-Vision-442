import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import maestro
import time
import numpy as np
import math
import tkinter as tk
import random

import socket, time
import threading
import queue

from Controller import Controller
from faceDetection import faceDetection

# The drvier handles the State level logic and transitions of the robot's pathing & choice making
# TLDR: It decides what it is currently doing.
class Driver:

    def __init__(self):
        self.cap = PiCamera()
        self.cap.resolution = (640, 480)
        self.rawCapture = PiRGBArray(self.cap)
        self.rawCapture.truncate(0)
        self.fr = faceDetection("haarcascade_frontalface_default.xml")

        for i in [ "Starting up..."]:
                    time.sleep(1)
                    client.sendData(i)
                    time.sleep(2)

        # Initialize controller and straighten out the head to start
        self.controller = Controller()
        self.controller.kill()
        self.controller.L_Grip(4000)
        self.controller.moveL_SholderV(8000)
        self.controller.bodyTo(6000)

        cv2.namedWindow("Video")
        self.currentTime = int(round(time.time() * 1000))

        # Initialize to the starting state (0)
        self.state = 0
        self.iter = 0
        self.bot_clearance = 50 # TODO: Refine this value with testing
        self.TEMP_Timer = time.time()
        self.headDown()
        self.done = False

    def run(self):
        for frame in self.cap.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):

            img = frame.array[102:480, 208:640]

            # TODO: Remove test codes & fill out main loop logic

            if self.done:
                self.controller.kill()
                break

            if self.state is 0 or self.state is 1 or self.state is 3 or self.state is 4:
                # Orient self and cross the line while avoiding bounds & obstacles
                self.lineState(img)
            elif self.state is 2:
                # Search for a person and acquire ice
                self.miningState(img)
            elif self.state is 5:
                # Find the box we want, go over to it, and drop the marker in
                self.find_pink_box(img)
                # Closest pink value

            # cv2.imshow("This", img)

            # Resets the camera buffer
            self.rawCapture.truncate(0)
            k = cv2.waitKey(1)
            if k == 27:
                self.controller.kill()
                break
        cv2.destroyAllWindows()

    def drop_off_state(self, img):
        # First off we need to search for the box (pink)
        # Sraighten out
        # Go to the box
        self.find_pink_box(img)
        # Stop when we are right up next to the box (brown center of mass detected in range)
        # Align our marker's center of mass within acceptable margin of the box's COM.
        # Drop the marker.

    bin_centered = False

    def find_pink_box(self, img):
        hsv_check = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Create the mask
        tape_region = cv2.inRange(hsv_check, self.min_Pink, self.max_Pink)
        # Erode & Dilate image to get rid of slight noise
        tape_region = cv2.erode(tape_region, None, iterations=3)
        tape_region = cv2.dilate(tape_region, None, iterations=4)

        contours, hierarchy = cv2.findContours(tape_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        x, y = self.getClosestCentroid(contours, img)

        # Draw contour on source frame
        for i, c in enumerate(contours):
            area = cv2.contourArea(c)
            if area > 100:
                cv2.drawContours(img, contours, i, (255, 255, 0), 2)
                cv2.drawContours(hsv_check, contours, i, (255, 255, 0), 2)
        cv2.imshow("Video", hsv_check)

        self.controller.R_Grip(10000)
        if x is not None:
            frame_height, frame_width, _ = img.shape
            if self.centerOnBox(x, y):
                print("Centered on box")
                if self.close_check(x, y, img):
                    self.say("We're by the box")
                    print("By the box")
                    self.lazy_drop_check()
                    #self.drop_check(img)
                else:
                    self.controller.burstForward
                    # Move forward if the close condition is not met
        else:
            self.searchNextPos()
            # search for the bin if it has not yet been centered on
            # If it has been centered on, assume we are by the bin & try to drop the marker in
            #self.drop_check(img)
            print("DEFAULT Drop check search")
    box_x = None
    box_y = None
    ice_x = None
    ice_y = None

    # TODO: Cases not handled currently:
    # If the box is not in view
    # If the box & marker are deemed to far apart
    # If the marker is somehow lost and isn't in the view
    def lazy_drop_check(self):
        self.controller.extend_arm()
        time.sleep(3)
        self.controller.bodyTo(5000)
        self.say("Boom.")
        self.dropObject()
        print("Lazy Dropped")
        self.done = True
        time.sleep(3)

    def drop_check(self, img):
        if self.box_x is None:
            self.find_box_center(img)
        elif self.ice_x is None:
            # TODO: move arm into position in front of the camera
            self.find_ice_center(img)
        else:
            # Distance between the two center of masses:
            distance = abs((self.box_y-self.ice_y)/(self.box_x-self.ice_x))
            if distance < 50:
                self.say("Boom.")
                self.dropObject()

        # Drops the object once it is aligned properly
        self.dropObject()



    def find_box_center(self, img):
        hsv_check = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        tape_region = cv2.inRange(hsv_check, self.min_Pink, self.max_Pink)
        tape_region = cv2.erode(tape_region, None, iterations=3)
        tape_region = cv2.dilate(tape_region, None, iterations=4)

        contours, hierarchy = cv2.findContours(tape_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Get the centroid of the box
        self.box_x, self.box_y = self.getClosestCentroid(contours, img)

    def find_ice_center(self, img):
        hsv_check = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        tape_region = cv2.inRange(hsv_check, self.min_Green, self.max_Green)
        tape_region = cv2.erode(tape_region, None, iterations=3)
        tape_region = cv2.dilate(tape_region, None, iterations=4)

        contours, hierarchy = cv2.findContours(tape_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Get the centroid of the ice
        self.ice_x, self.ice_y = self.getClosestCentroid(contours, img)

    def bin_in_range(self, img):
        hsv_check = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        tape_region = cv2.inRange(hsv_check, self.min_Pink, self.max_Pink)
        tape_region = cv2.erode(tape_region, None, iterations=3)
        tape_region = cv2.dilate(tape_region, None, iterations=4)

        contours, hierarchy = cv2.findContours(tape_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Get the centroid of the ice
        x, y = self.getClosestCentroid(contours, img)

        # Navigate to the centroid up very close like
        # TODO: Make it so turning body towards it is useful
        self.turnBodyTowardsLine()


    personFoundTimer = time.time()
    personFound = False
    timerFlag = True
    miningStateFlag = True
    def miningState(self, img):
        # Finds a person and centers on them
        if self.miningStateFlag:
            self.say("Entered Mining Zone.")
            self.miningStateFlag = False
            time.sleep(.4)
        if not self.personFound:
            self.findPerson(img)
        elif not self.iceValidated:
            # cv2.destroyAllWindows
            if self.timerFlag:
                self.TEMP_Timer = time.time()
                self.timerFlag = False
            self.askForIce(img)
        else:
            # Mining completed, return to obstacle course
            self.controller.bodyTo(6000)
            self.state+=1

    def say(self, string):
        for i in [string]:
            time.sleep(1)
            client.sendData(i)

    # Replace this with body/face movement?
    # Finds a person
    def findPerson(self, img):
        # Displays face tracker
            img, x, y, width = self.fr.process_img(img)
            self.lastFaceWidth = width
            #cv2.imshow("Video", img)
            if x is not None:
                self.personFoundTimer = time.time()
                self.centerOnFace(x, y)
                return True
            elif time.time() - self.personFoundTimer > 5:
                # If no face is seen for a few seconds, begin searching for one
                self.searchNextPosPerson()
            else:
                self.controller.kill()
            return False

    # Gives the next search position in the person finding pattern.
    def searchNextPos(self):
        # In order of tilt, turn, body turn.
        positions = [(5000, 6000, 6000), (5000, 7000, 6500), (4000, 7000, 6500),
                     (5000, 6000, 6000), (4000, 6000, 5500), (4000, 5000, 5500), (5000, 5000, 5500)]

        self.controller.neckVertiTo(positions[self.iter][0])
        self.controller.neckHoriTo(positions[self.iter][1])
        self.controller.bodyTo(positions[self.iter][2])
        time.sleep(.7)
        self.iter+=1
        if self.iter is 7:
            self.controller.burstLeft()
            # TODO: make it a longer burst?
        self.iter%=7

    def searchNextPosPerson(self):
        # In order of tilt, turn, body turn.
        positions = [(7000, 6000, 6000), (7000, 7000, 6500), (8000, 7000, 6500),
                     (7000, 7000, 6500), (6000, 7000, 6500), (7000, 6000, 6000),
                     (6000, 5000, 5500), (7000, 5000, 5500), (8000, 5000, 5500)]

        self.controller.neckVertiTo(positions[self.iter][0])
        self.controller.neckHoriTo(positions[self.iter][1])
        self.controller.bodyTo(positions[self.iter][2])
        time.sleep(.7)
        self.iter+=1
        if self.iter is 9:
            self.controller.burstLeft()
            # TODO: make it a longer burst?
        self.iter%=9

    # Centers the robot's camera on the last closest face it saw
    def centerOnFace(self, x, y):
        if x > 100:
            if x < 160:
                if y > 60:
                    if y < 120:
                        self.turnBodyTowards()
                    else:
                        self.controller.neckDown()
                else:
                    self.controller.neckUp()
            else:
                self.controller.neckLeft()
        else:
            self.controller.neckRight()

    # Centers the robot's camera on the closest pink Box
    def centerOnBox(self, x, y):
        if x > 132:
            if x < 300:
                return self.turnBodyTowardsBox()
            else:
                self.controller.neckLeft()
        else:
            self.controller.neckRight()
        return False

        # This swivels the body to face the person it is looking at & corrects the head to look forward.
    def turnBodyTowards(self):
        if self.controller.headTurn <= 5750:
            self.controller.headTurn = self.controller.headTurn + 250
            self.controller.burstRight()                                                                                                                                 
        elif self.controller.headTurn >= 6250:
            self.controller.headTurn = self.controller.headTurn - 250
            self.controller.burstLeft()
        elif self.controller.getBodyPos() >= 6250:
            self.controller.bodyTo(self.controller.getBodyPos()-250)
            self.controller.burstLeft()
        elif self.controller.getBodyPos() <= 5750:
            self.controller.bodyTo(self.controller.getBodyPos()+250)
            self.controller.burstRight()
            # TODO: Confirm these values work for turning the body the appropriate amount
        else:
            self.controller.killMotors()
            print("IN TURN BODY TOWARDS")
            # Person found
            self.distanceCorrection()    # This swivels the body to face the person it is looking at & corrects the head to look forward.

    def turnBodyTowardsBox(self):
        if self.controller.headTurn <= 5750:
            self.controller.headTurn = self.controller.headTurn + 250
            self.controller.burstRight()
        elif self.controller.headTurn >= 6250:
            self.controller.headTurn = self.controller.headTurn - 250
            self.controller.burstLeft()
        elif self.controller.getBodyPos() >= 6250:
            self.controller.bodyTo(self.controller.getBodyPos()-250)
            self.controller.burstLeft()
        elif self.controller.getBodyPos() <= 5750:
            self.controller.bodyTo(self.controller.getBodyPos()+250)
            self.controller.burstRight()
            # TODO: Confirm these values work for turning the body the appropriate amount
        else:
            # self.controller.killMotors()
            print("IN TURN BODY TOWARDS")
            # Box found & centered
            return True
        return False

    def turnBodyTowardsLine(self):
        if self.controller.headTurn <= 5750:
            self.controller.headTurn = self.controller.headTurn + 250
            self.controller.burstRight()
            return False
        elif self.controller.headTurn >= 6250:
            self.controller.headTurn = self.controller.headTurn - 250
            self.controller.burstLeft()
            return False
        elif self.controller.getBodyPos() >= 6250:
            self.controller.bodyTo(self.controller.getBodyPos()-250)
            self.controller.burstLeft()
            return False
        elif self.controller.getBodyPos() <= 5750:
            self.controller.bodyTo(self.controller.getBodyPos()+250)
            self.controller.burstRight()
            return False
            # TODO: Confirm these values work for turning the body the appropriate amount
        else:
            self.controller.killMotors()
            print("IN TURN BODY TOWARDS Line")
            # Person found
            # TODO Bounds check here, & line close check

            # self.controller.burstForward()
            self.iter = 0
            return True
            # Once the person is found, never search for them again

    # Makes the head angle down wards
    def headDown(self):
        self.controller.neckVertiTo(4000)
        time.sleep(.5)

    lastFaceWidth = None
    # This moves closer or farther to the person depending on the area of their face
    def distanceCorrection(self):
        # if square is big boi, burst backward
        # if square is small boi burst forward, both are used in conjunction with the face tracking loop
        if self.lastFaceWidth:
            if self.lastFaceWidth <= 75:
                self.controller.burstForward()
            elif self.lastFaceWidth >= 110:
                self.controller.burstBackward()
            else:
                self.controller.killMotors()
                # TODO: Ask for ice here?
                self.personFound = True
                self.iter = 0
                # Once the person is found, never search for them again

    hasAskedForIce = False
    object_grabbed = False
    validatingIce = False
    iceValidated = False
    def askForIce(self, img):
        # At this point the robot beleive it is centered physically on the person's face.
        # Extends the arm of the robot
        # print(time.time() - self.TEMP_Timer)
        #print("Have asked for ice:", self.hasAskedForIce)
        if not self.hasAskedForIce:
            print("Asking for ice")
            # self.controller.moveL_SholderV(4000)
            self.controller.extend_arm()
            for i in ["Ice please."]:
                client.sendData(i)
                time.sleep(1)
            self.hasAskedForIce = True
            time.sleep(1.5)
            self.TEMP_Timer = time.time()

        # Waits 10 seconds to grab
        elif (not self.object_grabbed) and (time.time() - self.TEMP_Timer > 5):
            self.controller.R_Grip(10000)
            time.sleep(2)
            self.object_grabbed = True
            for i in ["Thank you."]:
                time.sleep(1)
                client.sendData(i)
            self.validatingIce = True
            self.controller.neckVertiTo(4000)
            self.controller.neckHoriTo(4000)

            self.controller.arm_check()
            time.sleep(.5)

        elif self.validatingIce:

            if self.checkIceColor(img):
                self.iceValidated = True
                self.controller.neckVertiTo(6000)
                self.controller.neckHoriTo(6000)
                self.extendArm()
                for i in ["This Ice pleases me."]:
                    time.sleep(1)
                    client.sendData(i)
                self.extendArm()
                time.sleep(.5)
                self.state += 1
                self.controller.moveR_SholderV(5000)
                # Move onto next state

            else:
                # The ice is the wrong color
                for i in ["DO YOU TAKE ME FOR A FOOL?!"]:
                    time.sleep(1)
                    client.sendData(i)
                self.controller.neckVertiTo(6000)
                self.controller.neckHoriTo(6000)
                self.controller.relax_arm()
                time.sleep(1)
                # reset to ask for ice again
                self.hasAskedForIce = False
                self.object_grabbed = False
                self.iceValidated = False
                self.validatingIce = False
                self.TEMP_Timer = time.time()

    def extendArm(self):
        self.controller.extend_arm()

    def armDown(self):
        self.controller.moveL_SholderV(8000)
        # TODO:  Check Value for this

    def dropObject(self):
        #self.controller.L_Grip(4000) # TODO: Refine value to ensure it drops the object
        self.controller.R_Grip(4000)

    # Returns true if the color the marker is supposed to be is present.
    def checkIceColor(self, img):
        hsv_check = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Create the mask
        tape_region = cv2.inRange(hsv_check, self.min_Green, self.max_Green)
        # Erode & Dilate image to get rid of slight noise
        tape_region = cv2.erode(tape_region, None, iterations=3)
        tape_region = cv2.dilate(tape_region, None, iterations=4)

        contours, hierarchy = cv2.findContours(tape_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw contour on source frame
        for i, c in enumerate(contours):
            area = cv2.contourArea(c)
            if area > 100:
                cv2.drawContours(img, contours, i, (255, 255, 0), 2)
                cv2.drawContours(hsv_check, contours, i, (255, 255, 0), 2)
        cv2.imshow("Video", img)
        print("Should see me now")
        # TODO: Remove this image after debugging is done
        if len(contours) > 0:
            return True
        return False

    # HSV range for white
    min_White = np.array([15, 0, 225], np.uint8)
    max_White = np.array([135, 10, 255], np.uint8)

    # HSV range for pink
    # min_Pink = np.array([160, 60, 0], np.uint8)
    # max_Pink = np.array([180, 255, 255], np.uint8)
    # min_Pink = np.array([140, 20, 225], np.uint8)
    # max_Pink = np.array([174, 40, 256], np.uint8)
    min_Pink = np.array([160, 80, 100], np.uint8)
    max_Pink = np.array([175, 255, 255], np.uint8)

    min_Green = np.array([30, 20, 0], np.uint8)
    max_Green = np.array([45, 255, 255], np.uint8)

    min_Light_Pink = np.array([140, 20, 200], np.uint8)
    max_Light_Pink = np.array([175, 80, 255], np.uint8)

    # HSV range for orange
    # min_Orange = np.array([10, 100, 50], np.uint8)
    # max_Orange = np.array([30, 120, 255], np.uint8)
    # min_Orange = np.array([15, 100, 230], np.uint8)
    # max_Orange = np.array([26, 255, 255], np.uint8)
    min_Orange = np.array([15, 50, 100], np.uint8)
    max_Orange = np.array([26, 255, 255], np.uint8)

    # HSV range for blue
    min_Blue = np.array([100, 50, 50], np.uint8)
    max_Blue = np.array([130, 255, 255], np.uint8)

    # def lineState(self, img):
    #     # Avoid going out of bounds/ dodge white
    #     self.avoidBounds()
    #     # TODO: Orient so that the line is in view
    #     # TODO: Face the line
    #     # TODO: Go up to the line
    #     # TODO: Cross the line

    def lineState(self, img):
        # filter the current image for the color
        hsv_check = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        x = None
        y = None

        # Create the mask for line we are looking for depending on the state
        if self.state is 0 or self.state is 4:
            tape_region = cv2.inRange(hsv_check, self.min_Orange, self.max_Orange)
        elif self.state is 1 or self.state is 3:
            tape_region = cv2.inRange(hsv_check, self.min_Light_Pink, self.max_Light_Pink)
        else:
            print("Error, state:", self.state, "is not supposed to call 'findLine()'")

        if tape_region is not None:
            tape_region = cv2.erode(tape_region, None, iterations=3)
            tape_region = cv2.dilate(tape_region, None, iterations=4)

            contours, hierarchy = cv2.findContours(tape_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # TODO: get LARGEST centroid, not the closest.
            # x, y = self.getClosestCentroid(contours, img)

            if len(contours) > 0:
                largest_area = cv2.contourArea(contours[0])
                largest_cont = contours[0]

                # Get the largest centroid:
                for c in contours:
                    temp = cv2.contourArea(c)
                    if temp > largest_area:
                        largest_area = temp
                        largest_cont = c

                m = cv2.moments(largest_cont)
                # print(m)
                x = int(m['m10'] / m['m00'])
                y = int(m['m01'] / m['m00'])

                # # Draw contour on source frame
                # for i, c in enumerate(contours):
                #     area = cv2.contourArea(c)
                #     if area > 100:
                #         cv2.drawContours(img, contours, i, (255, 255, 0), 2)
                #         cv2.drawContours(hsv_check, contours, i, (255, 255, 0), 2)
                # cv2.imshow("Video", hsv_check)

                if x is not None:
                    if not self.turnBodyTowardsLine():
                        print("Turning Body Towards Line")
                    elif self.close_check(x, y, img):
                        # if the line is close enough to the bot move to next state after moving forward
                        pan, tilt, = self.controller.getServoPos()
                        if tilt <= 4000:
                            print("TILT:", tilt)
                            self.controller.burstForward()
                            self.controller.burstForward()
                            # TODO: Edit if it is not enough or to much
                            self.say(("Passing into state: " + str(self.state+1)))
                            self.state += 1
                        else:
                            self.headDown()
                            print("Line close: TILT:", tilt)
                    else:
                        print("Passes neck & body check")
                        # get the image x value for reference
                        _, frame_mid, _ = img.shape
                        # Checks if the centroid is to the left of center & has clearance to move forward
                        if abs((frame_mid / 2) - x) < 70:
                            print("Line CENTERED in View")
                            if self.avoidBounds(img):
                                self.controller.burstForward()
                                self.headDown()
                                print("Moving forward")
                            else:
                                # we see the line and are centered on it, but have an obstacle in the way
                                self.avoiding_obstace = True
                                print("Trying to avoid obstacle")
                        elif (frame_mid / 2) - x > -1:
                            self.controller.burstLeft()
                            print("Turning towards line [LEFT]:", str((frame_mid / 2) - x))
                        else:
                            self.controller.burstRight()
                            print("Turning towards line [RIGHT]:", str((frame_mid / 2) - x))

                        # The line is in our field of view
                        return True, x, y
                else:
                    # if self.avoiding_obstace:
                    #     print("Avoiding obstacle I guess?")
                    #     if self.avoidBounds(img):
                    #         # Provided we are avoiding obstacles & there is no obstacle in sight,
                    #         # move forward & check to see if we now have a valid path.
                    #         self.controller.burstForward()
                    #         self.avoiding_obstace = False
                    # else:
                        # Finds the line
                        self.controller.killMotors()
                        self.searchNextPos()
                        print("State:", self.state)
                        if self.state is 3:
                            self.controller.burstLeft()
                            print("Special case bust left")

        return False

    def close_check(self, x, y, img):
        # TODO: This checks if the line is close enough to the bot to be crossed
        frame_height, frame_width, _ = img.shape
        if y > 300:
            # if x < 150:
            #     # The line is to the left of it
            #     self.controller.burstLeft()
            #     print("LINE is to the Left:", x, "Frame width is:", frame_width)
            # elif x > 490:
            #     # The line is to the right of it
            #     self.controller.burstRight()
            #     print("LINE is to the Right:", x, "Frame width is:", frame_width)
            # else:
            print("LINE IS CLOSE:", y, "Frame height is:", frame_height)
            return True
        else:
            self.controller.burstForward()
            print("LINE IS NOT CLOSE ENOUGH:", y, "Frame height is:", frame_height)

        return False

    def check_neck_and_body_pos(self):
        if self.controller.getBodyPos() is not 6000:
            # print("Body at pos:", self.controller.getBodyPos())
            return False
        tilt, pan = self.controller.getServoPos()
        if tilt < 6300:
            # print("Bit head is 'Tilted' @:" + tilt)
            return False
        if pan is not 6000:
            # print("Bit head is 'Panned' @:"+pan)
            return False
        return True

    def check_body(self):
        if self.controller.getBodyPos() is not 6000:
            # print("Body at pos:", self.controller.getBodyPos())
            return False
        return True

    def center_on_line(self, x, y):
        pass # TODO: Center on the line?
    avoiding_obstace = False
    def circumventObstactle(self, img):
        pass # TODO: Make it so obstacles are avoided using this method?
    # Returns true if we will sucessfully avoid the boundries/obstacles
    def avoidBounds(self, img):
        self.headDown()
        # filter the current image for the color
        # Gets the lower half of the image to check for White

        hsv_check = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        white_check = hsv_check[120:480, 640:640]

        # Create the mask
        tape_region = cv2.inRange(hsv_check, self.min_White, self.max_White)
        # Erode & Dilate image to get rid of slight noise
        tape_region = cv2.erode(tape_region, None, iterations=3)
        tape_region = cv2.dilate(tape_region, None, iterations=4)

        contours, hierarchy = cv2.findContours(tape_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Now that we have the contours, we make our decision based on them
        x, y, will_clear = self.getCentermostCentroid(contours, white_check)

        if will_clear:
                # self.controller.killMotors()
            return True

        # Otherwise, we want to turn away from the nearest white centroid
        _, frame_mid, _ = white_check.shape
        # Checks if the centroid is to the left of center
        if (frame_mid/2) - x > -1:
            self.controller.burstRight()
            print("Turning away [RIGHT] from obstacle:", str((frame_mid/2) - x))
        else:
            self.controller.burstLeft()
            print("Turning away [LEFT] from obstacle:", str((frame_mid / 2) - x))
        return False

    def getCentermostCentroid(self, contours, img):
        frame_height, frame_mid, _ = img.shape
        centerX = frame_mid/2
        centerY = frame_height/2

        shortest_distance_from_center = None
        cx_closest = None
        cy_closest = None
        will_clear = True

        for cnt in contours:
            m = cv2.moments(cnt)
            cx = int(m['m10'] / m['m00'])
            cy = int(m['m01'] / m['m00'])

            # Calculates the distance from the current centroid to the center of the image

            try:
                distance = abs((centerY - cy) / centerX - cx)
            except:
                distance = centerY - cy

            if shortest_distance_from_center is None or distance < shortest_distance_from_center:
                cx_closest = cx
                cy_closest = cy
                shortest_distance_from_center = distance
            # TODO May need adjusting
            if shortest_distance_from_center < self.bot_clearance:
                will_clear = False
        return cx_closest, cy_closest, will_clear

    def getClosestCentroid(self, contours, img):

        frameHeight, frameMid, _ = img.shape

        shortest_distance = None
        cx_closest = None
        cy_closest = None

        for cnt in contours:
            m = cv2.moments(cnt)
            # print(m)
            cx = int(m['m10'] / m['m00'])
            cy = int(m['m01'] / m['m00'])

            # Calculates the distance from the current centroid to the bot
            distance = abs((frameHeight-cy)/frameMid-cx)

            if shortest_distance is None or distance < shortest_distance:
                cx_closest = cx
                cy_closest = cy
                shortest_distance = distance

        return cx_closest, cy_closest

    # Need to define testing states

globalVar = ""

class ClientSocket(threading.Thread):
    def __init__(self, IP, PORT):
        super(ClientSocket, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((IP, PORT))
  
        print ('connected')
        self.alive = threading.Event()
        self.alive.set()

    def recieveData(self):
        global globalVar
        try:
            data = self.s.recv(105)
            # print (data)
            globalVar = data
        except IOError as e:
            if e.errno == errno.EWOULDBLOCK:
                pass

    def sendData(self, sendingString):
        print ('sending')
        sendingString += "\n"
        self.s.send(sendingString.encode('UTF-8'))
        print ('done sending')

    def run(self):
        global globalVar
        while self.alive.isSet():
            data = self.s.recv(105)
            # print (data)
            globalVar = data
            if(data == "0"):
                self.killSocket()
            
    def killSocket(self):
        self.alive.clear()
        self.s.close()
        print("Goodbye")
        exit()
            
IP = '10.200.17.181'
PORT = 5010
client = ClientSocket(IP, PORT)

driver = Driver()
driver.run()