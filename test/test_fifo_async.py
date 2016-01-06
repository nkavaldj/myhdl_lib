import unittest
import itertools

from myhdl import *
from myhdl_lib.fifo_async import fifo_async
import myhdl_lib.simulation as sim


class TestFifoAsync(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def setUp(self):
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 128
        DEPTH_MAX = 101

        self.wfull = Signal(bool(0))
        self.we = Signal(bool(0))
        self.wdata = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX))
        self.rempty = Signal(bool(0))
        self.re = Signal(bool(0))
        self.rdata = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX))

        self.wclk = sim.Clock(val=0, period=7, units="ns")
        self.rclk = sim.Clock(val=0, period=11, units="ns")
        self.wrst = sim.ResetSync(clk=self.wclk, val=0, active=1)
        self.rrst = sim.ResetSync(clk=self.rclk, val=0, active=1)
        self.wclkgen = self.wclk.gen()
        self.rclkgen = self.rclk.gen()

    def tearDown(self):
        pass

    def wreset(self):
        yield self.wrst.pulse(5)

    def rreset(self):
        yield self.rrst.pulse(5)

    def fifo_write(self, val):
        yield self.wclk.posedge
        self.we.next = 1
        self.wdata.next = val
        yield self.wclk.posedge
        self.we.next = 0
        self.wdata.next = 0

    def fifo_read(self):
        yield self.rclk.posedge
        self.re.next = 1
        yield self.rclk.posedge
        self.re.next = 0

    def fifo_state_check(self, WFull, REmpty, RData=None):
        yield delay(1)
        if  WFull is not None:
            assert self.wfull==WFull, "Full: expected={}, detected={}".format(WFull, self.wfull)
        if REmpty is not None:
            assert self.rempty==REmpty,"Empty: expected={}, detected={}".format(REmpty, self.rempty)
        if RData!=None:
            assert self.rdata==RData,"Dout: expected={}, detected={}".format(RData, self.rdata)


    def testEmptyFull(self):
        ''' FIFO_Async: Empty and Full, up and down'''
        DEPTH = [4, 8, 16]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                data_out = itertools.cycle(xrange(128))

                yield self.rreset()
                yield self.wreset()
                yield self.fifo_state_check(WFull=0, REmpty=1)

                for _ in range(5):
                    # Fill up to DEPTH-1
                    do = data_out.next()
                    for i in range(DEPTH-1):
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(WFull=0, REmpty=None, RData=do)
                    # Fill up to DEPTH
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(WFull=1, REmpty=None, RData=do)
                    # Drain down to 1
                    for i in range(DEPTH-1):
                        yield self.fifo_read()
                        yield self.fifo_state_check(WFull=None, REmpty=0, RData=data_out.next())
                    # Drain to 0
                    yield self.fifo_read()
                    yield self.fifo_state_check(WFull=0, REmpty=1)
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    for _ in range(3): yield self.rclk.posedge # Waith for clock domain crossing sync and update of empty
                    yield self.fifo_read()
                    data_out.next()

                yield self.wclk.posedge
                yield self.rclk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut( fifo_async,
                              wrst=self.wrst,
                              rrst=self.rrst,
                              wclk=self.wclk,
                              rclk=self.rclk,
                              wfull=self.wfull,
                              we=self.we,
                              wdata=self.wdata,
                              rempty=self.rempty,
                              re=self.re,
                              rdata=self.rdata,
                              depth=dpt,
                              width=None
                            )
                stm = stim(dpt)
                Simulation(self.wclkgen, self.rclkgen, dut, stm).run()
                del dut, stm


    def testOverflowUnderflow(self):
        ''' FIFO_Async: Does not write when full, does not read when empty'''
        DEPTH = [4, 8, 16]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                data_out = itertools.cycle(xrange(128))

                yield self.rreset()
                yield self.wreset()
                yield self.fifo_state_check(WFull=0, REmpty=1)

                for _ in range(5):
                    # Fill up to DEPTH-1
                    do = data_out.next()
                    for i in range(DEPTH-1):
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(WFull=0, REmpty=None, RData=do)
                    # Fill up to DEPTH
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(WFull=1, REmpty=None, RData=do)
                    # Write when full
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(WFull=1, REmpty=None, RData=do)
                    # Drain down to 1
                    for i in range(DEPTH-1):
                        yield self.fifo_read()
                        yield self.fifo_state_check(WFull=None, REmpty=0, RData=data_out.next())
                    # Drain to 0
                    yield self.fifo_read()
                    yield self.fifo_state_check(WFull=0, REmpty=1)
                    # Read when empty
                    yield self.fifo_read()
                    yield self.fifo_state_check(WFull=0, REmpty=1)
                    data_out.next() # Remove the data written when full
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    for _ in range(3): yield self.rclk.posedge # Waith for clock domain crossing sync and update of empty
                    yield self.fifo_read()
                    data_out.next()

                yield self.wclk.posedge
                yield self.rclk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut( fifo_async,
                              wrst=self.wrst,
                              rrst=self.rrst,
                              wclk=self.wclk,
                              rclk=self.rclk,
                              wfull=self.wfull,
                              we=self.we,
                              wdata=self.wdata,
                              rempty=self.rempty,
                              re=self.re,
                              rdata=self.rdata,
                              depth=dpt,
                              width=None
                            )
                stm = stim(dpt)
                Simulation(self.wclkgen, self.rclkgen, dut, stm).run()
                del dut, stm


    def testDataWidth1(self):
        ''' FIFO_Async: Data width 1'''
        DEPTH = [4, 8, 16]
        self.wdata = Signal(bool(0)) # <-- Bool
        self.rdata = Signal(bool(0)) # <-- Bool

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(2))
                data_out = itertools.cycle(xrange(2))

                yield self.rreset()
                yield self.wreset()
                yield self.fifo_state_check(WFull=0, REmpty=1)

                for _ in range(5):
                    # Fill up to DEPTH-1
                    do = data_out.next()
                    for i in range(DEPTH-1):
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(WFull=0, REmpty=None, RData=do)
                    # Fill up to DEPTH
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(WFull=1, REmpty=None, RData=do)
                    # Drain down to 1
                    for i in range(DEPTH-1):
                        yield self.fifo_read()
                        yield self.fifo_state_check(WFull=None, REmpty=0, RData=data_out.next())
                    # Drain to 0
                    yield self.fifo_read()
                    yield self.fifo_state_check(WFull=0, REmpty=1)
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    for _ in range(3): yield self.rclk.posedge # Waith for clock domain crossing sync and update of empty
                    yield self.fifo_read()
                    data_out.next()

                yield self.wclk.posedge
                yield self.rclk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut( fifo_async,
                              wrst=self.wrst,
                              rrst=self.rrst,
                              wclk=self.wclk,
                              rclk=self.rclk,
                              wfull=self.wfull,
                              we=self.we,
                              wdata=self.wdata,
                              rempty=self.rempty,
                              re=self.re,
                              rdata=self.rdata,
                              depth=dpt,
                              width=None
                            )
                stm = stim(dpt)
                Simulation(self.wclkgen, self.rclkgen, dut, stm).run()
                del dut, stm

    def testDatawidth0(self):
        ''' FIFO_Async: Data width 0 '''
        DEPTH = [4, 8, 16]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                data_out = itertools.cycle(xrange(128))

                yield self.rreset()
                yield self.wreset()
                yield self.fifo_state_check(WFull=0, REmpty=1)

                for _ in range(5):
                    # Fill up to DEPTH-1
                    do = data_out.next()
                    for i in range(DEPTH-1):
                        yield self.fifo_write(data_in.next())
                        yield self.fifo_state_check(WFull=0, REmpty=None, RData=None)
                    # Fill up to DEPTH
                    yield self.fifo_write(data_in.next())
                    yield self.fifo_state_check(WFull=1, REmpty=None, RData=None)
                    # Drain down to 1
                    for i in range(DEPTH-1):
                        yield self.fifo_read()
                        yield self.fifo_state_check(WFull=None, REmpty=0, RData=None)
                    # Drain to 0
                    yield self.fifo_read()
                    yield self.fifo_state_check(WFull=0, REmpty=1)
                    # Write, Read (to move the pointers one step further)
                    yield self.fifo_write(data_in.next())
                    for _ in range(3): yield self.rclk.posedge # Waith for clock domain crossing sync and update of empty
                    yield self.fifo_read()
                    data_out.next()

                yield self.wclk.posedge
                yield self.rclk.posedge

                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                dut = getDut( fifo_async,
                              wrst=self.wrst,
                              rrst=self.rrst,
                              wclk=self.wclk,
                              rclk=self.rclk,
                              wfull=self.wfull,
                              we=self.we,
                              wdata=None, # <-- Not connected
                              rempty=self.rempty,
                              re=self.re,
                              rdata=None, # <-- Not connected
                              depth=dpt,
                              width=None
                            )
                stm = stim(dpt)
                Simulation(self.wclkgen, self.rclkgen, dut, stm).run()
                del dut, stm



if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testFifo']
    unittest.main()
