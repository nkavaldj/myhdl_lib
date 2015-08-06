import random
import copy

def payload_generator(levels=0, dimensions=None, sequential=True, string=True, max_int=255, max_pkt_len=150, max_dim_size=3):
    """ Generates random data in a form of nested lists, to be used as a test packet payload
            levels - nesting levels:
                0 - list of integers (single packet payload)
                1 - list of lists of integers (list of packets)
                2 - list of lists of lists of integers (list of packets, each packet containing list of messages)
                etc.
            dimensions - specifies the size of the lists; the specification can be partial, as what is not specified will be chosen randomly
                if level=0:
                    dimensions=None - list of integers of random length in the range [1,max_pkt_len]
                    dimensions=5 - list of integers of length 5
                if level=1:
                    dimensions=None - list of random length in the range [1, max_dim_size], each element is an integer list of random length in the range [1, max_pkt_len]
                    dimensions=5 - list of length 5, each element is an integer list of random length in the range [1, max_pkt_len]
                    dimensions=[2, 3] - list of 2 elements, each element is an integer list, the first one of length 2, the second on of length 3
                if level=2:
                    dimensions=None - list of random length in the range [1, max_dim_size], each element is a list of random length in the range [1, max_dim_size], 
                                      each element of the second level lists is an integer list of random length in the range [1, max_pkt_len]
                    dimensions=5 - list of length 5, each element is a list of random length in the range [1, max_dim_size], each element of the second level lists 
                                   is an integer list of random length in the range [1, max_pkt_len]
                    dimensions=[2, 3] - list of 2 elements, each element is a list, the first one of length 2, the second on of length 3, each element of the second 
                                        level lists is an integer list of random length in the range [1, max_pkt_len]
                    dimensions=[[3, 5], [6, 7, 8]] - list of 2 elements, each element is a list, the first one of length 2, the second on of length 3, each element of the second 
                                        level lists is an integer list of length respectively 3, 5, 6, 7, 8
                if level=3:
                    etc.
                It is possible to specify dimensions partially, e.g dimensions=[[3, None], [6, 7, 8]] or dimensions=[None, [6, 7, 8]]. Dimensions that are not specified are 
                chosen randomly
            sequential - if True, the payload is a cyclic sequence if integers in the range [0, max_int]
                         if False, the payload is a sequence of random integers in the range [0, max_int]
            string - if True, the payload is a byte string, e.g. '\x04\x05\x06\x07' as each byte is in the range [0, min(255, max_int)]
                     if False, the payload is a list of integers in the range [0, max_int]
            max_int - Upper limit for the integer range for the payload
            max_pkt_len - Upper limit for the randomly chosen payload length
            max_dim_size - Upper limit for the randomly chosen dimension sizes
    """

    MAX_INT = max_int
    if string:
        MAX_INT = min(255, max_int)

    MAX_DIM_SIZE = max_dim_size
    MAX_PKT_LEN = max_pkt_len

    def next_i():
        ''' Generates next number from a cyclic integer sequence [0..MAX_INT]'''
        next_i.i = (next_i.i+1)%(MAX_INT+1)
        return next_i.i
    next_i.i = 0;

    def payload(length):
        ''' Generates payload of given length '''
        if (sequential) :
            pld = [next_i() for _ in xrange(length)]
        else:
            pld = [random.randint(0, MAX_INT) for _ in xrange(length)]
        if string:
            pld = str(bytearray(pld))
        return pld

    def next_level(level, pld):
        ''' Generates the next level of nested lists '''
        if level>0:
            # Next level of nested lists
            if pld==None:
                pld = random.randint(1, MAX_DIM_SIZE)
            if isinstance(pld, int):
                pld = pld*[None]
            if isinstance(pld, list):
                for i in range(len(pld)):
                    pld[i] = next_level(level-1, pld[i])
                return pld
            else:
                raise TypeError("Expected None, int or list, got {}: {}".format(type(pld), pld))
        elif level==0:
            # Generate payload
            if pld==None:
                pld = random.randint(1, MAX_PKT_LEN)
            if isinstance(pld, int):
                return payload(pld)
            else:
                raise TypeError("Expected None or int, got {}: {}".format(type(pld), pld))
        else:
            raise ValueError("Expected int>=0, got {}".format(level))

    pld = copy.deepcopy(dimensions)

    pld = next_level(levels, pld)

    return pld


if __name__ == '__main__':
    print payload_generator(levels=2, dimensions=[[3,4,5],[5,5,5]], sequential=False, string=False, max_int=8)
#     pass
