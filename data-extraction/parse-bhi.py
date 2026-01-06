#!/usr/bin/env python
# coding: utf-8

# # DBLP VIS Paper Parser
# 
# This code extracts papers and their deduped authors from DBLP.
# To run this code first do the following:
# 
# - Go to the DBLP website https://dblp.org/xml/
# - Download the latest .xml and .dtd and put them into the **data** subfolder folder of the dblp-data-extraction folder in this repository.
# 
# 
# 
# This code is inspired by and copies from: https://github.com/26hzhang/DBLPParser/blob/master/src/dblp_parser.py
# 
# A DBLP parser by ZHANG HAO

from lxml import etree
import re
import codecs
from tqdm import tqdm
from time import sleep
import ujson
import gzip

all_elements = {"article", "inproceedings", "proceedings", "book", "incollection", "phdthesis", "mastersthesis", "www"}

def context_iter(dblp_path):
    """Create a dblp data iterator of (event, element) pairs for processing"""
    if dblp_path.endswith(".gz"):
        dblp_path = gzip.open(dblp_path)
    return etree.iterparse(source=dblp_path, dtd_validation=True, load_dtd=True)

def clear_element(element):
    """Free up memory for temporary element tree after processing the element"""
    element.clear()
    while element.getprevious() is not None:
        del element.getparent()[0]

def extract_feature(elem, features, include_key=False):
    """Extract the value of each feature"""
    if include_key:
        attribs = {'key': [elem.attrib['key']]}
    else:
        attribs = {}
    for feature in features:
        attribs[feature] = []
    for sub in elem:
        if sub.tag not in features:
            continue
        if sub.tag == 'title':
            text = re.sub("<.*?>", "", etree.tostring(sub).decode('utf-8')) if sub.text is None else sub.text
        else:
            text = sub.text
        if text is not None and len(text) > 0:
            attribs[sub.tag] = attribs.get(sub.tag) + [text]
    return attribs

def parse_bhi(dblp_path, save_path, save_to_csv=False, include_key=True):
    type_name = ['inproceedings']  # Assuming "conf/bhi" publications are in "inproceedings"
    features = ['title', 'author', 'year', 'ee']  # Properties to extract

    def is_bhi_publication(key):
        return key.lower().startswith('conf/bhi')

    def parse_entity_bhi(dblp_path, save_path, type_name, features=None, save_to_csv=False, include_key=False):
        print("PROCESS: Start parsing for {}...".format(str(type_name)))
        assert features is not None, "features must be assigned before parsing the dblp dataset"
        results = []
        attrib_count, full_entity, part_entity = {}, 0, 0
        pbar = tqdm(position=0, leave=True)

        itercount = 0
        iterstep = 100000

        for _, elem in context_iter(dblp_path):

            if itercount >= iterstep:
                sleep(0.1)
                pbar.update(iterstep)
                itercount = 0
            itercount = itercount + 1

            if elem.tag in type_name:
                attrib_values = extract_feature(elem, features, include_key)  # extract required features
                key = attrib_values['key'][0]
                if is_bhi_publication(key):
                    results.append(attrib_values)  # add record to results array
                    for key, value in attrib_values.items():
                        attrib_count[key] = attrib_count.get(key, 0) + len(value)
                    cnt = sum([1 if len(x) > 0 else 0 for x in list(attrib_values.values())])
                    if cnt == len(features):
                        full_entity += 1
                    else:
                        part_entity += 1
            elif elem.tag not in all_elements:
                continue

            clear_element(elem)

        with codecs.open(save_path, mode='w', encoding='utf8', errors='ignore') as f:
            ujson.dump(results, f)
        return full_entity, part_entity, attrib_count

    info = parse_entity_bhi(dblp_path, save_path, type_name, features, save_to_csv=save_to_csv, include_key=include_key)
    print('Total BHI publications found: {}, publications contain all features: {}, publications contain part of features: {}'
            .format(info[0] + info[1], info[0], info[1]))
    print("Features information: {}".format(str(info[2])))

dblp_path = '../data/extraction/dblp.xml'
save_path = '../data/extraction/bhi_publications.json'
try:
    context_iter(dblp_path)
    print("LOG: Successfully loaded \"{}\".".format(dblp_path))
except IOError:
    print("ERROR: Failed to load file \"{}\". Please check your XML and DTD files.".format(dblp_path))

parse_bhi(dblp_path, save_path, save_to_csv=False)
print("DONE")



