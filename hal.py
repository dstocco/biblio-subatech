#!/usr/bin/env python

"""Utilities to query the HAL webpage"""

import urllib.request
import urllib.parse
import json


def _make_query(query_string, out_fields, ymin, ymax, size):
    query = {
        "omitHeader": "true",
        "wt": "json",
        "q": query_string,
        "rows": size,
        "fl": out_fields,
        "fq": f"producedDateY_i:[{ymin} TO {ymax}]",
    }
    return urllib.parse.urlencode(query)


def get_parsed(query_string, out_fields, ymin, ymax=2100, size=9000):
    """Query HAL website and returns a parsed dictionary"""
    query = _make_query(query_string, out_fields, ymin, ymax, size)
    url = "https://api.archives-ouvertes.fr/search/index/"
    print("Query: " + url + "?" + query)
    with urllib.request.urlopen(url, query.encode(), timeout=100) as response:
        parsed = json.loads(response.read().decode("utf-8"))
        entries = parsed["response"]["docs"]
        print(f"Entries found {len(entries)} (max set: {size})")
        return entries


def get_eprint(arxiv):
    """Returns the eprint information if any"""
    if not arxiv:
        return None
    if "/" in arxiv:
        return arxiv.split("/")[1]
    return arxiv
