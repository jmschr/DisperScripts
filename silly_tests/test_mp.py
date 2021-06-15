# ##############################################################################
#  Copyright (c) 2021 Aquiles Carattino, Dispertech B.V.                       #
#  test_mp.py is part of disperscripts                                         #
#  This file is released under an MIT license.                                 #
#  See LICENSE.MD for more information.                                        #
# ##############################################################################

import multiprocessing as mp
import time


time.sleep(2)
print('First message!')

def do_something():
    print('Doing something')


if __name__ == '__main__':
    t0 = time.time()
    do_something()
    print(f'Elapsed time: {time.time()-t0}')

    # t0 = time.time()
    p = mp.Process(target=do_something)
    p.start()

    p.join()
    print(f'Elapsed time: {time.time() - t0}')
