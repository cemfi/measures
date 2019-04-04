from glob import glob
from itertools import tee
import json
import os
import shutil
from time import strftime

from lxml import etree
import matplotlib.pyplot as plt
from shapely.geometry import box
from tqdm import tqdm

# Template
dataset = {
    "metadata": {
        "name": "IMSLP Random",
        "date": strftime('%Y-%m-%d'),
        "contributors": ["Simon Waloschek", "Alexander Leemhuis"]
    },
    "root_dir": "imslp",
    "concordances": [],
    "sources": {}
}

count_sources = 0
count_pages = 0
count_measures = 0

# Extract data
for xml_path in tqdm(glob('../data/**/*.mei'), desc='Extract', ncols=80):
    count_sources += 1
    source_name = os.path.splitext(os.path.basename(xml_path))[0]
    score_type = os.path.normpath(xml_path).split(os.sep)[-2]

    xml = etree.parse(xml_path).getroot()

    dataset['sources'][source_name] = {
        "root_dir": source_name,
        "type": score_type,
        "pages": []
    }

    source = dataset['sources'][source_name]

    for surface in xml.xpath('//*[local-name()="surface"]'):
        count_pages += 1
        graphic = surface[0]
        image_filename = graphic.get('target').split('/')[-1]
        page_width = int(graphic.get('width'))
        page_height = int(graphic.get('height'))

        measures = []
        for zone in surface.xpath('./*[local-name()="zone"][@type="measure"]'):
            count_measures += 1
            zone_id = zone.get('{http://www.w3.org/XML/1998/namespace}id')

            # Make sure coords do not exceed page limits
            ulx = max(int(zone.get('ulx')), 0)
            uly = max(int(zone.get('uly')), 0)
            lrx = min(int(zone.get('lrx')), page_width - 1)
            lry = min(int(zone.get('lry')), page_height - 1)

            measures.append({
                "bbox": {
                    "x": ulx,
                    "y": uly,
                    "width": lrx - ulx,
                    "height": lry - uly
                }
            })

        source['pages'].append({
            "image": image_filename,
            "width": page_width,
            "height": page_height,
            "annotations": {
                "measures": measures
            }
        })


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


values = []

max_overlap = 0
max_overlap_image = None

for source in tqdm(dataset['sources'].values()):
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
                overlap = intersection.area / shapes[0].area
                values.append(overlap)
                if overlap > max_overlap:
                    max_overlap = overlap
                    max_overlap_image = f"{page['image']} {shapes[0].__str__()} {shapes[1].__str__()}"

print(f'max overlap: {max_overlap} in source {max_overlap_image}')

plt.hist(values, bins=100)
plt.xlabel('Overlap')
plt.tight_layout()
plt.show()
