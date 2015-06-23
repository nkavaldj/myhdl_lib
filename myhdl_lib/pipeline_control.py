from myhdl import *

def pipeline_control(rst, clk, rx_rdy, rx_vld, tx_rdy, tx_vld, stage_enable, stop_rx=None, stop_tx=None):
    """ Pipeline control unit
            rx_vld, rx_rdy       - handshake at the pipeline input (front of the pipeline)
            tx_vld, tx_rdy       - handshake at the pipeline output (back of the pipeline)
            stage_enable         - (output) vector of enable signals, one signal per stage, that controls the data registration in the stages;
                                   The length of this vector determines the number of stages in the pipeline
            stop_rx              - (input, optional) vector of signals, one signal per stage; when asserted, the corresponding stage stops consuming data;
                                   allows for multicycle execution in a stage (e.g. consume a data, then process it multiple cycles)
            stop_tx              - (input, optional) vector of signals, one signal per stage; when asserted, the corresponding stage stops producing data;
                                    allows for multicycle execution in a stage (consume multiple data to produce single data )

            stop_rx and stop_tx  - If you do not need them, then do not connect them
    """

    NUM_STAGES = len(stage_enable)

    if (stop_rx == None):
        stop_rx = Signal(intbv(0)[NUM_STAGES:])

    if (stop_tx == None):
        stop_tx = Signal(intbv(0)[NUM_STAGES:])

    assert (len(stop_rx)==NUM_STAGES), "PIPELINE_CONTROL ERROR: len(stop_rx)={:} must be equal to len(stage_enable)={:}".format(len(stop_rx),NUM_STAGES)
    assert (len(stop_tx)==NUM_STAGES), "PIPELINE_CONTROL ERROR: len(stop_rx)={:} must be equal to len(stage_enable)={:}".format(len(stop_tx),NUM_STAGES)

    valid_reg       = Signal(intbv(0)[NUM_STAGES:])
    valid_sl        = Signal(intbv(0)[NUM_STAGES:])
    rdy_sl          = Signal(intbv(0)[NUM_STAGES:])
    rdy_shd_sl      = Signal(intbv(0)[NUM_STAGES:])

    @always(clk.posedge)
    def regs():
        if rst:
            valid_reg.next = 0
        else:
            for s in range(NUM_STAGES):
                if rdy_sl[s]:
                    valid_reg.next[s] = valid_sl[s]

    @always_comb
    def comb_chain():
        valid_sl.next[0]            = rx_vld  or stop_rx[0]
        rdy_sl.next[NUM_STAGES-1]   = tx_rdy  or stop_tx[NUM_STAGES-1] or not valid_reg[NUM_STAGES-1]
        for i in range(1,NUM_STAGES):
            valid_sl.next[i]            = (valid_reg[i-1]               and not stop_tx[i-1]             ) or stop_rx[i]
            rdy_sl.next[NUM_STAGES-1-i] = (rdy_shd_sl[NUM_STAGES-1-i+1] and not stop_rx[NUM_STAGES-1-i+1]) or stop_tx[NUM_STAGES-1-i]

    @always_comb
    def comb_assign():
        tx_vld.next                 = valid_reg[NUM_STAGES-1] and not stop_tx[NUM_STAGES-1]
        rx_rdy.next                 = rdy_sl[0]               and not stop_rx[0]
        stage_enable.next           = valid_sl[NUM_STAGES:] & rdy_sl[NUM_STAGES:]
        rdy_shd_sl.next             = rdy_sl


    return instances()


