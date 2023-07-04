#!/usr/bin/env python
import urllib.request
import urllib.parse
import json


def _makeQuery(queryString, outFields, ymin, ymax, size):
    query = {
        "omitHeader": "true",
        "wt": "json",
        "q": queryString,
        "rows": size,
        "fl": outFields,
        "fq": "producedDateY_i:[{} TO {}]".format(ymin, ymax),
    }
    return urllib.parse.urlencode(query)


def getParsed(queryString, outFields, ymin, ymax=2100, size=9000):
    query = _makeQuery(queryString, outFields, ymin, ymax, size)
    url = "https://api.archives-ouvertes.fr/search/index/"
    print("Query: " + url + "?" + query)
    with urllib.request.urlopen(url, query.encode(), timeout=100) as response:
        parsed = json.loads(response.read().decode("utf-8"))
        entries = parsed["response"]["docs"]
        print("Entries found {} (max set: {})".format(len(entries), size))
        return entries


def getEprint(arxiv):
    if not arxiv:
        return None
    if "/" in arxiv:
        return arxiv.split("/")[1]
    return arxiv
