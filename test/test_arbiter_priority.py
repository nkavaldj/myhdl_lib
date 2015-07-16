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
        sel = Signal(intbv(0, min=0, max=NUM_REQ))

        def stim():
            @instance
            def _inst():
                req_vec.next = 0
                yield delay(10)
                assert 0 == sel, "Select: expected {}, detected {}".format(0, sel)

                for i in range(NUM_REQ):
                    req_vec.next = 1 << i
                    yield delay(10)
                    assert i == sel, "Select: expected {}, detected {}".format(i, sel)

                for i in range(NUM_REQ-1,-1,-1):
                    req_vec.next = 1 << i
                    yield delay(10)
                    assert i == sel, "Select: expected {}, detected {}".format(i, sel)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut = getDut(arbiter_priority, req_vec=req_vec, sel=sel )
            stm = stim()
            Simulation(dut, stm).run()
            del dut, stm


    def testJohnson(self):
        ''' ARBITER_RPIORITY: Johnson requests'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        sel = Signal(intbv(0, min=0, max=NUM_REQ))

        def stim():
            @instance
            def _inst():
                req_vec.next = 0
                yield delay(10)
                assert 0 == sel, "Select: expected {}, detected {}".format(0, sel)

                mask = req_vec.max-1
                for i in range(NUM_REQ):
                    req_vec.next = (mask << i) & mask
                    yield delay(10)
                    assert i == sel, "Select {}: expected {}, detected {}".format(i, i, sel)

                for i in range(NUM_REQ-1,-1,-1):
                    req_vec.next = (req_vec.max-1) >> i
                    yield delay(10)
                    assert 0 == sel, "Select: expected {}, detected {}".format(0, sel)

                yield delay(10)
                raise StopSimulation
            return _inst


        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut = getDut(arbiter_priority, req_vec=req_vec, sel=sel )
            stm = stim()
            Simulation(dut, stm).run()
            del dut, stm


    def testCount(self):
        ''' ARBITER_RPIORITY: Count'''
        NUM_REQ = 5
        req_vec = Signal(intbv(0)[NUM_REQ:])
        sel = Signal(intbv(0, min=0, max=NUM_REQ))

        def stim():
            @instance
            def _inst():
                req_vec.next = 0
                yield delay(10)
                assert 0 == sel, "Select: expected {}, detected {}".format(0, sel)

                x = intbv(0)[NUM_REQ:]
                for i in range(x.max):
                    x[:] = i
                    req_vec.next = x
                    yield delay(10)

                    s = 0
                    for k in range(NUM_REQ):
                        if x[k]==1:
                            s = k
                            break

                    assert s == sel, "Select: expected {}, detected {}".format(s, sel)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut = getDut(arbiter_priority, req_vec=req_vec, sel=sel )
            stm = stim()
            Simulation(dut, stm).run()
            del dut, stm




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()