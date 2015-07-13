from myhdl import *
from myhdl_lib.arbiter import arbiter_priority, arbiter_roundrobin


'''
    Handshake

     -------      ready      -------
    |       |<--------------|       |
    |       |               |       |
    |  src  |     valid     |  dst  |
    |       |-------------->|       |
    |       |               |       |
    |       |     data      |       |
    |       |==============>|       |
     -------                 -------

              ___   ___   ___   ___   ___   ___   ___   ___   ___   ___   ___   ___   ___   ___   ___   
    clk   ___|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |___
              ______________________________            ____________      ______      ______            
  ready   ___|                             |___________|           |_____|     |_____|     |____________
                    ____________      ______      ______________________________            ______      
  valid   _________|           |_____|     |_____|                             |___________|     |______
                    _____ _____       _____       ___________ _____ ___________            _____        
   data   xxxxxxxxxX_____X_____XxxxxxX_____XxxxxxX___________X_____X___________XxxxxxxxxxxX_____Xxxxxxxx
                      ^     ^           ^                 ^     ^           ^                           
  transactions        ^     ^           ^                 ^     ^           ^                           


    Simple synchronization interface. Allows modules to synchronize their operation with other modules. 
    Signals:
        ready (or rdy) 
        valid (or vld)
        data (or dat)


'''


def hs_join(ls_hsi, hso):
    """ [Many-to-one] Synchronizes (joins) a list of input handshake interfaces: output is ready when ALL inputs are ready
            ls_hsi - list of input handshake tuples (ready, valid)
            hso - an output handshake tuple (ready, valid)
    """
    N = len(ls_hsi)
    ls_hsi_rdy, ls_hsi_vld = zip(*ls_hsi)
    ls_hsi_rdy, ls_hsi_vld = list(ls_hsi_rdy), list(ls_hsi_vld)
    hso_rdy, hso_vld = hso

    @always_comb
    def _join():
        all_vld = True
        for i in range(N):
            all_vld = all_vld and ls_hsi_vld[i]
        hso_vld.next = all_vld
        for i in range(N):
            ls_hsi_rdy[i].next = all_vld and hso_rdy

    return _join


def hs_fork(hsi, ls_hso):
    """ [One-to-many] Synchronizes (forks) to a list of output handshake interfaces: input is ready when ALL outputs are ready
            hsi - a input handshake tuple (ready, valid)
            ls_hso - list of output handshake tuples (ready, valid)
    """
    N = len(ls_hso)
    hsi_rdy, hsi_vld = hsi
    ls_hso_rdy, ls_hso_vld = zip(*ls_hso)
    ls_hso_rdy, ls_hso_vld = list(ls_hso_rdy), list(ls_hso_vld)

    @always_comb
    def _fork():
        all_rdy = True
        for i in range(N):
            all_rdy = all_rdy and ls_hso_rdy[i]
        hsi_rdy.next = all_rdy
        for i in range(N):
            ls_hso_vld[i].next = all_rdy and hsi_vld

    return _fork


def hs_mux(sel, ls_hsi, hso):
    """ [Many-to-one] Multiplexes a list of input handshake interfaces
            ls_hsi - list of input handshake tuples (ready, valid)
            hso - a output handshake tuple (ready, valid)
            sel - selects an input handshake interface to be connected to the output
    """
    N = len(ls_hsi)
    ls_hsi_rdy, ls_hsi_vld = zip(*ls_hsi)
    ls_hsi_rdy, ls_hsi_vld = list(ls_hsi_rdy), list(ls_hsi_vld)
    hso_rdy, hso_vld = hso

    @always_comb
    def mux_comb():
        hso_vld.next = 0
        for i in range(N):
            ls_hsi_rdy[i].next = 0
            if i == sel:
                hso_vld.next = ls_hsi_vld[i]
                ls_hsi_rdy[i].next = hso_rdy

    return mux_comb


def hs_demux(sel, hsi, ls_hso):
    """ [One-to-many] Demultiplexes to a list of output handshake interfaces
            hsi - a input handshake tuple (ready, valid)
            ls_hso - list of output handshake tuples (ready, valid)
            sel - selects an output handshake interface to connect to the input
    """
    N = len(ls_hso)
    hsi_rdy, hsi_vld = hsi
    ls_hso_rdy, ls_hso_vld = zip(*ls_hso)
    ls_hso_rdy, ls_hso_vld = list(ls_hso_rdy), list(ls_hso_vld)

    @always_comb
    def demux_comb():
        hsi_rdy.next = 0
        for i in range(N):
            ls_hso_vld[i].next = 0
            if i == sel:
                hsi_rdy.next = ls_hso_rdy[i]
                ls_hso_vld[i].next = hsi_vld

    return demux_comb


def hs_arbmux(rst, clk, ls_hsi, hso, sel, ARBITER_TYPE="priority"):
    """ [Many-to-one] Arbitrates multiple input handshake interfaces
        Arbitrated only between inputs that currently have active valid
        ls_hsi - list of input (ready, valid) tuples
        hso    - a output (ready, valid) tuple
        sel    - output that indicates the currently selected input handshake interface
        ARBITER_TYPE - selects the type of arbiter to be used, priority or roundrobin
    """
    ls_vld = [hs[1] for hs in ls_hsi]
    sho_rdy, hso_vld = hso
    s = Signal(intbv(0), min=0, max=len(ls_vld))
    prio_update = Signal(bool(0))

    @always_comb
    def comb():
        prio_update.next = sho_rdy and hso_vld
        sel.next = s

    if (ARBITER_TYPE == "priority"):
        arb = arbiter_priority(ls_vld, s)
    elif (ARBITER_TYPE == "roundrobin"):
        arb = arbiter_roundrobin(rst, clk, ls_vld, s, prio_update)
    else:
        assert "hs_arbmux: Unknown arbiter type: {}".format(ARBITER_TYPE)

    mux = hs_mux(s, ls_hsi, hso)

    return instances()


def hs_arbdemux(rst, clk, hsi, ls_hso, sel, ARBITER_TYPE="priority"):
    """ [One-to-many] Arbitrates to multiple output handshake interfaces
        Arbitrates only between autputs that currently have active ready
        hsi    - a input (ready, valid) tuple
        ls_hso - list of output (ready, valid) tuples
        sel    - output that indicates the currently selected output handshake interface
        ARBITER_TYPE - selects the type of arbiter to be used, priority or roundrobin
    """
    shi_rdy, hsi_vld = hsi
    ls_rdy = [hs[0] for hs in ls_hso]
    s = Signal(intbv(0), min=0, max=len(ls_rdy))
    prio_update = Signal(bool(0))

    @always_comb
    def comb():
        prio_update.next = shi_rdy and hsi_vld
        sel.next = s

    if (ARBITER_TYPE == "priority"):
        arb = arbiter_priority(ls_rdy, s)
    elif (ARBITER_TYPE == "roundrobin"):
        arb = arbiter_roundrobin(rst, clk, ls_rdy, s, prio_update)
    else:
        assert "hs_arbdemux: Unknown arbiter type: {}".format(ARBITER_TYPE)

    demux = hs_demux(s, hsi, ls_hso)

    return instances()





if __name__ == '__main__':
    pass