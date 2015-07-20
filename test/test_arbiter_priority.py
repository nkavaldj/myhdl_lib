import unittest

from myhdl import *
from myhdl_lib.arbiter import arbiter_priority
import myhdl_lib.simulation as sim


class TestArbiterPriority(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]


    def testOneHot(self):
        ''' ARBITER_RPIORITY: One Hot requests'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_idx = Signal(intbv(0, min=0, max=NUM_REQ))
        gnt_vld = Signal(bool(0))

        def check(vec, idx, vld):
            assert vec == gnt_vec, "gnt_vec: expected {}, detected {}".format(vec, gnt_vec)
            assert idx == gnt_idx, "gnt_idx: expected {}, detected {}".format(idx, gnt_idx)
            assert vld == gnt_vld, "gnt_vld: expected {}, detected {}".format(vld, gnt_vld)

        def stim():
            @instance
            def _inst():
                req_vec.next = 0
                yield delay(10)
                check(vec=0, idx=0, vld=0)

                for i in range(NUM_REQ):
                    req_vec.next = 1 << i
                    yield delay(10)
                    check(vec=1<<i, idx=i, vld=1)

                for i in range(NUM_REQ-1,-1,-1):
                    req_vec.next = 1 << i
                    yield delay(10)
                    check(vec=1<<i, idx=i, vld=1)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut = getDut(arbiter_priority, req_vec=req_vec, gnt_vec=gnt_vec, gnt_idx=gnt_idx, gnt_vld=gnt_vld)
            stm = stim()
            Simulation(dut, stm).run()
            del dut, stm


    def testJohnson(self):
        ''' ARBITER_RPIORITY: Johnson requests'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_idx = Signal(intbv(0, min=0, max=NUM_REQ))
        gnt_vld = Signal(bool(0))

        def check(vec, idx, vld):
            assert vec == gnt_vec, "gnt_vec: expected {}, detected {}".format(vec, gnt_vec)
            assert idx == gnt_idx, "gnt_idx: expected {}, detected {}".format(idx, gnt_idx)
            assert vld == gnt_vld, "gnt_vld: expected {}, detected {}".format(vld, gnt_vld)

        def stim():
            @instance
            def _inst():
                req_vec.next = 0
                yield delay(10)
                check(vec=0, idx=0, vld=0)

                mask = req_vec.max-1
                for i in range(NUM_REQ):
                    req_vec.next = (mask << i) & mask
                    yield delay(10)
                    check(vec=1<<i, idx=i, vld=1)

                for i in range(NUM_REQ-1,-1,-1):
                    req_vec.next = mask >> i
                    yield delay(10)
                    check(vec=1<<0, idx=0, vld=1)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut = getDut(arbiter_priority, req_vec=req_vec, gnt_vec=gnt_vec, gnt_idx=gnt_idx, gnt_vld=gnt_vld)
            stm = stim()
            Simulation(dut, stm).run()
            del dut, stm


    def testCount(self):
        ''' ARBITER_RPIORITY: Count'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_vec = Signal(intbv(0)[NUM_REQ:])
        gnt_idx = Signal(intbv(0, min=0, max=NUM_REQ))
        gnt_vld = Signal(bool(0))

        def check(vec, idx, vld):
            assert vec == gnt_vec, "gnt_vec: expected {}, detected {}".format(vec, gnt_vec)
            assert idx == gnt_idx, "gnt_idx: expected {}, detected {}".format(idx, gnt_idx)
            assert vld == gnt_vld, "gnt_vld: expected {}, detected {}".format(vld, gnt_vld)

        def stim():
            @instance
            def _inst():
                req_vec.next = 0
                yield delay(10)
                check(vec=0, idx=0, vld=0)

                x = intbv(0)[NUM_REQ:]
                for i in range(x.max):
                    x[:] = i
                    req_vec.next = x
                    yield delay(10)

                    s = 0
                    v = 0
                    for k in range(NUM_REQ):
                        if x[k]==1:
                            s = k
                            v = 1
                            break
                    check(vec=(1<<s)*v, idx=s, vld=v)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut = getDut(arbiter_priority, req_vec=req_vec, gnt_vec=gnt_vec, gnt_idx=gnt_idx, gnt_vld=gnt_vld)
            stm = stim()
            Simulation(dut, stm).run()
            del dut, stm




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()