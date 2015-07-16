import unittest

from myhdl import *
from myhdl_lib.arbiter import arbiter_roundrobin
import myhdl_lib.simulation as sim



class TestArbiterRoundrobin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def testOneHot(self):
        ''' ARBITER_ROUNDROBIN: One Hot requests'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        sel = Signal(intbv(0, min=0, max=NUM_REQ))
        strob = Signal(bool(0))

        rst = ResetSignal(val=0, active=1, async=False)
        clk = Signal(bool(0))

        def stim():
            @instance
            def _inst():
                strob.next = 0
                req_vec.next = 0
                yield rst.negedge
                assert 0 == sel, "Select: expected {}, detected {}".format(0, sel)

                strob.next = 1
                for _ in range(3):
                    for i in range(NUM_REQ):
                        req_vec.next = 1 << i
                        yield delay(1)
                        assert i == sel, "Select: expected {}, detected {}".format(i, sel)
                        yield clk.posedge

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            clkgen = sim.clock_generator(clk, PERIOD=10)
            rstgen = sim.reset_generator(rst, clk, RST_LENGTH_CC=3)
            dut = getDut(arbiter_roundrobin, rst=rst, clk=clk, req_vec=req_vec, sel=sel, en=strob)
            stm = stim()
            Simulation(rstgen, clkgen, dut, stm).run()
            del rstgen, clkgen, dut, stm


    def testCount(self):
        ''' ARBITER_ROUNDROBIN: Count '''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        sel = Signal(intbv(0, min=0, max=NUM_REQ))
        strob = Signal(bool(0))

        rst = ResetSignal(val=0, active=1, async=False)
        clk = Signal(bool(0))

        def stim():
            @instance
            def _inst():
                strob.next = 0
                req_vec.next = 0
                yield rst.negedge
                yield clk.posedge
                assert 0 == sel, "Select: expected {}, detected {}".format(0, sel)

                strob.next = 1
                prio = NUM_REQ-1
                x = intbv(0)[NUM_REQ:]
                for i in range(x.max):
                    x[:] = i
                    req_vec.next = x
                    yield delay(1)

                    print i, bin(x), prio, sel
                    s = 0
                    for k in range(NUM_REQ):
                        kk = (prio + k + 1)%NUM_REQ
                        if x[kk]==1:
                            s = kk
                            break

                    assert s == sel, "Select: expected {}, detected {}".format(s, sel)

                    yield clk.posedge

                    if strob==1:
                            prio = s

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            clkgen = sim.clock_generator(clk, PERIOD=10)
            rstgen = sim.reset_generator(rst, clk, RST_LENGTH_CC=3)
            dut = getDut(arbiter_roundrobin, rst=rst, clk=clk, req_vec=req_vec, sel=sel, en=strob)
            stm = stim()
            Simulation(rstgen, clkgen, dut, stm).run()
            del rstgen, clkgen, dut, stm


    def testAll(self):
        ''' ARBITER_ROUNDROBIN: All requests'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        sel = Signal(intbv(0, min=0, max=NUM_REQ))
        strob = Signal(bool(0))

        rst = ResetSignal(val=0, active=1, async=False)
        clk = Signal(bool(0))

        def stim():
            @instance
            def _inst():
                strob.next = 0
                req_vec.next = 0
                yield rst.negedge
                assert 0 == sel, "Select: expected {}, detected {}".format(0, sel)

                mask = req_vec.max-1
                req_vec.next = mask
                strob.next = 1
                for _ in range(3):
                    for i in range(NUM_REQ):
                        yield delay(1)
                        assert i == sel, "Select: expected {}, detected {}".format(i, sel)
                        yield clk.posedge

                yield clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            clkgen = sim.clock_generator(clk, PERIOD=10)
            rstgen = sim.reset_generator(rst, clk, RST_LENGTH_CC=3)
            dut = getDut(arbiter_roundrobin, rst=rst, clk=clk, req_vec=req_vec, sel=sel, en=strob)
            stm = stim()
            Simulation(rstgen, clkgen, dut, stm).run()
            del rstgen, clkgen, dut, stm

    def testAllGap(self):
        ''' ARBITER_ROUNDROBIN: All requests, gappy strobe'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        sel = Signal(intbv(0, min=0, max=NUM_REQ))
        strob = Signal(bool(0))

        rst = ResetSignal(val=0, active=1, async=False)
        clk = Signal(bool(0))

        def stim():
            @instance
            def _inst():
                strob.next = 0
                req_vec.next = 0
                yield rst.negedge
                yield clk.posedge
                assert 0 == sel, "Select: expected {}, detected {}".format(0, sel)

                mask = req_vec.max-1
                req_vec.next = mask
                for i in range(NUM_REQ):
                    for _ in range(3):
                        yield delay(1)
                        assert i == sel, "Select: expected {}, detected {}".format(i, sel)
                        strob.next = 0
                        yield clk.posedge
                    else:
                        yield delay(1)
                        assert i == sel, "Select: expected {}, detected {}".format(i, sel)
                        strob.next = 1
                        yield clk.posedge

                yield clk.posedge
                strob.next = 0
                yield clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            clkgen = sim.clock_generator(clk, PERIOD=10)
            rstgen = sim.reset_generator(rst, clk, RST_LENGTH_CC=3)
            dut = getDut(arbiter_roundrobin, rst=rst, clk=clk, req_vec=req_vec, sel=sel, en=strob)
            stm = stim()
            Simulation(rstgen, clkgen, dut, stm).run()
            del rstgen, clkgen, dut, stm



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()