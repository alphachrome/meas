import time
import numpy as np
import serial
import usbtmc
from matplotlib import pyplot as plt
from myinstruments import GPD, BK8600, DM3058

# Measurement Configuration
VIN_0 = 4.5
VIN_N = 6
VIN_STEP = 0.02

FILE="CISIL-IV.csv"
# Start measurement...
# 
RANGE = np.linspace(VIN_0, VIN_N, num=(VIN_N-VIN_0+VIN_STEP)/VIN_STEP)
RANGE = [round(f,3) for f in RANGE]
#RANGE = np.array(range(VIN_0, VIN_N+VIN_STEP, VIN_STEP))
print RANGE

power = GPD()
meter = DM3058()

power.set_volt(1,VIN_0)
power.set_curr(1,1.1)
power.set_output(1)
time.sleep(1)

plt.axis([VIN_0, VIN_N, 0, 1])
plt.xlabel('VOLTAGE (V)')
plt.ylabel('CURRENT (A)')
plt.grid()
plt.ion()

vin_l=[]
pin_l=[]
pout_l=[]
eff_l=[]
loss_l=[]

with open(FILE, "w") as f:
    f.write("Vin_V,Iin_A\n")
    for vin in RANGE:

        power.set_volt(1,vin)

        time.sleep(1)
        
        iin_meas = float(power.get_curr(1))
        vin_meas = float(meter.get_volt())

        print "  --MEAS: Vin:{:.2f}V--Iin:{:.2f}A".format(vin_meas, iin_meas)
        
        plt.scatter(vin_meas, iin_meas, marker='s', alpha=0.5)
        plt.pause(0.05)

        f.write("{},{}\n".format(vin_meas,iin_meas))

        if iin_meas>1:
            RANGE = np.array(RANGE)
            RANGE = RANGE[RANGE <= vin]
            print "Input overcurrent!"
            break

power.set_volt(1,0)

print "Done!"
