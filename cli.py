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
    def __init__(self, cmd_dict, prefix="RC"):
        self.cmds=cmd_dict
        self.prefix=prefix
        
    def shell(self):
        while True:
            try:
                inps = raw_input(self.prefix+"> ")
                inp = inps.split(" ")
                
                
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
                elif len(inps)>0:
                    exec("{}.{}".format(self.prefix,inps))
                else:
                    print (", ".join(sorted(self.cmds.keys())))
                    
            except Exception as e:
                print (" **{}".format(e))

def test1():
    print ('test1')

def test2():
    print ('test2')

if __name__ == "__main__":
    root_cmd = { 't1': test1, 't2': test2 }
    Cmd(root_cmd).shell()
