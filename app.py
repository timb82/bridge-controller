"""Raspberry Pi Pico W bridge controller
----------------------------------------
Start/Stop for power transfer with LED_MAIN_CONV indicator

Comm send with button and LED_COMM_TRANS indicator (when COMM button is pressed)
Comm receive with LED_COMM_RCVR indicator (when COMM button is not pressed)
"""
# TODO: Buttons require debouncing, no pullups

from micropython import const
from machine import Pin, PWM
from cpwm import CompPWM
from ios import Button, Comm, PowerTransfer

# PIN assignments
# LEDs
_LED_MAIN_CONV = const(2)
_LED_COMM_TRANS = const(3)
_LED_COMM_RCVR = const(4)
_SIG_TRANS = const(6)  # 31 kHz 50% PWM for 3 seconds on button pressed
# Gate drive signals
_G_Q1Q4 = const(8)  # Gate drive signal for Q2 and Q5
# G_Q2Q3 = 9  # Gate drive signal for Q3 and Q4, by default G_Q1Q4 +1
# Buttons
_START_BTN = const(22)  # Power transmission start button
_STOP_BTN = const(21)  # Power transmission stop button
_COMM_BTN = const(26)  # Comm send button
_COMM_READ = const(27)  # Input from comm receiver # FIXME requires voltage divider


# POWER TRANSFER CONTROLS
power = PowerTransfer(_G_Q1Q4, _LED_MAIN_CONV, freq=20_000, duty=0.5, dt_ns=500)
btn_start = Button(_START_BTN, callback=power.start_btn_callback)
btn_stop = Button(_STOP_BTN, callback=power.stop_btn_callback)

# COMMUNICATION CONTROLS
comm = Comm(_COMM_BTN, _LED_COMM_TRANS, _LED_COMM_RCVR, _SIG_TRANS, _COMM_READ)

while True:
    pass
