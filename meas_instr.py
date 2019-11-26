import time
import numpy as np
import serial
import usbtmc
from matplotlib import pyplot as plt
from myinstruments import GPD, BK8600, DM3058

power = GPD()
meter = DM3058()
load = BK8600()

power.set_volt(1,12)
power.set_curr(1,3.1)
power.set_output(1)

load.set_func('VOLT')
load.set_remsens('ON')
load.set_cv(13)
load.set_input('ON')
