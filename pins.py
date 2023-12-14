import machine
import time

inputPins = [3]
topic = "nodeEG/gpio/{}"
resendFreq = 120

class pinHandler():
    def __init__(self, mqttClient):
        self.pins = []
        self.pinState = []
        self.resendComplete = False
        self.client = mqttClient
        for pinNumber in inputPins:
            pin = machine.Pin(pinNumber, machine.Pin.IN, machine.Pin.PULL_UP)
            self.pins.append(pin)
            self.pinState.append(pin.value())
            if pin.value() == 0:
                val = b"OFF"
            else:
                val = b"ON"
            self.client.publish(topic.format(str(pinNumber)), val)

    def checkPins(self):
        checkCounter=int(time.time())%resendFreq
        for i in range(0, len(inputPins)):
            pinNumber = inputPins[i]
            pin = self.pins[i]
            state = self.pinState[i]
            newState = pin.value()
            if newState == 0:
                val = b"CLOSED"
            else:
                val = b"OPEN"
            if checkCounter == 2:
                if self.resendComplete is False:
                    self.client.publish(topic.format(str(pinNumber)), val)
                    self.resendComplete = True
            else:
                    self.resendComplete = False
            if newState == state:
                continue
            self.pinState[i] = newState
            self.client.publish(topic.format(str(pinNumber)), val)
