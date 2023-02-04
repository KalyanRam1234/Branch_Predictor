from nmigen import *  # importing nmigen and other modules required
from nmigen.back.pysim import *
from nmigen import Elaboratable, Module, Signal
from nmigen.build import Platform
from nmigen.cli import main_parser, main_runner
n=int(input("Enter n: ")) # number of LSB bits to be used for branch prediction
class DynamicBranch(Elaboratable): # module that will make dynamic branch prediction
    #implementing the FSM of a 2-bit dynamic branch predictor taught in class(00 - ST, 01 - WT, 10- WNT, 11- SNT)
    def __init__(self):# initializing ports of this module
        self.x=Signal(unsigned(32)) #address port
        self.y=Signal(unsigned(1)) #outcome of branch
        self.array=Array([Signal(unsigned(2)) for _ in range(2**n)]) #defining an array of size 2^n. 
        self.z=Signal(unsigned(1)) #outputs 1 if Hit , 0 if Miss
        self.p=Signal(unsigned(n))
        self.Hit=Signal(unsigned(32)) #counts number of Hits
    def elaborate(self, platform: Platform) -> Module: # main logic
        m = Module()
        m.d.comb+=self.p.eq(self.x[0:n]) #slicing n LSB bits from the given address input
        i=Signal(range(0,2**n))
        m.d.comb+=i.eq(self.p) 
        with m.If(self.y==1): #if self.y is 1, it means that actual branch outcome is T
            with m.If(self.array[i]==0): #if the value in the array corresponding to the sliced index is 0 or 1 then it means
                #then our prediction is Hit. If the value is 1 then it is currently in Weakly Taken state so, we make it Strongly Taken
                m.d.sync+=self.z.eq(1)
                m.d.sync+=self.array[i].eq(self.array[i])
            with m.Elif(self.array[i]==1):
                m.d.sync+=self.z.eq(1)
                m.d.sync+=self.array[i].eq(self.array[i]-1)
            with m.Elif(self.array[i]>=2): # if the value in the array is greater than 1 then the prediction is Miss and the value in the array
                #is changed from WNT->WT or SNT->WNT 
                m.d.sync+=self.z.eq(0)
                m.d.sync+=self.array[i].eq(self.array[i]-1)

        with m.Elif(self.y==0): #if self.y is 0, it means that actual branch outcome is NT
            with m.If(self.array[i]==3):
                #if the value in the array corresponding to the sliced index is 2 or 3 then it means
                #then our prediction is Hit. If the value is 2 then it is currently in Weakly Not Taken state so, we make it Strongly Not Taken
                m.d.sync+=self.z.eq(1)
                m.d.sync+=self.array[i].eq(self.array[i])
            with m.Elif(self.array[i]==2):
                m.d.sync+=self.z.eq(1)
                m.d.sync+=self.array[i].eq(self.array[i]+1)
                # if the value in the array is lesser than 2 then the prediction is Miss and the value in the array
                #is changed from WT->WNT or ST->WT 
            with m.Elif(self.array[i]<2):
                m.d.sync+=self.z.eq(0)
                m.d.sync+=self.array[i].eq(self.array[i]+1)
        with m.If(self.z==1):
            m.d.sync+=self.Hit.eq(self.Hit+1)
        return m

    def ports(self):
        return [self.x, self.y, self.z, self.Hit]
if __name__=="__main__":
    parser = main_parser()
    args = parser.parse_args()
    m=Module()
    m.domains.sync = sync = ClockDomain("sync", async_reset=True) #define a clock domain
    branch=DynamicBranch()
    m.submodules+=branch #adding the modules made above into the main module

    x=Signal(unsigned(32))
    y=Signal(unsigned(1))

    m.d.sync+=branch.x.eq(x)
    m.d.sync+=branch.y.eq(y)

    sim=Simulator(m) #Simulator is used to test our modules with the testcases given in the assignment
    sim.add_clock(1e-9,domain="sync")
    filename=input("Enter filename: ")
    file=open(filename, 'r')
    x1=[]
    x2=[]

    for element in file: # reading trace file and storing addresses in x1 and T or NT in x2 list
        p=element.split(" ")
        x1.append(int(p[0]))
        if(p[1][0]=='T'): 
            x2.append(1)
        else: 
            x2.append(0)
    def process():
        yield x.eq(0)
        yield y.eq(1)
        yield
        for i in range(len(x1)):
            yield x.eq(x1[i])
            yield y.eq(x2[i])
            yield
sim.add_sync_process(process, domain="sync")
with sim.write_vcd("dynamicbranch.vcd", "dynamicbranch.gtkw", traces=branch.ports()):
    sim.run_until((len(x1)+4)*(1e-9), run_passive=True)
