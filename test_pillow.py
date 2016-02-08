#!/usr/bin/env python
# im.thumbnail(size)
# im.save('thumbnail_1.jpg', 'JPEG')
from __future__ import print_function
import os, sys
from PIL import Image

size = (256, 256)

for infile in sys.argv[1:]:
    outfile = os.path.splitext(infile)[0] + ".thumbnail"
    if infile != outfile:
        try:
            im = Image.open(infile)
            im.thumbnail(size, Image.ANTIALIAS)
            im.save(outfile, "JPEG")
        except IOError:
            print("cannot create thumbnail for", infile)
