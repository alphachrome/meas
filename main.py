from myinstruments import GPD, BK8600, DM3058
from cli import Cmd

#instr = [GPD(), DM3058(), BK8660()]


instr_list = []

class Instrument:
    def __init__(self, dev, name=''):
        self.instr = dev()
        self.name = name
        instr_list.append(self.instr)
            
    def help(self):
        methods = [m for m in dir(self.instr) if callable(getattr(self.instr, m))]
        methods = ", ".join(methods)
        print methodspy


power = Instrument(GPD)
meter = Instrument(DM3058)
load = Instrument(BK8600)


root_cmd = dict()

root_cmd['power'] = Cmd({
    'help': power.help,}, prefix='power').shell

Cmd(root_cmd).shell()
    




