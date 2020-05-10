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
from FitnessEquipment import FitnessEquipment

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

last_time = time.time()
def updatePower(self, cadence, accPower, power):
    current_time = time.time()
    global last_time
    if current_time - last_time > 0.5:
        last_time = current_time
        pm.update(cadence, accPower, power)

fe = FitnessEquipment(antnode, network, callbacks = {'onPowerUpdated': updatePower})

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

print("+++++++++++++++++++---------------")
fe.close()
pm.close()
pm.unassign()
antnode.stop()