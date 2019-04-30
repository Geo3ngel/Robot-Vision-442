import cv2
import numpy as np
from picamera import PiCamera
from picamera.array import PiRGBArray
import tkinter as tk

class RectDetect:

    def __init__(self):
        self.cap = PiCamera()
        self.cap.resolution = (640, 480)
        self.rawCapture = PiRGBArray(self.cap)
        self.rawCapture.truncate(0)
        cap = cv2.VideoCapture(0)
        cv2.namedWindow("Video")

        for frame in self.cap.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):

            img = frame.array[102:480, 208:640]

            # Blur the image(may be unnecessary)
            img = cv2.GaussianBlur(img, (3, 3), 0)
            # Convert img to hsv
            hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Define contour range for orange (Or was it yellow?)
            # min_Orange = np.array([15, 50, 100], np.uint8)
            # max_Orange = np.array([26, 255, 255], np.uint8)
            # BLUE RANGE:
            # min_Orange = np.array([110, 70, 100], np.uint8)
            # max_Orange = np.array([120, 255, 255], np.uint8)
            # GREEN COLOR:
            # min_Orange = np.array([30, 20, 0], np.uint8)
            # max_Orange = np.array([45, 255, 255], np.uint8)
            # ORANGE RANGE
            # min_Orange = np.array([10, 50, 50], np.uint8)
            # max_Orange = np.array([27, 200, 255], np.uint8)
            #PINK RANGE
            # min_Orange = np.array([140, 0, 0], np.uint8)
            # max_Orange = np.array([190, 255, 256], np.uint8)
            # Pretty good LIGHT PINK range
            # min_Orange = np.array([140, 20, 200], np.uint8)
            # max_Orange = np.array([175, 80, 255], np.uint8)
            # min_Orange = np.array([140, 0, 100], np.uint8)
            # max_Orange = np.array([175, 100, 255], np.uint8)
            # BRIGHT PINK (Perfect
            min_Orange = np.array([150, 150, 100], np.uint8)
            max_Orange = np.array([175, 255, 255], np.uint8)
            # min_Orange = np.array([160, 20, 200], np.uint8)
            # max_Orange = np.array([175, 80, 255], np.uint8)

            # Create mask w/ boundaries (Mask is the black & white)
            TapeRegion = cv2.inRange(hsv_img, min_Orange, max_Orange)

            # Erode & Dilate image to get rid of slight noise
            TapeRegion = cv2.erode(TapeRegion, None, iterations=5)
            TapeRegion = cv2.dilate(TapeRegion, None, iterations=6)

            contours, hierarchy = cv2.findContours(TapeRegion, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Draw contour on source frame
            for i, c in enumerate(contours):
                area = cv2.contourArea(c)
                if area > 100:
                    cv2.drawContours(img, contours, i, (255, 255, 0), 2)
                    cv2.drawContours(hsv_img, contours, i, (255, 255, 0), 2)

            # Prints out contour values
            # TODO: Go to closest centroid first
            if len(contours) > 0:
                cnt = contours[0]
                M = cv2.moments(cnt)
                # print(M)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                x, y = self.getClosestCentroid(contours, img)
                # print("cx:", x, "cy:", y)
            cv2.imshow("Video", img)
            cv2.imshow("HSV", hsv_img)
            cv2.imshow("Orange", TapeRegion)
            self.rawCapture.truncate(0)

            k = cv2.waitKey(1)
            if k == 27:
                break
        cv2.destroyAllWindows()

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

            # 0print("cx:", cx_closest, "cy:", cy_closest)

        return [cx_closest, cy_closest]

rd = RectDetect();