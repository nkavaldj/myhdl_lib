from myhdl import ResetSignal, delay

# This code is a shameless copy of Christopher Felton's _reset class: https://github.com/cfelton/minnesota/blob/master/mn/system/_reset.py
class ResetSync(ResetSignal):
    ''' Synchronous reset '''
    def __init__(self, clk, val, active):
        self.clk = clk
        ResetSignal.__init__(self, val, active, async=False)

    def pulse(self, length_cc=10):
        self.next = self.active
        for _ in range(length_cc):
            yield self.clk.posedge
        self.next = not self.active

    def set(self):
        self.next = self.active

    def clear(self):
        self.next = not self.active
