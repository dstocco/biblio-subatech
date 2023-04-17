#!/usr/bin/env python

import csv
import os
import datetime
import re
import yaml
import json
import hal


def _isSameTitle(title, refTitle):
    words = title.split(" ")
    nWords = len(words)
    nFound = 0
    for word in words:
        if word in refTitle:
            nFound += 1
    return float(nFound)/float(nWords) > 0.6


def _checkDuplicated(contrib, mergedContributions):
    for merged in mergedContributions:
        if contrib.get("lastname") and merged.get("lastname"):
            if contrib["lastname"] == merged["lastname"]:
                if _isSameTitle(contrib["title"], merged["title"]):
                    # The contribution is already present
                    # Let us add any additional information
                    # that might be present in the second contribution
                    for key in contrib.keys():
                        if key not in merged:
                            merged[key] = contrib[key]
                    return True
    return False


def _addContribution(event, mergedList):
    # Add the contributions
    for mergedEvent in mergedList:
        if event["start"] == mergedEvent["start"]:
            end1 = event.get("end")
            end2 = mergedEvent.get("end")
            if end1 and end2 and (end1 != end2):
                continue
            for contrib in event["contributions"]:
                if _checkDuplicated(contrib, mergedEvent["contributions"]):
                    print("Duplicated contribution:")
                    print(contrib)
                else:
                    mergedEvent["contributions"].append(contrib)
            return
    mergedList.append(event)


def _mergeEvents(eventList):
    # Merges the contributions in the same event
    mergedList = []
    for event in eventList:
        _addContribution(event, mergedList)
    for event in mergedList:
        # sort
        contributions = event.get("contributions")
        if contributions:
            event["contributions"] = sorted(
                contributions, key=lambda sel: sel.get("lastname") if "lastname" in sel else "zzz")
    return mergedList


def _getMeetingType(title):
    if re.search("workshop", title, re.IGNORECASE):
        return "Workshop"
    if re.search("symposium", title, re.IGNORECASE):
        return "Symposium"
    if re.search("s[eé]minai?re?", title, re.IGNORECASE) or re.search("colloque", title, re.IGNORECASE):
        return "Seminar"
    return "Conference"


def _readCountryMap():
    # File taken from https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes/blob/master/all/all.csv
    scriptDir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(scriptDir, "utils/country_codes.csv")
    countryMap = {}
    with open(filename) as inFile:
        rdr = csv.reader(inFile)
        for row in rdr:
            countryMap[row[1].lower()] = row[0]
        return countryMap


def _getCountryMap():
    countryMap = _readCountryMap()
    countryMap["kr"] = "Republic of Korea"
    countryMap["gb"] = "United Kingdom"
    return countryMap


def _readHalPatch(group):
    scriptDir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(
        scriptDir, "groups/{}/conferences_patch_hal.json".format(group))

    if os.path.exists(filename):
        with open(filename) as inFile:
            infos = json.load(inFile)
            infoDict = {}
            for info in infos["patches"]:
                for id in info["ids"]:
                    infoDict[id] = {k: v for k,
                                    v in info.items() if k != "ids"}
            return infoDict


def _patchHal(group, entries):
    patches = _readHalPatch(group)
    spellChanges = {"AndrÉ": "André", "Guittière": "Guittiere"}
    for entry in entries:
        changes = patches.get(entry["halId_s"])
        if changes:
            for key, val in changes.items():
                entry[key] = val
        author = entry["authLastName_s"][0]
        for key, val in spellChanges.items():
            if key in author:
                entry["authLastName_s"][0] = val


def _getHalEntries(group):
    # Parse the json file from HAL
    audienceMap = {"2": "International", "3": "National"}

    # This could be done with pycountry
    countryMap = _getCountryMap()
    eventList = []
    queryStr = "collCode_s:{} AND (docType_s:COMM OR docType_s:POSTER)".format(
        group)
    entries = hal.getParsed(
        queryStr, "halId_s,conferenceStartDate_s,conferenceEndDate_s,conferenceTitle_s,title_s,city_s,country_s,publisherLink_s,audience_s,authFirstName_s,authLastName_s,invitedCommunication_s,docType_s,doiId_s,arxivId_s", 2015)
    _patchHal(group, entries)
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
            entry["city_s"], countryMap[entry["country_s"]])
        urls = entry.get("publisherLink_s")
        if urls:
            event["url"] = urls[0]
        else:
            print("Missing url for " + entry["halId_s"])
        audience = entry["audience_s"]
        event["type"] = "{} {}".format(
            audienceMap[audience], _getMeetingType(event["conference"]))

        # Get contribution info
        contrib = {}
        authors = entry["authLastName_s"]
        contrib["nauthors"] = len(authors)
        contrib["lastname"] = authors[0]
        contrib["firstname"] = entry["authFirstName_s"][0]
        contribType = entry["docType_s"]
        if contribType == "POSTER":
            contribType = "Poster"
        else:
            contribType = "Talk"
        contrib["type"] = contribType
        contrib["title"] = entry["title_s"][0]
        isInvited = False
        if (entry["invitedCommunication_s"] == "1"):
            isInvited = True
        contrib["invited"] = isInvited
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
        eventList.append(event)
    return eventList


def getEvents(group):
    eventList = _getHalEntries(group)
    scriptDir = os.path.dirname(os.path.realpath(__file__))
    yamlFilename = os.path.join(
        scriptDir, "groups/{}/conferences.yaml".format(group))
    with open(yamlFilename) as inFile:
        eventList += list(yaml.safe_load(inFile.read()))

    # Merge the events
    mergedEvents = _mergeEvents(
        sorted(eventList, key=lambda it: (it["start"], it["conference"]), reverse=True))

    return mergedEvents


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Utility for conferences")
    parser.add_argument("--group", help="Group",
                        dest="group", default="SUBATECH-PLASMA")

    args = parser.parse_args()
    events = getEvents(args.group)
    print(events)
    sys.exit(0)
