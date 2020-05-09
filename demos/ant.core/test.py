from __future__ import print_function

from ant.plus.plus import DeviceProfile
import time

from ant.core import driver
from ant.core.node import Node, Network, ChannelID
from ant.core.constants import NETWORK_KEY_ANT_PLUS, NETWORK_NUMBER_PUBLIC
from config import *

class GenericDevice(DeviceProfile):

    channelPeriod = 1070
    name = 'Generic'

    def __init__(self, node, network, deviceType, callbacks=None):
        """
        :param node: The ANT node to use
        :param network: The ANT network to connect on
        :param deviceType: type of device
        :param callbacks: Dictionary of string-function pairs specifying the callbacks to
                use for each event. In addition to the events supported by `DeviceProfile`,
                `HeartRate` also has the following:
                'onHeartRateData'
        """
        callbacks = {'onDevicePaired': self.device_found}
        super(GenericDevice, self).__init__(node, network, callbacks)

        self._detected_device = None
        self.deviceType = deviceType

    def device_found(self, obj, channel_id):
        print("Detect: ", str(channel_id))

    def processData(self, data):
        with self.lock:
            print("broadcast message from device ", self.deviceType)
            length = 16
            line = 0
            while data:
                row = data[:length]
                data = data[length:]
                hex_data = ['%02X' % byte for byte in row]
                print ('%04X' % line, ' '.join(hex_data))


device = driver.USB2Driver(log=LOG, debug=DEBUG, idProduct=0x1008)
antnode = Node(device)
antnode.start()
network = Network(key=NETWORK_KEY_ANT_PLUS, name='N:ANT+')
antnode.setNetworkKey(NETWORK_NUMBER_PUBLIC, network)

#BIKE_POWER(11, "Bike Power Sensors"),
#CONTROLLABLE_DEVICE(16, "Controls"),
#FITNESS_EQUIPMENT(17, "Fitness Equipment Devices"),
#BLOOD_PRESSURE(18, "Blood Pressure Monitors"),
#GEOCACHE(19, "Geocache Transmitters"),
#ENVIRONMENT(25, "Environment Sensors"),
#WEIGHT_SCALE(119, "Weight Sensors"),
#HEARTRATE(120, "Heart Rate Sensors"),
#BIKE_SPDCAD(121, "Bike Speed and Cadence Sensors"),
#BIKE_CADENCE(122, "Bike Cadence Sensors"),
#BIKE_SPD(123, "Bike Speed Sensors"),
#STRIDE_SDM(124, "Stride-Based Speed and Distance Sensors")

dev_type_list = [11, 16, 17, 120, 121, 122, 123, 0]

dev_list = []
for dev_type in dev_type_list:
    dev_list.append(GenericDevice(antnode, network, dev_type))

# Unpaired, search:
for dev in dev_list:
    dev.open()

# Paired to a specific device:
#hr.open(ChannelID(23359, 120, 1))
#hr.open(ChannelID(21840, 120 ,81))

monitor = None
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break

for dev in dev_list:
    dev.close()
antnode.stop()