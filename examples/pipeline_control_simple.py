from myhdl import *
from myhdl_lib.pipeline_control import pipeline_control



def twos_complement(rst, clk, rx_rdy, rx_vld, rx_dat, tx_rdy, tx_vld, tx_dat):
    ''' Two's complement conversion of a binary number
        Input handshake & data
            rx_rdy - (o) Ready
            rx_vla - (i) Valid
            rx_dat - (i) Data
        Output handshake & data
            tx_rdy - (i) Ready
            tx_vla - (o) Valid
            tx_dat - (o) Data

        Implementation: 3-stage pipeline
            stage 0: registers input data
            stage 1: inverts data coming from stage 0 and registers them
            stage 2: increments data coming from stage 1 and registers them

            Each stage is implemented as a separate process controlled by a central pipeline control unit via an enable signal
            The pipeline control unit manages the handshake and synchronizes the operation of the stages
    '''

    DATA_WIDTH = len(rx_dat)

    NUM_STAGES = 3

    stage_en = Signal(intbv(0)[NUM_STAGES:])

    pipe_ctrl = pipeline_control( rst = rst,
                                  clk = clk,
                                  rx_vld = rx_vld,
                                  rx_rdy = rx_rdy,
                                  tx_vld = tx_vld,
                                  tx_rdy = tx_rdy,
                                  stage_enable = stage_en)

    s0_dat = Signal(intbv(0)[DATA_WIDTH:])

    @always_seq(clk.posedge, reset=rst)
    def stage_0():
        ''' Register input data'''
        if (stage_en[0]):
            s0_dat.next = rx_dat


    s1_dat = Signal(intbv(0)[DATA_WIDTH:])

    @always_seq(clk.posedge, reset=rst)
    def stage_1():
        ''' Invert data'''
        if (stage_en[1]):
            s1_dat.next = ~s0_dat


    s2_dat = Signal(intbv(0)[DATA_WIDTH:])

    @always_seq(clk.posedge, reset=rst)
    def stage_2():
        ''' Add one to data'''
        if (stage_en[2]):
            s2_dat.next = s1_dat + 1


    @always_comb
    def comb():
        tx_dat.next = s2_dat.signed()

    return instances()



class Driver():
    ''' Drives input handshake interface '''
    def __init__(self, rst, clk, rdy, vld, dat):
        self.rst = rst
        self.clk = clk
        self.rdy = rdy
        self.vld = vld
        self.dat = dat

    def write(self, dat):
        while self.rst:
            yield self.clk.posedge

        self.vld.next = 1
        self.dat.next = dat

        yield self.clk.posedge

        while not self.rdy:
            yield self.clk.posedge

        self.vld.next = 0
        self.dat.next = 0


class Capture():
    ''' Captures output handshake interface '''
    def __init__(self, rst, clk, rdy, vld, dat):
        self.rst = rst
        self.clk = clk
        self.rdy = rdy
        self.vld = vld
        self.dat = dat

        self.d = None


    def read(self):
        while self.rst:
            yield self.clk.posedge

        self.rdy.next = 1

        yield self.clk.posedge

        while not self.vld:
            yield self.clk.posedge

        self.rdy.next = 0
        self.d = int(self.dat)


def reset_generator(rst, clk, RST_LENGTH_CC=10):
    ''' Generates initial reset '''
    @instance
    def _reset():
        rst.next = rst.active
        for _ in range(RST_LENGTH_CC):
            yield clk.posedge
        rst.next = not rst.active
    return _reset


def clock_generator(clk, PERIOD):
    ''' Generates continuous clock '''
    @always(delay(PERIOD//2))
    def _clkgen():
        clk.next = not clk
    return _clkgen


def pipeline_control_simple():

    rst = ResetSignal(val=0, active=1, async=False)
    clk = Signal(bool(0))

    rx_rdy, rx_vld, tx_rdy, tx_vld = [Signal(bool(0)) for _ in range(4)]
    rx_dat = Signal(intbv(0)[7:0])
    tx_dat = Signal(intbv(0, min=-128, max=1))

    clkgen = clock_generator(clk, 10)
    rstgen = reset_generator(rst, clk)
    dut = twos_complement(rst, clk, rx_rdy, rx_vld, rx_dat, tx_rdy, tx_vld, tx_dat)
#     dut = traceSignals(twos_complement, rst, clk, rx_rdy, rx_vld, rx_dat, tx_rdy, tx_vld, tx_dat)
    drv = Driver(rst, clk, rx_rdy, rx_vld, rx_dat)
    cap = Capture(rst, clk, tx_rdy, tx_vld, tx_dat)

    data_in = []
    data_out = []

    def stim(GAP=0):
        ''' Stimulates the pipeline input '''
        @instance
        def _stim():
            yield clk.posedge
            for i in range(1, 10):
                yield drv.write(i)
                data_in.append(i)
                for _ in range(GAP):
                    yield clk.posedge
            for _ in range(10):
                yield clk.posedge
            raise StopSimulation
        return _stim


    def drain(GAP=0):
        ''' Drains the pipeline output '''
        @instance
        def _drain():
            yield clk.posedge
            while True:
                yield cap.read()
                data_out.append(cap.d)
                for _ in range(GAP):
                    yield clk.posedge
        return _drain

    # You can play with the gap size at the input and at the output to see how the pipeline responds (see time diagrams)
    Simulation(rstgen, clkgen, dut, stim(GAP=0), drain(GAP=0)).run()

    print "data_in ({}): {}".format(len(data_in), data_in)
    print "data_out ({}): {}".format(len(data_out), data_out)


if __name__ == '__main__':
    pipeline_control_simple()
