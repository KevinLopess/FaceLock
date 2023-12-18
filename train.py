#!/usr/bin/python

from imutils import paths
import face_recognition
import pickle
import cv2
import os
import RPi.GPIO as GPIO
import time

LED_PIN = 16
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)

def blink_led():
    GPIO.output(LED_PIN, GPIO.HIGH)
    time.sleep(0.25)
    GPIO.output(LED_PIN, GPIO.LOW)
    time.sleep(0.25)

print("[INFO] start processing faces...")
imagePaths = list(paths.list_images("dataset"))


knownEncodings = []
knownNames = []


for (i, imagePath) in enumerate(imagePaths):
    print("[INFO] processing image {}/{}".format(i + 1, len(imagePaths)))
    name = imagePath.split(os.path.sep)[-2]

    image = cv2.imread(imagePath)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    boxes = face_recognition.face_locations(rgb, model="hog")

    encodings = face_recognition.face_encodings(rgb, boxes)

    for encoding in encodings:
        knownEncodings.append(encoding)
        knownNames.append(name)
        
        blink_led()


print("[INFO] serializing encodings...")
data = {"encodings": knownEncodings, "names": knownNames}
with open("encodings.pickle", "wb") as f:
    f.write(pickle.dumps(data))


GPIO.output(LED_PIN, GPIO.LOW)
GPIO.cleanup()
