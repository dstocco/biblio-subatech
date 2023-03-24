#!/usr/bin/env python
import sys
import re
import os
import argparse
import yaml
import hal


def getMembers():
    scriptDir = os.path.dirname(os.path.realpath(__file__))
    groupsDir = os.path.join(scriptDir, "groups")
    groups = os.listdir(groupsDir)
    members = {}
    for group in groups:
        filename = os.path.join(groupsDir, group, "members.yaml")
        if os.path.exists(filename):
            with open(filename) as inFile:
                gm = yaml.safe_load(inFile)
                members[group] = {}
                for author, info in gm.items():
                    authInfo = {
                        "ymin": 2000,
                        "ymax": 2100
                    }
                    if info:
                        if "ymin" in info:
                            authInfo["ymin"] = info["ymin"]
                        if "ymax" in info:
                            authInfo["ymax"] = info["ymax"]
                    members[group][author] = authInfo
    return members


def check_hal_untagged(ymin, ymax):

    members = getMembers()
    membersRE = {}
    for group, authInfo in members.items():
        membersRE = {}
        for author, info in authInfo.items():
            groupInfo = {
                "group": group,
                "ymin": info["ymin"],
                "ymax": info["ymax"]
            }
            if not author in membersRE:
                membersRE[author] = {
                    "groups": [],
                    "re": re.compile(r"\b{}\b".format(author), re.IGNORECASE)
                }
            membersRE[author]["groups"].append(groupInfo)

    entries = hal.getParsed(
        "collCode_s:SUBATECH", "halId_s,collCode_s,authFullName_s,title_s,authIdHasPrimaryStructure_fs,producedDateY_i", ymin, ymax)
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
        authorsFound = []
        group = "UNKNOWN"
        for authInst in entry["authIdHasPrimaryStructure_fs"]:
            if "SUBATECH" in authInst or "Laboratoire de physique subatomique et des technologies associées" in authInst:
                fmtAuthInst = re.sub(
                    r'_JoinSep_[0-9]+_FacetSep_', " ", authInst)
                for author, info in membersRE.items():
                    if (info["re"].search(fmtAuthInst)):
                        for groupInfo in info["groups"]:
                            if (year >= groupInfo["ymin"] and year <= groupInfo["ymax"]):
                                authorsFound.append(author)
                                group = groupInfo["group"]
                            break
        info = {"id":  entry["halId_s"],
                "title": entry["title_s"][0],
                "authors": authorsFound
                }
        if not group in untagged:
            untagged[group] = []
        untagged[group].append(info)

    for group, info in sorted(untagged.items()):
        print("\nUntagged for {}:".format(group))
        for val in info:
            out = val["id"]
            if val["authors"]:
                out += ": found authors {}  title: {}".format(
                    ",".join(val["authors"]), val["title"])
            print(out)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utility for bibliography")
    parser.add_argument("--ymin", help="Minimum year",
                        type=int, default="2010")
    parser.add_argument("--ymax", help="Maximum year",
                        type=int, default="2100")

    args = parser.parse_args()
    rc = check_hal_untagged(args.ymin, args.ymax)
    sys.exit(rc)
