import unittest
import itertools

from myhdl import *
from myhdl_lib.fifo_speculative import fifo_speculative
from myhdl_lib import sfifo_beh
import myhdl_lib.simulation as sim


class TestSFifo(unittest.TestCase):

    COMMIT = 0
    DISCARD = 1
    DISCARD_COMMIT = 2

    @classmethod
    def setUpClass(cls):
        cls.simulators = ["myhdl", "icarus"]

    def setUp(self):
        DATA_RANGE_MIN = 0
        DATA_RANGE_MAX = 128
        DEPTH_MAX = 101

        self.sfifo_model = None

        self.full = Signal(bool(0))
        self.we = Signal(bool(0))
        self.din = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX))
        self.empty = Signal(bool(0))
        self.re = Signal(bool(0))
        self.dout = Signal(intbv(0, min=DATA_RANGE_MIN, max=DATA_RANGE_MAX))
        self.wr_commit = Signal(bool(0))
        self.wr_discard = Signal(bool(0))
        self.rd_commit = Signal(bool(0))
        self.rd_discard = Signal(bool(0))
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

    def fifo_command(self, wcmd=None, rcmd=None):
        self.sfifo_model.command(wcmd, rcmd)
        self.wr_commit.next = 1 if (wcmd == self.COMMIT  or wcmd == self.DISCARD_COMMIT) else 0
        self.wr_discard.next = 1 if (wcmd == self.DISCARD or wcmd == self.DISCARD_COMMIT) else 0
        self.rd_commit.next = 1 if (rcmd == self.COMMIT  or rcmd == self.DISCARD_COMMIT) else 0
        self.rd_discard.next = 1 if (rcmd == self.DISCARD or rcmd == self.DISCARD_COMMIT) else 0
        yield self.clk.posedge
        self.wr_commit.next = 0
        self.wr_discard.next = 0
        self.rd_commit.next = 0
        self.rd_discard.next = 0

    def fifo_write(self, val, wcmd=None, rcmd=None):
        self.sfifo_model.write(val, wcmd, rcmd)
        self.we.next = 1
        self.din.next = val
        self.wr_commit.next = 1 if (wcmd == self.COMMIT  or wcmd == self.DISCARD_COMMIT) else 0
        self.wr_discard.next = 1 if (wcmd == self.DISCARD or wcmd == self.DISCARD_COMMIT) else 0
        self.rd_commit.next = 1 if (rcmd == self.COMMIT  or rcmd == self.DISCARD_COMMIT) else 0
        self.rd_discard.next = 1 if (rcmd == self.DISCARD or rcmd == self.DISCARD_COMMIT) else 0
        yield self.clk.posedge
        self.we.next = 0
        self.din.next = 0
        self.wr_commit.next = 0
        self.wr_discard.next = 0
        self.rd_commit.next = 0
        self.rd_discard.next = 0

    def fifo_read(self, wcmd=None, rcmd=None):
        self.sfifo_model.read(wcmd, rcmd)
        self.re.next = 1
        self.wr_commit.next = 1 if (wcmd == self.COMMIT  or wcmd == self.DISCARD_COMMIT) else 0
        self.wr_discard.next = 1 if (wcmd == self.DISCARD or wcmd == self.DISCARD_COMMIT) else 0
        self.rd_commit.next = 1 if (rcmd == self.COMMIT  or rcmd == self.DISCARD_COMMIT) else 0
        self.rd_discard.next = 1 if (rcmd == self.DISCARD or rcmd == self.DISCARD_COMMIT) else 0
        yield self.clk.posedge
        self.re.next = 0
        self.wr_commit.next = 0
        self.wr_discard.next = 0
        self.rd_commit.next = 0
        self.rd_discard.next = 0

    def fifo_write_read(self, val, wcmd=None, rcmd=None):
        self.sfifo_model.write_read(val, wcmd, rcmd)
        self.we.next = 1
        self.din.next = val
        self.re.next = 1
        self.wr_commit.next = 1 if (wcmd == self.COMMIT  or wcmd == self.DISCARD_COMMIT) else 0
        self.wr_discard.next = 1 if (wcmd == self.DISCARD or wcmd == self.DISCARD_COMMIT) else 0
        self.rd_commit.next = 1 if (rcmd == self.COMMIT  or rcmd == self.DISCARD_COMMIT) else 0
        self.rd_discard.next = 1 if (rcmd == self.DISCARD or rcmd == self.DISCARD_COMMIT) else 0
        yield self.clk.posedge
        self.re.next = 0
        self.din.next = 0
        self.we.next = 0
        self.wr_commit.next = 0
        self.wr_discard.next = 0
        self.rd_commit.next = 0
        self.rd_discard.next = 0

    def fifo_state_check(self):
        yield delay(1)
        m = self.sfifo_model
        assert m.isFull()==self.full, "Full: expected={}, detected={}".format(m.isFull(), self.full)
        assert m.isEmpty()==self.empty, "Empty: expected={}, detected={}".format(m.isEmpty(), self.empty)
        assert m.isAFull()==self.afull, "AFull: expected={}, detected={}".format(m.isAFull(), self.afull)
        assert m.isAEmpty()==self.aempty, "AEmpty: expected={}, detected={}".format(m.isAEmpty(), self.aempty)
        assert m.getCount()==self.count, "Count: expected={}, detected={}".format(m.getCount(), self.count)
        assert m.getCountMax()==self.count_max, "CountMax: expected={}, detected={}".format(m.getCountMax(), self.count_max)
        assert m.isOvf()==self.ovf, "Overflow: expected={}, detected={}".format(m.isOvf(), self.ovf)
        assert m.isUdf()==self.udf, "Underflow: expected={}, detected={}".format(m.isUdf(), self.udf)
        if (not m.isEmpty() and not self.empty):
            assert m.getDout()==self.dout,"Dout: expected={}, detected={}".format(m.getDout(), self.dout)


    def testWriteThenReadCommitAtEveryOperation(self):
        ''' SFIFO:  Write then Read, Commit at every operation '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                yield self.reset()
                yield self.fifo_state_check()

                for i in range(1,DEPTH+1):
                    # Fill up to i
                    for _ in range(1,i+1):
                        yield self.fifo_write(data_in.next(), wcmd=self.COMMIT)
                        yield self.fifo_state_check()
                    # Drain down to 0
                    for _ in range(1,i+1):
                        yield self.fifo_read(rcmd=self.COMMIT)
                        yield self.fifo_state_check()

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                self.sfifo_model = sfifo_beh.sfifo_beh(dpt)
                dut = getDut( fifo_speculative,
                              rst = self.rst,
                              clk = self.clk,
                              full = self.full,
                              we = self.we,
                              din = self.din,
                              empty = self.empty,
                              re = self.re,
                              dout = self.dout,
                              wr_commit = self.wr_commit,
                              wr_discard = self.wr_discard,
                              rd_commit = self.rd_commit,
                              rd_discard = self.rd_discard,
                              afull = self.afull,
                              aempty = self.aempty,
                              count = self.count,
                              afull_th = None,
                              aempty_th = None,
                              ovf = self.ovf,
                              udf = self.udf,
                              count_max = self.count_max,
                              depth = dpt,
                              width = None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testWriteThenReadCommitAtTheLastOperation(self):
        ''' SFIFO:  Write then Read, Commit at the last operation '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                yield self.reset()
                yield self.fifo_state_check()

                for i in range(1,DEPTH+1):
                    # Fill up to i
                    for w in range(1,i+1):
                        if (w != i):
                            yield self.fifo_write(data_in.next());
                            yield self.fifo_state_check()
                        else:
                            yield self.fifo_write(data_in.next(), wcmd=self.COMMIT)
                            yield self.fifo_state_check()
                    # Drain down to 0
                    for r in range(1,i+1):
                        if (r != i):
                            yield self.fifo_read();
                            yield self.fifo_state_check()
                        else:
                            yield self.fifo_read(rcmd=self.COMMIT)
                            yield self.fifo_state_check()

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                self.sfifo_model = sfifo_beh.sfifo_beh(dpt)
                dut = getDut( fifo_speculative,
                              rst = self.rst,
                              clk = self.clk,
                              full = self.full,
                              we = self.we,
                              din = self.din,
                              empty = self.empty,
                              re = self.re,
                              dout = self.dout,
                              wr_commit = self.wr_commit,
                              wr_discard = self.wr_discard,
                              rd_commit = self.rd_commit,
                              rd_discard = self.rd_discard,
                              afull = self.afull,
                              aempty = self.aempty,
                              count = self.count,
                              afull_th = None,
                              aempty_th = None,
                              ovf = self.ovf,
                              udf = self.udf,
                              count_max = self.count_max,
                              depth = dpt,
                              width = None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testWriteThenReadCommitAfterTheLastOperation(self):
        ''' SFIFO:  Write then Read, Commit after the last operation '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                yield self.reset()
                yield self.fifo_state_check()

                for i in range(1,DEPTH+1):
                    # Fill up to i
                    for _ in range(1,i+1):
                        yield self.fifo_write(data_in.next());
                        yield self.fifo_state_check()
                    self.fifo_command(wcmd=self.COMMIT)
                    yield self.fifo_state_check()
                    # Drain down to 0
                    for _ in range(1,i+1):
                        yield self.fifo_read();
                        yield self.fifo_state_check()
                    self.fifo_command(rcmd=self.COMMIT)
                    yield self.fifo_state_check()

                yield self.clk.posedge
                raise StopSimulation
            return _inst


        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                self.sfifo_model = sfifo_beh.sfifo_beh(dpt)
                dut = getDut( fifo_speculative,
                              rst = self.rst,
                              clk = self.clk,
                              full = self.full,
                              we = self.we,
                              din = self.din,
                              empty = self.empty,
                              re = self.re,
                              dout = self.dout,
                              wr_commit = self.wr_commit,
                              wr_discard = self.wr_discard,
                              rd_commit = self.rd_commit,
                              rd_discard = self.rd_discard,
                              afull = self.afull,
                              aempty = self.aempty,
                              count = self.count,
                              afull_th = None,
                              aempty_th = None,
                              ovf = self.ovf,
                              udf = self.udf,
                              count_max = self.count_max,
                              depth = dpt,
                              width = None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testWriteAndReadCommitAtEveryOperation(self):
        ''' SFIFO:  Write and Read simultaneously, Commit at every operation '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                yield self.reset()
                yield self.fifo_state_check()
                yield self.fifo_write(data_in.next(), wcmd=self.COMMIT)
                yield self.fifo_state_check()

                for i in range(2,DEPTH+1):
                    for _ in range(1,i+1):
                        yield self.fifo_write_read(data_in.next(), wcmd=self.COMMIT, rcmd=self.COMMIT)
                        yield self.fifo_state_check()

                yield self.fifo_read(data_in.next(), rcmd=self.COMMIT)
                yield self.fifo_state_check()

                yield self.clk.posedge
                raise StopSimulation
            return _inst


        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                self.sfifo_model = sfifo_beh.sfifo_beh(dpt)
                dut = getDut( fifo_speculative,
                              rst = self.rst,
                              clk = self.clk,
                              full = self.full,
                              we = self.we,
                              din = self.din,
                              empty = self.empty,
                              re = self.re,
                              dout = self.dout,
                              wr_commit = self.wr_commit,
                              wr_discard = self.wr_discard,
                              rd_commit = self.rd_commit,
                              rd_discard = self.rd_discard,
                              afull = self.afull,
                              aempty = self.aempty,
                              count = self.count,
                              afull_th = None,
                              aempty_th = None,
                              ovf = self.ovf,
                              udf = self.udf,
                              count_max = self.count_max,
                              depth = dpt,
                              width = None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testWriteAndReadCommitAtTheLastOperation(self):
        ''' SFIFO:  Write and Read simultaneously, Commit at the last operation '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                yield self.reset()
                yield self.fifo_state_check()
                yield self.fifo_write(data_in.next(), wcmd=self.COMMIT);
                yield self.fifo_state_check()

                for i in range(2,DEPTH+1):
                    for w in range(1,i+1):
                        if (w != i):
                            yield self.fifo_write_read(data_in.next());
                            yield self.fifo_state_check()
                        else:
                            yield self.fifo_write_read(data_in.next(), wcmd=self.COMMIT, rcmd=self.COMMIT)
                            yield self.fifo_state_check()

                yield self.fifo_read(data_in.next(), rcmd=self.COMMIT);
                yield self.fifo_state_check()

                yield self.clk.posedge
                raise StopSimulation
            return _inst


        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                self.sfifo_model = sfifo_beh.sfifo_beh(dpt)
                dut = getDut( fifo_speculative,
                              rst = self.rst,
                              clk = self.clk,
                              full = self.full,
                              we = self.we,
                              din = self.din,
                              empty = self.empty,
                              re = self.re,
                              dout = self.dout,
                              wr_commit = self.wr_commit,
                              wr_discard = self.wr_discard,
                              rd_commit = self.rd_commit,
                              rd_discard = self.rd_discard,
                              afull = self.afull,
                              aempty = self.aempty,
                              count = self.count,
                              afull_th = None,
                              aempty_th = None,
                              ovf = self.ovf,
                              udf = self.udf,
                              count_max = self.count_max,
                              depth = dpt,
                              width = None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testWriteAndReadCommitAfterTheLastOperation(self):
        ''' SFIFO:  Write and Read simultaneously, Commit after the last operation '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                yield self.reset()
                yield self.fifo_state_check()
                yield self.fifo_write(data_in.next(), wcmd=self.COMMIT);
                yield self.fifo_state_check()

                for i in range(1,DEPTH+1):
                    # Fill up to i
                    for _ in range(1,i+1):
                        yield self.fifo_write(data_in.next());
                        yield self.fifo_state_check()
                    self.fifo_command(wcmd=self.COMMIT)
                    yield self.fifo_state_check()
                    # Drain down to 0
                    for _ in range(1,i+1):
                        yield self.fifo_read();
                        yield self.fifo_state_check()
                    self.fifo_command(rcmd=self.COMMIT)
                    yield self.fifo_state_check()

                yield self.fifo_read(rcmd=self.COMMIT);
                yield self.fifo_state_check()

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                self.sfifo_model = sfifo_beh.sfifo_beh(dpt)
                dut = getDut( fifo_speculative,
                              rst = self.rst,
                              clk = self.clk,
                              full = self.full,
                              we = self.we,
                              din = self.din,
                              empty = self.empty,
                              re = self.re,
                              dout = self.dout,
                              wr_commit = self.wr_commit,
                              wr_discard = self.wr_discard,
                              rd_commit = self.rd_commit,
                              rd_discard = self.rd_discard,
                              afull = self.afull,
                              aempty = self.aempty,
                              count = self.count,
                              afull_th = None,
                              aempty_th = None,
                              ovf = self.ovf,
                              udf = self.udf,
                              count_max = self.count_max,
                              depth = dpt,
                              width = None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testWriteThenReadDiscardAtEveryOperation(self):
        ''' SFIFO:  Write then Read, Discard at every operation '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                yield self.reset()
                yield self.fifo_state_check()

                for i in range(1,DEPTH+1):
                    # Fill up to i and Discard
                    for _ in range(1,i+1):
                        yield self.fifo_write(data_in.next(), wcmd=self.DISCARD)
                        yield self.fifo_state_check()
                    # Fill up to i and Commit
                    for _ in range(1,i+1):
                        yield self.fifo_write(data_in.next(), wcmd=self.COMMIT)
                        yield self.fifo_state_check()
                    # Drain down to 0 and Discard
                    for _ in range(1,i+1):
                        yield self.fifo_read(rcmd=self.DISCARD)
                        yield self.fifo_state_check()
                    # Drain down to 0 and Commit
                    for _ in range(1,i+1):
                        yield self.fifo_read(rcmd=self.COMMIT)
                        yield self.fifo_state_check()

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                self.sfifo_model = sfifo_beh.sfifo_beh(dpt)
                dut = getDut( fifo_speculative,
                              rst = self.rst,
                              clk = self.clk,
                              full = self.full,
                              we = self.we,
                              din = self.din,
                              empty = self.empty,
                              re = self.re,
                              dout = self.dout,
                              wr_commit = self.wr_commit,
                              wr_discard = self.wr_discard,
                              rd_commit = self.rd_commit,
                              rd_discard = self.rd_discard,
                              afull = self.afull,
                              aempty = self.aempty,
                              count = self.count,
                              afull_th = None,
                              aempty_th = None,
                              ovf = self.ovf,
                              udf = self.udf,
                              count_max = self.count_max,
                              depth = dpt,
                              width = None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testWriteThenReadDiscardAtTheLastOperation(self):
        ''' SFIFO:  Write then Read, Discard at the last operation '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                yield self.reset()
                yield self.fifo_state_check()

                for i in range(1,DEPTH+1):
                    # Fill up to i and Discard
                    for w in range(1,i+1):
                        if (w != i):
                            yield self.fifo_write(data_in.next());
                            yield self.fifo_state_check()
                        else:
                            yield self.fifo_write(data_in.next(), wcmd=self.DISCARD)
                            yield self.fifo_state_check()
                    # Fill up to i and Commit
                    for w in range(1,i+1):
                        if (w != i):
                            yield self.fifo_write(data_in.next());
                            yield self.fifo_state_check()
                        else:
                            yield self.fifo_write(data_in.next(), wcmd=self.COMMIT)
                            yield self.fifo_state_check()
                    # Drain down to 0 and Discard
                    for r in range(1,i+1):
                        if (r != i):
                            yield self.fifo_read();
                            yield self.fifo_state_check()
                        else:
                            yield self.fifo_read(rcmd=self.DISCARD)
                            yield self.fifo_state_check()
                    # Drain down to 0 and Commit
                    for r in range(1,i+1):
                        if (r != i):
                            yield self.fifo_read();
                            yield self.fifo_state_check()
                        else:
                            yield self.fifo_read(rcmd=self.COMMIT)
                            yield self.fifo_state_check()

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                self.sfifo_model = sfifo_beh.sfifo_beh(dpt)
                dut = getDut( fifo_speculative,
                              rst = self.rst,
                              clk = self.clk,
                              full = self.full,
                              we = self.we,
                              din = self.din,
                              empty = self.empty,
                              re = self.re,
                              dout = self.dout,
                              wr_commit = self.wr_commit,
                              wr_discard = self.wr_discard,
                              rd_commit = self.rd_commit,
                              rd_discard = self.rd_discard,
                              afull = self.afull,
                              aempty = self.aempty,
                              count = self.count,
                              afull_th = None,
                              aempty_th = None,
                              ovf = self.ovf,
                              udf = self.udf,
                              count_max = self.count_max,
                              depth = dpt,
                              width = None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm


    def testWriteThenReadDiscardAfterTheLastOperation(self):
        ''' SFIFO:  Write then Read, Discard after the last operation '''
        DEPTH = [2, 4, 7, 8, 9, 10]

        def stim(DEPTH):
            @instance
            def _inst():
                data_in = itertools.cycle(xrange(128))
                yield self.reset()
                yield self.fifo_state_check()

                for i in range(1,DEPTH+1):
                    # Fill up to i and Discard
                    for _ in range(1,i+1):
                        yield self.fifo_write(data_in.next());
                        yield self.fifo_state_check()
                    self.fifo_command(wcmd=self.DISCARD)
                    yield self.fifo_state_check()
                    # Fill up to i and Commit
                    for _ in range(1,i+1):
                        yield self.fifo_write(data_in.next());
                        yield self.fifo_state_check()
                    self.fifo_command(wcmd=self.COMMIT)
                    yield self.fifo_state_check()
                    # Drain down to 0 and Discard
                    for _ in range(1,i+1):
                        yield self.fifo_read();
                        yield self.fifo_state_check()
                    self.fifo_command(rcmd=self.DISCARD)
                    yield self.fifo_state_check()
                    # Drain down to 0 and Commit
                    for _ in range(1,i+1):
                        yield self.fifo_read();
                        yield self.fifo_state_check()
                    self.fifo_command(rcmd=self.COMMIT)
                    yield self.fifo_state_check()

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        getDut = sim.DUTer()

        for s in self.simulators:
            getDut.selectSimulator(s)
            for dpt in DEPTH:
                self.sfifo_model = sfifo_beh.sfifo_beh(dpt)
                dut = getDut( fifo_speculative,
                              rst = self.rst,
                              clk = self.clk,
                              full = self.full,
                              we = self.we,
                              din = self.din,
                              empty = self.empty,
                              re = self.re,
                              dout = self.dout,
                              wr_commit = self.wr_commit,
                              wr_discard = self.wr_discard,
                              rd_commit = self.rd_commit,
                              rd_discard = self.rd_discard,
                              afull = self.afull,
                              aempty = self.aempty,
                              count = self.count,
                              afull_th = None,
                              aempty_th = None,
                              ovf = self.ovf,
                              udf = self.udf,
                              count_max = self.count_max,
                              depth = dpt,
                              width = None)
                stm = stim(dpt)
                Simulation(self.clkgen, dut, stm).run()
                del dut, stm



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSFifo']
    unittest.main()
