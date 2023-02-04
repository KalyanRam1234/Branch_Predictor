from nmigen import *  # importing nmigen and other modules required
from nmigen.back.pysim import *
from nmigen import Elaboratable, Module, Signal
from nmigen.build import Platform
from nmigen.cli import main_parser, main_runner

class PredictTaken(Elaboratable): # This class is a module that outputs 1 if the branch is taken

    def __init__(self): #initializing ports 
        self.x=Signal(unsigned(32)) #address port
        self.y=Signal(unsigned(1)) #outcome of branch(T or NT)
        self.taken=Signal(unsigned(1)) # outputs Hit or Miss
        self.counterT=Signal(unsigned(32)) # counts number of Hits

    def elaborate(self, platform: Platform) -> Module: #main logic 
        m = Module()
        with m.If(self.y==1): #if the outcome branch is T then is a hit else it is a miss
            m.d.sync+=self.taken.eq(1)
            m.d.sync+=self.counterT.eq(self.counterT+1)
        with m.Elif(self.y==0):
            m.d.sync+=self.taken.eq(0)
        return m

    def ports(self):
        return [self.x, self.y, self.taken, self.counterT] #returns ports which were initialized above
class PredictNotTaken(Elaboratable): # This class is a module that outputs 1 if the branch is not taken

    def __init__(self):
        self.y=Signal(unsigned(1)) #outcome of branch(T or NT)
        self.nottaken=Signal(unsigned(1))  # outputs Hit or Miss
        self.counterN=Signal(unsigned(32)) #counts number of Misses
    def elaborate(self, platform: Platform) -> Module: # main logic
        m = Module()
        with m.If(self.y==0): #if the outcome of branch is NT then it is a Hit
            m.d.sync+=self.nottaken.eq(1)
            m.d.sync+=self.counterN.eq(self.counterN+1)
        with m.Elif(self.y==1):
            m.d.sync+=self.nottaken.eq(0)
        return m

    def ports(self):
        return [self.nottaken, self.counterN] #returns ports initialized in this class

if __name__=="__main__":
    parser = main_parser()
    args = parser.parse_args()

    m=Module()
    m.domains.sync = sync = ClockDomain("sync", async_reset=True) #define a clock domain
    branch=PredictTaken()
    branch1=PredictNotTaken()

    m.submodules+=branch #adding the modules made above into the main module
    m.submodules+=branch1
    x = Signal(32)
    y = Signal(1)

    m.d.sync+=branch.x.eq(x)
    m.d.sync+=branch.y.eq(y)
    m.d.sync+=branch1.y.eq(y)

    sim=Simulator(m) #Simulator is used to test our modules with the testcases given in the assignment
    sim.add_clock(1e-9,domain="sync")
    filename=input("Enter filename: ")
    file=open(filename, 'r')
    x1=[]
    x2=[]
    c=0
    for element in file: # reading trace file and storing addresses x1 and T or NT in x2 list
        p=element.split(" ")
        x1.append(int(p[0]))
        if(p[1][0]=='T'): 
            x2.append(1)
        else: 
            x2.append(0)
            c+=1
    #print(c)
    def process(): 
        counterT=0
        counterN=0
        for i in range(len(x1)):
            if(x2[i]==1): counterT+=1
            else: counterN+=1
            yield x.eq(x1[i])
            yield y.eq(x2[i])
            yield
        print(f"Number of Taken: {counterT}\nNumber of Not Taken: {counterN}")

sim.add_sync_process(process, domain="sync")
with sim.write_vcd("predicttaken.vcd", "predicttaken.gtkw", traces=branch.ports()+branch1.ports()):
    sim.run_until((len(x1)+2.5)*(1e-9), run_passive=True)
