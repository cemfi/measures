from itertools import tee
import json

from shapely.geometry import box
from tqdm import tqdm
import matplotlib.pyplot as plt


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


values = []
dataset_path = '../exported/imslp/dataset.json'

with open(dataset_path) as fp:
    data = json.load(fp)
for source in tqdm(data['sources'].values()):
    for page in source['pages']:
        measures = page['annotations']['measures']
        pairs = pairwise(measures)
        for pair in pairs:
            shapes = []
            for shape in pair:
                bbox = shape['bbox']
                shape_box = box(
                    bbox['x'],
                    bbox['y'],
                    bbox['x'] + bbox['width'],
                    bbox['y'] + bbox['height'],
                )
                shapes.append(shape_box)
            intersection = shapes[0].intersection(shapes[1])
            if shapes[0].area != 0 and intersection.area != 0:
                values.append(intersection.area / shapes[0].area)

plt.hist(values, bins=100)
plt.xlabel('Overlap')
plt.tight_layout()
plt.show()
