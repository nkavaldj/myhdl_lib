import unittest
import itertools

from myhdl import *
from myhdl_lib.fifo import fifo
import myhdl_lib.simulation as sim


class TestFifo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def setUp(self):
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 128
        DEPTH_MAX = 101

        self.full = Signal(bool(0))
        self.we = Signal(bool(0))
        self.din = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX))
        self.empty = Signal(bool(0))
        self.re = Signal(bool(0))
        self.dout = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX))
        self.afull = Signal(bool(0))
        self.aempty = Signal(bool(0))
        self.afull_th = Signal(intbv(0, min=0, max=DEPTH_MAX))
        self.aempty_th = Signal(intbv(0, min=0, max=DEPTH_MAX))
        self.count = Signal(intbv(0, min=0, max=DEPTH_MAX))
        self.count_max = Signal(intbv(0, min=0, max=DEPTH_MAX))
        self.ovf = Signal(bool(0))
        self.udf = Signal(bool(0))

        self.clk = sim.Clock(val=0, period=10, units="ns")
        self.rst = sim.ResetSync(clk=self.clk, val=0, active=1)
        self.clkgen = self.clk.gen()


    def tearDown(self):
        pass


    def reset(self):
        yield self.rst.pulse(5)

    def fifo_write(self, val):
        self.we.next = 1
        self.din.next = val
        yield self.clk.posedge
        self.we.next = 0
        self.din.next = 0

    def fifo_read(self):
        self.re.next = 1
        yield self.clk.posedge
        self.re.next = 0

    def fifo_write_read(self,val):
        self.we.next = 1
        self.din.next = val
        self.re.next = 1
        yield self.clk.posedge
        self.re.next = 0
        self.din.next = 0
        self.we.next = 0

    def fifo_state_check(self, aFull, aEmpty, aDout=None, aAlmostFull=None, aAlmostEmpty=None, aCount=None,aCountMax=None, aOverflow=None, aUnderflow=None):
        yield delay(1)
        assert self.full==aFull, "Full: expected={}, detected={}".format(aFull, self.full)
        assert self.empty==aEmpty,"Empty: expected={}, detected={}".format(aEmpty, self.empty)
        if aDout!=None:
            assert self.dout==aDout,"Dout: expected={}, detected={}".format(aDout, self.dout)
        if aAlmostFull!=None:
            assert self.afull==aAlmostFull, "AFull: expected={}, detected={}".format(aAlmostFull, self.afull)
        if aAlmostEmpty!=None:
            assert self.aempty==aAlmostEmpty, "AEmpty: expected={}, detected={}".format(aAlmostEmpty, self.aempty)
        if aCount!=None:
            assert self.count==aCount, "Count: expected={}, detected={}".format(aCount, self.count)
        if aCountMax!=None:
            assert self.count_max==aCountMax, "CountMax: expected={}, detected={}".format(aCountMax, self.count_max)
        if aOverflow!=None:
            assert self.ovf==aOverflow, "Overflow: expected={}, detected={}".format(aOverflow, self.ovf)
        if aUnderflow!=None:
            assert self.udf==aUnderflow, "Underflow: expected={}, detected={}".format(aUnderflow, self.udf)


    def testEmptyFull(self):
        ''' FIFO: Empty and Full, up and down'''
        DEPTH = [1, 2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                data_out = itertools.cycle(xrange(128))

                yield self.reset()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=0, aOverflow=0, aUnderflow=0)

                for _ in range(3):
                    # Fill up to DEPTH-1
                    do = data_out.next()
                    for i in range(DEPTH-1):
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=i+1, aOverflow=0, aUnderflow=0)
                    # Fill up to DEPTH
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(aFull=1, aEmpty=0, aDout=do, aCount=DEPTH, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Drain down to 1
                    for i in range(DEPTH-1):
                        yield self.fifo_read()
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=data_out.next(), aCount=DEPTH-i-1, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Drain to 0
                    yield self.fifo_read()
                    yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_read()
                    data_out.next()

                yield self.clk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut( fifo,
                              rst=self.rst,
                              clk=self.clk,
                              full=self.full,
                              we=self.we,
                              din=self.din,
                              empty=self.empty,
                              re=self.re,
                              dout=self.dout,
                              afull=None,
                              aempty=None,
                              count=self.count,
                              afull_th=None,
                              aempty_th=None,
                              ovf=self.ovf,
                              udf=self.udf,
                              count_max=self.count_max,
                              depth=dpt,
                              width=None
                            )
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testEmptyFull1(self):
        ''' FIFO: Empty and Full, circular (simultaneous Write and Read) '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                data_out = itertools.cycle(xrange(128))

                yield self.reset()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=0, aOverflow=0, aUnderflow=0)

                for _ in range(3):
                    # Fill up to DEPTH-1
                    do = data_out.next()
                    for i in range(DEPTH-1):
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=i+1, aOverflow=0, aUnderflow=0)
                    # Cycle 
                    for _ in range(DEPTH+1):
                        yield self.fifo_write_read(data_in.next())
                        do = data_out.next()
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=DEPTH-1, aOverflow=0, aUnderflow=0)
                    # Fill up to DEPTH
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(aFull=1, aEmpty=0, aDout=do, aCount=DEPTH, aOverflow=0, aUnderflow=0)
                    # Drain down to 1
                    for i in range(DEPTH-1):
                        yield self.fifo_read()
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=data_out.next(), aCount=DEPTH-i-1, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Cycle
                    for _ in range(DEPTH+1):
                        yield self.fifo_write_read(data_in.next())
                        do = data_out.next()
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=1, aOverflow=0, aUnderflow=0)
                    # Drain to 0
                    yield self.fifo_read()
                    yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_read()
                    data_out.next()

                yield self.clk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut(fifo,
                              rst=self.rst,
                              clk=self.clk,
                              full=self.full,
                              we=self.we,
                              din=self.din,
                              empty=self.empty,
                              re=self.re,
                              dout=self.dout,
                              afull=None,
                              aempty=None,
                              count=self.count,
                              afull_th=None,
                              aempty_th=None,
                              ovf=self.ovf,
                              udf=self.udf,
                              count_max=self.count_max,
                              depth=dpt,
                              width=None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testCount(self):
        ''' FIFO: Count and CountMax '''
        DEPTH = [7, 8, 9]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                data_out = itertools.cycle(xrange(128))

                yield self.reset()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=0, aOverflow=0, aUnderflow=0)

                cmax = 0
                for j in range(DEPTH):
                    # Fill up to j
                    do = data_out.next()
                    for i in range(j):
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=i+1, aCountMax=cmax, aOverflow=0, aUnderflow=0)
                    yield self.fifo_write(data_in.next())
                    cmax += 1
                    full = (j+1==DEPTH)
                    yield self.fifo_state_check(aFull=full, aEmpty=0, aDout=do, aCount=j+1, aCountMax=cmax, aOverflow=0, aUnderflow=0)

                    if not full:
                        # Cycle
                        for _ in range(j+1):
                            yield self.fifo_write_read(data_in.next())
                            do = data_out.next()
                            yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=j+1, aCountMax=cmax, aOverflow=0, aUnderflow=0)
                    # Drain down to 0
                    for i in range(j,0,-1):
                        yield self.fifo_read()
                        do = data_out.next()
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=i, aCountMax=cmax, aOverflow=0, aUnderflow=0)
                    yield self.fifo_read()
                    yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=cmax, aOverflow=0, aUnderflow=0)

                yield self.clk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut(fifo,
                              rst=self.rst,
                              clk=self.clk,
                              full=self.full,
                              we=self.we,
                              din=self.din,
                              empty=self.empty,
                              re=self.re,
                              dout=self.dout,
                              afull=None,
                              aempty=None,
                              count=self.count,
                              afull_th=None,
                              aempty_th=None,
                              ovf=self.ovf,
                              udf=self.udf,
                              count_max=self.count_max,
                              depth=dpt, width=None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testOverflowUnderflow(self):
        ''' FIFO: Overflow and Underflow '''
        DEPTH = [1, 2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                data_out = itertools.cycle(xrange(128))

                yield self.reset()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=0, aOverflow=0, aUnderflow=0)

                # Fill up to DEPTH-1
                do = data_out.next()
                for i in range(DEPTH-1):
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=i+1, aOverflow=0, aUnderflow=0)
                # Fill up to DEPTH
                yield self.fifo_write(data_in.next())
                yield self.fifo_state_check(aFull=1, aEmpty=0, aDout=do, aCount=DEPTH, aOverflow=0, aUnderflow=0)
                # Overflow
                for _ in range(2):
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(aFull=1, aEmpty=0, aDout=do, aCount=DEPTH, aCountMax=DEPTH, aOverflow=1, aUnderflow=0)
                # Drain down to 1
                for i in range(DEPTH-1):
                    yield self.fifo_read()
                    yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=data_out.next(), aCount=DEPTH-i-1, aCountMax=DEPTH, aOverflow=1, aUnderflow=0)
                # Drain to 0
                yield self.fifo_read()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=DEPTH, aOverflow=1, aUnderflow=0)
                # Underflow
                for _ in range(2):
                    yield self.fifo_read()
                    yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=DEPTH, aOverflow=1, aUnderflow=1)
                    data_out.next()
                # Write, Read (to move the pointers one step further)
                yield self.fifo_write(data_in.next())
                yield self.fifo_read()
                data_out.next()

                # Fill up to DEPTH-1
                do = data_out.next()
                for i in range(DEPTH-1):
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=i+1, aOverflow=1, aUnderflow=1)
                # Fill up to DEPTH
                yield self.fifo_write(data_in.next())
                yield self.fifo_state_check(aFull=1, aEmpty=0, aDout=do, aCount=DEPTH, aOverflow=1, aUnderflow=1)
                # Overflow
                for _ in range(2):
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(aFull=1, aEmpty=0, aDout=do, aCount=DEPTH, aCountMax=DEPTH, aOverflow=1, aUnderflow=1)
                # Drain down to 1
                for i in range(DEPTH-1):
                    yield self.fifo_read()
                    yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=data_out.next(), aCount=DEPTH-i-1, aCountMax=DEPTH, aOverflow=1, aUnderflow=1)
                # Drain to 0
                yield self.fifo_read()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=DEPTH, aOverflow=1, aUnderflow=1)
                # Underflow
                for _ in range(2):
                    yield self.fifo_read()
                    yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=DEPTH, aOverflow=1, aUnderflow=1)
                    data_out.next()
                # Write, Read (to move the pointers one step further)
                yield self.fifo_write(data_in.next())
                yield self.fifo_read()
                data_out.next()


                yield self.clk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut(fifo,
                             rst=self.rst,
                             clk=self.clk,
                             full=self.full,
                             we=self.we,
                             din=self.din,
                             empty=self.empty,
                             re=self.re,
                             dout=self.dout,
                             afull=None,
                             aempty=None,
                             count=self.count,
                             afull_th=None,
                             aempty_th=None,
                             ovf=self.ovf,
                             udf=self.udf,
                             count_max=self.count_max,
                             depth=dpt,
                             width=None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testAlmostEmptyAlmostFullDefaultThreshold(self):
        ''' FIFO: AlmostEmpty and AlmostFull with default thresholds '''
        DEPTH = [1, 2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            DEFAULTH_THRESHOLD = DEPTH//2
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                data_out = itertools.cycle(xrange(128))

                yield self.reset()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=0, aOverflow=0, aUnderflow=0, aAlmostEmpty=1)

                for _ in range(3):
                    # Fill up to DEPTH
                    do = data_out.next()
                    for i in range(1,DEPTH+1):
                        full = (i==DEPTH)
                        aempty = (i<=DEFAULTH_THRESHOLD)
                        afull = (i>=DEPTH-DEFAULTH_THRESHOLD)
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(aFull=full, aEmpty=0, aDout=do, aCount=i, aAlmostEmpty=aempty, aAlmostFull=afull)
                    # Drain down to 0
                    for i in range(DEPTH-1, -1,-1):
                        aempty = (i<=DEFAULTH_THRESHOLD)
                        afull = (i>=DEPTH-DEFAULTH_THRESHOLD)
                        yield self.fifo_read()
                        if (i!=0):
                            do = data_out.next()
                            yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=i, aAlmostEmpty=aempty, aAlmostFull=afull)
                        else:
                            yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=i, aAlmostEmpty=aempty, aAlmostFull=afull)
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_read()
                    data_out.next()

                yield self.clk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut(fifo,
                              rst=self.rst,
                              clk=self.clk,
                              full=self.full,
                              we=self.we,
                              din=self.din,
                              empty=self.empty,
                              re=self.re,
                              dout=self.dout,
                              afull=self.afull,
                              aempty=self.aempty,
                              count=self.count,
                              afull_th=None,
                              aempty_th=None,
                              ovf=self.ovf,
                              udf=self.udf,
                              count_max=self.count_max,
                              depth=dpt,
                              width=None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testAlmostEmptyAlmostFullConfigureThreshold(self):
        ''' FIFO: AlmostEmpty and AlmostFull with programmed thresholds '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                data_out = itertools.cycle(xrange(128))

                yield self.reset()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=0, aOverflow=0, aUnderflow=0, aAlmostEmpty=1)

                for THRESHOLD in [0, 1, DEPTH//2-1, DEPTH//2+1, DEPTH-1, DEPTH]:
                    AE_THRESHOLD = THRESHOLD
                    AF_THRESHOLD = THRESHOLD
                    self.aempty_th.next = AE_THRESHOLD
                    self.afull_th.next = AF_THRESHOLD
                    yield self.clk.posedge
                    # Fill up to DEPTH
                    do = data_out.next()
                    for i in range(1,DEPTH+1):
                        full = (i==DEPTH)
                        aempty = (i<=AE_THRESHOLD)
                        afull = (i>=DEPTH-AF_THRESHOLD)
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(aFull=full, aEmpty=0, aDout=do, aCount=i, aAlmostEmpty=aempty, aAlmostFull=afull)
                    # Drain down to 0
                    for i in range(DEPTH-1, -1,-1):
                        aempty = (i<=AE_THRESHOLD)
                        afull = (i>=DEPTH-AF_THRESHOLD)
                        yield self.fifo_read()
                        if (i!=0):
                            do = data_out.next()
                            yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=i, aAlmostEmpty=aempty, aAlmostFull=afull)
                        else:
                            yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=i, aAlmostEmpty=aempty, aAlmostFull=afull)
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_read()
                    data_out.next()

                yield self.clk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut(fifo,
                              rst=self.rst,
                              clk=self.clk,
                              full=self.full,
                              we=self.we,
                              din=self.din,
                              empty=self.empty,
                              re=self.re,
                              dout=self.dout,
                              afull=self.afull,
                              aempty=self.aempty,
                              count=self.count,
                              afull_th=self.afull_th,
                              aempty_th=self.aempty_th,
                              ovf=self.ovf,
                              udf=self.udf,
                              count_max=self.count_max,
                              depth=dpt,
                              width=None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()


    def testDataWidth1(self):
        ''' FIFO: Data width 1'''
        DEPTH = [1, 2, 4, 7, 8, 9, 10]
        self.din = Signal(bool(0)) # <-- Bool
        self.dout = Signal(bool(0)) # <-- Bool

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(2))
                data_out = itertools.cycle(xrange(2))

                yield self.reset()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=0, aOverflow=0, aUnderflow=0)

                for _ in range(3):
                    # Fill up to DEPTH-1
                    do = data_out.next()
                    for i in range(DEPTH-1):
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=do, aCount=i+1, aOverflow=0, aUnderflow=0)
                    # Fill up to DEPTH
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(aFull=1, aEmpty=0, aDout=do, aCount=DEPTH, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Drain down to 1
                    for i in range(DEPTH-1):
                        yield self.fifo_read()
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=data_out.next(), aCount=DEPTH-i-1, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Drain to 0
                    yield self.fifo_read()
                    yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_read()
                    data_out.next()

                yield self.clk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut( fifo,
                              rst=self.rst,
                              clk=self.clk,
                              full=self.full,
                              we=self.we,
                              din=self.din,
                              empty=self.empty,
                              re=self.re,
                              dout=self.dout,
                              afull=None,
                              aempty=None,
                              count=self.count,
                              afull_th=None,
                              aempty_th=None,
                              ovf=self.ovf,
                              udf=self.udf,
                              count_max=self.count_max,
                              depth=dpt,
                              width=None
                            )
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testDatawidth0(self):
        ''' FIFO: Data width 0 '''
        DEPTH = [1, 2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(2))
                data_out = itertools.cycle(xrange(2))

                yield self.reset()
                yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=0, aOverflow=0, aUnderflow=0)

                for _ in range(3):
                    # Fill up to DEPTH-1
#                     do = data_out.next()
                    for i in range(DEPTH-1):
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=None, aCount=i+1, aOverflow=0, aUnderflow=0)
                    # Fill up to DEPTH
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(aFull=1, aEmpty=0, aDout=None, aCount=DEPTH, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Drain down to 1
                    for i in range(DEPTH-1):
                        yield self.fifo_read()
                        yield self.fifo_state_check(aFull=0, aEmpty=0, aDout=None, aCount=DEPTH-i-1, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Drain to 0
                    yield self.fifo_read()
                    yield self.fifo_state_check(aFull=0, aEmpty=1, aCount=0, aCountMax=DEPTH, aOverflow=0, aUnderflow=0)
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_read()
                    data_out.next()

                yield self.clk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut( fifo,
                              rst=self.rst,
                              clk=self.clk,
                              full=self.full,
                              we=self.we,
                              din=None, # <-- Not connected
                              empty=self.empty,
                              re=self.re,
                              dout=None, # <-- Not connected
                              afull=None,
                              aempty=None,
                              count=self.count,
                              afull_th=None,
                              aempty_th=None,
                              ovf=self.ovf,
                              udf=self.udf,
                              count_max=self.count_max,
                              depth=dpt,
                              width=None
                            )
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testFifo']
    unittest.main()

