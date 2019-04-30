import cv2
import numpy as np

# This program is meant to track the face of people. duh.
class faceDetection:

    # Takes in the path to haar cascade xml
    def __init__(self, xml_path):
        # Creates the haar cascade
        self.faceCascade = cv2.CascadeClassifier(xml_path)

    def process_img(self, img):

        # equalize image
        img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)

        # equalize the histogram of the Y channel
        img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])

        # convert the YUV image back to RGB format
        img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

        # greyscale img
        gray = cv2.cvtColor(img_output, cv2.COLOR_BGR2GRAY)

        # Detect faces in the image
        faces = self.faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(faces) > 0:
            largestface = faces[0]
            # Detect the largest face
            for (x, y, w, h) in faces:
                # Can use these face positions to tell which face to lock onto, and how to interact w/ it (ie step away)
                if w*h > largestface[2]*largestface[3]:
                    largestface = (x, y, w, h)

            x = largestface[0]
            y = largestface[1]
            w = largestface[2]
            h = largestface[3]

            # Draw the rectange on only the largest face recognized.
            cv2.rectangle(gray, (x, y), (x + w, y + h), (0, 255, 0), 2)

            return gray, x, y, w
        return gray, None, None, None