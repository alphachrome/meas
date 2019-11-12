#!/usr/local/conda2/bin/python
# author: roychan@
# date: 5/2019
#
from time import sleep, time
import serial
import matplotlib.pyplot as plt

#COM_PORT = "COM7"
#COM_PORT = "COM14"
BAUDRATE = 115200

tohex = lambda v: ('00'+hex(v).split('x')[1])[-2:]
toasc = lambda v: '.' if v<32 else chr(v)

setBitHi = lambda val, bit: val | (1<<bit)
setBitLo = lambda val, bit: val & ~(1<<bit)

verbose=False

END='\r' # Endline character

class I2cdev():
    def __init__(self, com, address=0):
        self.com = com
        self.addr = tohex(address)
        self.verbose = False
        
    def read(self, reg, num=1):
        # Format: rDDRRNN\n
        #   DD: Device number in HEX (00~FF)
        #   RR: Register number in HEX (00~FF)
        #   NN: Number to read in HEX (00~FF)
        #   \n: Newline (0xA)

        cmd = "r{}{}{}".format(self.addr, tohex(reg), tohex(num))

        if verbose:
            print cmd

        self.com.write (cmd+END)
        ret = self.com.readline().rstrip()

        if ret[0]=='-':
            raise Exception('I2C Read Error = {}'.format(ret))
        elif num>1:
            ret = ret.split(' ')
            ret = [ int(r,16) for r in ret ]
            return ret        
        else:
            return int(ret,16)

    def write(self, reg, val):
        # Format: wDDRRVV\n
        #   DD: Device number in HEX (00~FF)
        #   RR: Register number in HEX (00~FF)
        #   VV: value to write in HEX (00~FF)
        #   \n: Newline (0xA)
        cmd = "w{}{}{}".format(self.addr, tohex(reg), tohex(val))
        
        #if self.verbose:
        #raw_input(cmd)
        #print cmd

        self.com.write(cmd+END)
        val = self.com.readline()
        if val[0]=='-':
            raise Exception('I2C write Error = {}'.format(val))
        
        if verbose:
            print(cmd)
            print val
            
        return

    def write_many(self, val_list):
        # To MCU: 
        #   W<DEV><REG><Num><VALUE>...<VALUE>
        reg = val_list[0]
        cnt = len(val_list[1:])
        buf = "".join([ tohex(v) for v in val_list[1:] ])
        
        cmd = "W{}{}{}{}".format(self.addr, tohex(reg), tohex(cnt), buf)
        #print cmd
        
        self.com.write(cmd+END)
        val = self.com.readline()
        if val[0]=='-':
            raise Exception('I2C write Error = {}'.format(val))
            
        #verbose=True
        if verbose:
            print(cmd)
            print val
            
        return

    def read_many(self, num=1):
        # To MCU: 
        #   R<DEV><Num>

        cmd = "R{}{}".format(self.addr, tohex(num))

        if verbose:
            print cmd

        self.com.write (cmd+END)
        ret = self.com.readline().rstrip()

        if ret[0]=='-':
            raise Exception('I2C Read Error = {}'.format(ret))
        elif num>1:
            ret = ret.split(' ')
            try:
                ret = [ int(r,16) for r in ret ]
            except:
                pass
            return ret        
        else:
            return int(ret,16)    

    def setRegBitHi (self, reg, pos):
        return self.write(reg, setBitHi(self.read(reg), pos) )

    def setRegBitLo (self, reg, pos):
        return self.write(reg, setBitLo(self.read(reg), pos) )

    def setRegBit(self, reg, pos, val):
        if val==1:
            self.setRegBitHi(reg, pos)
        elif val==0:
            self.setRegBitLo(reg, pos)

    def print_regs(self, n_row):
        #print "     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f"
        for i in range(n_row):
            val = self.read(i*16,4) + self.read(i*16+4, 4) + self.read(i*16+8, 4)  + self.read(i*16+12, 4)         
            hex_str = " ".join( [ tohex(v) for v in val ] )
            asc_str = "".join( [ toasc(v) for v in val ] )        
            print "{}: {}  {}".format(tohex(i*16), hex_str, asc_str )
            sleep(0.1)

    def dump(self, filename, start, end):
        with open(filename,'w') as fd:    
            for reg in range(start, end+1):
                fd.write("{} {}\n".format(hex(reg), hex(self.read(reg)) ))

    def print_regval(self, regspec):
            val = self.read(regspec.reg)
            print "{} ({}): {}".format(regspec.name, hex(regspec.reg), bin(val))
            for n,s in enumerate(regspec.desc[-1::-1]):
                if s!="RES":
                    print("  b{}:{:<15} = {}".format(n, s, (val>>n)&1))
                
    def cmd_read(self, reg='', num='1'):
        # Arguments: reg, num in string format

        if reg=='':
            print " read <reg in hex> <num in dec>"
        else:
            reg = int(reg, 16)
            cnt = int(num)
            cnt = 32 if cnt>32 else cnt
            
            if cnt==1:
                print hex( self.read(reg) )
            else:
                print " ".join( [tohex(v) for v in self.read(reg, cnt)] )
                    
    def cmd_write(self, reg=None , val=None):
        if reg==None:
            print " write <reg in hex> <val in hex>"
        else:
            if val!=None:
                reg = int(reg, 16)
                val = int(val, 16)
                self.write(reg, val)
                
PG_CTRL = (  # (bit_name, reg_num, bit_pos)
  ('vcom',   0x64, 1),
  ('color',  0x64, 2),
  ('scroll', 0x65, 0),
  ('invert', 0x65, 1),
  ('scale',  0x65, 6) )

class Fpdl_Patgen(I2cdev):
## Device Initialization
#    def __init__(self, dev):
#        self.dev = dev

    def write_pg(self, addr, val):
        self.write(0x66, addr)
        self.write(0x67, val)
        
    def init_pg_720p(self):
        # Configure 720p Test Pattern
        self.write_pg(0x03, 0x03)    #PGCDC1
        self.write_pg(0x04, 0x70)    #PGTFS1
        self.write_pg(0x05, 0xE6)    #PGTFS2
        self.write_pg(0x06, 0x2E)    #PGTFS3
        self.write_pg(0x07, 0x00)    #PGAFS1
        self.write_pg(0x08, 0x05)    #PGAFS2
        self.write_pg(0x09, 0x2D)    #PGAFS3
        self.write_pg(0x0A, 0x50)    #PGHSW
        self.write_pg(0x0B, 0x05)    #PGVSW
        self.write_pg(0x0C, 0xD8)    #PGHBP
        self.write_pg(0x0D, 0x16)    #PGVBP
    
    def cmd_pg(self, cmd='', option=None):
        if cmd=='on':
            self.setRegBitHi(0x64, 0)
            
        elif cmd=='off':
            self.setRegBitLo(0x64, 0)
    
        elif cmd in ["pattern", 'p']:
            v = self.read(0x64)
            n = int(option)
            if n >=0 and n <=15:
                v = (v&0xF) | (n<<4)
                self.write(0x64, (v&0xF) | (n<<4))
                
        elif cmd in ['help', '']:
            print "pg"
            print "   [on|off]"
            print "   pattern <0-15>"
            print "   [color|scroll|vcom|invert|scale] [on|off]"
            
        else:
            for name, reg, pos in PG_CTRL:
                if cmd==name:
                    if option in ['on', '1', ' ']:
                        self.setRegBitHi(reg, pos)
                        break
                    elif option in ['off', '0']:
                        self.setRegBitLo(reg, pos)
                        break  
# [pin] description:
#
# [0] D2: DES_GPIO0, CHG, interrupt (input)
# [1] D3: DES_GPIO1, LED Driver fault (input)
# [2] D4: DES_GPIO2, LED Driver PWM (output)
# [3] D5: DES_GPIO3, Touch IC Reset (output)
# [4] D6: SER_GPIO5_REG (input)
# [5] D7: SER_GPIO6_REG (input)
# [6] D8: SER_GPIO7_REG (input)
# [7] D9: SER_GPIO8_REG (input)
# [8] D10: DES_INTB (input)
# [9] A0: DES_PDB, high: power up, low: power down (ouput)
# [10] A3: Local load switch, 12V_Display Enable (output)
# [11] A6: Local load switch, 12V_Display Flag (input)
# [12] A7: HPD (output)     
class Mcu_Gpio:
    def __init__(self, com, pin, out=None, label=""):
        self.com = com
        self.pin = pin
        self.label = label
        if out!=None:
            self.setoutput(out)
    
    def setoutput(self, val):
        cmd = "O{}{}".format(tohex(self.pin), tohex(val))
        #print cmd
        self.com.write(cmd+END)
        
    def getdir(self):
        cmd = "I{}".format(tohex(self.pin))
        self.com.write(cmd+END)
        ret = self.com.readline().rstrip().split(':')
        return 'IN' if ret[0]=='0' else 'OUT'
    
    def getinput(self):
        cmd = "I{}".format(tohex(self.pin))
        #print cmd
        self.com.write(cmd+END)
        ret = self.com.readline().rstrip().split(':')
        return int(ret[1])     

    def getoutput(self):
        return self.getinput() 

class Fpdl_Gpio(I2cdev):
    def __init__(self, dev, reg, pos, mode=None, out=0, label=""):
        self.dev = dev
        self.reg = reg
        self.pos = pos
                
        self.setlabel(label)
        
        if mode!=None:
            self.setmode(mode)
            if (mode>>1)&1:
                self.setdir("IN")
            else:
                self.setdir("OUT")
                
        self.setoutput(out)

    def enable(self):
        self.dev.setRegBitHi(self.reg, self.pos)

    def disable(self):
        self.dev.setRegBitLo(self.reg, self.pos)
    
    def setlabel(self, label):
        self.label = label

    def setmode(self, mode):
        val = self.dev.read(self.reg) & (0xF0 if self.pos==0 else 0x0F)
        
        val = val | (mode << self.pos)
        self.dev.write(self.reg, val)

    def getmode(self):
        return self.dev.read(self.reg) >> (self.pos+2)

    def getdir(self):
        mode = self.dev.read(self.reg) >> self.pos
        iodir = (mode >> 1)&1
        return "IN" if iodir==1 else "OUT"

    def setdir(self, iodir):
        #  SER(0x3) input  -> DES(0x5) output
        #  SER(0x5) output <- DES(0x3) input
        if iodir=="OUT":
            self.iodir="OUT"
            mode = 5
        elif iodir=="IN":
            self.iodir="IN"
            mode = 3
        else:
            return
                  
        self.setmode(mode)
        
    def setoutput(self, val):
        if val==1:
            self.dev.setRegBitHi(self.reg, self.pos+3)               
        elif val==0:
            self.dev.setRegBitLo(self.reg, self.pos+3)    
    
    def getoutput(self):
        return (self.dev.read(self.reg)>>(self.pos+3)) & 1
               
    def getinput(self):
        return (self.dev.read(self.gpi_reg)>>(self.gpi_pos)) & 1

class Fpdl_Gpio_Reg:
    # Initialize DES for GPIO_REG[5-8]

    def __init__(self, dev, reg, pos, iodir=None, label="", out=None, en=False, gpi_reg=None, gpi_pos=None):    
        self.dev = dev
        self.reg = reg
        self.pos = pos
        self.gpi_reg = gpi_reg
        self.gpi_pos = gpi_pos
        self.iodir = self.getdir()
        
        self.setlabel(label)
        # Setting:
        #    Nibble:   Bit-3       Bit-2      Bit-1    Bit-0
        #   Funtion:   OUTPUT_VAL  RESERVED   DIR      ENABLE
        #                                     DIR=0: output
        #                                     DIR=1: input
        if iodir!=None:
            self.setdir(iodir)
        
            if iodir=="OUT" and out!=None:
                self.setoutput(out)
        
        if en:
            self.enable()

    def enable(self):
        self.dev.setRegBitHi(self.reg, self.pos)

    def disable(self):
        self.dev.setRegBitLo(self.reg, self.pos)
    
    def setlabel(self, label):
        self.label = label

    def setoutput(self, val):
        #print "gpio_reg setoutput"
        if val in [1, '1']:
            self.dev.setRegBitHi(self.reg, self.pos+3)               
        elif val in [0, '0']:
            self.dev.setRegBitLo(self.reg, self.pos+3)   

        if self.iodir=="IN":
            print " *Warning: GPIO is a input pin"
            
    def getoutput(self):
        return (self.dev.read(self.reg)>>(self.pos+3)) & 1

    def getinput(self):
        return (self.dev.read(self.gpi_reg)>>(self.gpi_pos)) & 1
    
    def setdir(self, iodir):
        self.iodir = iodir.upper()
        
        if iodir=="IN":
            iodir=1
        elif iodir=="OUT":
            iodir=0
        else:
            return
       
        self.dev.setRegBit(self.reg, self.pos+1, iodir)
    
    def getdir(self):
        mode = self.dev.read(self.reg) >> self.pos
        iodir = (mode >> 1)&1
        return "IN" if iodir==1 else "OUT"        

class Regspec:
    def __init__(self, reg, name, desc):
        self.reg = reg
        self.name = name
        self.desc = desc
        
SER_G_STATUS = Regspec(reg=0x0C,
                       name="General Status",
                       desc=("RES", "RES", "RES", "LINK_LOSS_P0/1", 
                             "BIST_ERR_P0/1", "TDMS_CLK_DETECT", "DES_ERROR_P0/1", "LINK_DET_P0/1"))
SER_B_STATUS = Regspec(reg=0x50,
                       name="Bridge Status",
                       desc=("RX5V_DET", "HDMI_INT", "RES", "INIT_DONE", "REM_EDID_LOAD", 
                             "CFG_DONE", "CFG_CHKSUM_OK", "EDID_CHKSUM_OK"))
SER_MODESEL = Regspec(reg=0x13,
                       name="Model Select",
                       desc=("SEL1 DONE", "SEL1_B2", "SEL1_B1", "SEL1_B0", 
                             "SEL0 DONE", "SEL0_B2", "SEL0_B1", "SEL0_B0"))
SER_DUAL_STS = Regspec(reg=0x5a,
                       name="Dual Status",
                       desc=("FPDL3_RDY", "TX STS", "PORT1_STS", "PORT0_STS",
                             "TMDS_VALID", "HDMI_PLL_LCK", "NO_HDMI_CLK", "FREQ_STB"))

MCU_GPIO=[]

SER_GPIO={ 0:(0x0D, 0),
           1:(0x0E, 0),
           2:(0x0E, 4),
           3:(0x0F, 0) }

SER_GPIO_REG = { 5:(0x10,0), 
                 6:(0x10,4), 
                 7:(0x11,0), 
                 8:(0x11, 4) }  # GPIO_REG[5-8]

SER_GPI_REG = { 0: (0x1c, 0), 
                1: (0x1c, 1),
                2: (0x1c, 2),
                3: (0x1c, 3),
                5: (0x1c, 5),
                6: (0x1c, 6),
                7: (0x1c, 7),
                8: (0x1d, 0) }

SER_GPIO_MODE = {
    "FUNCTIONAL": 0b000,
    "TRISTATE": 0b010,
    "GPIO_OUTPUT": 0b001,
    "GPIO_INPUT": 0b011,
    "REMOTE_HOLD": 0b101,
    "REMOTE": 0b111}

class Fpdl_Ser(I2cdev, Fpdl_Patgen):
    
    def __init__(self, interface, i2c_addr):
        I2cdev.__init__(self, interface, i2c_addr)
        
        self.init()
        self.print_info()
        
#        Fpdl_Patgen.__init__(self, interface)
        
        self.gpio = {} # GPIO[0-3], None, GPIO_REG[5-8]

        for num, (reg, pos) in SER_GPIO.items():
            self.gpio[num] = Fpdl_Gpio(self, reg, pos)
            
        for num, (reg, pos) in SER_GPIO_REG.items(): # (num, iodir, output)
            self.gpio[num] = Fpdl_Gpio_Reg(self, reg, pos)
            
        for num, (reg, pos) in SER_GPI_REG.items():
            #print self.gpio[num].gpi_reg, reg, pos, "<<"
            self.gpio[num].gpi_reg = reg
            self.gpio[num].gpi_pos = pos
            #print self.gpio[num].gpi_reg,  "<<"
        
    def init(self):
        
        # Enable remote I2C access
        self.setRegBitHi(0x3, 3)
        self.setRegBitHi(0x17, 7)
        
        # Use internal clock for PG
        self.setRegBitHi(0x65, 2)
    
        # Disable EDID
        self.setRegBitHi(0x4F,0)
    
        self.init_pg_720p()
        #self.init_edid_sram()
        
    def init_edid_sram(self):
        edid = "00 FF FF FF FF FF FF 00 04 AF 00 00 01 01 01 01 22 10 01 03 81 00 00 FF 0A 01 01 01 01 01 01 01 01 01 01 00 00 00 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 F4 1A 00 C8 50 D0 35 20 02 01 01 00 B1 63 00 00 00 18 00 00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 CA"
        edid = edid.split(' ')
        for addr, data in enumerate(edid):
            self.write(0x49, addr)
            self.write(0x4A, 0)
            self.write(0x48, 0xB)
            self.write(0x4B, int(data,16))
            #print hex(self.read(0x4B))exit
    
    def print_edid(self):
        for i in range(8):
            line=[]
            self.write(0x4A,0)
            for j in range(16):
                self.write(0x49,i*16+j)
                self.write(0x48, 0xB)
                line.append(tohex(self.read(0x4B)))
            print " ".join(line)
        
    def print_status(self):
        self.print_regval(SER_G_STATUS) 
        self.print_regval(SER_B_STATUS) 
        self.print_regval(SER_MODESEL)
        self.print_regval(SER_DUAL_STS)
        msb=self.read(0xB)
        lsb=self.read(0xA)
        print ("CRC Error (back channel): {}".format( (msb<<8)+lsb))

        val=self.read(0x15)
        print ("I2C Voltage Select: {}".format("3.3V" if val else "1.8V"))

        print "Local ID: {} ({})".format(hex(self.read(0x0)), hex(self.read(0x0)>>1))
        print "Remote ID: {} ({})".format(hex(self.read(0x7)), hex(self.read(0x7)>>1))

        
    def print_info(self):
        val = self.read(0xF0, 6)
        print "  TX ID: {}".format("".join( [toasc(v) for v in val] ))
        print " REV ID: {}".format(self.read(0x0D)>>4 )
        print " I2C ID: {} ({})".format(hex(self.read(0)),hex(self.read(0)>>1))
        
    def reset(self):
        self.setRegBitHi(0x01, 1) # This bit is self-clearing
        
    def clear(self):  # Clear Error
        self.write(0x04, 1<<5)
        self.write(0x04, 0)   
        
    def cmd_gpio(self, num=None, val=None):
        if num==None:
            for num, g in self.gpio.items():
                iodir = g.getdir()
                if iodir=="IN":
                    val = g.getinput()
                elif iodir=="OUT":
                    val = g.getoutput()
                else:
                    val = "??"
                if num in [0,1,2,3]:
                    remote = "(Rmt)" if g.getmode()&1==1 else ""                     
                    print "{}: {:<15}{:>3}{} = {}".format(num, g.label, iodir, remote, val)
                else:
                    print "{}: {:<15}{:>3} = {}".format(num, g.label, iodir, val)
                
        elif num in ['0','1','2','3','5','6','7','8'] and val in ['0', '1']:
            num=int(num)
            val=int(val)
            print num,val
            if self.gpio[num]!=None:
                self.gpio[num].setoutput(val)

#DES_G_STATUS = ("RES", "RES", "RES", "RES", "I2S_LOCKED", "CRC_ERROR", "RES", "LOCK")
DES_G_STATUS = Regspec(
                reg= 0x1C, 
                name= "General Status", 
                desc= ("RES", "RES", "RES", "RES", "RES", "CRC_ERROR", "RES", "LOCK"))

DES_G_CFG0 = Regspec(
              reg= 0x02,
              name= "General Config 0",
              desc= ("OEN", "OEN/OSSSEL_OVRD", "AUTO_CLK_EN", "OSS_SEL", "BKWD OVRD", "BKWD_MODE", "LFMODE_OVRD", "LFMODE"))

AEQ_CTRL = Regspec(
              reg= 0x35,
              name= "AEQ Control",
              desc= ("RES", "RESTART", "LCBL_OVRD", "LCBL", "RES", "RES", "RES", "RES"))

GPI_STATUS = ("7","8","6","5","RES","4","3","2","1","0")

DES_GPIO = { 0:(0x1D, 0),
             1:(0x1E, 0),
             2:(0x1E, 4),
             3:(0x1F, 0) }

DES_GPIO_REG = { 5:(0x20, 0),
                 6:(0x20, 4),
                 7:(0x21, 0),
                 8:(0x21, 4) }  # GPIO_REG[5-8]

DES_GPI_REG = { 0: (0x6E, 0), 
                1: (0x6E, 1),
                2: (0x6E, 2),
                3: (0x6E, 3),
                5: (0x6E, 5),
                6: (0x6E, 6),
                7: (0x6E, 7),
                8: (0x6F, 0) }

class Fpdl_Des(I2cdev, Fpdl_Patgen):
    def __init__(self, interface, i2c_addr):
        I2cdev.__init__(self, interface, i2c_addr)
        
        self.init()
        self.print_info()

        self.gpio = {} # GPIO[0-3], None, GPIO_REG[5-8]
        
        for num, (reg, pos) in DES_GPIO.items():
            self.gpio[num] = Fpdl_Gpio(self, reg, pos)
            
        for num, (reg, pos) in DES_GPIO_REG.items(): # (num, iodir, output)
            self.gpio[num] = Fpdl_Gpio_Reg(self, reg, pos)
            
        for num, (reg, pos) in DES_GPI_REG.items():
            #print self.gpio[num].gpi_reg, reg, pos, "<<"
            self.gpio[num].gpi_reg = reg
            self.gpio[num].gpi_pos = pos
            #print self.gpio[num].gpi_reg,  "<<"
        
    def init(self):
        #Enable PG internal clock
        self.setRegBitHi(0x39, 1)
        
        #Use internal clock for PG
        self.setRegBitHi(0x65, 2)
            
        self.init_pg_720p()
    
        return
        #
        # Setting:
        #    Nibble:   Bit-3       Bit-2      Bit-1    Bit-0
        #   Funtion:   OUTPUT_VAL  RESERVED   DIR      ENABLE
        #                                     DIR=0: output
        #                                     DIR=1: input
        
        #GPIO_REG5 = 0b0011
        #GPIO_REG6 = 0b0001
        #GPIO_REG7 = 0b1001
        #GPIO_REG8 = 0b0001
    
        #Des.write(0x20, (GPIO_REG6<<4) + GPIO_REG5)
        #Des.write(0x21, (GPIO_REG8<<4) + GPIO_REG7)

    def reset(self):
        self.setRegBitHi(0x01, 1) # This bit is self-clearing
        
    def print_status(self):
        self.print_regval(DES_G_STATUS)
        self.print_regval(DES_G_CFG0)     
        self.print_regval(AEQ_CTRL)
        print "AEQ Status (0x3B): ", self.read(0x3B)
        
        val = self.read(0x4B)
        print "LVDS Setting (0x4B):{} ({})".format(val, ["400mV","600mV","?","?"][val&3])
        print "Local ID: {} ({})".format(hex(self.read(0x0)), hex(self.read(0x0)>>1))
        print "Remote ID: {} ({})".format(hex(self.read(0x7)), hex(self.read(0x7)>>1))

        
    def print_info(self):
        print "  RX ID: {}".format( "".join( [toasc(v) for v in self.read(0xF0, 6)] ))
        print " REV ID: {}".format(self.read(0x1D)>>4 )
        print " I2C ID: {} ({})".format(hex(self.read(0)),hex(self.read(0)>>1))

    def cmd_gpio(self, num=None, val=None):
        if num==None:
            for num, g in self.gpio.items():
                iodir = g.getdir()
                if iodir=="IN":
                    val = g.getinput()
                elif iodir=="OUT":
                    val = g.getoutput()
                else:
                    val = "??"
                if num in [0,1,2,3]:
                    remote = "(Rmt)" if g.getmode()&1==1 else ""     
                    print "{}: {:<15}{:>3}{} = {}".format(num, g.label, iodir, remote, val)
                else:
                    print "{}: {:<15}{:>3} = {}".format(num, g.label, iodir, val)
                
        elif num in ['0','1','2','3','5','6','7','8'] and val in ['0', '1']:
            num=int(num)
            val=int(val)
            if self.gpio[num]!=None:
                self.gpio[num].setoutput(val)           
                
STATUS = Regspec(
        reg=0x0E,
        name="STATUS",
        desc=['RES','RES','RES','RES','BRT_SLOPE_DONE', 'TEMP_RES_MISSING', 'EXT_TEMP_LOW', 'EXT_TEMP_HIGH'])

FAULT = Regspec(
        reg=0xF,
        name="FAULT",
        desc=['RES','VIN_OVP', 'VIN_UVLO', 'THERM_SHUTDOWN', 'BOOST_OCP', 'BOOST_OVP', 'PWR_FET', 'CHRG_PUMP'])

LED_FAULT = Regspec(
        reg=0x10,
        name="LED FAULT",
        desc=['RES','RES','OPEN_LED','SHORT_LED','LED4','LED3','LED2','LED1'])

class Led_Driver(I2cdev):
    def __init__(self, interface, i2c_addr):
        I2cdev.__init__(self, interface, i2c_addr)

        self.init()
        self.print_info()
        
    def init(self):
        # LED Brightness Mode = Brightness Register
        #Leddrv.setRegBit(0x66, 2)
        
        # Config: 80mA, Adv slope, 105ms
        #Leddrv.write(0x0D, 0x4C)
    
        # Set LCD backlight max current
        #self.write(0x02, 0)  # MSB_4bit
        #self.write(0x03, 100) # LSB_8bit
    
        # Set W-Logo backlight max current
        self.write(0x0c, 0x10)
    
        self.set_blu(0xffff)
        #self.set_logo(0x7ff)
    
    def print_info(self):   
        v = int(self.read(0x12, 1))
        print " Full layer Revision: {}".format((v>>4)&0xF)                
        print " Metal Mask Revision: {}".format(v&0xF)
        
    def print_status(self):
        
        val = (self.read(0x00)<<8) + self.read(0x01)
        disp_brt = val/65535.0*100
        print "{:.<35}: {:.1f} % ({})".format("BLU brightness (0x00_01)", disp_brt, hex(val))
        
        val = (self.read(0x0a)<<8) + self.read(0x0b)
        logo_brt = val/8191.0*100
        
        print "{:.<35}: {:.1f} % ({})".format("LOGO Brightness (0x0A_0B)", logo_brt, hex(val))
        
        val = self.read(0x73)&(2**6-1)
        print "{:.<35}: {:.2f} V ({})".format("Boost Init Voltage (0x73[5:0])", val/63.0*(47.5-16)+16, hex(val))
        
        val = (self.read(0x0d)>>4)&7
        scale= [25,30,50,60,80,100,120,150][val]
        
        print "{:.<35}: {:.3f} mA ({})".format("Current Scale (0x0D[6:4])", scale, bin(val))

        cl = ((self.read(0x2)&0xF)<<8) +self.read(0x3)
                
        tmp = cl/4095.0 * scale
        print "{:.<35}: {:.3f} mA ({})".format("BLU Current Limit (0x02_03)", tmp, hex(cl))
        
        
        #tmp = tmp*disp_brt/100
        #print "DISP AVG Current Setting------: {:.0f} mA".format(tmp)        
        
        cl = self.read(0xC)
        
        tmp = cl/255.0 * scale
        print "{:.<35}: {:.3f} mA ({})".format("LOGO Current Limit (0x0C * Scale)", tmp, hex(cl))
        
        #tmp = tmp*logo_brt/100.0
        #print "LOGO AVG Current Setting------: {:.0f} mA".format(tmp)        
      
       
        msb = self.read(0x15)&0xff
        lsb = self.read(0x16)&0xff
        print "{:.<35}: {}".format("Display Current (0x15_16)", hex((msb<<8) + lsb))

        msb = self.read(0x17)&0xff
        lsb = self.read(0x18)&0xff
        print "{:.<35}: {}".format("PWM (0x17_18)", hex((msb<<8) + lsb))

        msb = self.read(0x13)&0xff
        lsb = self.read(0x14)&0xff
        print "{:.<35}: {}".format("Temperature (0x13_14)", hex((msb<<8) + lsb))
        
        val = self.read(0x70)
        
        clk_sel = (val>>4)&1
        print "{:.<35}: {} ({})".format("Boost Clock Source (0x70[4])", ['internal', 'external'][clk_sel], clk_sel)


        if clk_sel==0:
            freq_opts=[100,200,303,400,629,800,1100,2200]
        else:
            freq_opts=[100,200,303,400,625,833,1111,2500]

        curr = (val>>1)&7
        print "{:.<35}: {} A ({})".format("Boost Max Current (0x70[3:1])", curr+2, bin(curr))

        val=self.read(0x71)       
        freq = val & (2**3-1)
        
        val = self.read(0x6E)&15
        pwm_freq =[4882,9766,13428,17090,19531,20752,21973,23192,24412,25635,26855,28076,29297,30518,34180,39063][val]
        
        print "{:.<35}: {} kHz ({})".format("PWM Frequency (0x6E[3:0])", pwm_freq/1000.0, bin(val))
        
        print "{:.<35}: {} kHz ({})".format("Boost Frequency (0x71[2:0])", freq_opts[freq], bin(freq))
        
        ss = (val>>7) & 1
        print "{:.<35}: {} ({})".format("Boost Spread Spectrum (0x71[7])", ['disabled', 'enabled'][ss],ss)
        
        print "---"
        
        self.print_regval(STATUS)
        self.print_regval(LED_FAULT)
    
        #msb = Leddrv.read(0x15)& 0b1111
        #lsb = Leddrv.read(0x16)
        #print "LED CURRENT: {}".format( hex((msb<<8) + lsb) )
        
        self.print_regval(FAULT)
        
#        temp=self.get_temp()
#        print "TEMP: {} ({})".format( temp, hex(temp) )
    
#    def print_eeprom(self):
#        
#        parse = lambda reg, msb, lsb, val_list: val_list[(self.read(reg)>>lsb)&(2**(msb-lsb+1)-1)]
#        
#        #curr_scale= [25,30,50,60,80,100,120,150][(self.read(0x03)>>4)&7]
#        curr_scale = parse(0x63, 6, 4, [25,30,50,60,80,100,120,150])
#        
#        print "Scale Current Limit: {} mA".format(curr_scale)
#        
#        tmp = ((self.read(0x60)&0xF)<<8) + self.read(0x61)
#        print "LED Current Control: {:0.1f} % ({})".format(tmp/4095.0*100, hex(tmp))          
#        
        
    def reset(self):
        return
    
    def unlock(self):
        # Unlock EEPROM
        self.write(0x1A, 0x08)
        self.write(0x1A, 0xBA)
        self.write(0x1A, 0xEF)
    
    def lock(self):
        self.write(0x1A, 0x00)
        
    def program(self, filename="lp8860.eeprom"):
        print "Writing to EEPROM.."
        print "Input file: "+filename
        with open(filename,'r') as fd:
            lines=[]
            for line in fd:
                if line.find("#")<0:
                    byte = line.split(' ')
                    lines.append( (int(byte[0], 16), int(byte[1].rstrip(), 16)) )
    
            # PWM=0, PLL=0
            bak=[]
            reg_b = [0,1,4,5,7,8,0xa,0xb]
            for reg in reg_b:
                bak.append( self.read(reg) )
    
            for reg in reg_b:
                self.write(reg, 0)
            
            self.setRegBitLo(0x6D, 4)
            
            # Unlock EEPROM
            self.unlock()
        
            for byte in lines:
                self.write(byte[0], byte[1])
                print "{} <- {}".format(hex(byte[0]), hex(byte[1]))
                sleep(0.01)
    
            self.write(0x19, 0x2)
            sleep(0.5)
            self.write(0x19, 0)
    
            # Read from EEPROM to Register
            #self.load()
            
            # Restore PWM and PLL
            for reg, b in zip(reg_b, bak):
                self.write(reg, b)
            
            #self.setRegBitHi(0x6D, 4)
    
            sleep(0.5)
            print "Verifying..."
            for byte in lines:
                val = self.read(byte[0])
                #print "{}: {} ({})".format(hex(byte[0]), hex(val), hex(byte[1]))
                if val!=byte[1]:
                    print "EEPROM Program Failed!"

                    return
    
            self.write(0x19, 0)
            # Lock EEPROM
            self.lock()
            
            print "OK"
            
    def set_blu(self, brt=''):
        if brt=='':
            print "blu <0-100>"
            return
        brt = float(brt)
        brt = int(min(brt,100)/100.0 * 0xffff)
        self.write(0x00, brt>>8)
        self.write(0x01, brt & 0xFF)
    
    def set_logo(self, brt=''):
        if brt=='':
            print "logo <0-100>"
            return
        brt = float(brt)
        brt = int(min(brt,100)/100.0 * 0x1fff)
        
        self.write(0x0a, brt>>8)
        self.write(0x0b, brt & 0xFF)
        
    def load(self): # Load from EEPROM
        self.unlock()
        self.write(0x19, 1)
        sleep(0.01)
        self.write(0x19, 0)      
        
    def clear(self): # Clear errors
        self.write(0x11, 1)
        
    def get_temp(self):
        msb = self.read(0x13) & 0b111
        lsb = self.read(0x14)
        return (msb<<8)+lsb

class Touch(I2cdev):
    def __init__(self, interface, i2c_addr):
        I2cdev.__init__(self, interface, i2c_addr)

        self.init()
        self.print_info()
        
    def init(self):
        # T100 - Multiple Touch object (Addr = 0x0C2F)
        T100 = [0x2F, 0x0C, 
                0x83, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x00, 0x00, 
                0x20, 0x2A, 0x00, 0x00, 0xFF, 0x0F, 0x00, 0x00, 0x00, 0x00, 
                0x00, 0x14, 0x2A, 0x00, 0x00, 0xFF, 0x0F, 0x00, 0x00, 0x0B, 
                0x00, 0x1E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    
        # Unknown object (0x0C6A)
        TT = [ 0x6A, 0x0C, 
              0,0,0,0,0, 0,0,0,0,0, 0,0,0 ]
    
        # T7 - Power Configuration object (Addr = 0x09C1)
        T7= [0xC1, 0x09, 0xFF, 0xFF, 0x32, 0x02, 0x00, 0x00, 0x00]
    
        self.write_many(T100)
        #self.write_many(TT)
        self.write_many(T7)
    
        #Touch.write(0x2F, 0x0C)
        #print Touch.read_many(10)       
    
    
    def listen(self):
        plotit = raw_input("Plot? (y/n)")
        plotit = True if plotit in ['y', 'Y'] else False
        
        print "Press CTRL+C to stop"
        try:
            self.com.write("t1"+END)

            for i in range(50):
                # clear message buffer 
                self.com.write("I0"+END) # CHG status
                
                val = self.com.readline().rstrip()
                
                if len(val)==3:
                    if val[2]=='0':
                        #print "msg ", i
                        self.write(0x87, 0x06)
                        self.read_many(11)
                
            if plotit:
                fig, ax = plt.subplots()
                ax.set_xlim(0,4000)
                ax.set_ylim(0,4000)
                plt.show(block=False)
            
            num_tch=0
            rate=0
            plot_dt=time()
            colors=['r', 'b', 'm', 'g', 'c', 'y' ,'k']
            event=['-', 'move', 'unsup', 'sup', '<---down', '<---up', 'unsupsup', 'unsupup', 'downsup', 'downup']
            while True:

                if num_tch==0:
                    tstart=time()
                    
                line = self.com.readline().rstrip()

                if len(line)>24:
                    if line[0:2]=="T5":
                        num_tch += 1
                        
                        dt=time()-tstart
                        
                        #print "----",dt, num_tch
                        if dt>=1:
                            rate = num_tch
                            num_tch=0
                            
                        byte=line.split(" ")
                        if len(byte)>7:
                            try:
                                status = int(byte[2],16)
                                finger = int(byte[1],16) & 0xF
                                x = int(byte[4] + byte[3], 16)
                                y = int(byte[6] + byte[5], 16)
                            
                                if plotit:
                                    ax.scatter(x,y, color=colors[min(finger, len(colors)-1)], s=1)
                                    if (time()-plot_dt)>0.1:
                                        fig.canvas.draw()
                                        fig.canvas.flush_events()
                                        plot_dt = time()
                                elif finger<10:
                                    print "[{} chg/s] {} {}, {} ({})".format(rate, "           "*finger, x, y, event[status&0xF])
                            except:
                                print "x"

        except KeyboardInterrupt:
            # clear message buffer 
            self.com.write("t0"+END) # CHG status
            
            if plotit:
                plt.close()

    def listen2(self):
        plotit = raw_input("Plot? (y/n)")
        plotit = True if plotit in ['y', 'Y'] else False
        
        print "Press CTRL+C to stop"
        try:
            self.com.write("t0"+END)
            
            if plotit:
                fig, ax = plt.subplots()
                ax.set_xlim(0,4100)
                ax.set_ylim(0,4100)
                plt.show(block=False)
            
            num_tch=0
            rate=0
            plot_dt=time()
            colors=['r', 'b', 'm', 'g', 'c', 'y' ,'k']
            while True:

                self.com.write("I0"+END) # CHG status
                if self.com.readline()[2]!='0':
                    continue

                if num_tch==0:
                    tstart=time()
                
                self.write(0x87, 0x06)

                byte = [0]+ self.read_many(11)

                num_tch += 1
                
                dt=time()-tstart
                
                #print "----",dt, num_tch
                if dt>=1:
                    rate = num_tch
                    num_tch=0
                    
                #byte=line.split(" ")
                if len(byte)>7:
                    try:
                        finger = byte[1] & 0xF
                        x = (byte[4]<<8) + byte[3]
                        y = (byte[6]<<8) + byte[5]
                    
                        if plotit:
                            ax.scatter(x, y, color=colors[min(finger, len(colors)-1)], s=1)
                            if (time()-plot_dt)>0.1:
                                fig.canvas.draw()
                                fig.canvas.flush_events()
                                plot_dt = time()
                        elif finger<10:
                            print "[{} chg/s] {} {}, {}".format(rate, "           "*finger, x, y)
                    except Exception as e:
                        print e
#                else:
#                    sleep(0.01)

        except KeyboardInterrupt:
            self.com.write("t0"+END)
            if plotit:
                plt.close()
                
    def get_msg(self):
        self.write(0x87, 0x06)
        print self.read_many(11)

    def print_info(self):
        self.write(0x00, 0x00)
        val = self.read_many(7)
        desc = ("Family Id", "Variant Id", "Version", "Build", "Matrix X Size", "Matrix Y Size", "Num of Obj")
        for n, d in enumerate(desc):
            print "{:>15}: {} ({})".format(d, hex(val[n]), val[n])

    def print_table(self):
        self.write(0x00, 0x00)
        val = self.read_many(7)
        
        for i in range(val[6]):
            self.write(i*6+7,0)
            obj = self.read_many(6)
            print "{}: type={}, size={}, #inst={}, rpt_id={}".format(hex((obj[2]<<8) + obj[1]), obj[0], obj[3], obj[4], obj[5])

    def print_dmsg(self):
        # Command Processor T6 (0x692)
        self.write_many([0x92+5, 0x06, 0x10])
        
        # Debug Diag T37 (0x604)
        data = []
        for i in range(10):
        
            self.write(0x04, 0x06)
            for i in range(128/16):
                dat = self.read_many(18)[2:]
                
                for i in range(8):
                    data.append((dat[i*2+1]<<8)+dat[i*2])
                    #data.append(dat[i*2+1])
                    #data.append(dat[i*2])

            self.write_many([0x92+5, 0x06, 0x01]) # page up
        
        for i in range(5):
            print data[i*20:i*20+128]
            
        while True:
            self.write(0x04, 0x06)
            d=self.read_many(4)
            #print d
            if d[1]>0:
                self.write_many([0x92+5, 0x06, 0x02]) # page down
            else:
                break

class Eeprom(I2cdev): #<=16K
    
    def __init__(self, interface, i2c_addr):
        I2cdev.__init__(self, interface, i2c_addr)
        self.init()
        
    def init(self):
        self.read(0) # Check if device exist?
            
class Eeprom_big(I2cdev): #32K_64K
    
    def __init__(self, interface, i2c_addr):
        I2cdev.__init__(self, interface, i2c_addr)
        self.init()
        
    def init(self):
        self.read(0) # Check if device exist?
        
    def cmd_read(self, addr, num='1'):  ## NOT VERIFIED!
        addr = int(addr, 16)
        num = int(num)
        buf = [addr>>8, addr&0xFF]
        self.write_many(buf)
        return self.read_many(num)
        
    def cmd_write(self, addr, data):  ## NOT VERIFIED!
        addr = int(addr, 16)
        data = int(data, 16)
        buf = [addr>>8, addr&0xFF, data ]
        self.write_many(buf)

    def print_regs(self, n_row=16):  ## NOT VERIFIED!
        #print "     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f"
        for i in range(n_row):
            val = self.cmd_read(hex(i*16), '16')      
            hex_str = " ".join( [ tohex(v) for v in val ] )
            asc_str = "".join( [ toasc(v) for v in val ] )        
            print "{}: {}  {}".format(tohex(i*16), hex_str, asc_str )
            
#    def program(self):
#        addr=int('0x10',16)
#        data= "00 FF FF FF FF FF FF 00 04 AF 00 00 01 01 01 01"
#        
#        data = data.split(" ")
#        data = [int(d,16) for d in data]
#        for d in data:
#            buf = [addr>>8, addr&0xFF, d]
#            self.write_many(buf)
#            sleep(0.01)
        
class Temp_Sens(I2cdev):
    def __init__(self, interface, i2c_addr):
        self.__init__(self, interface, i2c_addr)

def find_com(start=1,end=0x7F):
    ports = ['COM%s' % (i + 1) for i in range(start, end)]
    for p in ports:
        try:
            com = serial.Serial(p, baudrate=BAUDRATE, timeout=0.3)
            sleep(3)
            com.write("p"+END)
            ret = com.readline().rstrip()
            if len(ret)>4 and ret[:4]=="FPDL":
                #print
                print "  Found {} at {}".format(ret, p)
#            if (ret=="FPDL_DISP_ITL_1.0"):
            return com
        except (OSError, serial.SerialException):
            pass

    raise Exception(" Interface Board not found!")

if __name__=="__main__":
    
    # TPK PCBA I2C address
    I2C_SER = 0x0C
    I2C_DES = 0x76 >> 1
    I2C_LED = 0x5A >> 1
    I2C_EEPROM1 = 0xA0 >> 1
    I2C_EEPROM2 = 0xAA >> 1
    I2C_TOUCH = 0x96 >> 1
    I2C_TEMP = 0x98 >> 1

    # EVM I2C address
    I2C_SER = 0x0C
    I2C_DES = 0x2C
    I2C_LED = 0x2D
    I2C_EEPROM1 = 0x50
    I2C_EEPROM2 = 0x50
    I2C_TOUCH = 0x4B
    print "Start.."
    try:
        com = serial.Serial(COM_PORT, baudrate=BAUDRATE, timeout=2)
    except Exception as e:
        print e
        exit()

    sleep(3)

    Ser = Fpdl_Ser(com, I2C_SER)
    Des = Fpdl_Des(com, I2C_DES)
    Led = Led_Driver(com, I2C_LED)
    Tch = Touch(com, I2C_TOUCH)
    Eeprom1 = Eeprom(com, I2C_EEPROM1)
    Eeprom2 = Eeprom(com, I2C_EEPROM2)