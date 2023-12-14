# the main executable for esp32 
# should be started/imported in boot.py
# it assumes boot.py initialises wifi

import time
import os
import gc

from config import conf
from cc1101 import cc1101
from eleroProtocol import eleroProtocol
from machine import WDT
from mqttconnection import mqttconnection


# mqtt
# The callback for when a PUBLISH message is received from the server.
def on_message(topic, msg):
    command = msg.decode("utf-8").rstrip()
    topic = topic.decode("utf-8").rstrip()
    print(topic+" "+command)
    if command in elero.eleroCmds:
        blind = (topic.split('/')[2]) + ":"
        first = (command[0] != 'P')  # for programming commands we want the last remote that knows the blind
        targetBlind, targetRemote = elero.getTarget(blind, first)
        if (targetBlind and conf.enable_cc1101):
            if (command == "Prog"):
                txmsg = elero.construct_msg(targetRemote, targetBlind, 'P1')
                for i in range(conf.retrans):
                    radio.transmit(txmsg)
                #print("sent P1 to "+blind)
                # any blinds in Async mode will send their address as a 0xD4 type message
                # but for simplicity we'll ignore that and use the address/channel in conf.py
                time.sleep(2.1)
                txmsg = elero.construct_msg(targetRemote, targetBlind, 'P2')
                for i in range(conf.retrans):
                    radio.transmit(txmsg)
                #print("sent P2 to "+blind)
                time.sleep(0.5)
                txmsg = elero.construct_msg(targetRemote, targetBlind, 'P3')
                for i in range(conf.retrans):
                    radio.transmit(txmsg)
                #print("sent P3 to "+blind)
            else:
                txmsg = elero.construct_msg(targetRemote, targetBlind, command)
                print("sending: ",''.join('{:02X}:'.format(a) for a in targetRemote),targetBlind[3],''.join('{:02X}:'.format(a) for a in targetBlind[0:3]), command)
                for i in range(conf.retrans):
                    radio.transmit(txmsg)
                    time.sleep(0.1)
                print("sent "+command+" to "+blind)
        else:
            print(blind+" blind not found")
            pass
    else:
        print(command+": invalid command")
        pass


# main
# enable watchdog timer.
if (os.uname()[0] != 'esp8266'):
    wdt = WDT(timeout=conf.wdtTimeout)
    wdt.feed()
if conf.enable_cc1101:
    radio = cc1101(spibus=conf.spibus, spics=conf.spics, speed=conf.speed, gdo0=conf.gdo0, gdo2=conf.gdo2)
elero = eleroProtocol()
client = mqttconnection()
client.connectMqtt(on_message)
lastCheck = time.time()
checkChannel = 0

import pins

pinHandler = pins.pinHandler(client)

blindChecked = False
blindlist = []
for remoteIndex in range(0, len(conf.remote_addr)):
    for blind in conf.remote_blind_id[remoteIndex]:
        if blind[3] > 0:
            blindlist.append((conf.remote_addr[remoteIndex], blind))

client.publish(topic=conf.mqtt_availability_topic, payload="online")
while True:
    if conf.enable_cc1101:
        data = radio.checkBuffer()
    else:
        data = False
    if (data):
        (length, cnt, typ, chl, src, bwd, fwd, dests, payload, rssi, lqi, crc) = elero.interpretMsg(data)
        if (length > 0):  # length 0 => interpretation failed
            print("len= {:d}, cnt= {:d}, typ={:02X}, chl={:d}".format(length,cnt,typ,chl), end=',')
            print('src=[{:02X}{:02X}{:02X}]'.format(src[0],src[1],src[2]),end=',')
            print('bwd=[{:02X}{:02X}{:02X}]'.format(bwd[0],bwd[1],bwd[2]),end=',')
            print('fwd=[{:02X}{:02X}{:02X}]'.format(fwd[0],fwd[1],fwd[2]),end=' - ')
            print('des={:d}'.format(len(dests)),end=':')
            for dest in dests:
                if (len(dest) > 1):
                    print(':[{:02X}{:02X}{:02X}]'.format(dest[0],dest[1],dest[2]),end=',')
                    pass
                else:
                    print(':[{:d}]'.format(dest[0]),end=',')
                    pass
            print("rssi={:.1f},lqi={:d},crc={:d}".format(rssi,lqi,crc),end=', ')
            print("pay="+''.join('{:02X}:'.format(a) for a in payload))

            if (typ == 0xD4):  # responses during programming - we only handle 1 case:
                if (sum(dests[0]) == 0):  # programming complete
                    txmsg = elero.construct_msg(fwd, src + [chl], 'Pdone')
                    print("sending: ",''.join('{:02X}:'.format(a) for a in fwd),chl,''.join('{:02X}:'.format(a) for a in src), "Pdone")
                    for i in range(conf.retrans):
                        radio.transmit(txmsg)
                    print("sent Pdone")

            if (typ == 0xCA):
                topic = conf.mqtt_status_topic + "{:02X}:{:02X}:{:02X}".format(src[0], src[1], src[2])
                print("Sending Topic ",topic," with payload ", elero.eleroState[payload[6]])
                try:
                    client.publish(topic, elero.eleroState[payload[6]])
                    if (os.uname()[0] != 'esp8266'):
                        wdt.feed()
                except Exception as e:
                    print(str(e),payload[6])
                    pass
                # only makes sense to post rssi for the actual transmitter (bwd)
                topic = conf.mqtt_rssi_topic + "{:02X}:{:02X}:{:02X}".format(bwd[0], bwd[1], bwd[2])
                client.publish(topic, "{:.1f}".format(rssi))
    client.check_msg()
    client.ping()

    pinHandler.checkPins()

    checkCounter = int(time.time()) % conf.checkFreq

    # garbage collection once every checkFreq seconds
    if (checkCounter == 16):
        if gcComplete == False:
            print("Garbage Collection - free: ",gc.mem_free()," alloc: ", gc.mem_alloc())
            client.publish(conf.mqtt_memory_topic, str(gc.mem_free()))
            gc.collect()
            gcComplete = True
    else:
        gcComplete = False
    # check blind status - one per remote per second at the start of the checkFreq cycle
    if conf.checkBlinds and (checkCounter != checkChannel) and checkCounter < len(blindlist):
        remote, blind = blindlist[checkCounter]
        print("Check blind status for ",remote, blind)
        msg = elero.construct_msg(remote, blind, "Check")
        if conf.enable_cc1101:
            radio.transmit(msg)
        checkChannel = checkCounter
