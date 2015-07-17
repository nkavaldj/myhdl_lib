from myhdl import *
from utils import assign

def pipeline_control(rst, clk, rx_rdy, rx_vld, tx_rdy, tx_vld, stage_enable, stop_rx=None, stop_tx=None):
    """ Pipeline control unit
            rx_rdy, rx_vld,      - (o)(i) handshake at the pipeline input (front of the pipeline)
            tx_rdy, tx_vld,      - (i)(o) handshake at the pipeline output (back of the pipeline)
            stage_enable         - (o) vector of enable signals, one signal per stage, that controls the data registration in the stages;
                                   The length of this vector determines the number of stages in the pipeline
            stop_rx              - (i) optional, vector of signals, one signal per stage; when asserted, the corresponding stage stops consuming data;
                                   allows for multicycle execution in a stage (e.g. consume a data, then process it multiple cycles)
            stop_tx              - (i) optional, vector of signals, one signal per stage; when asserted, the corresponding stage stops producing data;
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



def pipeline_control_new(rst, clk, rx_rdy, rx_vld, tx_rdy, tx_vld, stage_enable, stop_rx=None, stop_tx=None):
    """ Pipeline control unit
            rx_rdy, rx_vld,      - (o)(i) handshake at the pipeline input (front of the pipeline)
            tx_rdy, tx_vld,      - (i)(o) handshake at the pipeline output (back of the pipeline)
            stage_enable         - (o) vector of enable signals, one signal per stage, that controls the data registration in the stages;
                                   The length of this vector determines the number of stages in the pipeline
            stop_rx              - (i) optional, vector of signals, one signal per stage; when asserted, the corresponding stage stops consuming data;
                                   allows for multicycle execution in a stage (e.g. consume a data, then process it multiple cycles)
            stop_tx              - (i) optional, vector of signals, one signal per stage; when asserted, the corresponding stage stops producing data;
                                    allows for multicycle execution in a stage (consume multiple data to produce single data )

            stop_rx and stop_tx  - If you do not need them, then do not connect them
    """

    NUM_STAGES = len(stage_enable)

    if (stop_rx == None):
        stop_rx = Signal(intbv(0)[NUM_STAGES:])

    if (stop_tx == None):
        stop_tx = Signal(intbv(0)[NUM_STAGES:])

    assert (len(stop_rx)==NUM_STAGES), "pipeline_control: expects len(stop_rx)=len(stage_enable), but len(stop_rx)={} len(stage_enable)={}".format(len(stop_rx),NUM_STAGES)
    assert (len(stop_tx)==NUM_STAGES), "pipeline_control: expects len(stop_tx)=len(stage_enable), but len(stop_tx)={} len(stage_enable)={}".format(len(stop_tx),NUM_STAGES)

    FIRST_STAGE = 0
    LAST_STAGE = NUM_STAGES-1

    stg = NUM_STAGES*[None]
    rdy = (NUM_STAGES+1)*[Signal(bool(0))]
    vld = (NUM_STAGES+1)*[Signal(bool(0))]
    BC = NUM_STAGES*[False]

    rdy[0] = rx_rdy
    vld[0] = rx_vld
    rdy[-1] = tx_rdy
    vld[-1] = tx_vld
    BC[-1] = True

    for i in range(NUM_STAGES):
        stg[i] = _stage_ctrl(rst=rst, clk=clk, rx_rdy=rdy[i], rx_vld=vld[i], tx_rdy=rdy[i+1], tx_vld=vld[i+1], stage_en=stage_enable[i], stop_rx=stop_rx[i], stop_tx=stop_tx[i])

    return instances()

def _stage_ctrl(rst, clk, rx_rdy, rx_vld, tx_rdy, tx_vld, stage_en, stop_rx=None, stop_tx=None, BC=False):
    '''  '''
    state = Signal(bool(0))
    a = Signal(bool(0))
    b = Signal(bool(0))
    bc_link = state if BC else True

    @always_comb
    def _comb():
        a.next = tx_rdy or stop_tx or not bc_link
        b.next = rx_vld or stop_rx
        rx_rdy.next = a and not stop_rx
        tx_vld.next = state and not stop_tx
        stage_en.next = a and b

    @always_seq(clk.posedge, reset=rst)
    def _state():
        if a:
            state.next = b

    return _comb, _state







