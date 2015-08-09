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
        gnt_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_idx = Signal(intbv(0, min=0, max=NUM_REQ))
        gnt_vld = Signal(bool(0))
        gnt_rdy = Signal(bool(0))

        clk = sim.Clock(val=0, period=10, units="ns")
        rst = sim.ResetSync(clk=clk, val=0, active=1)

        def check(vec, idx, vld):
            assert vec == gnt_vec, "gnt_vec: expected {}, detected {}".format(vec, gnt_vec)
            assert idx == gnt_idx, "gnt_idx: expected {}, detected {}".format(idx, gnt_idx)
            assert vld == gnt_vld, "gnt_vld: expected {}, detected {}".format(vld, gnt_vld)

        def stim():
            @instance
            def _inst():
                gnt_rdy.next = 0
                req_vec.next = 0
                yield rst.pulse(10)
                check(vec=0, idx=0, vld=0)

                gnt_rdy.next = 1
                for _ in range(3):
                    for i in range(NUM_REQ):
                        req_vec.next = 1 << i
                        yield delay(1)
                        check(vec=1<<i, idx=i, vld=1)
                        yield clk.posedge

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            clkgen = clk.gen()
            dut = getDut(arbiter_roundrobin, rst=rst, clk=clk, req_vec=req_vec, gnt_vec=gnt_vec, gnt_idx=gnt_idx, gnt_vld=gnt_vld, gnt_rdy=gnt_rdy)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del clkgen, dut, stm


    def testCount(self):
        ''' ARBITER_ROUNDROBIN: Count '''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_idx = Signal(intbv(0, min=0, max=NUM_REQ))
        gnt_vld = Signal(bool(0))
        gnt_rdy = Signal(bool(0))

        clk = sim.Clock(val=0, period=10, units="ns")
        rst = sim.ResetSync(clk=clk, val=0, active=1)

        def check(vec, idx, vld):
            assert vec == gnt_vec, "gnt_vec: expected {}, detected {}".format(vec, gnt_vec)
            assert idx == gnt_idx, "gnt_idx: expected {}, detected {}".format(idx, gnt_idx)
            assert vld == gnt_vld, "gnt_vld: expected {}, detected {}".format(vld, gnt_vld)

        def stim():
            @instance
            def _inst():
                gnt_rdy.next = 0
                req_vec.next = 0
                yield rst.pulse(10)
                yield clk.posedge
                check(vec=0, idx=0, vld=0)

                gnt_rdy.next = 1
                prio = NUM_REQ-1
                x = intbv(0)[NUM_REQ:]
                for i in range(x.max):
                    x[:] = i
                    req_vec.next = x
                    s = 0
                    v = 0
                    for k in range(NUM_REQ):
                        kk = (prio + k + 1)%NUM_REQ
                        if x[kk]==1:
                            s = kk
                            v = 1
                            break

                    yield delay(1)
                    check(vec=(1<<s)*v, idx=s, vld=v)

                    yield clk.posedge

                    if gnt_rdy==1:
                            prio = s

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            clkgen = clk.gen()
            dut = getDut(arbiter_roundrobin, rst=rst, clk=clk, req_vec=req_vec, gnt_vec=gnt_vec, gnt_idx=gnt_idx, gnt_vld=gnt_vld, gnt_rdy=gnt_rdy)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del clkgen, dut, stm


    def testAll(self):
        ''' ARBITER_ROUNDROBIN: All requests'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_idx = Signal(intbv(0, min=0, max=NUM_REQ))
        gnt_vld = Signal(bool(0))
        gnt_rdy = Signal(bool(0))

        clk = sim.Clock(val=0, period=10, units="ns")
        rst = sim.ResetSync(clk=clk, val=0, active=1)

        def check(vec, idx, vld):
            assert vec == gnt_vec, "gnt_vec: expected {}, detected {}".format(vec, gnt_vec)
            assert idx == gnt_idx, "gnt_idx: expected {}, detected {}".format(idx, gnt_idx)
            assert vld == gnt_vld, "gnt_vld: expected {}, detected {}".format(vld, gnt_vld)

        def stim():
            @instance
            def _inst():
                gnt_rdy.next = 0
                req_vec.next = 0
                yield rst.pulse(10)
                check(vec=0, idx=0, vld=0)

                mask = req_vec.max-1
                req_vec.next = mask
                gnt_rdy.next = 1
                for _ in range(3):
                    for i in range(NUM_REQ):
                        yield delay(1)
                        check(vec=1<<i, idx=i, vld=1)
                        yield clk.posedge

                yield clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            clkgen = clk.gen()
            dut = getDut(arbiter_roundrobin, rst=rst, clk=clk, req_vec=req_vec, gnt_vec=gnt_vec, gnt_idx=gnt_idx, gnt_vld=gnt_vld, gnt_rdy=gnt_rdy)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del clkgen, dut, stm


    def testAllDummy(self):
        ''' ARBITER_ROUNDROBIN: All requests, dummy strobe'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_idx = Signal(intbv(0, min=0, max=NUM_REQ))
        gnt_vld = Signal(bool(0))
        gnt_rdy = Signal(bool(0))

        clk = sim.Clock(val=0, period=10, units="ns")
        rst = sim.ResetSync(clk=clk, val=0, active=1)

        def check(vec, idx, vld):
            assert vec == gnt_vec, "gnt_vec: expected {}, detected {}".format(vec, gnt_vec)
            assert idx == gnt_idx, "gnt_idx: expected {}, detected {}".format(idx, gnt_idx)
            assert vld == gnt_vld, "gnt_vld: expected {}, detected {}".format(vld, gnt_vld)

        def stim():
            @instance
            def _inst():
                gnt_rdy.next = 0
                req_vec.next = 0
                yield rst.pulse(10)
                check(vec=0, idx=0, vld=0)

                mask = req_vec.max-1
                req_vec.next = mask
                gnt_rdy.next = 1
                for _ in range(3):
                    for i in range(NUM_REQ):
                        # gnt_vld & gnt_rdy
                        req_vec.next = mask
                        yield delay(1)
                        check(vec=1<<i, idx=i, vld=1)
                        yield clk.posedge
                        # /gnt_vld & gnt_rdy
                        req_vec.next = 0
                        yield delay(1)
                        check(vec=0, idx=0, vld=0)
                        yield clk.posedge

                yield clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            clkgen = clk.gen()
            dut = getDut(arbiter_roundrobin, rst=rst, clk=clk, req_vec=req_vec, gnt_vec=gnt_vec, gnt_idx=gnt_idx, gnt_vld=gnt_vld, gnt_rdy=gnt_rdy)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del clkgen, dut, stm

    def testAllGap(self):
        ''' ARBITER_ROUNDROBIN: All requests, gappy strobe'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_idx = Signal(intbv(0, min=0, max=NUM_REQ))
        gnt_vld = Signal(bool(0))
        gnt_rdy = Signal(bool(0))

        clk = sim.Clock(val=0, period=10, units="ns")
        rst = sim.ResetSync(clk=clk, val=0, active=1)

        def check(vec, idx, vld):
            assert vec == gnt_vec, "gnt_vec: expected {}, detected {}".format(vec, gnt_vec)
            assert idx == gnt_idx, "gnt_idx: expected {}, detected {}".format(idx, gnt_idx)
            assert vld == gnt_vld, "gnt_vld: expected {}, detected {}".format(vld, gnt_vld)

        def stim():
            @instance
            def _inst():
                gnt_rdy.next = 0
                req_vec.next = 0
                yield rst.pulse(10)
                yield clk.posedge
                check(vec=0, idx=0, vld=0)

                mask = req_vec.max-1
                req_vec.next = mask
                for i in range(NUM_REQ):
                    for _ in range(3):
                        yield delay(1)
                        check(vec=1<<i, idx=i, vld=1)
                        gnt_rdy.next = 0
                        yield clk.posedge
                    else:
                        yield delay(1)
                        check(vec=1<<i, idx=i, vld=1)
                        gnt_rdy.next = 1
                        yield clk.posedge

                yield clk.posedge
                gnt_rdy.next = 0
                yield clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            clkgen = clk.gen()
            dut = getDut(arbiter_roundrobin, rst=rst, clk=clk, req_vec=req_vec, gnt_vec=gnt_vec, gnt_idx=gnt_idx, gnt_vld=gnt_vld, gnt_rdy=gnt_rdy)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del clkgen, dut, stm



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()