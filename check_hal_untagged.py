#!/usr/bin/env python

"""Check for entries in HAL that are tagged as SUBATECH but not tagged for a sub-group"""

import sys
import re
import os
import argparse
import yaml
import hal


def _read_members():
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


def _get_members_dict(members):
    """
    Reorganize member information: use author surname as key and store:
    - a regex to match the author surname
    - the information of the author belonging to a group
    """
    members_regex = {}
    for group, auth_info in members.items():
        for author, info in auth_info.items():
            group_info = {"group": group, "ymin": info["ymin"], "ymax": info["ymax"]}
            if not author in members_regex:
                members_regex[author] = {
                    "groups": [],
                    "re": re.compile(r"\b{}\b".format(author), re.IGNORECASE),
                }
            members_regex[author]["groups"].append(group_info)
    return members_regex


def _has_group_tag(entry):
    """Check if the entry in HAL has a group tag"""
    for colls in entry["collCode_s"]:
        if "SUBATECH-" in colls:
            return True
    return False


def _matched_authors(fmt_auth_inst_list, members_regex):
    """Search for surname matching known subatech members in the lisit of authors"""
    matched = []
    for fmt_auth_inst in fmt_auth_inst_list:
        for author, info in members_regex.items():
            if info["re"].search(fmt_auth_inst):
                matched.append(author)
    return matched


def _matched_authors_and_groups(matched_authors, members_regex, entry):
    """
    Check if the author was really affiliated to a subatech group
    in the year of the publication
    """
    year = int(entry["producedDateY_i"])
    matched = {}
    for author in matched_authors:
        info = members_regex.get(author)
        for group_info in info["groups"]:
            if group_info["ymin"] <= year <= group_info["ymax"]:
                group = group_info["group"]
                if not group in matched:
                    matched[group] = []
                matched[group].append(author)
    return matched


def check_hal_untagged(ymin, ymax):
    """Main function: check for entries in HAL that are tagged as SUBATECH but not tagged for a sub-group"""
    # Load the group members information
    members = _read_members()

    # Create a dictionary with author keys
    # and assign a list of groups and a regex to match the author in publication
    members_regex = _get_members_dict(members)

    # Retrieve the bibliography from HAL
    entries = hal.get_parsed(
        "collCode_s:SUBATECH",
        "halId_s,collCode_s,authFullName_s,title_s,authIdHasPrimaryStructure_fs,producedDateY_i",
        ymin,
        ymax,
    )

    # Loop on entries
    untagged = {}
    for entry in sorted(entries, key=lambda item: item["halId_s"]):
        if _has_group_tag(entry):
            continue

        # Extract the list of authors affiliated with subatech
        fmt_auth_inst_list = [
            re.sub(r"_JoinSep_[0-9]+_FacetSep_", " ", auth_inst)
            for auth_inst in entry["authIdHasPrimaryStructure_fs"]
            if "SUBATECH" in auth_inst
            or "Laboratoire de physique subatomique et des technologies associées"
            in auth_inst
        ]

        # Search for known members of subatech groups in this entry
        possible_matches = _matched_authors(fmt_auth_inst_list, members_regex)

        # Build output
        matched = _matched_authors_and_groups(possible_matches, members_regex, entry)

        info = {"id": entry["halId_s"], "title": entry["title_s"][0], "authors": []}
        if not matched:
            matched["UNKNOWN"] = []
        for group, authors in matched.items():
            info["authors"] = authors
            if not group in untagged:
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
