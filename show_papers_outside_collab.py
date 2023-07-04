#!/usr/bin/env python3
import sys
import argparse
import urllib.request
import urllib.parse
import json
import hal


def _updateMetadata(entries):
    print("Collecting additional metadata from INSPIRE-HEP. This may take a while")
    for entry in entries:
        if entry.get("collaboration_s"):
            continue
        url = "https://inspirehep.net/api/"
        doi = entry.get("doiId_s")
        if doi:
            url += "doi/" + doi
        else:
            arxiv = entry.get("arxivId_s")
            if arxiv:
                url += "arxiv/" + arxiv
        with urllib.request.urlopen(url) as req:
            inspire = json.loads(req.read().decode("utf-8"))
            insmeta = inspire.get("metadata")
            if insmeta:
                collabs = insmeta.get("collaborations")
                if collabs:
                    entry["collaboration_s"] = collabs[0]["value"]


def show_papers_outside_collab(group, ymin):
    entries = hal.getParsed(
        "collCode_s:{} docType_s:ART".format(group),
        "halId_s,authFullName_s,collaboration_s,title_s,arxivId_s,doiId_s,producedDateY_i",
        ymin,
    )
    _updateMetadata(entries)
    papers = []
    for entry in entries:
        if "collaboration_s" in entry:
            continue
        papers.append(entry)

    for entry in sorted(papers, key=lambda pap: pap["halId_s"]):
        print(
            "id: {}  year: {}  first_author: {}  title: {}".format(
                entry["halId_s"],
                entry["producedDateY_i"],
                entry["authFullName_s"][0],
                entry["title_s"],
            )
        )

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utility for bibliography")
    parser.add_argument("--group", help="Subatech group", default="SUBATECH-PLASMA")
    parser.add_argument("--ymin", help="Minimum year", type=int, default=2007)

    args = parser.parse_args()
    rc = show_papers_outside_collab(args.group, args.ymin)

    sys.exit(rc)
