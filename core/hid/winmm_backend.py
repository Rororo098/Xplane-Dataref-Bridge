"""
Windows Multimedia API backend for joystick input.
This solves the scrambling issue by using Windows drivers to decode raw HID data.
"""

import ctypes
from ctypes import wintypes

# Define the structures for Windows Joystick API
class JOYCAPS(ctypes.Structure):
    _fields_ = [
        ('wMid', wintypes.WORD),
        ('wPid', wintypes.WORD),
        ('szPname', ctypes.c_char * 32),
        ('wXmin', wintypes.UINT),
        ('wXmax', wintypes.UINT),
        ('wYmin', wintypes.UINT),
        ('wYmax', wintypes.UINT),
        ('wZmin', wintypes.UINT),
        ('wZmax', wintypes.UINT),
        ('wNumButtons', wintypes.UINT),
        ('wPeriodMin', wintypes.UINT),
        ('wPeriodMax', wintypes.UINT),
        ('wRmin', wintypes.UINT),
        ('wRmax', wintypes.UINT),
        ('wUmin', wintypes.UINT),
        ('wUmax', wintypes.UINT),
        ('wVmin', wintypes.UINT),
        ('wVmax', wintypes.UINT),
        ('wCaps', wintypes.UINT),
        ('wMaxAxes', wintypes.UINT),
        ('wNumAxes', wintypes.UINT),
        ('wMaxButtons', wintypes.UINT),
        ('szRegKey', ctypes.c_char * 32),
        ('szOEMVxD', ctypes.c_char * 260),
    ]

class JOYINFOEX(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('dwXpos', wintypes.DWORD),
        ('dwYpos', wintypes.DWORD),
        ('dwZpos', wintypes.DWORD),
        ('dwRpos', wintypes.DWORD),
        ('dwUpos', wintypes.DWORD),
        ('dwVpos', wintypes.DWORD),
        ('dwButtons', wintypes.DWORD),
        ('dwButtonNumber', wintypes.DWORD),
        ('dwPOV', wintypes.DWORD),
        ('dwReserved1', wintypes.DWORD),
        ('dwReserved2', wintypes.DWORD),
    ]

# Load winmm.dll
winmm = ctypes.windll.winmm

# Constants
JOY_RETURNALL = 0x000000FF
JOYERR_NOERROR = 0

def get_num_devices():
    """Get the number of joystick devices."""
    return winmm.joyGetNumDevs()

def get_device_caps(joy_id):
    """Get capabilities of a joystick device."""
    caps = JOYCAPS()
    res = winmm.joyGetDevCapsA(joy_id, ctypes.byref(caps), ctypes.sizeof(JOYCAPS))
    if res == JOYERR_NOERROR:
        return caps
    return None

def get_device_state(joy_id):
    """Get the current state of a joystick device."""
    info = JOYINFOEX()
    info.dwSize = ctypes.sizeof(JOYINFOEX)
    info.dwFlags = JOY_RETURNALL
    res = winmm.joyGetPosEx(joy_id, ctypes.byref(info))
    if res == JOYERR_NOERROR:
        return info
    return None