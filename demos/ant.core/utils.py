import os
import time
from subprocess import Popen, PIPE
import fcntl
import hashlib

USBDEVFS_RESET= 21780

def prepare_usb(driver):
    try:
        lsusb_out = Popen("lsusb | grep -i %s"%driver, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip().split()
        bus = lsusb_out[1]
        device = lsusb_out[3][:-1]
        print("use %s"%driver)
        print("reset /dev/bus/usb/%s/%s"%(bus.decode(), device.decode()))
        f = open("/dev/bus/usb/%s/%s"%(bus.decode(), device.decode()), 'w', os.O_WRONLY)
        fcntl.ioctl(f, USBDEVFS_RESET, 0)
        time.sleep(1)
    except Exception:
        print ("failed to reset device")

    return 0x1008

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

def id_from_serial(offset = 0):
    return int(int(hashlib.md5(getserial().encode()).hexdigest(), 16) & 0xfffe) + offset