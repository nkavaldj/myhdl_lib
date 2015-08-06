import unittest

from myhdl_lib.simulation.payload_generator import payload_generator

class TestPayloadGenerator(unittest.TestCase):


    def testLevels(self):
        MAX_INT = 67
        MAX_PKT_LEN = 7
        MAX_DIM_SIZE = 14

        for _ in range(10):
            for l in range(0, 3):
                pld = payload_generator(levels=l, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=False, sequential=False)

                pld = [pld] # level -1
                for _ in range(l):
                    # For each level
                    for ls in pld:
                        # check sublevels
                        assert isinstance(ls, list)
                        assert 1<=len(ls)
                        assert len(ls)<=MAX_DIM_SIZE
                    # flatten
                    pld = [x for ls in pld for x in ls]

                # For level 1
                for ls in pld:
                    # check payload length
                    assert isinstance(ls, list)
                    assert 1<=len(ls)
                    assert len(ls)<=MAX_PKT_LEN, "{}".format(ls)
                # flatten
                pld = [x for ls in pld for x in ls]

                # for level 0
                for x in pld:
                    # check payload elements
                    assert isinstance(x, int)
                    assert 0<=x
                    assert x<=MAX_INT

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()