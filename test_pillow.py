#!/usr/bin/env python
from PIL import Image
im = Image.open('1.jpg')
# size = (400,300)
# im.thumbnail(size)
# im.save('thumbnail_1.jpg', 'JPEG')
def roll(image, delta):
    "Roll an image sideways"

    xsize, ysize = image.size

    delta = delta % xsize
    if delta == 0: return image

    part1 = image.crop((0, 0, delta, ysize))
    part2 = image.crop((delta, 0, xsize, ysize))
    image.paste(part2, (0, 0, xsize-delta, ysize))
    image.paste(part1, (xsize-delta, 0, xsize, ysize))

    return image
if __name__ == '__main__':
	t_im = roll(im,400)
	t_im.save('roll_1.jpg','JPEG')