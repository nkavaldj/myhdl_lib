import unittest
from itertools import cycle, dropwhile, islice

from myhdl_lib.simulation.payload_generator import payload_generator

class TestPayloadGenerator(unittest.TestCase):


    def testLevels(self):
        ''' PAYLOAD_GENERATOR: Levels'''
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


    def testSequential(self):
        ''' PAYLOAD_GENERATOR: Sequential'''
        MAX_INT = 67
        MAX_PKT_LEN = 7
        MAX_DIM_SIZE = 14

        def expected_sequence(l):
            cycled = cycle(range(MAX_INT+1))
            skipped = dropwhile(lambda x: x != 1, cycled)
            sliced = islice(skipped, None, len(pld))
            return list(sliced)

        for i in range(10):
            sequential = (i%2)==0
            # Single packet
            pld = payload_generator(levels=0, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=False, sequential=sequential)
            assert isinstance(pld, list)
            if sequential:
                assert pld==expected_sequence(len(pld))
            else:
                assert pld!=expected_sequence(len(pld))

            # Two packets
            pld = payload_generator(levels=1, dimensions=2, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=False, sequential=sequential)
            assert isinstance(pld, list)
            assert len(pld)==2
            assert isinstance(pld[0], list)
            assert isinstance(pld[1], list)
            # flatten
            pld = [x for ls in pld for x in ls]
            if sequential:
                assert pld==expected_sequence(len(pld))
            else:
                assert pld!=expected_sequence(len(pld))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()