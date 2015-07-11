from myhdl import *

def reset_generator(rst, clk, RST_LENGTH_CC=10):
    ''' Generates single reset at startup
            rst - MyHDL ResetSignal
            RST_LENGTH_CC - reset length in clock cycles
    '''
    @instance
    def _reset():
        rst.next = rst.active
        for _ in range(RST_LENGTH_CC):
            yield clk.posedge
        rst.next = not rst.active
    return _reset


def clock_generator(clk, PERIOD=10):
    ''' Generates continuous clock
            PERIOD - clock period in ns(?)
    '''
    @always(delay(PERIOD//2))
    def _clkgen():
        clk.next = not clk
    return _clkgen




if __name__ == '__main__':
    pass