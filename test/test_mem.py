import unittest
import random

from myhdl import *
from myhdl_lib.mem import rom, ram_sp_rf, ram_sp_wf, ram_sp_ar,ram_sdp_rf, ram_sdp_wf, ram_sdp_ar, ram_dp_rf, ram_dp_wf, ram_dp_ar
import myhdl_lib.simulation as sim

def mem_fill(clk, we, addr, di, content):
    for a, d in enumerate(content):
        we.next = 1
        addr.next = a
        di.next = d
        yield clk.posedge
    we.next = 0
    addr.next = 0
    di.next = 0

def mem_verify(clk, addr, do, content, ASYNC_RD=False):
    X = 1 if ASYNC_RD else 2
    for a, d in enumerate(content):
        addr.next = a
        for _ in range(X):
            yield clk.posedge
        assert d==do, "Verify@addr {}: expected={}, detected={} \nDATA:{}".format(a, d, do, content)
    addr.next = 0

def mem_write_and_read(clk, we, addrw, addrr, di, do, content_wr, content_rd, ASYNC_RD=False):
    X = 1 if ASYNC_RD else 2
    for a, d in enumerate(content_wr):
        we.next = 1
        addrw.next = a
        addrr.next = a
        di.next = d
        for _ in range(X):
            yield clk.posedge
        assert content_rd[a]==do, "Write&Read@addr {}: expected={}, detected={} \nDATA:{}".format(a, content_rd[a], do, content_rd)
    we.next = 0
    addrw.next = 0
    addrr.next = 0
    di.next = 0


class TestMem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def testRom(self):
        ''' ROM '''
        DATA_RANGE_MIN = -128
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        addr = Signal(intbv(0, min=0, max=ADDR_MAX))
        dout = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        CONTENT = tuple([random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)])

        def stim():
            @instance
            def _inst():
                yield delay(1)
                addr.next = addr.max-1
                yield delay(10)
                for a in range(ADDR_MAX):
                    addr.next = a
                    yield delay(1)
                    assert CONTENT[a]==dout, "At addr {}: expected {}, detected {}".format(a, CONTENT[a], dout)
                raise StopSimulation
            return _inst


        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            stm = stim()
            dut = getDut(rom, addr=addr, dout=dout, CONTENT=CONTENT)
            Simulation(dut, stm).run()
            del dut, stm


    def testRamSpRf(self):
        ''' RAM: Single-Port, Read-First '''
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        we = Signal(bool(0))
        addr = Signal(intbv(0, min=0, max=ADDR_MAX))
        di = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        do = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))

        CONTENT = [[random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)] for _ in range(5)]

        clk = sim.Clock(val=0, period=10, units="ns")
        clkgen = clk.gen()

        def stim():
            @instance
            def _inst():
                yield clk.posedge
                yield mem_fill(clk, we, addr, di, CONTENT[0])
                yield mem_verify(clk, addr, do, CONTENT[0])
                for i in range(1,len(CONTENT)):
                    yield mem_write_and_read(clk, we, addr, addr, di, do, content_wr=CONTENT[i], content_rd=CONTENT[i-1])
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut = getDut(ram_sp_rf, clk=clk, we=we, addr=addr, di=di, do=do)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del dut, stm


    def testRamSpWf(self):
        ''' RAM: Single-Port, Write-First '''
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        we = Signal(bool(0))
        addr = Signal(intbv(0, min=0, max=ADDR_MAX))
        di = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        do = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))

        CONTENT = [[random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)] for _ in range(5)]

        clk = sim.Clock(val=0, period=10, units="ns")
        clkgen = clk.gen()

        def stim():
            @instance
            def _inst():
                yield clk.posedge
                yield mem_fill(clk, we, addr, di, CONTENT[0])
                yield mem_verify(clk, addr, do, CONTENT[0])
                for i in range(1,len(CONTENT)):
                    yield mem_write_and_read(clk, we, addr, addr, di, do, content_wr=CONTENT[i], content_rd=CONTENT[i])
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut = getDut(ram_sp_wf, clk=clk, we=we, addr=addr, di=di, do=do)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del dut, stm


    def testRamSpAr(self):
        ''' RAM: Single-Port, Asynchronous Read '''
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        we = Signal(bool(0))
        addr = Signal(intbv(0, min=0, max=ADDR_MAX))
        di = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        do = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))

        CONTENT = [[random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)] for _ in range(5)]

        clk = sim.Clock(val=0, period=10, units="ns")
        clkgen = clk.gen()

        def stim():
            @instance
            def _inst():
                yield clk.posedge
                yield mem_fill(clk, we, addr, di, CONTENT[0])
                yield mem_verify(clk, addr, do, CONTENT[0], ASYNC_RD=True)
                for i in range(1,len(CONTENT)):
                    yield mem_write_and_read(clk, we, addr, addr, di, do, content_wr=CONTENT[i], content_rd=CONTENT[i-1], ASYNC_RD=True)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut = getDut(ram_sp_ar, clk=clk, we=we, addr=addr, di=di, do=do)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del dut, stm


    def testRamSdpRf(self):
        ''' RAM: Simple-Dual-Port, Read-First '''
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        we = Signal(bool(0))
        addrw = Signal(intbv(0, min=0, max=ADDR_MAX))
        addrr = Signal(intbv(0, min=0, max=ADDR_MAX))
        di = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        do = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))

        CONTENT = [[random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)] for _ in range(5)]

        clk = sim.Clock(val=0, period=10, units="ns")
        clkgen = clk.gen()

        def stim():
            @instance
            def _inst():
                yield clk.posedge
                yield mem_fill(clk, we, addrw, di, CONTENT[0])
                yield mem_verify(clk, addrr, do, CONTENT[0])
                for i in range(1,len(CONTENT)):
                    yield mem_write_and_read(clk, we, addrw, addrr, di, do, content_wr=CONTENT[i], content_rd=CONTENT[i-1])
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut = getDut(ram_sdp_rf, clk=clk, we=we, addrw=addrw, addrr=addrr, di=di, do=do)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del dut, stm


    def testRamSdpWf(self):
        ''' RAM: Simple-Dual-Port, Write-First '''
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        we = Signal(bool(0))
        addrw = Signal(intbv(0, min=0, max=ADDR_MAX))
        addrr = Signal(intbv(0, min=0, max=ADDR_MAX))
        di = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        do = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))

        CONTENT = [[random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)] for _ in range(5)]

        clk = sim.Clock(val=0, period=10, units="ns")
        clkgen = clk.gen()

        def stim():
            @instance
            def _inst():
                yield clk.posedge
                yield mem_fill(clk, we, addrw, di, CONTENT[0])
                yield mem_verify(clk, addrr, do, CONTENT[0])
                for i in range(1, len(CONTENT)):
                    yield mem_write_and_read(clk, we, addrw, addrr, di, do, content_wr=CONTENT[i], content_rd=CONTENT[i])
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut = getDut(ram_sdp_wf, clk=clk, we=we, addrw=addrw, addrr=addrr, di=di, do=do)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del dut, stm


    def testRamSdpAr(self):
        ''' RAM: Simple-Dual-Port, Asynchronous Read '''
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        we = Signal(bool(0))
        addrw = Signal(intbv(0, min=0, max=ADDR_MAX))
        addrr = Signal(intbv(0, min=0, max=ADDR_MAX))
        di = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        do = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))

        CONTENT = [[random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)] for _ in range(5)]

        clk = sim.Clock(val=0, period=10, units="ns")
        clkgen = clk.gen()

        def stim():
            @instance
            def _inst():
                yield clk.posedge
                yield mem_fill(clk, we, addrw, di, CONTENT[0])
                yield mem_verify(clk, addrr, do, CONTENT[0], ASYNC_RD=True)
                for i in range(1, len(CONTENT)):
                    yield mem_write_and_read(clk, we, addrw, addrr, di, do, content_wr=CONTENT[i], content_rd=CONTENT[i-1], ASYNC_RD=True)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut = getDut(ram_sdp_ar, clk=clk, we=we, addrw=addrw, addrr=addrr, di=di, do=do)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del dut, stm


    def testRamDpRf(self):
        ''' RAM: Dual-Port, Read-First '''
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        wea = Signal(bool(0))
        web = Signal(bool(0))
        addra = Signal(intbv(0, min=0, max=ADDR_MAX))
        addrb = Signal(intbv(0, min=0, max=ADDR_MAX))
        dia = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        dib = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        doa = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        dob = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))

        CONTENT = [[random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)] for _ in range(5)]

        clka = sim.Clock(val=0, period=10, units="ns")
        clkb = sim.Clock(val=0, period=17, units="ns")
        clkagen = clka.gen()
        clkbgen = clkb.gen()

        def stim():
            @instance
            def _inst():
                yield clka.posedge
                yield mem_fill(clka, wea, addra, dia, CONTENT[0])
                yield mem_verify(clka, addra, doa, CONTENT[0])
                yield mem_verify(clkb, addrb, dob, CONTENT[0])
                for i in range(1, len(CONTENT)):
                    yield mem_write_and_read(clka, wea, addra, addra, dia, doa, content_wr=CONTENT[i], content_rd=CONTENT[i-1])
                yield mem_fill(clkb, web, addrb, dib, CONTENT[0])
                yield mem_verify(clkb, addrb, dob, CONTENT[0])
                yield mem_verify(clka, addra, doa, CONTENT[0])
                for i in range(1, len(CONTENT)):
                    yield mem_write_and_read(clkb, web, addrb, addrb, dib, dob, content_wr=CONTENT[i], content_rd=CONTENT[i-1])
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut = getDut(ram_dp_rf, clka=clka, clkb=clkb, wea=wea, web=web, addra=addra, addrb=addrb, dia=dia, dib=dib, doa=doa, dob=dob)
            stm = stim()
            Simulation(clkagen, clkbgen, dut, stm).run()
            del dut, stm


    def testRamDpWf(self):
        ''' RAM: Dual-Port, Write-First '''
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        wea = Signal(bool(0))
        web = Signal(bool(0))
        addra = Signal(intbv(0, min=0, max=ADDR_MAX))
        addrb = Signal(intbv(0, min=0, max=ADDR_MAX))
        dia = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        dib = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        doa = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        dob = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))

        CONTENT = [[random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)] for _ in range(5)]

        clka = sim.Clock(val=0, period=10, units="ns")
        clkb = sim.Clock(val=0, period=14, units="ns")
        clkagen = clka.gen()
        clkbgen = clkb.gen()

        def stim():
            @instance
            def _inst():
                yield clka.posedge
                yield mem_fill(clka, wea, addra, dia, CONTENT[0])
                yield mem_verify(clka, addra, doa, CONTENT[0])
                yield mem_verify(clkb, addrb, dob, CONTENT[0])
                for i in range(1, len(CONTENT)):
                    yield mem_write_and_read(clka, wea, addra, addra, dia, doa, content_wr=CONTENT[i], content_rd=CONTENT[i])
                yield mem_fill(clkb, web, addrb, dib, CONTENT[0])
                yield mem_verify(clkb, addrb, dob, CONTENT[0])
                yield mem_verify(clka, addra, doa, CONTENT[0])
                for i in range(1, len(CONTENT)):
                    yield mem_write_and_read(clkb, web, addrb, addrb, dib, dob, content_wr=CONTENT[i], content_rd=CONTENT[i])
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut = getDut(ram_dp_wf, clka=clka, clkb=clkb, wea=wea, web=web, addra=addra, addrb=addrb, dia=dia, dib=dib, doa=doa, dob=dob)
            stm = stim()
            Simulation(clkagen, clkbgen, dut, stm).run()
            del dut, stm


    def testRamDpAr(self):
        ''' RAM: Dual-Port, Asynchronous Read '''
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 127
        ADDR_MAX = 100

        wea = Signal(bool(0))
        web = Signal(bool(0))
        addra = Signal(intbv(0, min=0, max=ADDR_MAX))
        addrb = Signal(intbv(0, min=0, max=ADDR_MAX))
        dia = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        dib = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        doa = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))
        dob = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX+1))

        CONTENT = [[random.randint(DATA_RANGE_MIN, DATA_RANGE_MAX) for _ in range(ADDR_MAX)] for _ in range(5)]

        clka = sim.Clock(val=0, period=10, units="ns")
        clkb = sim.Clock(val=0, period=14, units="ns")
        clkagen = clka.gen()
        clkbgen = clkb.gen()

        def stim():
            @instance
            def _inst():
                yield clka.posedge
                yield mem_fill(clka, wea, addra, dia, CONTENT[0])
                yield mem_verify(clka, addra, doa, CONTENT[0], ASYNC_RD=True)
                yield mem_verify(clkb, addrb, dob, CONTENT[0], ASYNC_RD=True)
                for i in range(1, len(CONTENT)):
                    yield mem_write_and_read(clka, wea, addra, addra, dia, doa, content_wr=CONTENT[i], content_rd=CONTENT[i-1], ASYNC_RD=True)
                yield mem_fill(clkb, web, addrb, dib, CONTENT[0])
                yield mem_verify(clkb, addrb, dob, CONTENT[0], ASYNC_RD=True)
                yield mem_verify(clka, addra, doa, CONTENT[0], ASYNC_RD=True)
                for i in range(1, len(CONTENT)):
                    yield mem_write_and_read(clkb, web, addrb, addrb, dib, dob, content_wr=CONTENT[i], content_rd=CONTENT[i-1], ASYNC_RD=True)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut = getDut(ram_dp_ar, clka=clka, clkb=clkb, wea=wea, web=web, addra=addra, addrb=addrb, dia=dia, dib=dib, doa=doa, dob=dob)
            stm = stim()
            Simulation(clkagen, clkbgen, dut, stm).run()
            del dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()