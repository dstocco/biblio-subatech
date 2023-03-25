#!/usr/bin/env python3
import sys
import argparse
import hal


def _getData(group, docTypes, ymin):
    entries = {}
    for dt in docTypes:
        entries[dt] = hal.getParsed("collCode_s:{} docType_s:{}".format(
            group, dt), "halId_s,producedDateY_i", ymin)
    return entries


def _count(entries):
    pubs = {}
    for entry in entries:
        year = entry.get("producedDateY_i")
        if not year:
            print("Caveat: no year found in")
            print(entry)
            year = "0"
        if not year in pubs:
            pubs[year] = 0
        pubs[year] += 1
    return pubs


def _showStats(entries, min):
    pubs = _count(entries)
    for key in sorted(pubs.keys(), reverse=True):
        if (int(key) < min):
            continue
        print("{}: {}".format(key, pubs[key]))
    return 0


def show_stats(group, docTypes, ymin):
    data = _getData(group, docTypes, ymin)
    for key, val in data.items():
        print("Publication type: " + key)
        _showStats(val, ymin)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utility for bibliography")
    parser.add_argument("--group", help="Subatech group",
                        default="SUBATECH-PLASMA")
    parser.add_argument("--ymin", help="Minimum year",
                        type=int, default=2015)

    args = parser.parse_args()
    docTypes = ["ART", "COMM", "THESE", "POSTER"]
    rc = show_stats(args.group, docTypes, args.ymin)

    sys.exit(rc)
