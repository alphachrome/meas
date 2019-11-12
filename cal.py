import time
import numpy as np
import serial
import usbtmc
from matplotlib import pyplot as plt
from myinstruments import GPD, BK8600, DM3058

DUT="CISIL-LED"

VIN = 12

START=0.1
END=3.1
RANGE = np.linspace(START, END, num=16)
print RANGE

# Start measurement...
power = GPD()
meter = DM3058()
load = BK8600()

power.set_volt(1,VIN)
power.set_curr(1,3.1)
power.set_output(1)

load.set_cv(10)
load.set_func('CURR')
load.set_remsens('ON')
load.set_input('ON')

fig, ax = plt.subplots(2, figsize=(8,12))

ax[0].set_ylabel('V_ERR (V)', color='b')

ax[0].axis([START, END, -0.02, 0])

ax[1].set_xlabel('IOUT_SET (A)')
ax[1].set_ylabel('I_ERR (A)', color='r')

ax[1].axis([START, END, -0.005, 0])


while True:
    for x in RANGE:
        
        print "IOUT_SET: {:.2f}A-->".format(x)
        load.set_cc(x)
        time.sleep(2.5)
        
        vout_meas = float(load.get_volt())
        iout_meas = float(load.get_curr())
        
        vin_meas = float(meter.get_volt())
        iin_meas = float(power.get_curr(1))

        print "  --MEAS: Vin:{:.3f}V--Iin:{:.3f}A--Vout:{:.3f}V--Iout:{:.3f}".format(
            vin_meas, iin_meas, vout_meas, iout_meas)

        v_err = vin_meas - vout_meas
        i_err = iin_meas - iout_meas
        
        print "  --ERR: V_ERR={:.3f}V--I_ERR={:.3f}A".format(v_err, i_err)
   
        ax[0].scatter(x, v_err, marker='x', alpha=0.5)
        ax[1].scatter(x, i_err, marker='x', alpha=0.5)
        
        plt.pause(0.05)

        if x>=END or iin_meas>=3:
            print "Input overcurrent!"
            break


print "Done!"
load.set_cv(0)

plt.ioff()
plt.close()

## Plot and save figures
fig, ax = plt.subplots(2, figsize=(8,12))

ax[0].plot(RANGE, eff_l, 'b-x')    
#ax[0].set_xlabel('Iout (A)')
ax[0].set_ylabel('EFFICIENCY (%)', color='b')

ax[0].axis([START, END, 90, 110])

major_ticks = np.arange(80, 101, 5)
minor_ticks = np.arange(80, 101, 1)
#ax[0].set_yticks(major_ticks)
#ax[0].set_yticks(minor_ticks, minor=True)

ax[0].grid(which='minor', alpha=0.7)
ax[0].grid(which='major')

ax[1].plot(RANGE, loss_l, 'r:x')
ax[1].set_xlabel('IOUT (A)')
ax[1].set_ylabel('LOSS (W)', color='r')

ax[1].axis([START, END, 0, 5])

major_ticks = np.arange(0, 5.1, 0.5)
minor_ticks = np.arange(0, 5, 0.1)
ax[1].set_yticks(major_ticks)   
ax[1].set_yticks(minor_ticks, minor=True)


ax[1].grid(which='minor', alpha=0.7)
ax[1].grid(which='major')

#fig.tight_layout()
#plt.savefig("{}_Vin{}V_Vout{}V.png".format(DUT, VIN, VOUT))
plt.show()
