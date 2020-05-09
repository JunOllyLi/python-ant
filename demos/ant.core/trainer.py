from __future__ import print_function

from ant.plus.plus import DeviceProfile
import time

from ant.core import driver
from ant.core.node import Node, Network, ChannelID
from ant.core.constants import NETWORK_KEY_ANT_PLUS, NETWORK_NUMBER_PUBLIC
from config import *
import struct
import structConstants      as sc
from PowerMeterTx import PowerMeterTx

pm = None

class FitnessEquipment(DeviceProfile):

    channelPeriod = 8070
    deviceType = 17
    name = 'Fitness'

    def __init__(self, node, network, callbacks=None):
        """
        :param node: The ANT node to use
        :param network: The ANT network to connect on
        :param callbacks: Dictionary of string-function pairs specifying the callbacks to
                use for each event. In addition to the events supported by `DeviceProfile`,
                `HeartRate` also has the following:
                'onHeartRateData'
        """
        callbacks = {'onDevicePaired': self.device_found}
        super(FitnessEquipment, self).__init__(node, network, callbacks)

        self._detected_device = None
        self.deviceType = FitnessEquipment.deviceType

    def device_found(self, obj, channel_id):
        print("Detect: ", str(channel_id))

    def msgUnpage25_TrainerData(self, info):
        fChannel            = sc.unsigned_char  #0 First byte of the ANT+ message content
        fDataPageNumber     = sc.unsigned_char  #1 First byte of the ANT+ datapage (payload)
        fEvent              = sc.unsigned_char  #2
        fCadence            = sc.unsigned_char  #3
        fAccPower           = sc.unsigned_short #4
        fInstPower          = sc.unsigned_short #5 The first four bits have another meaning!!
        fFlags              = sc.unsigned_char  #6

        format= sc.no_alignment + fDataPageNumber + fEvent + fCadence + fAccPower + fInstPower + fFlags
        tuple = struct.unpack (format, info)

        return tuple[0], tuple[1], tuple[2], tuple[3], tuple[4], tuple[5]

    def processData(self, data):
        with self.lock:
            if 25 == data[0]:
                DataPageNumber, xx_Event, FE_Cadence, xx_AccPower, FE_Power, xx_Flags = self.msgUnpage25_TrainerData(data)
                print("===== ", xx_AccPower, FE_Power)
                if pm:
                    pm.update(FE_Power)
            if DEBUG:
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

def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

#POWER_SENSOR_ID = int(int(hashlib.md5(getserial()).hexdigest(), 16) & 0xfffe) + 1
POWER_SENSOR_ID = 12345
pm = PowerMeterTx(antnode, network, POWER_SENSOR_ID)
fe = FitnessEquipment(antnode, network)

# Unpaired, search:
#fe.open()
pm.open()
# Paired to a specific device:
fe.open(ChannelID(53708, 17, 37))
#hr.open(ChannelID(21840, 120 ,81))

print("++++++++++++++++++++++++++++++++++")
monitor = None
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break

fe.close()
pm.close()
pm.unassign()
antnode.stop()