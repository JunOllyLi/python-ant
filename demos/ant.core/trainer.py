from __future__ import print_function

from ant.plus.plus import DeviceProfile
import time
from ant.plus.heartrate import HeartRate
from ant.core import driver
from ant.core.node import Node, Network, ChannelID
from ant.core.constants import NETWORK_KEY_ANT_PLUS, NETWORK_NUMBER_PUBLIC
from config import *
import struct
import structConstants      as sc
from PowerMeterTx import PowerMeterTx
from FitnessEquipment import FitnessEquipment
from utils import prepare_usb, id_from_serial
from ble_hrm import ble_hrm_start, ble_hrm_stop, ble_hrm_update_hr
from gi.repository import GLib

mainloop = None
def main():
    global mainloop
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

    def device_found(self, channelID):
        print("Detect %s" % str(channelID))

    def updatePower(self, cadence, accPower, power):
        pm.update(cadence, accPower, power)

    def heartrate_data(computed_heartrate, event_time_ms, rr_interval_ms):
        if HR_DEBUG:
            if rr_interval_ms is not None:
                print("Heart rate: %d, event time(ms): %d, rr interval (ms): %d" %
                      (computed_heartrate, event_time_ms, rr_interval_ms))
            else:
                print("Heart rate: %d" % (computed_heartrate, ))
        ble_hrm_update_hr(computed_heartrate)

    hr = HeartRate(antnode, network, callbacks = {'onDevicePaired': device_found,
                                                  'onHeartRateData': heartrate_data})

    fe = FitnessEquipment(antnode, network, callbacks = {'onDevicePaired': device_found,
                                                         'onPowerUpdated': updatePower})

    # Unpaired, search:
    hr.open()
    pm.open()
    fe.open()
    # Paired to a specific device:
    #fe.open(ChannelID(53708, 17, 37))
    #hr.open(ChannelID(21840, 120 ,81))

    print("++++++++++++++++++++++++++++++++++")
    monitor = None
    mainloop = GLib.MainLoop()
    ble_hrm_start()
    #while True:
    #    try:
    #        time.sleep(1)
    #    except KeyboardInterrupt:
    #        break

    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    ble_hrm_stop()

    print("+++++++++++++++++++---------------")
    fe.close()
    pm.close()
    hr.close()
    antnode.stop()

if __name__ == '__main__':
    main()