class conf():
    #WIFI configuration
    wifi_ssid            = 'Ludwig LAN Beethoven'
    wifi_password        = '!Whoo117py'
    wifi_ifconfig        =None
    #mqtt server config - currently as simple as possible
    mqtt_addr          = '192.168.68.112'
    mqtt_port          = 1883
    mqtt_alive         = 60
    mqtt_user          = "esp_pub"
    mqtt_password      = "esp_pub"
    mqtt_status_topic  = "elero/status/"
    mqtt_rssi_topic    = "elero/rssi/"
    mqtt_command_topic = "elero/command/"
    mqtt_memory_topic    = "elero/memory/"
    mqtt_reconnect_delay = 300
    mqtt_id              = "elero"

    enable_cc1101 = True
    spibus  = 1

    # spidev for RPi, bus num for esp32, remark: bus 0 reserved on nodeMCU
    speed   = 5000000

                 # GPIO ports for nodeMCU:
    gdo0    = 5  # D1 <=> GDO0 # Pins using GPIO numbering for additional cc1101 signals
    gdo2    = 4  # D2 <=> GDO2
                 # D5 <=> SCLK
                 # D6 <=> MISO
                 # D7 <=> MOSI
    spics   = 15 # D8 <=> CS

    # remotes/blinds config. 
    # Sniff the traffic to determine the 3 byte addresses and channel no.s of the blinds
    # the 3 byte address of each remote, you can have as many as you need
    remote_addr = [ [0xCE, 0x73, 0x55], [0x74, 0x6E, 0x55], [0x3D, 0x73, 0x55], [0x1E, 0xEB, 0x60]]
    # for each remote above a list of 3 byte addresses and channel number for blinds
    # there can be 1-255(?) entries per remote but all should have the same numbers of entries
    # entries with 0x00s will be ignored
    remote_blind_id = [         
        #  <3 byte address>, <chl>  
        [ [0xC3, 0x01, 0x38, 0x81], #Mine
        ],
        [ [0x3D, 0x01, 0x38, 0x51], #Bedroom
        ],
        [[0xCC, 0x01, 0x38, 0x11], #Aneta
         ],
        [[0x7D, 0x0B, 0x38, 0x21], #LV 01
         [0x7C, 0x0B, 0x38, 0x12],  #LV 02
         [0x3B, 0x0B, 0x38, 0x33], #LV 03
         [0x4E, 0x0B, 0x38, 0x24], #LV 04
         [0x0F, 0x0B, 0x38, 0x15], #LV 05
         ]
    ]

    retrans    = 3      # number of times to send each command >=1
    checkBlinds= False  # Enable frequent blind check
    checkFreq  = 300    # check blind state every n seconds
    wdtTimeout = 400000 # esp32 only - in msec, the watchdog timeout > checkFreq time
    sleepTime  = 0.01   # seconds to sleep if no message received, RPi only, so we don't hog a cpu
    rawTrace   = False  # print all bytes sent/received in raw hex
