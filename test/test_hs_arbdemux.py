import unittest

from myhdl import *
from myhdl_lib.handshake import hs_arbdemux
import myhdl_lib.simulation as sim
from myhdl_lib.utils import assign



class TestArbDemux(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    @staticmethod
    def hs_arbdemux_top(rst, clk, i_rdy, i_vld, o0_rdy, o0_vld, o1_rdy, o1_vld, o2_rdy, o2_vld, sel, ARBITER_TYPE):
        ''' Needed when hs_arbdemux is co-simulated as top level'''

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

        _inst = hs_arbdemux(clk=clk, rst=rst, hsi=hsi, ls_hso=ls_hso, sel=sel, ARBITER_TYPE=ARBITER_TYPE)

        return instances()


    def testArbDemux3Prio(self):
        ''' HS_ARBDEMUX: 3 outputs, priority arbiter '''
        NUM_OUTPUTS = 3

        hsi_rdy = Signal(bool(0))
        hsi_vld = Signal(bool(0))
        hsi = (hsi_rdy, hsi_vld)

        ls_hso_rdy = [Signal(bool(0)) for _ in range(NUM_OUTPUTS)]
        ls_hso_vld = [Signal(bool(0)) for _ in range(NUM_OUTPUTS)]
        ls_hso = zip(ls_hso_rdy, ls_hso_vld)

        sel = Signal(intbv(0)[NUM_OUTPUTS:])

        clk = sim.Clock(val=0, period=10, units="ns")
        rst = sim.ResetSync(clk=clk, val=0, active=1)

        argl = {"rst":None, "clk":None,
                "i_rdy":hsi[0], "i_vld":hsi[1],
                "o0_rdy":ls_hso[0][0], "o0_vld":ls_hso[0][1],
                "o1_rdy":ls_hso[1][0], "o1_vld":ls_hso[1][1],
                "o2_rdy":ls_hso[2][0], "o2_vld":ls_hso[2][1],
                "sel":sel, "ARBITER_TYPE":"priority"}

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

                    s = 0
                    for i in range(NUM_OUTPUTS):
                        if x[i]==1:
                            s = i
                            break

                    assert s==sel, "sel: expecte {}, dectected {}".format(s, sel)

                    for k in range(NUM_OUTPUTS):
                        if (s==k) and (x[NUM_OUTPUTS]==1):
                            assert 1==ls_hso_vld[k], "hso_vld[{}]: expected {}, detected {}".format(k, 1, ls_hso_vld[k])
                        else:
                            assert 0==ls_hso_vld[k], "hso_vld[{}]: expected {}, detected {}".format(k, 0, ls_hso_vld[k])

                    if x[s]==1:
                        assert 1==hsi_rdy, "hsi_rdy: expected {}, detected {}".format(1, hsi_rdy)
                    else:
                        assert 0==hsi_rdy, "hsi_rdy: expected {}, detected {}".format(0, hsi_rdy)

                yield delay(10)
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut=getDut(self.hs_arbdemux_top, **argl)
            clkgen = clk.gen()
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del clkgen, dut, stm


    def testArbDemux3RR(self):
        ''' HS_ARBDEMUX: 3 outputs, roundrobin arbiter '''
        NUM_OUTPUTS = 3

        hsi_rdy = Signal(bool(0))
        hsi_vld = Signal(bool(0))
        hsi = (hsi_rdy, hsi_vld)

        ls_hso_rdy = [Signal(bool(0)) for _ in range(NUM_OUTPUTS)]
        ls_hso_vld = [Signal(bool(0)) for _ in range(NUM_OUTPUTS)]
        ls_hso = zip(ls_hso_rdy, ls_hso_vld)

        sel = Signal(intbv(0)[NUM_OUTPUTS:])

        clk = sim.Clock(val=0, period=10, units="ns")
        rst = sim.ResetSync(clk=clk, val=0, active=1)

        argl = {"rst":rst, "clk":clk,
                "i_rdy":hsi[0], "i_vld":hsi[1],
                "o0_rdy":ls_hso[0][0], "o0_vld":ls_hso[0][1],
                "o1_rdy":ls_hso[1][0], "o1_vld":ls_hso[1][1],
                "o2_rdy":ls_hso[2][0], "o2_vld":ls_hso[2][1],
                "sel":sel, "ARBITER_TYPE":"roundrobin"}

        def stim():
            @instance
            def _inst():
                for i in range(NUM_OUTPUTS):
                    ls_hso_rdy[i].next = 0
                hsi_vld.next = 0
                yield rst.pulse(10)
                yield clk.posedge
                for i in range(NUM_OUTPUTS):
                    assert 0==ls_hso_vld[i], "hso_vld[{}]: expected {}, detected {}".format(i, 0, ls_hso_vld[i])
                assert 0==hsi_rdy, "hsi_rdy: expected {}, detected {}".format( 0, hsi_rdy)

                prio = NUM_OUTPUTS-1
                x = intbv(0)[NUM_OUTPUTS+1:]
                for i in range(x.max):
                    x[:] = i
                    for k in range(NUM_OUTPUTS):
                        ls_hso_rdy[k].next = x[k]
                    hsi_vld.next = x[NUM_OUTPUTS]

                    yield clk.posedge

                    s = 0
                    for p in range(NUM_OUTPUTS):
                        j = (prio+p+1)%NUM_OUTPUTS
                        if x[j]==1:
                            s = j
                            if hsi_rdy and hsi_vld:
                                prio = j
                            break

                    assert s==sel, "sel: expecte {}, dectected {}".format(s, sel)

                    for k in range(NUM_OUTPUTS):
                        if (s==k) and (x[NUM_OUTPUTS]==1):
                            assert 1==ls_hso_vld[k], "hso_vld[{}]: expected {}, detected {}".format(k, 1, ls_hso_vld[k])
                        else:
                            assert 0==ls_hso_vld[k], "hso_vld[{}]: expected {}, detected {}".format(k, 0, ls_hso_vld[k])

                    if x[s]==1:
                        assert 1==hsi_rdy, "hsi_rdy: expected {}, detected {}".format(1, hsi_rdy)
                    else:
                        assert 0==hsi_rdy, "hsi_rdy: expected {}, detected {}".format(0, hsi_rdy)

                yield clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            dut=getDut(self.hs_arbdemux_top, **argl)
            clkgen = clk.gen()
            stm = stim()
            Simulation(clkgen, dut, stm).run()
            del clkgen, dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()