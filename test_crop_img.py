import numpy as np
from PIL import Image

RED_UPPER = np.array([255, 127, 80])
RED_LOWER = np.array([156, 0, 0])


def in_range(value):
    return (value >= RED_LOWER).all() and (value <= RED_UPPER).all()


def main(src, dst):
    array = np.array(Image.open(src))
    R, C = len(array), len(array[0])
    r0 = r1 = c0 = c1 = -1
    for r in range(R):
        for c in range(C):
            valid = check_neighbors(array, r, c, R, C)
            if not valid:
                continue
            if r0 == -1:
                r0 = r
            if c0 == -1:
                c0 = c
            r1, c1 = r, c

    cropped_array = array[r0:r1 + 1, c0:c1 + 1, :]
    Image.fromarray(cropped_array).save(dst)


def check_neighbors(mat, r, c, R, C):
    if not in_range(mat[r][c]):
        return False
    top_left = True
    bottom_right = True
    for i in range(1 << 4):
        if c + i < C:
            top_left &= in_range(mat[r][c + i])
        if r + i < R:
            top_left &= in_range(mat[r + i][c])
        if r - i > -1:
            bottom_right &= in_range(mat[r - i][c])
        if c - i > -1:
            bottom_right &= in_range(mat[r][c - i])
    return top_left or bottom_right


if __name__ == '__main__':
    main('./sample666.jpg', './sample666_output.jpg')
    main('./sample.jpg', './sample_output.jpg')
