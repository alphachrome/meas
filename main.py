# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 12:47:11 2019

@author: roychan
"""
from datetime import datetime
from devices import *
import numpy as np


I2C_SER = 0xc
I2C_DES = 0x76 >> 1
I2C_LED = 0x5A >> 1
I2C_EEPROM1 = 0xA0 >> 1
I2C_EEPROM2 = 0xAA >> 1
I2C_TOUCH = 0x96 >> 1
I2C_TEMP = 0x98 >> 1

## EVM I2C address
#I2C_SER = 0x0C
#I2C_DES = 0x2C
#I2C_LED = 0x2D
#I2C_EEPROM1 = 0x50
#I2C_EEPROM2 = 0x50
#I2C_TOUCH = 0x4B
SER_PDB=1   #<<<<<<<<========1:ENABLE SERIALIZER============!!!!!

## Direct console commands
def cmd_com():
    while True:    
        cmd = raw_input('com> ')
        if cmd=='exit':
            break
        elif cmd=='r':
            print com.readline()          
        else:
            com.write(cmd+END)
            print com.readline()     
        
def set_gpio(dev, num, label, iodir, out=0):
    dev.gpio[num].setlabel(label)   
    dev.gpio[num].setdir(iodir)
    dev.gpio[num].setoutput(out)

def cmd_py():
    while True:
        inp = raw_input ("py> ")
        if inp=="exit":
            break
        else:
            try:
                if len(inp.split(" "))==1:
                    exec ("print "+inp)
                else:
                    exec(inp)
            except Exception as e:
                print " **{}".format(e)

class Cmd:
    def __init__(self, cmd_list, prefix="RC"):
        self.cmds=cmd_list
        self.prefix=prefix
        
    def shell(self):
        while True:
            try:
                inp = raw_input(self.prefix+"> ").split(" ")
                
                if inp[0] in ['q', 'exit', 'quit']:
                    break
                
                elif inp[0]=="py":
                    if len(inp)>1:
                        exec("print "+" ".join(inp[1:]))
                    else:
                        cmd_py()
                
                elif inp[0] in self.cmds.keys():
                    cmd = self.cmds[inp[0]]
    
                    if isinstance(cmd, tuple):
                        cmd[0](*cmd[1])
                    else:
                        if len(inp)==1:
                            cmd()
                        else:
                            cmd(*inp[1:])
                
                else:
                    print ", ".join(sorted(self.cmds.keys()))
                    
            except Exception as e:
                print " **{}".format(e)
    
def cmd_info():
    for k,dev in dev_list.items():
        print "{} (0x{})".format(k, dev.addr)
        

def cmd_scan():
    print "Scanning..."
    for i in range(128):
        cmd = "r{}0001\r".format(tohex(i))
        com.write(cmd+"\r")
        ret = com.readline()
        if ret[0]!='-':
            print " Found device at {}({}), Return: 0x{}".format(hex(i), hex(i<<1), ret.rstrip())
    print " done"

do_log = False
fd = open("cmd.log", "w")
def log(func):
    def wrapper(*args):
        if do_log:
            fd.write("{} - {}".format(datetime.now(), args[0]))
            fd.flush()
        return func(*args)
    return wrapper

def cmd_log(doit=do_log):
    global do_log
    if doit in ['True', 'yes', '1']:
        do_log=True
    elif doit in ['False', 'no', '0']:
        do_log=False
    print "log =" ,do_log


def cmd_mcu_gpo(pin, output):
    pin = int(pin)
    output = int(output)
    cmd = "O{}{}\r".format(tohex(pin), tohex(output))
    com.write(cmd)
    
def mcu_gpi(pin):
    cmd = "I{}\r".format(tohex( pin ))
    com.write(cmd)
    ret = com.readline().rstrip().split(':')
    iodir = 'IN' if ret[0]=='0' else 'OUT'
    return "{:>3}:{}".format(iodir, ret[1])     


# [0] D2: DES_GPIO0, CHG, interrupt (input)
# [1] D3: DES_GPIO1, LED Driver fault (input)
# [2] D4: DES_GPIO2, LED Driver PWM (output)
# [3] D5: DES_GPIO3, Touch IC Reset (output)
# [4] D6: SER_GPIO5_REG (input)
# [5] D7: SER_GPIO6_REG (input)
# [6] D8: SER_GPIO7_REG (input)
# [7] D9: SER_GPIO8_REG (input)
# [8] D10: SER_INTB (input)
# [9] A0: SER_PDB, high: power up, low: power down (ouput)
# [10] A3: Local load switch, 12V_Display Enable (output)
# [11] A6: Local load switch, 12V_Display Flag (input)
# [12] A7: HPD (output)        
Pin = ['CHG', 'LED_FAULT', 
       'LED_PWM', 'TOUCH_RESET',
       'SER_GPIO5_REG', 'SER_GPIO6_REG',
       'SER_GPIO7_REG', 'SER_GPIO8_REG',
       'DES_INTB', 'DES_PDB', 
       'DISP_PWR_EN', 'DISP_PWR_ALRT',
       'HPD']

def mcu_gpio_print():
    for i in range(13):
        print "{:>2}: {:<15}{}".format(i, Pin[i], mcu_gpi(i))

def program_edid(dev):
    edid = "00 FF FF FF FF FF FF 00 04 AF 00 00 01 01 01 01 22 10 01 03 81 00 00 FF 0A 01 01 01 01 01 01 01 01 01 01 00 00 00 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 F4 1A 00 C8 50 D0 35 20 02 01 01 00 B1 63 00 00 00 18 00 00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 CA"
    edid = edid.split(' ')
    for addr, data in enumerate(edid):
        dev.write(int(addr), int(data,16))

def cmd_gpio(num=None, val=None):
    if num==None:
        for num, g in enumerate(Gpio):
            iodir = g.getdir()
            if iodir=="IN":
                val = g.getinput()
            elif iodir=="OUT":
                val = g.getoutput()
            else:
                val = "??"

            print "{:>2}: {:<15} {:>3}:{}".format(num, g.label, iodir, val)
            
    elif val in ['0', '1']:
        num=int(num)
        val=int(val)
        print num,val
        if Gpio[num]!=None:
            Gpio[num].setoutput(val)

def cmd_power(cmd):
    if cmd in ['on', '1']:
        Mcu_Gpio(com, 10, out=0)
    elif cmd in ['off', '0']:
        Mcu_Gpio(com, 10, out=1)

def cmd_led_en(val=1):
    #print val
    Gpio[5].setoutput(val) 

def test_Led(num=1):
    for _ in range(int(num)):
        y=0
        n=2
        while y<0x1fff:
            if y>=0xF00:
                y=y+n*64
            elif y>=0x800:
                y=y+n*16
            elif y>=0x400:
                y=y+n*8
            elif y>=0x200:
                y=y+n*4
            elif y>=100:
                y=y+n*2
            else:
                y=y+n
                
            if y>0x1fff:
                y=0x1fff
            
            Led.write(0xA, (y>>8)&0xFF)      
            Led.write(0xB, y&0xFF)

            print "{} {:.2f}".format(hex(y), 100.0*y/0x1fff)

        Led.set_logo(0)
        sleep(1)
        
if __name__=="__main__":
    print "Start.."
    #with serial.Serial(COM_PORT, baudrate=BAUDRATE, timeout=2) as com:
    
    if True:
        try:
            print "[Serial Port]"
            com = find_com()
            
        except Exception as e:
            print e
        com.readline()   
#        while True:
#            try:
#                ret = com.readline()
#                break
#            except Exception as e:
#                print " [{}]".format(e)
#                sleep(0.5)
#                
        com.write = log(com.write)
            
        root_cmd = dict()
        dev_list = dict()

        #cmd_mcu_gpo('3', '0')
    
        Mcu_Gpio(com, 10, out=0, label="DISP_PWR_EN_L") 
        Mcu_Gpio(com, 9, out=SER_PDB, label="SER_PDB_L") # Enable Serializer
        if SER_PDB==0:
            print "  Serializer Power Down!"
    
        try:
        #if True:
            print "[Serializer]"
            Ser = Fpdl_Ser(com, I2C_SER)

            root_cmd['ser'] = Cmd({
                "info": Ser.print_info,
                "status": Ser.print_status,
                "regs": (Ser.print_regs, (16,)),
                "pg": Ser.cmd_pg,
                "clear": Ser.clear,
                "init": Ser.init,
                "reset": Ser.reset,
                "gpio": Ser.cmd_gpio,
                "read": Ser.cmd_read,
                "write": Ser.cmd_write,
                "edid": Ser.print_edid,
                "py": cmd_py
                }, prefix="SER").shell
    
            set_gpio(Ser, 0, "Touch CHG", "OUT")   
            set_gpio(Ser, 1, "LED Fault", "OUT")   
            set_gpio(Ser, 2, "LED PWM",   "IN")   
            set_gpio(Ser, 3, "Touch Reset", "IN")
            dev_list["Serializer"]=Ser

            print " Detecting Deserializer..."
            for i in range(2):
                des_addr = Ser.read(6)>>1
                if des_addr > 0:
                    I2C_DES = des_addr
                    break
                else:
                    sleep(0.4)
            if des_addr > 0:
                print "  Found Deserializer at", hex(des_addr)
            else:
                print "  Not found!"

        except Exception as e:
            print " **{}".format(e)

    if True:
        try: 
            print "[Deserializer]"
            Des = Fpdl_Des(com, I2C_DES)
            #Des.write(0x02, 0xf0)

            root_cmd['des'] = Cmd({
                "info": Des.print_info,
                "status": Des.print_status,
                "regs": (Des.print_regs, (16,)),
                "pg": Des.cmd_pg,
                "reset": Des.reset,
                "init": Des.init,
                "init": Des.init,
                "gpio": Des.cmd_gpio,
                "read": Des.cmd_read,
                "write": Des.cmd_write
                }, prefix="DES").shell
                   
            set_gpio(Des, 0, "Touch CHG", "IN")   
            set_gpio(Des, 1, "LED_FAULT", "IN")   
            set_gpio(Des, 2, "LED_PWM",   "OUT")   
            set_gpio(Des, 3, "TOUCH_RESET_L", "OUT")   
            set_gpio(Des, 5, "TEMP_ALERT", "IN")
            set_gpio(Des, 6, "LED_RESET_H",  "OUT", 0)   
            set_gpio(Des, 7, "LED_EN_H", "OUT", 1)   
            set_gpio(Des, 8, "EEPROM_WP_L",  "OUT", 1)
            
            for _,g in Des.gpio.items():
                g.enable()
                
            dev_list["Deserializer"]=Des 

        except Exception as e:
            print " **{}".format(e)

        try:
            Gpio = [ Mcu_Gpio(com, 0, label="CHG_L"),
                     Mcu_Gpio(com, 1, label="LED_FAULT"),   
                     Des.gpio[5],
                     #Mcu_Gpio(com, 2, out=0, label="LED_PWM"),
                     Mcu_Gpio(com, 3, out=1, label="TOUCH_RESET_L"),
    
                     Des.gpio[6],
                     Des.gpio[7],
                     Des.gpio[8],
                     Mcu_Gpio(com, 10, out=0, label="DISP_PWR_EN_L"),
    
                     Mcu_Gpio(com, 9, out=SER_PDB, label="SER_PDB_L"),
    #                 Mcu_Gpio(com, 8, label="SER_INTB"),
    #                 Mcu_Gpio(com, 4, label="SER_GPIO5_REG"),
    #                 Mcu_Gpio(com, 5, label="SER_GPIO6_REG"),
    #                 Mcu_Gpio(com, 6, label="SER_GPIO7_REG"),
    #                 Mcu_Gpio(com, 7, label="SER_GPIO8_REG"),
                     ]
        except Exception as e:
            print " **{}".format(e)            
#        
        sleep(0.5)
        
       #Setting Deserializer register: 0x1D=0x23, 0x1E=0x93, 0x1F=0x09, 0x20=0x93, 0x21=0x99;
        
        try:
            print "[LED Driver]"
            Led = Led_Driver(com, I2C_LED)

            root_cmd['led']= Cmd({
                "info": Led.print_info,
                #"ee": Led.print_eeprom,
                "status": Led.print_status,
                "blu": Led.set_blu,
                "logo": Led.set_logo,
                "lock": Led.lock,
                "unlock": Led.unlock,
                "clear": Led.clear,
                "load": Led.load,
                "init": Led.init,
                "prog": Led.program,
                "reset": Led.reset,
                "regs": (Led.print_regs, (8,)),
                "read": Led.cmd_read,
                "write": Led.cmd_write,
                "en": cmd_led_en,
                "test": test_Led
                }, prefix="LED").shell
            dev_list["LED Driver"]=Led   
        except Exception as e:
            print " **{}".format(e)

        try:
            print "[Touch Controller]"
            for _ in range(2):
                try:
                    Tch = Touch(com, I2C_TOUCH)
                    break
                except Exception as e:
                    print " ", e
                    print " retry.."
                    sleep(0.5)

            root_cmd['touch'] =  Cmd({
                "info": Tch.print_info,
                "table": Tch.print_table,
                "dmsg": Tch.print_dmsg,
                "init": Tch.init,
                "listen": Tch.listen,
                "listen2": Tch.listen2,
                "msg": Tch.get_msg,
                "read": Tch.cmd_read,
                "write": Tch.cmd_write
                }, prefix="TCH").shell
            dev_list["Touch"]=Tch     
        except Exception as e:
            print " **{}".format(e)
        
        try:
            print "[EEPROM 1]"
            Eeprom1 = Eeprom(com, I2C_EEPROM1)
            print " ok"
            root_cmd['ee1'] =  Cmd({
                "regs": (Eeprom1.print_regs, (16,)),
                "progedid": (program_edid, (Eeprom1,)),
                "read": Eeprom1.cmd_read,
                "write": Eeprom1.cmd_write},
                prefix="EE1").shell
            dev_list["EEPROM1"]=Eeprom1  
        except Exception as e:
            print " **{}".format(e)

        try:
            print "[EEPROM 2]"
            Eeprom2 = Eeprom(com, I2C_EEPROM2)
            print " ok"
            root_cmd['ee2'] =  Cmd({
                "regs": (Eeprom2.print_regs, (16,)),
                "read": Eeprom2.cmd_read,
                "write": Eeprom2.cmd_write},
                prefix="EE2").shell
            dev_list["EEPROM2"]=Eeprom2
        except Exception as e:
            print " **{}".format(e)            

    root_cmd['power'] = cmd_power
    root_cmd['com'] = cmd_com
    root_cmd['info'] = cmd_info
    root_cmd['log'] = cmd_log
    root_cmd['scan'] = cmd_scan
    root_cmd['mcu'] = Cmd({
            "gpi": mcu_gpio_print,
            "gpo": cmd_mcu_gpo},
                prefix="MCU").shell
            
    root_cmd['gpio'] = cmd_gpio
    
    Cmd(root_cmd, "RC").shell()
        

#com.close()