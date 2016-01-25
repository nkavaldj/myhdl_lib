from myhdl import *
from myhdl_lib.arbiter import arbiter
from myhdl_lib.utils import assign

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
                    _____ _____       _____       ___________ _____ ___________             _____        
   data   xxxxxxxxxX_____X_____XxxxxxX_____XxxxxxX___________X_____X___________XxxxxxxxxxxxX_____Xxxxxxxx
                      ^     ^           ^                 ^     ^           ^                           
  transactions        ^     ^           ^                 ^     ^           ^                           


    Simple interface used to synchronize interactions/data transfers between modules. 
    Signals:
        ready (or rdy) - indicates that in the current clock cycle the destination module is ready to receive
        valid (or vld) - indicates that in the current clock cycle the source module is ready to transmit (has valid data)
        data (or dat) - data to be transmitted

    - Signals "valid" and "ready" advertise *state* (as opposite to notifying about event)

    - The names "valid" and "ready" imply notion of direction by suggesting source and destination.
      Such notion is natural and intuitive when we have data transfer in one direction, which is 
      often the case. Then we can clearly identify data source and data destination, the source advertises 
      the validity of its data via the "valid" signal, and the destination advertises its readiness 
      to accept data via its "ready" signal.

      But unidirectional data transfer is not the only case when we need synchronization between modules. 
      Synchronization may be needed when there is no data transfer (just synchronization), or synchronization 
      may be needed when data is transferred in both directions (modules exchange data). In these two cases 
      the notion of source and destination is lost and the signal names "valid" and "ready" are not natural 
      and intuitive. Without the notion of direction both modules that need to synchronize their operation 
      become equal, and they drive the "ready" and "valid" signals to advertise their readiness. In that 
      sense both signals have meaning of "I_am_ready". From a point of view of a module, the signal driven 
      by the module has meaning of "I_am_ready" and the signal received from the other module has meaning of 
      "The_other_is_ready". Following that notion we can give the signals more intuitive local names like 
      "local_ready" and "foreign_ready", but this will solve the problem only on local level, level of a module,
      since the notion of local and foreign are relative - what is local for one module is foreign for the other 
      and vice versa. We still do not have unique, design independent names for the signals between the modules.

      For the moment we use the ready/valid naming, until a better one is proposed.


'''


def hs_join(ls_hsi, hso):
    """ [Many-to-one] Synchronizes (joins) a list of input handshake interfaces: output is ready when ALL inputs are ready
            ls_hsi - (i) list of input handshake tuples (ready, valid)
            hso    - (o) an output handshake tuple (ready, valid)
    """
    N = len(ls_hsi)
    ls_hsi_rdy, ls_hsi_vld = zip(*ls_hsi)
    ls_hsi_rdy, ls_hsi_vld = list(ls_hsi_rdy), list(ls_hsi_vld)
    hso_rdy, hso_vld = hso

    @always_comb
    def _hsjoin():
        all_vld = True
        for i in range(N):
            all_vld = all_vld and ls_hsi_vld[i]
        hso_vld.next = all_vld
        for i in range(N):
            ls_hsi_rdy[i].next = all_vld and hso_rdy

    return _hsjoin


def hs_fork(hsi, ls_hso):
    """ [One-to-many] Synchronizes (forks) to a list of output handshake interfaces: input is ready when ALL outputs are ready
            hsi    - (i) input handshake tuple (ready, valid)
            ls_hso - (o) list of output handshake tuples (ready, valid)
    """
    N = len(ls_hso)
    hsi_rdy, hsi_vld = hsi
    ls_hso_rdy, ls_hso_vld = zip(*ls_hso)
    ls_hso_rdy, ls_hso_vld = list(ls_hso_rdy), list(ls_hso_vld)

    @always_comb
    def _hsfork():
        all_rdy = True
        for i in range(N):
            all_rdy = all_rdy and ls_hso_rdy[i]
        hsi_rdy.next = all_rdy
        for i in range(N):
            ls_hso_vld[i].next = all_rdy and hsi_vld

    return _hsfork


def hs_mux(sel, ls_hsi, hso):
    """ [Many-to-one] Multiplexes a list of input handshake interfaces
            sel    - (i) selects an input handshake interface to be connected to the output
            ls_hsi - (i) list of input handshake tuples (ready, valid)
            hso    - (o) output handshake tuple (ready, valid)
    """
    N = len(ls_hsi)
    ls_hsi_rdy, ls_hsi_vld = zip(*ls_hsi)
    ls_hsi_rdy, ls_hsi_vld = list(ls_hsi_rdy), list(ls_hsi_vld)
    hso_rdy, hso_vld = hso

    @always_comb
    def _hsmux():
        hso_vld.next = 0
        for i in range(N):
            ls_hsi_rdy[i].next = 0
            if i == sel:
                hso_vld.next = ls_hsi_vld[i]
                ls_hsi_rdy[i].next = hso_rdy

    return _hsmux


def hs_demux(sel, hsi, ls_hso):
    """ [One-to-many] Demultiplexes to a list of output handshake interfaces
            sel    - (i) selects an output handshake interface to connect to the input
            hsi    - (i) input handshake tuple (ready, valid)
            ls_hso - (o) list of output handshake tuples (ready, valid)
    """
    N = len(ls_hso)
    hsi_rdy, hsi_vld = hsi
    ls_hso_rdy, ls_hso_vld = zip(*ls_hso)
    ls_hso_rdy, ls_hso_vld = list(ls_hso_rdy), list(ls_hso_vld)

    @always_comb
    def _hsdemux():
        hsi_rdy.next = 0
        for i in range(N):
            ls_hso_vld[i].next = 0
            if i == sel:
                hsi_rdy.next = ls_hso_rdy[i]
                ls_hso_vld[i].next = hsi_vld

    return _hsdemux


def hs_arbmux(rst, clk, ls_hsi, hso, sel, ARBITER_TYPE="priority"):
    """ [Many-to-one] Arbitrates a list of input handshake interfaces.
        Selects one of the active input interfaces and connects it to the output.
        Active input is an input interface with asserted "valid" signal
            ls_hsi - (i) list of input handshake tuples (ready, valid)
            hso    - (o) output handshake tuple (ready, valid)
            sel    - (o) indicates the currently selected input handshake interface
            ARBITER_TYPE - selects the arbiter type to be used, "priority" or "roundrobin"
    """
    N = len(ls_hsi)
    ls_hsi_rdy, ls_hsi_vld = zip(*ls_hsi)
    ls_hsi_vld = list(ls_hsi_vld)

    # Needed to avoid: "myhdl.ConversionError: Signal in multiple list is not supported:"
    ls_vld = [Signal(bool(0)) for _ in range(N)]
    _a = [assign(ls_vld[i], ls_hsi_vld[i]) for i in range(N)]

    sel_s = Signal(intbv(0, min=0, max=N))
    @always_comb
    def _sel():
        sel.next = sel_s

    priority_update = None

    if (ARBITER_TYPE == "roundrobin"):
        hso_rdy, hso_vld = hso
        priority_update = Signal(bool(0))

        @always_comb
        def _prio():
            priority_update.next = hso_rdy and hso_vld

    _arb = arbiter(rst=rst, clk=clk, req_vec=ls_vld, gnt_idx=sel_s, gnt_rdy=priority_update, ARBITER_TYPE=ARBITER_TYPE)

    _mux = hs_mux(sel=sel_s, ls_hsi=ls_hsi, hso=hso)

    return instances()


def hs_arbdemux(rst, clk, hsi, ls_hso, sel, ARBITER_TYPE="priority"):
    """ [One-to-many] Arbitrates a list output handshake interfaces
        Selects one of the active output interfaces and connects it to the input.
        Active is an output interface with asserted "ready" signal
            hsi    - (i) input handshake tuple (ready, valid)
            ls_hso - (o) list of output handshake tuples (ready, valid)
            sel    - (o) indicates the currently selected output handshake interface
            ARBITER_TYPE - selects the type of arbiter to be used, "priority" or "roundrobin"
    """
    N = len(ls_hso)
    ls_hso_rdy, ls_hso_vld = zip(*ls_hso)
    ls_hso_rdy = list(ls_hso_rdy)

    # Needed to avoid: "myhdl.ConversionError: Signal in multiple list is not supported:"
    ls_rdy = [Signal(bool(0)) for _ in range(N)]
    _a = [assign(ls_rdy[i], ls_hso_rdy[i]) for i in range(N)]

    sel_s = Signal(intbv(0, min=0, max=len(ls_rdy)))
    @always_comb
    def _sel():
        sel.next = sel_s

    priority_update = None
    if (ARBITER_TYPE == "roundrobin"):
        shi_rdy, hsi_vld = hsi
        priority_update = Signal(bool(0))

        @always_comb
        def _prio():
            priority_update.next = shi_rdy and hsi_vld

    _arb = arbiter(rst=rst, clk=clk, req_vec=ls_rdy, gnt_idx=sel_s, gnt_rdy=priority_update, ARBITER_TYPE=ARBITER_TYPE)

    _demux = hs_demux(sel_s, hsi, ls_hso)

    return instances()





if __name__ == '__main__':
    pass