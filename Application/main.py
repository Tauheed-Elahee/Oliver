# python3

import serial

ser = serial.Serial(
    port="COM4",
    baudrate=115200
)


def get_bpm(data_raw):
        data = data_raw.split(",")
        bpm = int(data[0])
        return bpm


try:
    while True:
        data_raw = ser.readline().decode().strip()
        if data_raw:
            bpm = get_bpm(data_raw)
            print(bpm)
except KeyboardInterrupt:
    ser.close()


finalMinRValue = 0.0
finalMinMValue = 0.0

# linear regression is just minimizing the distance from point to line

def findRValue(mValue, xOneValue, yOneValue, dataPointsY, i):

    if i >= len(dataPointsY):
        return 0

    if mValue != 0:
        x = (i/mValue + dataPointsY[i] + mValue*xOneValue - yOneValue)/(mValue+(1/mValue))
        y = mValue*(x-xOneValue)+yOneValue

        return (dataPointsY[i]-y)**2 + (i-x)**2 + findRValue(mValue, xOneValue, yOneValue, dataPointsY, i+1)

    return dataPointsY[i] + findRValue(mValue, xOneValue, yOneValue, dataPointsY, i+1)


def findBestLine(allDataPointsY):
    mValue = 0.0
    minRValue = 1000.0
    for i in range(0, len(allDataPointsY)):
        for j in range(i+1, len(allDataPointsY)):
            mEval = (allDataPointsY[j] - allDataPointsY[i])/(j-i)
            rEval = findRValue(mEval, j, allDataPointsY[j], allDataPointsY, 0)
            if(rEval < minRValue):
                minRValue = rEval
                mValue = mEval

    global finalMinRValue
    finalMinRValue = minRValue
    global finalMinMValue
    finalMinMValue = mValue

    return mValue < 0 and abs(mValue) > 1
