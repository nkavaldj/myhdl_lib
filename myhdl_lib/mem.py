from myhdl import *

def rom(addr, dout, CONTENT):
    ''' CONTENT == tuple of non-sparse values '''
    @always_comb
    def read():
        dout.next = CONTENT[int(addr)]

    return read


def ram_sp_rf(clk, we, addr, di, do):
    ''' RAM: Single-Port, Read-First '''

    memL = [Signal(intbv(0)[len(di):]) for _ in range(2**len(addr))]

    @always(clk.posedge)
    def write():
        if we:
            memL[int(addr)].next = di

        do.next = memL[int(addr)]

    return write


def ram_sp_wf(clk, we, addr, di, do):
    ''' RAM: Single-Port, Write-First '''

    memL = [Signal(intbv(0)[len(di):]) for _ in range(2**len(addr))]

    @always(clk.posedge)
    def write():        
        if we:
            memL[int(addr)].next = di
            do.next              = di
        else:
            do.next = memL[int(addr)]

    return write


def ram_sp_ar(clk, we, addr, di, do):
    ''' RAM: Single-Port, Asynchronous Read '''

    memL = [Signal(intbv(0)[len(di):]) for _ in range(2**len(addr))]

    @always(clk.posedge)
    def write():
        if we:
            memL[int(addr)].next = di

    @always_comb
    def read():
        do.next = memL[int(addr)]

    return write, read


def ram_sdp_rf(clk, we, addrw, addrr, di, do):
    ''' RAM: Simple-Dual-Port, Read-First '''

    memL = [Signal(intbv(0)[len(di):]) for _ in range(2**len(addrr))]

    @always(clk.posedge)
    def write():
        if we:
            memL[int(addrw)].next = di
        do.next = memL[int(addrr)]

    return write


def ram_sdp_wf(clk, we, addrw, addrr, di, do):
    ''' RAM: Simple-Dual-Port, Write-First '''

    memL = [Signal(intbv(0)[len(di):]) for _ in range(2**len(addrr))]
    addrr_r = Signal(intbv(0)[len(addrr):])

    @always(clk.posedge)
    def write():
        if we:
            memL[int(addrw)].next = di
        addrr_r.next          = addrr

    @always_comb
    def read():
        do.next = memL[int(addrr_r)]

    return write, read


def ram_sdp_ar(clk, we, addrw, addrr, di, do):
    ''' RAM: Simple-Dual-Port, Asynchronous Read'''

    memL = [Signal(intbv(0)[len(di):]) for _ in range(2**len(addrr))]

    @always(clk.posedge)
    def write():
        if we:
            memL[int(addrw)].next = di

    @always_comb
    def read():
        do.next = memL[int(addrr)]

    return write, read


def ram_dp_rf(clka, clkb, wea, web, addra, addrb, dia, dib, doa, dob):
    ''' RAM: Dual-Port, Read-First '''

    memL = [Signal(intbv(0)[len(dia):]) for _ in range(2**len(addra))]

    @always(clka.posedge)
    def writea():
        if wea:
            memL[int(addra)].next = dia

        doa.next = memL[int(addra)]

    @always(clkb.posedge)
    def writeb():
        if web:
            memL[int(addrb)].next = dib

        dob.next = memL[int(addrb)]

    return writea, writeb


def ram_dp_wf(clka, clkb, wea, web, addra, addrb, dia, dib, doa, dob):
    ''' RAM: Dual-Port, Write-First '''

    memL = [Signal(intbv(0)[len(dia):]) for _ in range(2**len(addra))]

    @always(clka.posedge)
    def writea():
        if wea:
            memL[int(addra)].next = dia
            doa.next              = dia
        else:
            doa.next = memL[int(addra)]

    @always(clkb.posedge)
    def writeb():
        if web:
            memL[int(addrb)].next = dib
            dob.next              = dib
        else:
            dob.next = memL[int(addrb)]

    return writea, writeb


def ram_dp_ar(clka, clkb, wea, web, addra, addrb, dia, dib, doa, dob):
    ''' RAM: Dual-Port, Asynchronous Read '''

    memL = [Signal(intbv(0)[len(dia):]) for _ in range(2**len(addra))]

    @always(clka.posedge)
    def writea():
        if wea:
            memL[int(addra)].next = dia

    @always_comb
    def reada():
        doa.next = memL[int(addra)]

    @always(clkb.posedge)
    def writeb():
        if web:
            memL[int(addrb)].next = dib

    @always_comb
    def readb():
        dob.next = memL[int(addrb)]

    return writea, reada, writeb, readb


#===============================================================================
# Conversion functions
#===============================================================================

def convert_rom(ADDR_WIDTH=8, DATA_WIDTH=8, CONTENT=(4,5,6,7)):
    ''' Convert ROM'''
    addr = Signal(intbv(0)[ADDR_WIDTH:])
    dout = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(rom, addr, dout, CONTENT)


def convert_ram_sp_rf(ADDR_WIDTH=8, DATA_WIDTH=8):
    ''' Convert RAM: Single-Port, Read-First '''
    clk = Signal(bool(0))
    we = Signal(bool(0))
    addr = Signal(intbv(0)[ADDR_WIDTH:])
    di = Signal(intbv(0)[DATA_WIDTH:])
    do = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(ram_sp_rf, clk, we, addr, di, do)


def convert_ram_sp_wf(ADDR_WIDTH=8, DATA_WIDTH=8):
    ''' Convert RAM: Single-Port, Write-First '''
    clk = Signal(bool(0))
    we = Signal(bool(0))
    addr = Signal(intbv(0)[ADDR_WIDTH:])
    di = Signal(intbv(0)[DATA_WIDTH:])
    do = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(ram_sp_wf, clk, we, addr, di, do)


def convert_ram_sp_ar(ADDR_WIDTH=8, DATA_WIDTH=8):
    ''' Convert RAM: Single-Port, Asynchronous Read '''
    clk = Signal(bool(0))
    we = Signal(bool(0))
    addr = Signal(intbv(0)[ADDR_WIDTH:])
    di = Signal(intbv(0)[DATA_WIDTH:])
    do = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(ram_sp_ar, clk, we, addr, di, do)


def convert_ram_sdp_rf(ADDR_WIDTH=8, DATA_WIDTH=8):
    ''' Convert RAM: Simple-Dual-Port, Read-First '''
    clk = Signal(bool(0))
    we = Signal(bool(0))
    addrw = Signal(intbv(0)[ADDR_WIDTH:])
    addrr = Signal(intbv(0)[ADDR_WIDTH:])
    di = Signal(intbv(0)[DATA_WIDTH:])
    do = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(ram_sdp_rf, clk, we, addrw, addrr, di, do)


def convert_ram_sdp_wf(ADDR_WIDTH=8, DATA_WIDTH=8):
    ''' Convert RAM: Simple-Dual-Port, Write-First '''
    clk = Signal(bool(0))
    we = Signal(bool(0))
    addrw = Signal(intbv(0)[ADDR_WIDTH:])
    addrr = Signal(intbv(0)[ADDR_WIDTH:])
    di = Signal(intbv(0)[DATA_WIDTH:])
    do = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(ram_sdp_wf, clk, we, addrw, addrr, di, do)


def convert_ram_sdp_ar(ADDR_WIDTH=8, DATA_WIDTH=8):
    ''' Convert RAM: Simple-Dual-Port, Asynchronous Read'''
    clk = Signal(bool(0))
    we = Signal(bool(0))
    addrw = Signal(intbv(0)[ADDR_WIDTH:])
    addrr = Signal(intbv(0)[ADDR_WIDTH:])
    di = Signal(intbv(0)[DATA_WIDTH:])
    do = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(ram_sdp_ar, clk, we, addrw, addrr, di, do)


def convert_ram_dp_rf(ADDR_WIDTH=8, DATA_WIDTH=8):
    ''' Convert RAM: Dual-Port, Read-First '''
    clka = Signal(bool(0))
    clkb = Signal(bool(0))
    wea = Signal(bool(0))
    web = Signal(bool(0))
    addra = Signal(intbv(0)[ADDR_WIDTH:])
    addrb = Signal(intbv(0)[ADDR_WIDTH:])
    dia = Signal(intbv(0)[DATA_WIDTH:])
    dib = Signal(intbv(0)[DATA_WIDTH:])
    doa = Signal(intbv(0)[DATA_WIDTH:])
    dob = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(ram_dp_rf, clka, clkb, wea, web, addra, addrb, dia, dib, doa, dob)


def convert_ram_dp_wf(ADDR_WIDTH=8, DATA_WIDTH=8):
    ''' Convert RAM: Dual-Port, Write-First '''
    clka = Signal(bool(0))
    clkb = Signal(bool(0))
    wea = Signal(bool(0))
    web = Signal(bool(0))
    addra = Signal(intbv(0)[ADDR_WIDTH:])
    addrb = Signal(intbv(0)[ADDR_WIDTH:])
    dia = Signal(intbv(0)[DATA_WIDTH:])
    dib = Signal(intbv(0)[DATA_WIDTH:])
    doa = Signal(intbv(0)[DATA_WIDTH:])
    dob = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(ram_dp_wf, clka, clkb, wea, web, addra, addrb, dia, dib, doa, dob)


def convert_ram_dp_ar(ADDR_WIDTH=8, DATA_WIDTH=8):
    ''' Convert RAM: Dual-Port, Asynchronous Read '''
    clka = Signal(bool(0))
    clkb = Signal(bool(0))
    wea = Signal(bool(0))
    web = Signal(bool(0))
    addra = Signal(intbv(0)[ADDR_WIDTH:])
    addrb = Signal(intbv(0)[ADDR_WIDTH:])
    dia = Signal(intbv(0)[DATA_WIDTH:])
    dib = Signal(intbv(0)[DATA_WIDTH:])
    doa = Signal(intbv(0)[DATA_WIDTH:])
    dob = Signal(intbv(0)[DATA_WIDTH:])
    toVerilog(ram_dp_ar, clka, clkb, wea, web, addra, addrb, dia, dib, doa, dob)




if __name__ == "__main__":
    convert_rom()
    convert_ram_sp_rf()
    convert_ram_sp_wf()
    convert_ram_sp_ar()
    convert_ram_sdp_rf()
    convert_ram_sdp_wf()
    convert_ram_sdp_ar()
    convert_ram_dp_rf()
    convert_ram_dp_wf()
    convert_ram_dp_ar()

