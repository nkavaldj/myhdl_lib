import unittest
from itertools import cycle, dropwhile, islice
from struct import unpack

from myhdl_lib.simulation.payload_generator import payload_generator

class TestPayloadGenerator(unittest.TestCase):


    def testLevels(self):
        ''' PAYLOAD_GENERATOR: Levels '''
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
        ''' PAYLOAD_GENERATOR: Sequential '''
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


    def testString(self):
        ''' PAYLOAD_GENERATOR: String '''
        MAX_INT = 67
        MAX_PKT_LEN = 7
        MAX_DIM_SIZE = 14

        for i in range(10):
            string = (i%2)==0
            # Single packet
            pld = payload_generator(levels=0, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=string, sequential=False)
            if string:
                assert isinstance(pld, str)
                for x in pld:
                    assert unpack('B', x)[0] >= 0
                    assert unpack('B', x)[0] <= MAX_INT
            else:
                assert isinstance(pld, list)
                for x in pld:
                    assert isinstance(x, int)
                    assert x >= 0
                    assert x <= MAX_INT

            # Two packets
            pld = payload_generator(levels=1, dimensions=2, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=string, sequential=False)
            assert isinstance(pld, list)
            assert len(pld)==2
            if string:
                assert isinstance(pld[0], str)
                assert isinstance(pld[1], str)
                pld = pld[0]+pld[1]
                for x in pld:
                    assert unpack('B', x)[0] >= 0
                    assert unpack('B', x)[0] <= MAX_INT
            else:
                assert isinstance(pld[0], list)
                assert isinstance(pld[1], list)
                pld = pld[0]+pld[1]
                for x in pld:
                    assert isinstance(x, int)
                    assert x >= 0
                    assert x <= MAX_INT


    def testDimensions(self):
        ''' PAYLOAD_GENERATOR: Dimensions '''
        MAX_INT = 67
        MAX_PKT_LEN = 7
        MAX_DIM_SIZE = 14

        lvls = 0
        dim = None
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, str)

        dim = 10
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, str)
        assert len(pld)==dim

        dim = [10]
        with self.assertRaises(TypeError):
            payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)

        lvls = 1
        dim = None
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        for ls in pld:
            assert isinstance(ls, str)

        dim = 3
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        assert len(pld)==dim
        for ls in pld:
            assert isinstance(ls, str)

        dim = [4,6,9]
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        assert len(pld)==len(dim)
        for ls, d in zip(pld,dim):
            assert isinstance(ls, str)
            assert len(ls)==d

        dim = [4,None,9]
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        assert len(pld)==len(dim)
        for ls in pld:
            assert isinstance(ls, str)

        dim = [4,6,[9]]
        with self.assertRaises(TypeError):
            payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)

        lvls = 2
        dim = None
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        for ls in pld:
            assert isinstance(ls, list)
            for s in ls:
                assert isinstance(s, str)

        dim = 5
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        assert len(pld)==dim
        for ls in pld:
            assert isinstance(ls, list)
            for s in ls:
                assert isinstance(s, str)

        dim = [2,3,4]
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        assert len(pld)==len(dim)
        for ls in pld:
            assert isinstance(ls, list)
            for s in ls:
                assert isinstance(s, str)

        dim = [[2],[3,4],[5,6,7]]
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        assert len(pld)==len(dim)
        for ls, d in zip(pld, dim):
            assert isinstance(ls, list)
            assert len(ls)==len(d)
            for s, dd in zip(ls,d):
                assert isinstance(s, str)
                assert len(s)==dd

        dim = [[2],[3,None],[5,6,7]]
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        assert len(pld)==len(dim)
        for ls, d in zip(pld, dim):
            assert isinstance(ls, list)
            assert len(ls)==len(d)
            for s in ls:
                assert isinstance(s, str)

        dim = [[2],None,[5,6,7]]
        pld = payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)
        assert isinstance(pld, list)
        assert len(pld)==len(dim)
        for ls in pld:
            assert isinstance(ls, list)
            for s in ls:
                assert isinstance(s, str)

        dim = [[2],[3,[4]],[5,6,7]]
        with self.assertRaises(TypeError):
            payload_generator(levels=lvls, dimensions=dim, max_int=MAX_INT, max_pkt_len=MAX_PKT_LEN, max_dim_size=MAX_DIM_SIZE, string=True, sequential=False)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()