#!/usr/bin/env python

"""Module to properly read and format the conference information"""

import csv
import os
import re
import json
import yaml
import hal


def _is_same_title(title, ref_title):
    words = title.split(" ")
    n_words = len(words)
    n_found = 0
    for word in words:
        if word in ref_title:
            n_found += 1
    return float(n_found) / float(n_words) > 0.6


def _check_duplicated(contrib, merged_contributions):
    for merged in merged_contributions:
        if contrib.get("lastname") and merged.get("lastname"):
            if contrib["lastname"] == merged["lastname"]:
                if _is_same_title(contrib["title"], merged["title"]):
                    # The contribution is already present
                    # Let us add any additional information
                    # that might be present in the second contribution
                    for key in contrib.keys():
                        if key not in merged:
                            merged[key] = contrib[key]
                    return True
    return False


def _add_contribution(event, merged_list):
    # Add the contributions
    for merged_event in merged_list:
        if event["start"] == merged_event["start"]:
            end1 = event.get("end")
            end2 = merged_event.get("end")
            if end1 and end2 and (end1 != end2):
                continue
            for contrib in event["contributions"]:
                if _check_duplicated(contrib, merged_event["contributions"]):
                    print("Duplicated contribution:")
                    print(contrib)
                else:
                    merged_event["contributions"].append(contrib)
            return
    merged_list.append(event)


def _merge_events(event_list):
    # Merges the contributions in the same event
    merged_list = []
    for event in event_list:
        _add_contribution(event, merged_list)
    for event in merged_list:
        # sort
        contributions = event.get("contributions")
        if contributions:
            event["contributions"] = sorted(
                contributions,
                key=lambda sel: sel.get("lastname") if "lastname" in sel else "zzz",
            )
    return merged_list


def _get_meeting_type(title):
    if re.search("workshop", title, re.IGNORECASE):
        return "Workshop"
    if re.search("symposium", title, re.IGNORECASE):
        return "Symposium"
    if re.search("s[eé]minai?re?", title, re.IGNORECASE) or re.search(
        "colloque", title, re.IGNORECASE
    ):
        return "Seminar"
    return "Conference"


def _read_country_map():
    # File taken from https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes/blob/master/all/all.csv
    script_dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(script_dir, "utils/country_codes.csv")
    country_map = {}
    with open(filename, encoding="utf-8") as in_file:
        rdr = csv.reader(in_file)
        for row in rdr:
            country_map[row[1].lower()] = row[0]
        return country_map


def _get_country_map():
    country_map = _read_country_map()
    country_map["kr"] = "Republic of Korea"
    country_map["gb"] = "United Kingdom"
    return country_map


def _read_hal_patch(group):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(script_dir, f"groups/{group}/conferences_patch_hal.json")

    if os.path.exists(filename):
        with open(filename, encoding="utf-8") as in_file:
            infos = json.load(in_file)
            info_dict = {}
            for info in infos["patches"]:
                for id_dict in info["ids"]:
                    info_dict[id_dict] = {k: v for k, v in info.items() if k != "ids"}
            return info_dict
    return None


def _patch_hal(group, entries):
    patches = _read_hal_patch(group)
    spell_changes = {"AndrÉ": "André", "Guittière": "Guittiere"}
    for entry in entries:
        changes = patches.get(entry["halId_s"])
        if changes:
            for key, val in changes.items():
                entry[key] = val
        author = entry["authLastName_s"][0]
        for key, val in spell_changes.items():
            if key in author:
                entry["authLastName_s"][0] = val


def _get_hal_entries(group):
    # Parse the json file from HAL
    audience_map = {"2": "International", "3": "National"}

    # This could be done with pycountry
    country_map = _get_country_map()
    event_list = []
    query_str = f"collCode_s:{group} AND (docType_s:COMM OR docType_s:POSTER)"
    entries = hal.get_parsed(
        query_str,
        "halId_s,conferenceStartDate_s,conferenceEndDate_s,conferenceTitle_s,title_s,city_s,country_s,publisherLink_s,audience_s,authFirstName_s,authLastName_s,invitedCommunication_s,docType_s,doiId_s,arxivId_s",
        2015,
    )
    _patch_hal(group, entries)
    for entry in entries:
        # Get conference info
        if "ignored" in entry:
            continue
        event = {}
        event["conference"] = entry["conferenceTitle_s"]
        event["start"] = entry["conferenceStartDate_s"]
        end = entry.get("conferenceEndDate_s")
        if end:
            event["end"] = end
        event["venue"] = "{}, {}".format(
            entry["city_s"], country_map[entry["country_s"]]
        )
        urls = entry.get("publisherLink_s")
        if urls:
            event["url"] = urls[0]
        else:
            print("Missing url for " + entry["halId_s"])
        audience = entry["audience_s"]
        event["type"] = "{} {}".format(
            audience_map[audience], _get_meeting_type(event["conference"])
        )

        # Get contribution info
        contrib = {}
        authors = entry["authLastName_s"]
        contrib["nauthors"] = len(authors)
        contrib["lastname"] = authors[0]
        contrib["firstname"] = entry["authFirstName_s"][0]
        contrib_type = entry["docType_s"]
        if contrib_type == "POSTER":
            contrib_type = "Poster"
        else:
            contrib_type = "Talk"
        contrib["type"] = contrib_type
        contrib["title"] = entry["title_s"][0]
        is_invited = False
        if entry["invitedCommunication_s"] == "1":
            is_invited = True
        contrib["invited"] = is_invited
        proc = entry.get("doiId_s")
        prefix = ""
        if proc:
            prefix = "https://dx.doi.org/"
        else:
            proc = entry.get("arxivId_s")
            if proc:
                prefix = "http://arxiv.org/pdf/"
        if proc:
            contrib["proceedings"] = prefix + proc

        event["contributions"] = [contrib]

        # Add patched info
        # The info keys do not contain _s as for HAL keys
        for key, val in entry.items():
            if not "_s" in key:
                event[key] = val
        event_list.append(event)
    return event_list


def get_events(group):
    """Formats the events"""
    event_list = _get_hal_entries(group)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    yaml_filename = os.path.join(script_dir, f"groups/{group}/conferences.yaml")
    with open(yaml_filename, encoding="utf-8") as in_file:
        event_list += list(yaml.safe_load(in_file.read()))

    # Merge the events
    merged_events = _merge_events(
        sorted(event_list, key=lambda it: (it["start"], it["conference"]), reverse=True)
    )

    return merged_events


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Utility for conferences")
    parser.add_argument(
        "--group", help="Group", dest="group", default="SUBATECH-PLASMA"
    )

    args = parser.parse_args()
    events = get_events(args.group)
    print(events)
    sys.exit(0)
