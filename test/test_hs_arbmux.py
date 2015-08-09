import unittest

from myhdl import *
from myhdl_lib.handshake import hs_arbmux
import myhdl_lib.simulation as sim


class TestArbMux(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    @staticmethod
    def hs_arbmux_top(rst, clk, i0_rdy, i0_vld, i1_rdy, i1_vld, i2_rdy, i2_vld, o_rdy, o_vld, sel, ARBITER_TYPE):
        ''' Needed when hs_arbmux is co-simulated as top level'''

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

        _inst = hs_arbmux(rst=rst, clk=clk, ls_hsi=ls_hsi, hso=hso, sel=sel, ARBITER_TYPE=ARBITER_TYPE)

        return instances()

    def testArbMux3Prio(self):
        "HS_ARBMUX: 3 inputs, priority arbiter"

        NUM_INPUTS = 3

        ls_hsi_rdy = [Signal(bool(0)) for _ in range(NUM_INPUTS)]
        ls_hsi_vld = [Signal(bool(0)) for _ in range(NUM_INPUTS)]
        ls_hsi = zip(ls_hsi_rdy, ls_hsi_vld)

        hso_rdy = Signal(bool(0))
        hso_vld = Signal(bool(0))
        hso = (hso_rdy, hso_vld)

        sel = Signal(intbv(0)[NUM_INPUTS:])

        clk = sim.Clock(val=0, period=10, units="ns")
        rst = sim.ResetSync(clk=clk, val=0, active=1)

        argl = {"rst":None, "clk":None,
                "i0_rdy":ls_hsi[0][0], "i0_vld":ls_hsi[0][1],
                "i1_rdy":ls_hsi[1][0], "i1_vld":ls_hsi[1][1],
                "i2_rdy":ls_hsi[2][0], "i2_vld":ls_hsi[2][1],
                "o_rdy":hso[0], "o_vld":hso[1], "sel":sel, "ARBITER_TYPE":"priority"}

        def stim():
            @instance
            def _inst():
                for i in range(NUM_INPUTS):
                    ls_hsi_vld[i].next = 0
                hso_rdy.next = 0
                yield delay(10)
                for i in range(NUM_INPUTS):
                    assert 0==ls_hsi_rdy[i], "hsi_rdy[{}]: expected {}, detected {}".format(i, 0, ls_hsi_rdy[i])
                assert 0==hso_vld, "hso_vld: expected {}, detected {}".format( 0, hso_vld)
                assert 0==sel, "sel: expected {}, detected {}".format( 0, sel)

                x = intbv(0)[NUM_INPUTS+1:]
                for i in range(x.max):
                    x[:] = i
                    for k in range(NUM_INPUTS):
                        ls_hsi_vld[k].next = x[k]
                    hso_rdy.next = x[NUM_INPUTS]

                    yield delay(10)

                    s = 0
                    for i in range(NUM_INPUTS):
                        if x[i]==1:
                            s = i
                            break

                    assert s==sel, "sel: expecte {}, dectected {}".format(s, sel)

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
            clkgen = clk.gen()

            dut=getDut(self.hs_arbmux_top, **argl)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del clkgen, dut, stm


    def testArbMux3RR(self):
        "HS_ARBMUX: 3 inputs, roundrobin arbiter"

        NUM_INPUTS = 3

        ls_hsi_rdy = [Signal(bool(0)) for _ in range(NUM_INPUTS)]
        ls_hsi_vld = [Signal(bool(0)) for _ in range(NUM_INPUTS)]
        ls_hsi = zip(ls_hsi_rdy, ls_hsi_vld)

        hso_rdy = Signal(bool(0))
        hso_vld = Signal(bool(0))
        hso = (hso_rdy, hso_vld)

        sel = Signal(intbv(0)[NUM_INPUTS:])

        clk = sim.Clock(val=0, period=10, units="ns")
        rst = sim.ResetSync(clk=clk, val=0, active=1)

        argl = {"rst":rst, "clk":clk,
                "i0_rdy":ls_hsi[0][0], "i0_vld":ls_hsi[0][1],
                "i1_rdy":ls_hsi[1][0], "i1_vld":ls_hsi[1][1],
                "i2_rdy":ls_hsi[2][0], "i2_vld":ls_hsi[2][1],
                "o_rdy":hso[0], "o_vld":hso[1], "sel":sel, "ARBITER_TYPE":"roundrobin"}

        def stim():
            @instance
            def _inst():
                for i in range(NUM_INPUTS):
                    ls_hsi_vld[i].next = 0
                hso_rdy.next = 0
                yield rst.pulse(10)
                yield clk.posedge
                for i in range(NUM_INPUTS):
                    assert 0==ls_hsi_rdy[i], "hsi_rdy[{}]: expected {}, detected {}".format(i, 0, ls_hsi_rdy[i])
                assert 0==hso_vld, "hso_vld: expected {}, detected {}".format( 0, hso_vld)
                assert 0==sel, "sel: expected {}, detected {}".format( 0, sel)

                prio = NUM_INPUTS-1
                x = intbv(0)[NUM_INPUTS+1:]
                for i in range(x.max):
                    x[:] = i
                    for k in range(NUM_INPUTS):
                        ls_hsi_vld[k].next = x[k]
                    hso_rdy.next = x[NUM_INPUTS]

                    yield clk.posedge

                    s = 0
                    for p in range(NUM_INPUTS):
                        j = (prio+p+1)%NUM_INPUTS
                        if x[j]==1:
                            s = j
                            if hso_rdy and hso_vld:
                                prio = j
                            break

                    assert s==sel, "sel: expecte {}, dectected {}".format(s, sel)

                    for k in range(NUM_INPUTS):
                        if (k==s) and (x[NUM_INPUTS]==1):
                            assert 1==ls_hsi_rdy[k], "hsi_rdy[{}]: expected {}, detected {}".format(k, 1, ls_hsi_rdy[k])
                        else:
                            assert 0==ls_hsi_rdy[k], "hsi_rdy[{}]: expected {}, detected {}".format(k, 0, ls_hsi_rdy[k])

                    if x[s]==1:
                        assert 1==hso_vld, "hso_vld: expected {}, detected {}".format(1, hso_vld)
                    else:
                        assert 0==hso_vld, "hso_vld: expected {}, detected {}".format(0, hso_vld)

                yield clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            clkgen = clk.gen()

            dut=getDut(self.hs_arbmux_top, **argl)
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del clkgen, dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()