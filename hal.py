#!/usr/bin/env python
import requests
import datetime


def _getUrl(queryString, outFields, ymin, ymax, size):
    return "https://api.archives-ouvertes.fr/search/index/?omitHeader=true&wt=json&q={}&rows={}&fl={}&fq=producedDateY_i:[{} TO {}]".format(
        queryString, size, outFields, ymin, ymax)


def getParsed(queryString, outFields, ymin, ymax=2100, size=9000):
    url = _getUrl(queryString, outFields, ymin, ymax, size)
    print("Query: " + url)
    req = requests.get(url, timeout=100)
    parsed = req.json()
    entries = parsed["response"]["docs"]
    print("Entries found {} (max set: {})".format(len(entries), size))
    return entries


def getEprint(arxiv):
    if not arxiv:
        return None
    if "/" in arxiv:
        return arxiv.split("/")[1]
    return arxiv
