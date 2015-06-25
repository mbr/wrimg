#!/usr/bin/env python

import os
import sys
import time


source = '/dev/zero'
dest = '/dev/sdg'

min_chunk_size = 4 * 1024
chunk_size = min_chunk_size
max_chunk_size = min_chunk_size * 1024 * 4

adaptive = True
total = 4 * 10 * 1024 * 1024


with open(source, 'rb') as src, open(dest, 'wb') as dst:
    while total:
        # measure time
        start = time.time()

        buf = src.read(min(total, chunk_size))
        dst.write(buf)
        dst.flush()
        os.fsync(dst.fileno())

        end = time.time()

        # adjust chunk size if needed
        if adaptive:
            if end - start > 2 and chunk_size > min_chunk_size:
                # took longer then two seconds, halve chunk_size
                chunk_size //= 2
                print '-',
            elif end - start < 0.5 and chunk_size < max_chunk_size:
                chunk_size *= 2
                print '+',

        total -= len(buf)
        print '.',
        sys.stdout.flush()
    print src
    print dst
