import imageio as iio
import os

def get_target_data(line):
    target_name, coords = line.strip().split(' : ')
    img = iio.imread(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        f"{target_name}.png"
    ))

    sn, tn = [int(s[-1]) for s in target_name.split('_')]
    x, y = map(int, coords.split())
    h, w = img.shape[:2]
    return sn, tn, x, y, h, w

def get_calibration_point_data(line):
    sn, coords = line.strip().split(' : ')
    sn = int(sn)
    x, y = map(int, coords.split())
    return sn, x, y