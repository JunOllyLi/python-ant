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
from utils import prepare_usb, id_from_serial

idProduct = prepare_usb("ANTUSB")

device = driver.USB2Driver(log=LOG, debug=DEBUG, idProduct=idProduct)
antnode = Node(device)
antnode.start()
network = Network(key=NETWORK_KEY_ANT_PLUS, name='N:ANT+')
antnode.setNetworkKey(NETWORK_NUMBER_PUBLIC, network)

POWER_SENSOR_ID = id_from_serial(1)
#POWER_SENSOR_ID = 12345
print("Start power meter ID %d"%POWER_SENSOR_ID)
pm = PowerMeterTx(antnode, network, POWER_SENSOR_ID)

last_time = time.time()
def updatePower(self, cadence, accPower, power):
    current_time = time.time()
    global last_time
    if current_time - last_time > 0.3:
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
antnode.stop()