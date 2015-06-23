import unittest

from myhdl import *
from myhdl_lib.pipeline_control import pipeline_control

def clock_generator(clk, PERIOD):
    @always(delay(PERIOD//2))
    def _clkgen():
        clk.next = not clk
    return _clkgen

class TestPipelineControl(unittest.TestCase):


    def setUp(self):
        self.rst = ResetSignal(val=0, active=1, async=False)
        self.clk = Signal(bool(0))
        self.clkgen = clock_generator(self.clk, PERIOD=10)

        self.rx_rdy = Signal(bool(0))
        self.rx_vld = Signal(bool(0))
        self.tx_rdy = Signal(bool(0))
        self.tx_vld = Signal(bool(0))


    def tearDown(self):
        pass

    def reset(self):
        self.rst.next = 1
        for _ in range (5): 
            yield self.clk.posedge 
        self.rst.next = 0

    def pipe_state_check(self, rx_rdy, tx_vld, stage_en):
        yield delay(1)
        assert rx_rdy==self.rx_rdy, "RX_VLD: expected {}, detected {}".format(rx_rdy, self.rx_rdy)
        assert tx_vld==self.tx_vld, "TX_VLD: expected {}, detected {}".format(tx_vld, self.tx_vld)
        assert stage_en==self.en, "STAGE_EN: expected {}, detected {}".format(bin(stage_en), bin(self.en))

    def pipe_drive(self, rx_vld, tx_rdy, stop_rx, stop_tx):
        self.rx_vld.next = rx_vld
        self.tx_rdy.next = tx_rdy
        self.stop_rx.next = stop_rx
        self.stop_tx.next = stop_tx
        yield self.clk.posedge
        self.rx_vld.next = 0
        self.tx_rdy.next = 0
        self.stop_rx.next = 0
        self.stop_tx.next = 0

    def testSingleWrite(self):
        ''' PIPE_CTRL: Single data '''
        DEPTH = [1,2,3,7,8,9]

        def stim(DEPTH):
            @instance
            def _inst():
                yield self.reset()
                yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                yield self.clk.posedge

                for _ in range(3):
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                    self.rx_vld.next = 1
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=1)
                    yield self.clk.posedge
                    self.rx_vld.next = 0
                    for i in range(1,DEPTH):
                        yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=1<<i)
                        yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=0, tx_vld=1, stage_en=0)
                    yield self.clk.posedge
                    self.tx_rdy.next = 1
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=1, stage_en=0)
                    yield self.clk.posedge
                    self.tx_rdy.next = 0
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                    yield self.clk.posedge

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        for dpt in DEPTH:
            self.stop_rx = Signal(intbv(0)[dpt:])
            self.stop_tx = Signal(intbv(0)[dpt:])

            self.en = Signal(intbv(0)[dpt:])

            dut = pipeline_control(self.rst, self.clk, self.rx_rdy, self.rx_vld, self.tx_rdy, self.tx_vld, self.en, stop_rx=None, stop_tx=None)
            stm = stim(dpt)
            Simulation(self.clkgen, dut, stm).run()


    def testContinuousWrite(self):
        ''' PIPE_CTRL: Continuous data '''
        DEPTH = [1,2,3,7,8,9]

        def stim(DEPTH):
            @instance
            def _inst():
                yield self.reset()
                yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                yield self.clk.posedge

                for _ in range(3):
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                    self.rx_vld.next = 1
                    for i in range(1,DEPTH+1):
                        yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=2**i-1)
                        yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=0, tx_vld=1, stage_en=0)
                    self.rx_vld.next = 0
                    yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=0, tx_vld=1, stage_en=0)
                    self.tx_rdy.next = 1
                    for i in range(1,DEPTH+1):
                        yield self.pipe_state_check(rx_rdy=1, tx_vld=1, stage_en=(2**DEPTH-1)-(2**i-1))
                        yield self.clk.posedge
                    self.tx_rdy.next = 0
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                    yield self.clk.posedge

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        for dpt in DEPTH:
            self.stop_rx = Signal(intbv(0)[dpt:])
            self.stop_tx = Signal(intbv(0)[dpt:])

            self.en = Signal(intbv(0)[dpt:])

            dut = pipeline_control(self.rst, self.clk, self.rx_rdy, self.rx_vld, self.tx_rdy, self.tx_vld, self.en, stop_rx=None, stop_tx=None)
            stm = stim(dpt)
            Simulation(self.clkgen, dut, stm).run()


    def testStopRX(self):
        ''' PIPE_CTRL: Stop RX '''
        DEPTH = [1,2,3,7,8,9]

        def stim(DEPTH):
            @instance
            def _inst():
                yield self.reset()
                yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                yield self.clk.posedge

                yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)

                for i in range(DEPTH):
                    # Stage i does not need input data, runs without waiting for stage i-1, and generates data to stage i+1
                    self.stop_rx.next = 1<<i
                    for j in range(i,DEPTH):
                        yield self.pipe_state_check(rx_rdy=0, tx_vld=0, stage_en=(2**(j+1)-1)-(2**i-1))
                        yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=0, tx_vld=1, stage_en=0)
                    self.stop_rx.next = 0
                    yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=0, tx_vld=1, stage_en=0)
                    self.tx_rdy.next = 1
                    # Drain the pipeline
                    for j in range(i,DEPTH):
                        yield self.pipe_state_check(rx_rdy=1, tx_vld=1, stage_en=(2**DEPTH-1)-(2**(j+1)-1))
                        yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                    self.tx_rdy.next = 0
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                    yield self.clk.posedge

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        for dpt in DEPTH:
            self.stop_rx = Signal(intbv(0)[dpt:])
            self.stop_tx = Signal(intbv(0)[dpt:])

            self.en = Signal(intbv(0)[dpt:])

            dut = pipeline_control(self.rst, self.clk, self.rx_rdy, self.rx_vld, self.tx_rdy, self.tx_vld, self.en, stop_rx=self.stop_rx, stop_tx=None)
            stm = stim(dpt)
            Simulation(self.clkgen, dut, stm).run()


    def testStopTX(self):
        ''' PIPE_CTRL: Stop TX '''
        DEPTH = [1,2,3,7,8,9]

        def stim(DEPTH):
            @instance
            def _inst():
                yield self.reset()
                yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                yield self.clk.posedge

                yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)

                for i in range(DEPTH):
                    self.stop_tx.next = 1<<i
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                    yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                    self.rx_vld.next = 1
                    for j in range(i+1):
                        yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=2**(j+1)-1)
                        yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=2**(i+1)-1)
                    yield self.clk.posedge
                    self.rx_vld.next = 0
                    for j in range(i):
                        yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=(2**(i+1)-1)-(2**(j+1)-1))
                        yield self.clk.posedge
                    self.stop_tx.next = 0
                    for j in range(i+1,DEPTH):
                        yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=1<<j)
                        yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=0, tx_vld=1, stage_en=0)
                    self.tx_rdy.next = 1
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=1, stage_en=0)
                    yield self.clk.posedge
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)
                    self.tx_rdy.next = 0
                    yield self.pipe_state_check(rx_rdy=1, tx_vld=0, stage_en=0)

                yield self.clk.posedge
                raise StopSimulation
            return _inst

        for dpt in DEPTH:
            self.stop_rx = Signal(intbv(0)[dpt:])
            self.stop_tx = Signal(intbv(0)[dpt:])

            self.en = Signal(intbv(0)[dpt:])

            dut = pipeline_control(self.rst, self.clk, self.rx_rdy, self.rx_vld, self.tx_rdy, self.tx_vld, self.en, stop_rx=None, stop_tx=self.stop_tx)
            stm = stim(dpt)
            Simulation(self.clkgen, dut, stm).run()



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testPipelineControl']
    unittest.main()