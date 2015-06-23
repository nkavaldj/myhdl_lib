'''
Created on Mar 1, 2014

@author: nkavaldj
'''
class sfifo_beh:
    ''' Speculative FIFO: behavioral model '''

    COMMIT = 0
    DISCARD = 1
    DISCARD_COMMIT = 2

    def __init__(self, depth, afull_th=None, aempty_th=None):
        self.depth = depth
        self.data = [] # Data (written, committed, not read )
        self.data_sw = [] # Speculatively written data
        self.data_sr = [] # Speculatively read data
        self.afull_th = afull_th if (afull_th != None) else depth//2
        self.aempty_th = aempty_th if (aempty_th != None) else depth//2
        self.ovf = False
        self.udf = False
        self.count_max = 0

    def reset(self):
        self.__init__(self.depth, self.afull_th, self.aempty_th)

    def isFull(self):
        return self.getCount() == self.depth

    def isEmpty(self):
        return len(self.data) == 0

    def isAFull(self):
        return (self.depth - self.getCount()) <= self.afull_th

    def isAEmpty(self):
        return len(self.data) <= self.aempty_th

    def isOvf(self):
        return self.ovf

    def isUdf(self):
        return self.udf

    def getCount(self):
        return len(self.data_sr) + len(self.data) + len(self.data_sw)

    def getCountMax(self):
        return self.count_max

    def getDout(self):
        return self.data[0]


    def _rcmd(self, cmd):
        if (cmd == self.DISCARD or cmd == self.DISCARD_COMMIT):
            self.data = self.data_sr + self.data
            self.data_sr = []
        elif (cmd == self.COMMIT):
            self.data_sr = []

    def _wcmd(self, cmd):
        if (cmd == self.DISCARD or cmd == self.DISCARD_COMMIT):
            self.data_sw = []
        elif (cmd == self.COMMIT):
            self.data.extend(self.data_sw)
            self.data_sw = []

    def command(self, wcmd=None, rcmd=None):
        self._wcmd(wcmd)
        self._rcmd(rcmd)

    def write(self, val, wcmd=None, rcmd=None):
        if (not self.isFull()):
            self.data_sw.append(val)
        else:
            self.ovf = True

        self._wcmd(wcmd)
        self._rcmd(rcmd)

        if (self.getCount() > self.count_max):
            self.count_max = self.getCount()

    def read(self, wcmd=None, rcmd=None):
        x = None
        if (not self.isEmpty()):
            x = self.data.pop(0)
            self.data_sr.append(x)
        else:
            self.udf = True

        self._wcmd(wcmd)
        self._rcmd(rcmd)

        return x

    def write_read(self, val, wcmd=None, rcmd=None):
        full = self.isFull()
        empty = self.isEmpty()

        if (not full):
            self.data_sw.append(val)
        else:
            self.ovf = True

        self._wcmd(wcmd)

        x = None
        if (not empty):
            x = self.data.pop(0)
            self.data_sr.append(x)
        else:
            self.udf = True

        self._rcmd(rcmd)

        if (self.getCount() > self.count_max):
            self.count_max = self.getCount()
        return x


    def status(self):
        return "FULL = {:}, EMPTY = {:}, COUNT = {:3}, AFULL = {:}, AEMPTY = {:}, OVF = {:}, UDF = {:}, COUNT_MAX = {:}, DOUT = {:}".format(int(self.isFull()), int(self.isEmpty()), int(self.getCount()), int(self.isAFull()), int(self.isAEmpty()), int(self.isOvf()), int(self.isUdf()), self.getCountMax(), self.data[0] if len(self.data)>0 else None)



        return "FULL = {:}, EMPTY = {:}, COUNT = {:3}, AFULL = {:}, AEMPTY = {:}, OVF = {:}, UDF = {:}, COUNT_MAX = {:}, DOUT = {:}".format(int(self.isFull()), int(self.isEmpty()), int(self.count()), int(self.isAFull()), int(self.isAEmpty()), int(self.isOvf()), int(self.isUdf()), self.maxCount(), self.data[0] if len(self.data)>0 else None)