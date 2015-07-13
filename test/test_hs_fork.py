import unittest

from myhdl import *
from myhdl_lib.handshake import hs_fork
import myhdl_lib.simulation as sim

class TestHSFork(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def testHSFork3(self):
        ''' HS_FORK: 3 outputs '''
        NUM_OUTPUTS = 3

        def hs_fork_top(i_rdy, i_vld, o0_rdy, o0_vld, o1_rdy, o1_vld, o2_rdy, o2_vld):
            ''' Needed when hs_fork is co-simulated as top level'''

            hsi_rdy = Signal(bool(0))
            hsi_vld = Signal(bool(0))
            hso0_rdy = Signal(bool(0))
            hso0_vld = Signal(bool(0))
            hso1_rdy = Signal(bool(0))
            hso1_vld = Signal(bool(0))
            hso2_rdy = Signal(bool(0))
            hso2_vld = Signal(bool(0))

            @always_comb
            def _assign():
                hso0_rdy.next = o0_rdy
                hso1_rdy.next = o1_rdy
                hso2_rdy.next = o2_rdy

                o0_vld.next = hso0_vld
                o1_vld.next = hso1_vld
                o2_vld.next = hso2_vld

                i_rdy.next = hsi_rdy
                hsi_vld.next = i_vld

            hsi = (hsi_rdy, hsi_vld)
            ls_hso = [(hso0_rdy, hso0_vld), (hso1_rdy, hso1_vld), (hso2_rdy, hso2_vld)]

            _inst = hs_fork(hsi=hsi, ls_hso=ls_hso)

            return instances()

        hsi_rdy = Signal(bool(0))
        hsi_vld = Signal(bool(0))
        hsi = (hsi_rdy, hsi_vld)

        ls_hso_rdy = [Signal(bool(0)) for _ in range(NUM_OUTPUTS)]
        ls_hso_vld = [Signal(bool(0)) for _ in range(NUM_OUTPUTS)]
        ls_hso = zip(ls_hso_rdy, ls_hso_vld)

        argl = {"i_rdy":hsi[0], "i_vld":hsi[1],
                "o0_rdy":ls_hso[0][0], "o0_vld":ls_hso[0][1],
                "o1_rdy":ls_hso[1][0], "o1_vld":ls_hso[1][1],
                "o2_rdy":ls_hso[2][0], "o2_vld":ls_hso[2][1]}

        def stim():
            @instance
            def _inst():
                for i in range(NUM_OUTPUTS):
                    ls_hso_rdy[i].next = 0
                hsi_vld.next = 0
                yield delay(10)
                for i in range(NUM_OUTPUTS):
                    assert 0==ls_hso_vld[i], "hso_vld[{}]: expected {}, detected {}".format(i, 0, ls_hso_vld[i])
                assert 0==hsi_rdy, "hsi_rdy: expected {}, detected {}".format( 0, hsi_rdy)

                x = intbv(0)[NUM_OUTPUTS+1:]
                for i in range(x.max):
                    x[:] = i
                    for k in range(NUM_OUTPUTS):
                        ls_hso_rdy[k].next = x[k]
                    hsi_vld.next = x[NUM_OUTPUTS]

                    yield delay(10)

                    if i==x.max-1:
                        for k in range(NUM_OUTPUTS):
                            assert 1==ls_hso_vld[k], "hso_vld[{}]: expected {}, detected {}".format(k, 1, ls_hso_vld[k])
                    else:
                        for k in range(NUM_OUTPUTS):
                            assert 0==ls_hso_vld[k], "hso_vld[{}]: expected {}, detected {}".format(k, 0, ls_hso_vld[k])

                    if (i==x.max-1) or (i==x.max/2-1):
                        assert 1==hsi_rdy, "hsi_rdy: expected {}, detected {}".format(1, hsi_rdy)
                    else:
                        assert 0==hsi_rdy, "hsi_rdy: expected {}, detected {}".format(0, hsi_rdy)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(hs_fork_top, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()