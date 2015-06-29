from myhdl import *
from mylib import pipeline_control



def arithmetic_mean4(rst, clk, rx_rdy, rx_vld, rx_dat, tx_rdy, tx_vld, tx_dat):
    ''' Calculates the arithmetic mean of every 4 numbers consecutive

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
            stage 1: sum each 4 consecutive numbers and produce the sum as a single result
            stage 2: divide the sum by 4

            Each stage is implemented as a separate process controlled by a central pipeline control unit via an enable signal
            The pipeline control unit manages the handshake and synchronizes the operation of the stages
    '''


    DATA_WIDTH = len(rx_dat)

    NUM_STAGES = 3

    stage_en = Signal(intbv(0)[NUM_STAGES:])

    stop_tx = Signal(intbv(0)[NUM_STAGES:])

    pipe_ctrl = pipeline_control( rst = rst,
                                  clk = clk,
                                  rx_vld = rx_vld,
                                  rx_rdy = rx_rdy,
                                  tx_vld = tx_vld,
                                  tx_rdy = tx_rdy,
                                  stage_enable = stage_en,
                                  stop_tx = stop_tx)


    s0_dat = Signal(intbv(0)[DATA_WIDTH:])

    @always_seq(clk.posedge, reset=rst)
    def stage_0():
        ''' Register input data'''
        if (stage_en[0]):
            s0_dat.next = rx_dat


    s1_sum = Signal(intbv(0)[DATA_WIDTH+2:])
    s1_cnt = Signal(intbv(0, min=0, max=4))

    @always(clk.posedge)
    def stage_1():
        ''' Sum each 4 consecutive data'''
        if (rst):
            s1_cnt.next = 0
            stop_tx.next[1] = 1
        elif (stage_en[1]):
            # Count input data
            s1_cnt.next = (s1_cnt + 1) % 4

            if (s1_cnt == 0):
                s1_sum.next = s0_dat
            else:
                s1_sum.next = s1_sum.next + s0_dat

            # Produce result only after data 0, 1, 2, and 3 have been summed
            if (s1_cnt == 3):
                stop_tx.next[1] = 0
            else:
                stop_tx.next[1] = 1
            ''' stop_tx[1] concerns the data currently registered in stage 1 - it determines whether 
                the data will be sent to the next pipeline stage (stop_tx==0) or will be dropped (stop_tx==1 ).
                The signals stop_rx and stop_tx must be registered '''


    s2_dat = Signal(intbv(0)[DATA_WIDTH:])

    @always_seq(clk.posedge, reset=rst)
    def stage_2():
        ''' Divide by 4'''
        if (stage_en[2]):
            s2_dat.next = s1_sum >> 2


    @always_comb
    def comb():
        tx_dat.next = s2_dat

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


def pipeline_control_stop_tx():
    ''' Instantiates the arithmetic_mean4 pipeline, feeds it with data and drains its output '''

    rst = ResetSignal(val=0, active=1, async=False)
    clk = Signal(bool(0))

    rx_rdy, rx_vld, tx_rdy, tx_vld = [Signal(bool(0)) for _ in range(4)]
    rx_dat = Signal(intbv(0)[8:])
    tx_dat = Signal(intbv(0)[8:])

    clkgen = clock_generator(clk, 10)
    rstgen = reset_generator(rst, clk)
#     dut = arithmetic_mean4(rst, clk, rx_rdy, rx_vld, rx_dat, tx_rdy, tx_vld, tx_dat)
    dut = traceSignals(arithmetic_mean4, rst, clk, rx_rdy, rx_vld, rx_dat, tx_rdy, tx_vld, tx_dat)
    drv = Driver(rst, clk, rx_rdy, rx_vld, rx_dat)
    cap = Capture(rst, clk, tx_rdy, tx_vld, tx_dat)

    data_in = []
    data_out = []

    def stim(GAP=0):
        ''' Stimulates the pipeline input '''
        @instance
        def _stim():
            yield clk.posedge
            for i in range(5*4):
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
    pipeline_control_stop_tx()