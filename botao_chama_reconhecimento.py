import RPi.GPIO as GPIO
import time
import subprocess

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(7, GPIO.OUT)

debounce_time = 0.20 

while True:
    input_state = GPIO.input(10)
    GPIO.output(7, GPIO.LOW)

    if input_state == GPIO.HIGH:
        time.sleep(debounce_time)  

        if GPIO.input(10) == GPIO.HIGH:
            GPIO.output(7, GPIO.HIGH)
            script_path = "./reconhecimento.py"
            subprocess.run(["python3",script_path])



