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

class FitnessEquipment(DeviceProfile):

    channelPeriod = 0x2000
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
        super(FitnessEquipment, self).__init__(node, network, callbacks)

        self._detected_device = None
        self.deviceType = FitnessEquipment.deviceType

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
                onPowerUpdated = self.callbacks.get('onPowerUpdated')
                if onPowerUpdated:
                    onPowerUpdated(self, FE_Cadence, xx_AccPower, FE_Power)
            if DEBUG:
                print("broadcast message from device ", self.deviceType)
                length = 16
                line = 0
                while data:
                    row = data[:length]
                    data = data[length:]
                    hex_data = ['%02X' % byte for byte in row]
                    print ('%04X' % line, ' '.join(hex_data))