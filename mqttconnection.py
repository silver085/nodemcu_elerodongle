import network
from umqttsimple import MQTTClient
import gc
from config import conf
import time
from machine import Pin

class mqttconnection:
    def __init__(self):
        self.sta_if = network.WLAN(network.STA_IF)
        self.led=Pin(2,Pin.OUT)
        self.led(1)
        self.mqttCheckComplete = False

    def do_connect(self):
        ap = network.WLAN(network.AP_IF)
        ap.active(False)
        if not self.sta_if.isconnected():
            #print('connecting to network...')
            self.sta_if.active(True)
            self.sta_if.connect(conf.wifi_ssid, conf.wifi_password)
            while not self.sta_if.isconnected():
                pass
            if conf.wifi_ifconfig:
                self.sta_if.ifconfig(conf.wifi_ifconfig)
        #print('network config:', self.sta_if.ifconfig())

    def connectMqtt(self, on_message):
        if not self.sta_if.isconnected():
            self.do_connect()
        self.client = MQTTClient(conf.mqtt_id,conf.mqtt_addr, conf.mqtt_port, keepalive=conf.mqtt_alive, user=conf.mqtt_user, password=conf.mqtt_password)
        self.client.set_callback(on_message)
        while True:
            try:
                self.client.connect()
                self.client.subscribe(conf.mqtt_command_topic+"#")
            except OSError:
                #print("Connection timeout for MQTT! Reconnect in " + str(conf.mqtt_reconnect_delay) + " seconds")
                self.client.disconnect
                time.sleep(conf.mqtt_reconnect_delay)
            else:
                break;
            gc.collect()
        #print("MQTT client connected! Starting main loop")

    def reconnect(self):
        try:
            #print("Keepalive timeout for MQTT! Reconnect in " + str(conf.mqtt_reconnect_delay) + " seconds")
            self.led(0)
            self.client.disconnect()
            while True:
                for i in range(0,conf.mqtt_reconnect_delay):
                    time.sleep(1)
                if not self.sta_if.isconnected():
                    #print('connecting to network...')
                    self.sta_if.connect(conf.wifi_ssid, conf.wifi_password)
                    time.sleep(5)
                try:
                    self.client.connect()
                except OSError:
                    pass
                    #print("Connection timeout for MQTT! Reconnect in " + str(conf.mqtt_reconnect_delay) + " seconds")
                else:
                    try:
                        self.client.subscribe(conf.mqtt_command_topic+"#")
                    except OSError:
                        #print("Error when subscribing ... disconnect and retry")
                        self.client.disconnect()
                    else:
                        break;
                gc.collect()
            self.led(1)
        except OSError as e:
            pass
            #print("Unexpected error when reconnected: " + str(e))

    def check_msg(self):
        try:
            self.client.check_msg()
        except OSError:
            self.reconnect()

    def publish(self, topic, payload):
        try:
            self.client.publish(topic, payload)
        except OSError:
            self.reconnect()

    def ping(self):
        mqttCheck=int(time.time())%(conf.mqtt_alive/4)
        if mqttCheck == 0:
            if self.mqttCheckComplete == False:
                try:
                    self.client.ping()
                except OSError:
                    self.reconnect()
                self.mqttCheckComplete = True
        else:
            self.mqttCheckComplete = False
