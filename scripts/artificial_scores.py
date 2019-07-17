import argparse
import datetime
import json
import os
import random
import subprocess
import time

from lxml import etree, objectify
import pandas as pd
from PIL import Image, ImageDraw

options = [
    # ['--even-note-spacing', []], # ?

    ['--bar-line-width', [0.1, 0.3, 0.8]],
    ['--beam-max-slope', [1, 10, 20]],
    # ['--beam-min-slope', []], broken documentation?
    ['--font', ['Leipzig', 'Bravura', 'Gootville', 'Petaluma']],
    ['--grace-factor', [0.5, 0.75, 1.0]],
    # ['--grace-rhythm-align', []], # ?
    # ['--grace-right-align', []], # ?
    ['--hairpin-size', [1.0, 3.0, 5.0, 8.0]],
    ['--left-position', [0.0, 0.8, 2.0]],
    ['--min-measure-width', [1, 15, 30]],
    # ['--measure-number', []], # ?
    ['--slur-control-pointsr', [1, 5, 10]],
    ['--slur-curve-factor', [1, 10, 30, 50, 70, 100]],
    ['--slur-height-factor', [1, 3, 10, 30, 50, 70, 100]],
    ['--slur-min-height', [0.3, 1.2, 2.0]],
    ['--slur-max-height', [2.0, 3.0, 4.0, 5.0, 6.0]],
    ['--slur-max-slope', [0, 20, 45]],
    ['--slur-thickness', [0.2, 0.6, 1.2]],

    # ['--spacing-dur-detection', []], # ?

    ['--spacing-linear', [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]],
    ['--spacing-non-linear', [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]],

    ['--spacing-staff', [0, 8, 16, 24]],
    ['--spacing-system', [0, 3, 6, 9, 12]],
    ['--staff-line-width', [0.1, 0.15, 0.3]],
    ['--stem-width', [0.1, 0.2, 0.5]],
    ['--tie-thickness', [0.2, 0.5, 1.0]],

    ['--default-bottom-margin', [0.0, 0.5, 2.0, 5.0]],
    ['--default-left-margin', [0.0, 1.0, 2.0]],
    ['--default-right-margin', [0.0, 1.0, 2.0]],
    ['--default-top-margin', [0.5, 0.75, 1.0]],
    ['--left-margin-accid', [0.0, 1.0, 2.0]],
    ['--left-margin-bar-line', [0.0, 1.0, 2.0]],
    ['--left-margin-beat-rpt', [0.0, 1.0, 2.0]],
    ['--left-margin-chord', [0.0, 1.0, 2.0]],
    ['--left-margin-clef', [0.0, 1.0, 2.0]],
    ['--left-margin-key-sig', [0.0, 1.0, 2.0]],
    ['--left-margin-left-bar-line', [0.0, 1.0, 2.0]],
    ['--left-margin-meter-sig', [0.0, 1.0, 2.0]],
    ['--left-margin-m-rest', [0.0, 1.0, 2.0]],
    ['--left-margin-m-rpt2', [0.0, 1.0, 2.0]],
    ['--left-margin-multi-rest', [0.0, 1.0, 2.0]],
    ['--left-margin-multi-rpt', [0.0, 1.0, 2.0]],
    ['--left-margin-note', [0.0, 1.0, 2.0]],
    ['--left-margin-rest', [0.0, 1.0, 2.0]],
    ['--left-margin-right-bar-line', [0.0, 1.0, 2.0]],
    ['--right-margin-accid', [0.0, 1.0, 2.0]],
    ['--right-margin-bar-line', [0.0, 1.0, 2.0]],
    ['--right-margin-beat-rpt', [0.0, 1.0, 2.0]],
    ['--right-margin-chord', [0.0, 1.0, 2.0]],
    ['--right-margin-clef', [0.0, 1.0, 2.0]],
    ['--right-margin-key-sig', [0.0, 1.0, 2.0]],
    ['--right-margin-left-bar-line', [0.0, 1.0, 2.0]],
    ['--right-margin-mensur', [0.0, 1.0, 2.0]],
    ['--right-margin-meter-sig', [0.0, 1.0, 2.0]],
    ['--right-margin-m-rest', [0.0, 1.0, 2.0]],
    ['--right-margin-m-rpt2', [0.0, 1.0, 2.0]],
    ['--right-margin-multi-rest', [0.0, 1.0, 2.0]],
    ['--right-margin-multi-rpt', [0.0, 1.0, 2.0]],
    ['--right-margin-note', [0.0, 1.0, 2.0]],
    ['--right-margin-rest', [0.0, 1.0, 2.0]],
    ['--right-margin-right-bar-line', [0.0, 1.0, 2.0]],
]


def sample_option(option, values):
    for v in values:
        yield [option, str(v)]


def sample_all_options():
    result = []
    for option in options:
        result.append(option[0])
        result.append(str(random.choice(option[1])))
    return result


class MakeScoreVariants:
    def __init__(self, mei_path, output_dir):
        self.all_ids = []
        self.mei_path = mei_path

        self.path_result = os.path.join(output_dir, os.path.split(mei_path)[-1].replace('.mei', '').replace('.', '_'))
        if not os.path.isdir(self.path_result):
            os.mkdir(self.path_result)
            self.make_mei_no_ties()
            self.call_verovio()
            self.parse_mei()
            self.render_png()
            self.extract_bb()
            self.make_json()
            self.cleanup()
            self.move_pngs()
        else:
            print(f'{self.path_result} already exists. Skipping')

    def make_mei_no_ties(self):
        parser = etree.XMLParser(remove_comments=True)
        root = objectify.parse(self.mei_path, parser=parser)
        tie_attributes = root.xpath('//*[@tie]')
        for tie in tie_attributes:
            tie.attrib.pop('tie')
        tie_elements = root.xpath('//m:tie', namespaces={'m': "http://www.music-encoding.org/ns/mei"})
        for tie in tie_elements:
            tie.getparent().remove(tie)
        # hairpin_elements = root.xpath('//m:hairpin', namespaces={'m': "http://www.music-encoding.org/ns/mei"})
        # for hairpin in hairpin_elements:
        #     hairpin.getparent().remove(hairpin)
        mei_filename = os.path.split(self.mei_path)[-1]
        path_mei_no_ties = os.path.join(self.path_result, mei_filename)
        with open(path_mei_no_ties, 'wb') as f:
            root.write(f)

    def call_verovio(self):
        mei_filename = os.path.split(self.mei_path)[-1]
        mei_filename_noext = os.path.splitext(mei_filename)[0]
        mei_filename_noext = mei_filename_noext.replace('.', '_')
        for i in range(3):
            options = sample_all_options()
            mei_filename = os.path.split(self.mei_path)[-1]
            path_mei_no_ties = os.path.join(self.path_result, mei_filename)
            subprocess.run(
                ['verovio', path_mei_no_ties, '-o', f'{self.path_result}/{mei_filename_noext}_r{i:02d}', '--no-footer',
                 '--no-header',
                 '--adjust-page-height', '--all-pages', *options])

    def parse_mei(self):
        parser = etree.XMLParser(remove_comments=True)
        root = objectify.parse(self.mei_path, parser=parser)

        for child in root.iter():
            if child.tag.endswith('measure'):
                self.all_ids.append(child.attrib['{http://www.w3.org/XML/1998/namespace}id'])

    def render_png(self):
        for filename in sorted(os.listdir(self.path_result)):
            if filename.endswith(".svg"):
                print(f'Making PNG for {filename}')
                relative_path = os.path.join(self.path_result, filename)
                relative_path_out = relative_path.replace('.svg', '.png')
                os.system(f'inkscape {relative_path} --export-png={relative_path_out} --export-background=ffffffff')

    def extract_bb(self):
        for filename in sorted(os.listdir(self.path_result)):
            if filename.endswith(".svg"):
                print(f'Extracting bounding boxes for {filename}')
                relative_path = os.path.join(self.path_result, filename)
                relative_path_out = os.path.join(self.path_result, filename).replace('.svg', '.csv')
                os.system(f'inkscape --without-gui --query-all {relative_path} > {relative_path_out}')

    def make_json(self):
        if not os.path.isdir(f'{self.path_result}/../check'):
            os.mkdir(f'{self.path_result}/../check')

        today = datetime.datetime.now().strftime("%Y/%m/%d")
        result_json = {
            "metadata": {
                "name": os.path.split(self.path_result)[-1],
                "date": today,
                "contributors": [
                    "artificial_scores.py"
                ]
            },
            "root_dir": os.path.split(self.path_result)[-1],
            "concordances": [],
            "sources": {
                'r00': {
                    'root_dir': 'r00',
                    'type': 'printed',
                    'pages': []
                },
                'r01': {
                    'root_dir': 'r01',
                    'type': 'printed',
                    'pages': []
                },
                'r02': {
                    'root_dir': 'r02',
                    'type': 'printed',
                    'pages': []
                }
            }
        }
        for filename in sorted(os.listdir(self.path_result)):
            if filename.endswith(".svg"):
                filename_x = filename
                filename_x = filename_x.replace('.svg', '.csv')

                print(f'Filtering bounding boxes for {filename}')
                relative_path = os.path.join(self.path_result, filename_x)
                df_xdir = pd.read_csv(relative_path, names=['id', 'x', 'y', 'w', 'h'])
                df_xdir = df_xdir[df_xdir.id.isin(self.all_ids)]
                # df.to_csv(relative_path, index=False)
                df_xdir['x'] = df_xdir['x'].astype('float32')
                df_xdir['y'] = df_xdir['y'].astype('float32')
                df_xdir['w'] = df_xdir['w'].astype('float32')
                df_xdir['h'] = df_xdir['h'].astype('float32')
                df_xdir.reset_index(drop=True, inplace=True)

                relative_path_img = os.path.join(self.path_result, filename).replace('svg', 'png')
                image = Image.open(relative_path_img)
                draw = ImageDraw.Draw(image)

                image_desc = {
                    "image": filename.replace('.svg', '.png'),
                    "height": image.size[1],
                    "width": image.size[0],
                    "annotations": {
                        "measures": []
                    }
                }

                edition = ''
                if 'r00' in filename:
                    edition = 'r00'
                elif 'r01' in filename:
                    edition = 'r01'
                elif 'r02' in filename:
                    edition = 'r02'
                else:
                    assert False
                result_json['sources'][edition]['pages'].append(image_desc)

                max_x = None
                prev_xywh = None
                MIN_SIZE_W = 10
                for index, row in df_xdir[::-1].iterrows():
                    x, y, w, h = (row['x'], row['y'], row['w'], row['h'])
                    is_contained = (prev_xywh is not None) and (y + w / 2) > prev_xywh[1] and (y + w / 2) < prev_xywh[
                        1] + prev_xywh[3]
                    if max_x is not None:
                        if is_contained and x + w > max_x and max_x - x > MIN_SIZE_W:
                            w = max_x - x
                    max_x = x
                    prev_xywh = (x, y, w, h)

                    if x + w > image_desc['width']:
                        w = image_desc['width'] - x
                    if y + h > image_desc['height']:
                        h = image_desc['height'] - y
                    if index % 2 == 0:
                        color = (255, 0, 0)
                    else:
                        color = (0, 0, 255)
                    draw.line((x, y, x + w, y), fill=color, width=4)
                    draw.line((x + w, y, x + w, y + h), fill=color, width=4)
                    draw.line((x + w, y + h, x, y + h), fill=color, width=4)
                    draw.line((x, y + h, x, y), fill=color, width=4)
                    path_check = os.path.join(f'{self.path_result}/../check', filename.replace('.svg', '.png'))
                    image.save(path_check)
                    annotation = {
                        "bbox": {
                            'x': int(x),
                            'y': int(y),
                            'width': int(w),
                            'height': int(h)
                        }
                    }
                    image_desc['annotations']['measures'].append(annotation)

                image_desc['annotations']['measures'] = [x for x in reversed(image_desc['annotations']['measures'])]

        page_r01 = 0
        measure_idx_r01 = 0
        page_r02 = 0
        measure_idx_r02 = 0
        for page_r00 in range(len(result_json['sources']['r00']['pages'])):
            for measure_idx_r00 in range(len(result_json['sources']['r00']['pages'][page_r00]['annotations']['measures'])):
                result_json['concordances'].append([
                    {
                        'source': 'r00',
                        'page': page_r00,
                        'measure': measure_idx_r00
                    },
                    {
                        'source': 'r01',
                        'page': page_r01,
                        'measure': measure_idx_r01
                    },
                    {
                        'source': 'r02',
                        'page': page_r02,
                        'measure': measure_idx_r02
                    }
                ])
                measure_idx_r01 += 1
                measure_idx_r02 += 1
                if measure_idx_r01 == len(result_json['sources']['r01']['pages'][page_r01]['annotations']['measures']):
                    measure_idx_r01 = 0
                    page_r01 += 1
                if measure_idx_r02 == len(result_json['sources']['r02']['pages'][page_r02]['annotations']['measures']):
                    measure_idx_r02 = 0
                    page_r02 += 1

        with open(f'{self.path_result}/dataset.json', 'w') as f:
            json.dump(result_json, f, indent=4)

    def show_variability(self):
        mei_filename = os.path.split(self.mei_path)[-1]
        mei_filename_noext = os.path.splitext(mei_filename)[0]
        for option in options:
            command = option[0]
            for argument in option[1]:
                str_arg = str(argument).replace('.', ',')
                subprocess.run(
                    ['verovio', self.mei_file, '-o', f'{self.path_result}/{mei_filename_noext}{command}{str_arg}',
                     '--no-footer',
                     '--no-header', '--adjust-page-height', command, str(argument)])

    def cleanup(self):
        for filename in sorted(os.listdir(self.path_result)):
            if filename.endswith('.csv') or filename.endswith('.svg') or filename.endswith('.mei'):
                os.remove(os.path.join(self.path_result, filename))

    def move_pngs(self):
        output_dir = self.path_result
        os.mkdir(os.path.join(output_dir, 'r00'))
        os.mkdir(os.path.join(output_dir, 'r01'))
        os.mkdir(os.path.join(output_dir, 'r02'))
        os.system(f'mv {self.path_result}/*r00* {output_dir}/r00/')
        os.system(f'mv {self.path_result}/*r01* {output_dir}/r01/')
        os.system(f'mv {self.path_result}/*r02* {output_dir}/r02/')

def main():
    parser = argparse.ArgumentParser(description='Generate artificial dataset from MEI file.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--mei_file', metavar='FILE', type=str, help='an MEI file')
    group.add_argument('--mei_dir', metavar='DIRECTORY', type=str, help='a directory with MEI files in it')
    parser.add_argument('--output_dir', metavar='DIR', type=str, help="the output directory", required=False)
    args = parser.parse_args()

    output_dir = args.output_dir
    if output_dir == None:
        output_dir = 'rendered'
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    if args.mei_file is not None:
        MakeScoreVariants(args.mei_file, output_dir)
    else:
        for filename in sorted(os.listdir(args.mei_dir)):
            if filename.endswith('.mei') or filename.endswith('.xml'):
                MakeScoreVariants(os.path.join(args.mei_dir, filename), output_dir)


if __name__ == '__main__':
    main()
