from myhdl import SignalType, instance, delay


# This code is a shameless copy of Christopher Felton's _clock class: https://github.com/cfelton/minnesota/blob/master/mn/system/_clock.py
class Clock(SignalType): 
    ''' Clock signal equipped with clock generator '''

    _frequency_units = {"Hz":1, "kHz":1e3, "Mhz":1e6, "GHz":1e9}
    _periode_units = {"sec":1,"s":1, "ms":1e-3, "us":1e-6, "ns":1e-9}

    def __init__(self, val, frequency=None, period=10, units="ns", ratio_high_to_low=0.5):
        ''' Sets clock parameters
                val - initial clock value
                frequency - clock frequency
                period - clock period, used if clock frequency is not defined
                units - units in which frequency or period is defined
                        allowed frequency units: "Hz", "kHz", "Mhz", "GHz"
                        allowed period units: "sec","s", "ms":, "us", "ns"
                ratio_high_to_low - clock signal ration, 0 < ratio_high_to_low < 1
        '''
        if frequency is not None:
            assert Clock._frequency_units.has_key(units), "Unknown frequency units {}. Allowed values: {}".format(units, Clock._frequency_units.keys())
            self._frequency_Hz = frequency*Clock._frequency_units[units]
            self._period_sec = 1.0/frequency
        else:
            assert Clock._periode_units.has_key(units), "Unknown time units {}. Allowed values: {}".format(units, Clock._periode_units.keys())
            self._period_sec = period*Clock._periode_units[units]
            self._frequency_Hz = 1.0/period

        self._periode_ns = self._period_sec*1e9

        assert (0 < ratio_high_to_low), "Expected 0 < ratio_high_to_low, got ratio_high_to_low={}".format(ratio_high_to_low)
        assert (ratio_high_to_low < 1), "Expected ratio_high_to_low < 1, got ratio_high_to_low={}".format(ratio_high_to_low)


        self._periode_high_ns = long(self._periode_ns * ratio_high_to_low)
        self._periode_low_ns = long(self._periode_ns - self._periode_high_ns)

        self._periode_ns = self._periode_high_ns + self._periode_low_ns
        self.periode_sec = self._periode_ns*1e-9
        self._frequency_Hz = 1e9/self._periode_ns

        SignalType.__init__(self, bool(val))

    @property
    def frequency(self):
        return self._frequency_Hz

    @property
    def period(self):
        return self._period_sec


    def gen(self):
        @instance
        def clkgen():
            if self.val:
                self.next = True
                yield delay(self._periode_high_ns)
            while True:
                self.next = False
                yield delay(self._periode_low_ns)
                self.next = True
                yield delay(self._periode_high_ns)

        return clkgen


if __name__ == '__main__':
    pass