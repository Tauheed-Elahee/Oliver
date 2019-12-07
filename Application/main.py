# python3

import time
import serial


def get_bpm(data_raw):
        data = data_raw.split(",")
        bpm = int(data[0])
        return bpm

ser = serial.Serial(
    port="/dev/ttyACM0",
    baudrate=115200
    )

try:
    while True:
        data_raw = ser.readline().decode().strip()
        if data_raw:
            bpm = get_bpm(data_raw)
            print(bpm)
except KeyboardInterrupt:
    ser.close()
