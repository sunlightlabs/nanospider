#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lifted and adapted from https://gist.github.com/vpetersson/f20efe6194460cc28d49 by @vpetersson (http://viktorpetersson.com)
who was in turn inspired by by Craig Addyman (http://www.craigaddyman.com/parse-an-xml-sitemap-with-python/)
"""

from lxml import etree, objectify
import requests

def strip_namespaces(root):
    for elem in root.getiterator():
        if not hasattr(elem.tag, 'find'): continue  # (1)
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i+1:]
    objectify.deannotate(root, cleanup_namespaces=True)
    return root

def get_sitemap(url):
    print url
    get_url = requests.get(url)

    if get_url.status_code == 200:
        return get_url.content
    else:
        get_url.raise_for_status()


def process_sitemap(s):
    doc = strip_namespaces(etree.fromstring(s))
    result = []

    for loc in doc.xpath('//loc'):
        result.append((loc.getparent().tag, loc.text.strip()))

    return result


def parse_sitemap(s):
    sitemap = process_sitemap(s)
    result = []

    while sitemap:
        loc_type, candidate = sitemap.pop()

        if loc_type == 'sitemap':
            sub_sitemap = get_sitemap(candidate)
            for i in process_sitemap(sub_sitemap):
                sitemap.append(i)
        else:
            result.append(candidate)

    return result

def get_and_parse_sitemap(url):
    return parse_sitemap(get_sitemap(url))