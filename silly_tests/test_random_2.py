# ##############################################################################
#  Copyright (c) 2021 Aquiles Carattino, Dispertech B.V.                       #
#  test_random_2.py is part of disperscripts                                   #
#  This file is released under an MIT license.                                 #
#  See LICENSE.md.MD for more information.                                        #
# ##############################################################################

import multiprocessing as mp
import numpy as np

def do_fft(img):
    np.fft.fft2(img)

if __name__ == '__main__':
    img = np.random.random((10000, 10000))
    imgs = [img for _ in range(5)]
    pool = mp.Pool(5)
    pool.map(do_fft, imgs)
