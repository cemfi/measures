from glob import glob
import json
import os
import shutil
from time import strftime

from lxml import etree
from tqdm import tqdm

image_root = 'E:/Zu Vertakten'
dst_path = '../exported'

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

# Extract data
for xml_path in tqdm(glob('../data/**/*.mei'), desc='Extract', ncols=80):
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
        graphic = surface[0]
        image_filename = graphic.get('target').split('/')[-1]
        page_width = int(graphic.get('width'))
        page_height = int(graphic.get('height'))

        measures = []
        for zone in surface.xpath('./*[local-name()="zone"][@type="measure"]'):
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

# Copy image files
os.makedirs(dst_path, exist_ok=True)

for source in tqdm(dataset['sources'].values(), desc='Copy', ncols=80):
    src = os.path.join(
        image_root,
        source['type'],
        source['root_dir']
    )
    dst = os.path.join(
        dst_path,
        'imslp',
        source['root_dir']
    )

    shutil.copytree(src, dst)

# Write dataset.json
with open(os.path.join(dst_path, 'imslp', 'dataset.json'), 'w') as fp:
    json.dump(dict(dataset), fp, indent=2)
