import sys
from ant.core import message
from ant.core.constants import *
from ant.core.exceptions import ChannelError
from ant.plus.plus import DeviceProfile
from config import VPOWER_DEBUG

CHANNEL_PERIOD = 8182
POWER_DEVICE_TYPE = 0x0B

# Transmitter for Bicycle Power ANT+ sensor
class PowerMeterTx(DeviceProfile):
    class PowerData:
        def __init__(self):
            self.eventCount = 0
            self.eventTime = 0
            self.cumulativePower = 0
            self.instantaneousPower = 0

    def __init__(self, antnode, network, sensor_id, callbacks=None):
        self.antnode = antnode

        super(PowerMeterTx, self).__init__(antnode, network, callbacks)
        # Get the channel
        self.channel = antnode.getFreeChannel()
        try:
            self.channel.name = 'C:POWER'
            self.channel.assign(network, CHANNEL_TYPE_TWOWAY_TRANSMIT)
            self.channel.setID(POWER_DEVICE_TYPE, sensor_id, 0)
            self.channel.period = 8182
            self.channel.frequency = 57
        except ChannelError as e:
            print ("Channel config error: "+e.message)
        self.powerData = PowerMeterTx.PowerData()

    def open(self):
        self.channel.open()

    def close(self):
        self.channel.close()

    def unassign(self):
        self.channel.unassign()

    # Power was updated, so send out an ANT+ message
    def update(self, cadence, accPower, power):
        with self.lock:
            if VPOWER_DEBUG: print ('PowerMeterTx: update called with power ', power)
            self.powerData.eventCount = (self.powerData.eventCount + 1) & 0xff
            if VPOWER_DEBUG: print ('eventCount ', self.powerData.eventCount)
            self.powerData.cumulativePower = (int(accPower) & 0xffff)
            if VPOWER_DEBUG: print ('cumulativePower ', self.powerData.cumulativePower)
            self.powerData.instantaneousPower = int(power)
            if VPOWER_DEBUG: print ('instantaneousPower ', self.powerData.instantaneousPower)

            payload = bytearray(b'\x00' * 8)  # standard power-only message
            payload[0] = 0x10
            payload[1] = self.powerData.eventCount
            payload[2] = 0xFF  # Pedal power not used
            payload[3] = int(cadence) & 0xFF
            payload[4] = self.powerData.cumulativePower & 0xff
            payload[5] = self.powerData.cumulativePower >> 8
            payload[6] = self.powerData.instantaneousPower & 0xff
            payload[7] = self.powerData.instantaneousPower >> 8
            ant_msg = message.ChannelBroadcastDataMessage(self.channel.number, data=payload)
            #sys.stdout.write('+')
            #sys.stdout.flush()
            if VPOWER_DEBUG: print ('Write message to ANT stick on channel ' + repr(self.channel.number))
            self.antnode.send(ant_msg)