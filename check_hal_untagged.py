#!/usr/bin/env python3

"""Check for entries in HAL that are tagged as SUBATECH but not tagged for a sub-group"""

import sys
import re
import os
import urllib
import argparse
import unicodedata
import yaml
import hal


def _extract_data_in_html_tag(html, tag, cl=None):
    """Extract the data between html tags"""
    reg_str = "<" + tag
    if cl:
        reg_str += f' class="{cl}"'
    reg_str += ">(.*?)</" + tag + ">"
    return re.findall(reg_str, html)


def _get_members_from_ldap():
    """Gets the Subatech members and their group from LDAP"""
    print("Query member list from ldap")
    with urllib.request.urlopen("https://annuaire.in2p3.fr/laboratory/11") as response:
        html = response.read().decode()
        authors = _extract_data_in_html_tag(html, "strong")
        groups = _extract_data_in_html_tag(html, "td", "text-black-50")

        members = {}
        author_group = zip(authors, groups)
        for author, grp in author_group:
            group = "SUBATECH-" + grp
            if group not in members:
                members[group] = {}
            members[group][author.lower()] = {"ymin": 2000, "ymax": 2100}
        return members


def _read_members():
    """Read the group members in local yaml files (if present)"""
    print("Read additional member information")
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


def _remove_accents(input_str):
    """Remove accents"""
    return "".join(
        c
        for c in unicodedata.normalize("NFD", input_str)
        if unicodedata.category(c) != "Mn"
    )


def _find_groups(auth, members_regex, year):
    """Find groups to which the author was affiliated at the time of publication"""
    matched_groups = {}
    norm_auth = _remove_accents(auth)
    for info in members_regex.values():
        if info["re"].search(norm_auth):
            for group_info in info["groups"]:
                if group_info["ymin"] <= year <= group_info["ymax"]:
                    group = group_info["group"]
                    if not group in matched_groups:
                        matched_groups[group] = []
                    matched_groups[group].append(auth)
            break
    if not matched_groups:
        matched_groups["UNKNOWN"] = [auth]
    return matched_groups


def _group_authors(affiliated_authors, members_regex, year):
    """
    Matches the the authors affiliated to subatech in HAL
    with the known list of authors
    """
    grouped = {}
    for auth in affiliated_authors:
        matched_groups = _find_groups(auth, members_regex, year)
        for group, authors in matched_groups.items():
            if not group in grouped:
                grouped[group] = []
            grouped[group] += authors
    return grouped


def _get_doc_types(info):
    """Returns the document type"""
    doc_types = set()
    for doc in info:
        doc_types.add(doc["doc_type"])
    return doc_types


def _print_summary(untagged):
    """Prints a summary for the untagged entry"""
    for group, info in sorted(untagged.items()):
        print(f"\nUntagged for {group}:")
        doc_types = _get_doc_types(info)
        for doc_type in sorted(doc_types):
            per_doc = [doc for doc in info if doc["doc_type"] == doc_type]
            if not per_doc:
                continue
            print("- doc_type: " + doc_type)
            for doc in per_doc:
                out = "  " + doc["id"]
                out += '  title: "' + doc["title"] + '"'
                authors = doc.get("authors")
                if authors:
                    out += ". Found authors: " + ",".join(authors)
                print(out)


def _get_auth_inst(auth_struct):
    """Extract the name and institute from the dedicated HAL field"""
    f_sep = "_FacetSep_"
    j_sep = "_JoinSep_"
    name_start = auth_struct.find(f_sep) + len(f_sep)
    name_end = auth_struct.find(j_sep)
    lab_start = auth_struct.find(f_sep, name_start) + len(f_sep)
    return {"author": auth_struct[name_start:name_end], "inst": auth_struct[lab_start:]}


def _get_affiliated_authors(auth_struct_list, inst_list):
    """Get the list of authors that are affiliated to one institute in the list in HAL"""
    affiliated = []
    for auth_struct in auth_struct_list:
        auth_inst = _get_auth_inst(auth_struct)
        if auth_inst["inst"] in inst_list:
            affiliated.append(auth_inst["author"])
    return affiliated


def check_hal_untagged(ymin, ymax):
    """Main function: check for entries in HAL that are tagged as SUBATECH but not tagged for a sub-group"""

    # Load the members from ldap
    members = _get_members_from_ldap()

    # Load the group members information
    members_local = _read_members()

    # Complete info in ldap
    for group, info in members_local.items():
        if group in members:
            for author, data in info.items():
                members[group][author] = data
        else:
            members[group] = info

    # Create a dictionary with author keys
    # and assign a list of groups and a regex to match the author in publication
    members_regex = _get_members_dict(members)

    # Retrieve the bibliography from HAL
    entries = hal.get_parsed(
        "collCode_s:SUBATECH",
        "halId_s,collCode_s,authFullName_s,title_s,authIdHasPrimaryStructure_fs,producedDateY_i,docType_s",
        ymin,
        ymax,
    )

    # Loop on entries
    untagged = {}
    for entry in sorted(entries, key=lambda item: item["halId_s"]):
        # Do nothing if the entry has at least one tagged subatech group
        # CAVEAT: there might be publications involving several
        # groups that would not be matched in this way,
        # But the number of fake positive is so large that it is better to neglect this case
        if _has_group_tag(entry):
            continue

        # Extract the list of authors affiliated with subatech
        affiliated_authors = _get_affiliated_authors(
            entry["authIdHasPrimaryStructure_fs"],
            [
                "Laboratoire SUBATECH Nantes",
                "Laboratoire de physique subatomique et des technologies associées",
            ],
        )

        year = int(entry["producedDateY_i"])

        # Split authors in groups
        grouped = _group_authors(affiliated_authors, members_regex, year)

        for group, authors in grouped.items():
            if not group in untagged:
                untagged[group] = []
            untagged[group].append(
                {
                    "id": entry["halId_s"],
                    "title": entry["title_s"][0],
                    "authors": authors,
                    "doc_type": entry["docType_s"],
                }
            )
    _print_summary(untagged)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utility for bibliography")
    parser.add_argument("--ymin", help="Minimum year", type=int, default="2010")
    parser.add_argument("--ymax", help="Maximum year", type=int, default="2100")

    args = parser.parse_args()
    RET_CODE = check_hal_untagged(args.ymin, args.ymax)
    sys.exit(RET_CODE)
