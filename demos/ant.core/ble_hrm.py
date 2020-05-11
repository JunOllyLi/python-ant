#!/usr/bin/env python3

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import array

from gi.repository import GLib
#import glib as GLib
from gatt_server import *
from random import randint

class ble_hrm_app(gatt_service_app):
    """
    org.bluez.GattApplication1 interface implementation
    """
    def __init__(self, bus):
        super(ble_hrm_app, self).__init__(bus)
        self.add_service(HeartRateService(bus, 0))

hr_measurement = None
class HeartRateService(Service):
    """
    Fake Heart Rate Service that simulates a fake heart beat and control point
    behavior.

    """
    HR_UUID = '0000180d-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index):
        global hr_measurement
        Service.__init__(self, bus, index, self.HR_UUID, True)
        hr_measurement = HeartRateMeasurementChrc(bus, 0, self)
        self.add_characteristic(hr_measurement)
        self.add_characteristic(BodySensorLocationChrc(bus, 1, self))
        self.add_characteristic(HeartRateControlPointChrc(bus, 2, self))
        self.energy_expended = 0


class HeartRateMeasurementChrc(Characteristic):
    HR_MSRMT_UUID = '00002a37-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.HR_MSRMT_UUID,
                ['notify'],
                service)
        self.notifying = False
        self.hr_ee_count = 0

    def update_hr(self, hr_reading):
        value = []
        value.append(dbus.Byte(0x06))

        value.append(dbus.Byte(hr_reading))

        if self.hr_ee_count % 10 == 0:
            value[0] = dbus.Byte(value[0] | 0x08)
            value.append(dbus.Byte(self.service.energy_expended & 0xff))
            value.append(dbus.Byte((self.service.energy_expended >> 8) & 0xff))

        self.service.energy_expended = \
                min(0xffff, self.service.energy_expended + 1)
        self.hr_ee_count += 1

        if self.notifying:
            self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': value }, [])

    def StartNotify(self):
        print("===============================StartNotify heart rate")
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True

    def StopNotify(self):
        print("-------------------------------StopNotify heart rate")
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False

class BodySensorLocationChrc(Characteristic):
    BODY_SNSR_LOC_UUID = '00002a38-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.BODY_SNSR_LOC_UUID,
                ['read'],
                service)

    def ReadValue(self, options):
        # Return 'Chest' as the sensor location.
        return [ 0x01 ]

class HeartRateControlPointChrc(Characteristic):
    HR_CTRL_PT_UUID = '00002a39-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.HR_CTRL_PT_UUID,
                ['write'],
                service)

    def WriteValue(self, value, options):
        print('Heart Rate Control Point WriteValue called')

        if len(value) != 1:
            raise InvalidValueLengthException()

        byte = value[0]
        print('Control Point value: ' + repr(byte))

        if byte != 1:
            raise FailedException("0x80")

        print('Energy Expended field reset!')
        self.service.energy_expended = 0

def register_app_cb():
    print('GATT application registered')


def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()

def register_ad_cb():
    print('Advertisement registered')


def register_ad_error_cb(error):
    print('Failed to register advertisement: ' + str(error))
    mainloop.quit()

def ble_hrm_update_hr(hr_reading):
    global hr_measurement
    hr_measurement.update_hr(hr_reading)

class HRMAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid('180D')
        self.add_manufacturer_data(0xffff, [0x00, 0x01, 0x02, 0x03, 0x04])
        self.add_service_data('9999', [0x00, 0x01, 0x02, 0x03, 0x04])
        #self.add_local_name('ANT_to_BLE_HRM')
        self.include_tx_power = True
        self.add_data(0x26, [0x01, 0x01, 0x00])

ad_manager = None
hrm_advertisement = None
def ble_hrm_start():
    global ad_manager
    global hrm_advertisement
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    adapter = find_adapter(bus)
    if not adapter:
        print('GattManager1 interface not found')
        return

    service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE)

    app = ble_hrm_app(bus)

    adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                   "org.freedesktop.DBus.Properties")
    print('Registering GATT application...')

    service_manager.RegisterApplication(app.get_path(), {},
                                    reply_handler=register_app_cb,
                                    error_handler=register_app_error_cb)
    
    #+++++++++++++++++++++++++++++++
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                LE_ADVERTISING_MANAGER_IFACE)

    hrm_advertisement = HRMAdvertisement(bus, 0)
    ad_manager.RegisterAdvertisement(hrm_advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)

def ble_hrm_stop():
    global ad_manager
    global hrm_advertisement
    ad_manager.UnregisterAdvertisement(hrm_advertisement)
    print('Advertisement unregistered')
    dbus.service.Object.remove_from_connection(hrm_advertisement)

mainloop = None
def main():
    global mainloop
    mainloop = GLib.MainLoop()

    ble_hrm_start()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    ble_hrm_stop()

if __name__ == '__main__':
    main()
