#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# System: macOS 12+
# Version: TeamViewer v15.x.x
# Python: 3.x.x
# Command: sudo python TeamViewer-15-id-changer.py
#

import os
import platform
import random
import re
import string
import sys

print(
    """
--------------------------------
TeamViewer 15 ID Changer for MAC OS
Version: 7 2022
--------------------------------
"""
)

if platform.system() != "Darwin":
    print("This script can be run only on MAC OS.")
    sys.exit()

if os.geteuid() != 0:
    print("This script must be run form root.")
    sys.exit()

if "SUDO_USER" in os.environ:
    USERNAME = os.environ["SUDO_USER"]
    if USERNAME == "root":
        print("Can not find user name. Run this script via sudo from regular user")
        sys.exit()
else:
    print("Can not find user name. Run this script via sudo from regular user")
    sys.exit()

HOMEDIRLIB = "/Users/" + USERNAME + "/library/preferences/"
GLOBALLIB = "/library/preferences/"

CONFIGS = []


# Find config files


def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]


for file in listdir_fullpath(HOMEDIRLIB):
    if "teamviewer" in file.lower():
        CONFIGS.append(file)

for file in listdir_fullpath(GLOBALLIB):
    if "teamviewer" in file.lower():
        CONFIGS.append(file)

if not CONFIGS:
    print(
        """
No TeamViewer configs found.
Maybe you have deleted it manually or never run TeamViewer after installation.
Nothing to delete.
"""
    )
else:
    # Delete config files
    print("Configs found:\n")
    for file in CONFIGS:
        print(file)
    print(
        """
These files will be DELETED permanently.
All TeamViewer settings will be lost
"""
    )
    input("Press Enter to continue or CTR+C to abort...")

    for file in CONFIGS:
        try:
            os.remove(file)
        except OSError:
            print("Cannot delete config files. Permission denied?")
            sys.exit()
    print("Done.")

# Find binaries

TMBINARIES = [
    "/Applications/TeamViewer.app/Contents/MacOS/TeamViewer",
    "/Applications/TeamViewer.app/Contents/MacOS/TeamViewer_Service",
    "/Applications/TeamViewer.app/Contents/MacOS/TeamViewer_Desktop_Proxy",
    "/Applications/TeamViewer.app/Contents/Helpers/TeamViewer_Assignment",
    "/Applications/TeamViewer.app/Contents/Helpers/Restarter",
]

for file in TMBINARIES:
    if os.path.exists(file):
        pass
    else:
        print("File not found: " + file)
        print("Install TeamViewer correctly")
        sys.exit()


# Patch files


def idpatch(fpath, platf, serial):
    file = open(fpath, "r+b")
    binary = file.read()
    PlatformPattern = "IOPlatformExpert.{6}"
    SerialPattern = "IOPlatformSerialNumber%s%s%s"

    binary = re.sub(str.encode(PlatformPattern), str.encode(platf), binary)
    binary = re.sub(
        str.encode(SerialPattern % (chr(0), "[0-9a-zA-Z]{8,8}", chr(0))),
        str.encode(SerialPattern % (chr(0), serial, chr(0))),
        binary,
    )

    file = open(fpath, "wb").write(binary)
    return True


def random_generator(
    size=8, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits
):
    return "".join(random.choice(chars) for _ in range(size))


RANDOMSERIAL = random_generator(8)
RANDOMPLATFORM = "IOPlatformExpert" + random_generator(6)

for file in TMBINARIES:
    try:
        idpatch(file, RANDOMPLATFORM, RANDOMSERIAL)
    except Exception as e:
        print("Error: can not patch file " + file)
        print(e)
        sys.exit()

print("PlatformDevice: " + RANDOMPLATFORM)
print("PlatformSerial: " + RANDOMSERIAL)

os.system("sudo codesign -f -s - /Applications/TeamViewer.app/")

print(
    """
ID changed sucessfully.
!!! Restart computer before using TeamViewer !!!!
"""
)