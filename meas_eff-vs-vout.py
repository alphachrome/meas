import time
import numpy as np
import serial
import usbtmc
from matplotlib import pyplot as plt
from myinstruments import GPD, BK8600, DM3058

# Measurement Configuration
DUT="CISIL-LED"

VOUT_0 = 10
VOUT_N = 16
VOUT_STEP = 0.25
VIN = 17
IIN = 3.2

FILE="CISIL-DRV-NEW_EFF-vs-VOUT_VIN{}V_IOUT1A.csv".format(VIN)
# Start measurement...
# 
RANGE = np.linspace(VOUT_0, VOUT_N, num=(VOUT_N-VOUT_0+VOUT_STEP)/VOUT_STEP)
RANGE = [round(f,3) for f in RANGE]

print RANGE

power = GPD()
meter = DM3058()
load = BK8600()

power.set_volt(1,VIN)
power.set_curr(1,IIN)
power.set_output(1)

time.sleep(1)
load.set_func('VOLT')
load.set_remsens('ON')
load.set_cv(VOUT_0)
load.set_input('ON')

plt.axis([VOUT_0, VOUT_N, 70, 90])
plt.xlabel('VOUT (V)')
plt.ylabel('EFFICIENCY (%)')
plt.grid()
plt.ion()

vin_l=[]
pin_l=[]
pout_l=[]
eff_l=[]
loss_l=[]

with open(FILE, "w") as f:
    f.write("Vin_V,Vout_V,Iin_A,Iout_A,Pin_W,Pout_W,Eff_%,Loss_W\n")
    for vout in RANGE:

        #load.set_input(0)
        load.set_cv(vout)
        #time.sleep(1)
        #load.set_input(1)
        time.sleep(5)
        
        vout_meas = float(load.get_volt())
        iout_meas = float(load.get_curr())
        
        vin_meas = float(meter.get_volt())
        iin_meas = float(power.get_curr(1))

        print "  --MEAS: Vin:{:.2f}V--Iin:{:.2f}A--Vout:{:.2f}V--Iout:{:.3f}".format(
            vin_meas, iin_meas, vout_meas, iout_meas)

        pin = vin_meas*iin_meas
        pout = vout_meas * iout_meas

        try:
            eff = pout/pin*100
        except Exception as e:
            print e
            eff = -1

        loss = (100-eff)/100*pin

        vin_l.append(vin_meas)
        pin_l.append(pin)
        pout_l.append(pout)
        eff_l.append(eff)
        loss_l.append(loss)
        
        print "      --Pin:{:.3f}W--Pout:{:.3f}--Loss:{:.2f}--Eff:{:.2f}%".format(
            pin, pout, loss, eff)
        
        plt.scatter(vout, eff, marker='s', alpha=0.5)
        plt.pause(0.05)

        f.write("{},{},{},{},{},{},{},{}\n".format(vin_meas,vout_meas,iin_meas,iout_meas,pin,pout,eff,loss))

        if iin_meas>=3.1:
            RANGE = np.array(RANGE)
            RANGE = RANGE[RANGE <= vout]
            print "Input overcurrent!"
            break



print "Done!"
#load.set_input(0)

plt.ioff()
plt.close()

## Plot and save figures
fig, ax = plt.subplots(2, figsize=(8,12))

ax[0].plot(RANGE, eff_l, 'b-x')    
#ax[0].set_xlabel('Iout (A)')
ax[0].set_ylabel('EFFICIENCY (%)', color='b')

ax[0].axis([VOUT_0, VOUT_N, 70, 90])

major_ticks = np.arange(70, 91, 5)
minor_ticks = np.arange(70, 91, 1)
ax[0].set_yticks(major_ticks)
ax[0].set_yticks(minor_ticks, minor=True)

ax[0].grid(which='minor', alpha=0.7)
ax[0].grid(which='major')

ax[1].plot(RANGE, loss_l, 'r:x')
ax[1].set_xlabel('VOUT (V)')
ax[1].set_ylabel('LOSS (W)', color='r')

ax[1].axis([VOUT_0, VOUT_N, 0, 5])

major_ticks = np.arange(0, 5.1, 0.5)
minor_ticks = np.arange(0, 5, 0.1)
ax[1].set_yticks(major_ticks)   
ax[1].set_yticks(minor_ticks, minor=True)


ax[1].grid(which='minor', alpha=0.7)
ax[1].grid(which='major')

#fig.tight_layout()
#plt.savefig("{}_Vin{}V_Vout{}V.png".format(DUT, VIN, VOUT))
plt.show()
