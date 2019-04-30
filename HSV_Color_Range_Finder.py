import numpy as np
import cv2

pink = np.uint8([[[255, 192, 203]]])
hsvGreen = cv2.cvtColor(pink,cv2.COLOR_BGR2HSV)
print(hsvGreen)
lowerLimit = (hsvGreen[0][0][0]-10,100,100)
upperLimit = (hsvGreen[0][0][0]+10,255,255)
print(upperLimit)
print(lowerLimit)