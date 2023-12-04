#!/usr/bin/env python3

"""Show statistics per group"""

import sys
import argparse
import hal


def _get_data(group, doc_types, ymin):
    entries = {}
    for dt in doc_types:
        entries[dt] = hal.get_parsed(
            f"collCode_s:{group} docType_s:{dt}",
            "halId_s,producedDateY_i",
            ymin,
        )
    return entries


def _count(entries):
    pubs = {}
    for entry in entries:
        year = entry.get("producedDateY_i")
        if not year:
            print("Caveat: no year found in")
            print(entry)
            year = "0"
        if year not in pubs:
            pubs[year] = 0
        pubs[year] += 1
    return pubs


def _show_stats(entries, ymin):
    pubs = _count(entries)
    for key in sorted(pubs.keys(), reverse=True):
        if int(key) < ymin:
            continue
        print(f"{key}: {pubs[key]}")
    return 0


def show_stats(group, doc_types, ymin):
    """Show statistics per group"""
    data = _get_data(group, doc_types, ymin)
    for key, val in data.items():
        print("Publication type: " + key)
        _show_stats(val, ymin)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utility for bibliography")
    parser.add_argument("--group", help="Subatech group", default="SUBATECH-PLASMA")
    parser.add_argument("--ymin", help="Minimum year", type=int, default=2015)

    args = parser.parse_args()
    g_doc_types = ["ART", "COMM", "THESE", "POSTER"]
    RET_CODE = show_stats(args.group, g_doc_types, args.ymin)

    sys.exit(RET_CODE)
