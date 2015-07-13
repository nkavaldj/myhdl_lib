import unittest

from myhdl import *
from myhdl_lib.handshake import hs_mux
import myhdl_lib.simulation as sim


class TestHSMux(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]


    def testHSMux3(self):
        ''' HS_MUX: 3 inputs '''
        NUM_INPUTS = 3

        def hs_mux_top(sel, i0_rdy, i0_vld, i1_rdy, i1_vld, i2_rdy, i2_vld, o_rdy, o_vld):
            ''' Needed when hs_mux is co-simulated as top level'''

            hsi0_rdy = Signal(bool(0))
            hsi0_vld = Signal(bool(0))
            hsi1_rdy = Signal(bool(0))
            hsi1_vld = Signal(bool(0))
            hsi2_rdy = Signal(bool(0))
            hsi2_vld = Signal(bool(0))
            hso_rdy = Signal(bool(0))
            hso_vld = Signal(bool(0))

            @always_comb
            def _assign():
                i0_rdy.next = hsi0_rdy
                i1_rdy.next = hsi1_rdy
                i2_rdy.next = hsi2_rdy

                hsi0_vld.next = i0_vld
                hsi1_vld.next = i1_vld
                hsi2_vld.next = i2_vld

                hso_rdy.next = o_rdy
                o_vld.next = hso_vld

            ls_hsi = [(hsi0_rdy, hsi0_vld), (hsi1_rdy, hsi1_vld), (hsi2_rdy, hsi2_vld)]
            hso = (hso_rdy, hso_vld)

            _inst = hs_mux(sel=sel, ls_hsi=ls_hsi, hso=hso)

            return instances()

        ls_hsi_rdy = [Signal(bool(0)) for _ in range(NUM_INPUTS)]
        ls_hsi_vld = [Signal(bool(0)) for _ in range(NUM_INPUTS)]
        ls_hsi = zip(ls_hsi_rdy, ls_hsi_vld)

        hso_rdy = Signal(bool(0))
        hso_vld = Signal(bool(0))
        hso = (hso_rdy, hso_vld)

        sel = Signal(intbv(0)[NUM_INPUTS:])

        argl = {"sel":sel,
                "i0_rdy":ls_hsi[0][0], "i0_vld":ls_hsi[0][1],
                "i1_rdy":ls_hsi[1][0], "i1_vld":ls_hsi[1][1],
                "i2_rdy":ls_hsi[2][0], "i2_vld":ls_hsi[2][1],
                "o_rdy":hso[0], "o_vld":hso[1]}

        def stim():
            @instance
            def _inst():
                sel.next = 0
                for i in range(NUM_INPUTS):
                    ls_hsi_vld[i].next = 0
                hso_rdy.next = 0
                yield delay(10)
                for i in range(NUM_INPUTS):
                    assert 0==ls_hsi_rdy[i], "hsi_rdy[{}]: expected {}, detected {}".format(i, 0, ls_hsi_rdy[i])
                assert 0==hso_vld, "hso_vld: expected {}, detected {}".format( 0, hso_vld)

                x = intbv(0)[NUM_INPUTS+1:]
                for s in range(NUM_INPUTS):
                    sel.next = s
                    for i in range(x.max):
                        x[:] = i
                        for k in range(NUM_INPUTS):
                            ls_hsi_vld[k].next = x[k]
                        hso_rdy.next = x[NUM_INPUTS]

                        yield delay(10)

                        for k in range(NUM_INPUTS):
                            if (k==s) and (x[NUM_INPUTS]==1):
                                assert 1==ls_hsi_rdy[k], "hsi_rdy[{}]: expected {}, detected {}".format(k, 1, ls_hsi_rdy[k])
                            else:
                                assert 0==ls_hsi_rdy[k], "hsi_rdy[{}]: expected {}, detected {}".format(k, 0, ls_hsi_rdy[k])

                        if x[s]==1:
                            assert 1==hso_vld, "hso_vld: expected {}, detected {}".format(1, hso_vld)
                        else:
                            assert 0==hso_vld, "hso_vld: expected {}, detected {}".format(0, hso_vld)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)

            dut=getDut(hs_mux_top, **argl)
            stm = stim()
            Simulation( dut, stm).run()
            del dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()