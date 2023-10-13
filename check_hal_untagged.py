#!/usr/bin/env python

"""Check for entries in HAL that are tagged as SUBATECH but not tagged for a sub-group"""

import sys
import re
import os
import argparse
import yaml
import hal


def get_members():
    """Read the members of the groups"""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    groups_dir = os.path.join(script_dir, "groups")
    groups = os.listdir(groups_dir)
    members = {}
    for group in groups:
        filename = os.path.join(groups_dir, group, "members.yaml")
        if os.path.exists(filename):
            with open(filename, encoding="utf-8") as in_file:
                gm = yaml.safe_load(in_file)
                members[group] = {}
                for author, info in gm.items():
                    auth_info = {"ymin": 2000, "ymax": 2100}
                    if info:
                        if "ymin" in info:
                            auth_info["ymin"] = info["ymin"]
                        if "ymax" in info:
                            auth_info["ymax"] = info["ymax"]
                    members[group][author] = auth_info
    return members


def check_hal_untagged(ymin, ymax):
    """Main function: check for entries in HAL that are tagged as SUBATECH but not tagged for a sub-group"""
    members = get_members()
    members_regex = {}
    for group, auth_info in members.items():
        members_regex = {}
        for author, info in auth_info.items():
            group_info = {"group": group, "ymin": info["ymin"], "ymax": info["ymax"]}
            if not author in members_regex:
                members_regex[author] = {
                    "groups": [],
                    "re": re.compile(r"\b{}\b".format(author), re.IGNORECASE),
                }
            members_regex[author]["groups"].append(group_info)

    entries = hal.get_parsed(
        "collCode_s:SUBATECH",
        "halId_s,collCode_s,authFullName_s,title_s,authIdHasPrimaryStructure_fs,producedDateY_i",
        ymin,
        ymax,
    )
    untagged = {}
    for entry in sorted(entries, key=lambda item: item["halId_s"]):
        year = int(entry["producedDateY_i"])
        found = False
        for colls in entry["collCode_s"]:
            if "SUBATECH-" in colls:
                found = True
                break

        if found:
            continue

        # Search for known members of subatech groups in this entry
        authors_found = []
        group = "UNKNOWN"
        for auth_inst in entry["authIdHasPrimaryStructure_fs"]:
            if (
                "SUBATECH" in auth_inst
                or "Laboratoire de physique subatomique et des technologies associées"
                in auth_inst
            ):
                fmt_auth_inst = re.sub(r"_JoinSep_[0-9]+_FacetSep_", " ", auth_inst)
                for author, info in members_regex.items():
                    if info["re"].search(fmt_auth_inst):
                        for group_info in info["groups"]:
                            if (
                                year >= group_info["ymin"]
                                and year <= group_info["ymax"]
                            ):
                                authors_found.append(author)
                                group = group_info["group"]
                            break
        info = {
            "id": entry["halId_s"],
            "title": entry["title_s"][0],
            "authors": authors_found,
        }
        if group not in untagged:
            untagged[group] = []
        untagged[group].append(info)

    for group, info in sorted(untagged.items()):
        print(f"\nUntagged for {group}:")
        for val in info:
            out = val["id"]
            if val["authors"]:
                out += ": found authors {}  title: {}".format(
                    ",".join(val["authors"]), val["title"]
                )
            print(out)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utility for bibliography")
    parser.add_argument("--ymin", help="Minimum year", type=int, default="2010")
    parser.add_argument("--ymax", help="Maximum year", type=int, default="2100")

    args = parser.parse_args()
    RET_CODE = check_hal_untagged(args.ymin, args.ymax)
    sys.exit(RET_CODE)
