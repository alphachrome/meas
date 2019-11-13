import time
import numpy as np
import serial
import usbtmc
from matplotlib import pyplot as plt
from myinstruments import GPD, BK8600, DM3058

# Measurement Configuration
DUT="CISIL-LED"

VIN=12
VOUT=14

FILE="CISIL-DRV-EVT1d5_IOUT-vs-V_IADJ_VOUT{}V.csv".format(VOUT)

# Start measurement...
# 
RANGE = np.linspace(0, 5, num=51)
print RANGE

power = GPD()
meter = DM3058()
load = BK8600()

power.set_volt(1,VIN)
power.set_curr(1,3.1)

load.set_func('VOLT')
load.set_remsens('ON')
load.set_cv(VOUT)
load.set_input('ON')

plt.xlabel('V_IADJ (V)')
plt.ylabel('I_OUT (A)')
plt.grid()
plt.ion()

with open(FILE, "w") as f:
    f.write("Viadj_V, Vin_V,Vout_V,Iin_A,Iout_A,Pin_W,Pout_W,Eff_%,Loss_W\n")
    for v_iadj in RANGE:

        power.set_volt(4,v_iadj)
        time.sleep(2)
        
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
        
        print "      --Pin:{:.3f}W--Pout:{:.3f}--Loss:{:.2f}--Eff:{:.2f}%".format(
            pin, pout, loss, eff)
        
        plt.scatter(v_iadj, iout_meas, marker='s', alpha=0.5)
        plt.pause(0.05)

        f.write("{},{},{},{},{},{},{},{},{}\n".format(v_iadj, vin_meas,vout_meas,iin_meas,iout_meas,pin,pout,eff,loss))

        if iin_meas>=3:
            RANGE = np.array(RANGE)
            RANGE = RANGE[RANGE <= vin]
            print "Input overcurrent!"
            break

print "Done!"
load.set_input(0)
