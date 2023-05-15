#!/usr/bin/env python3
import os
import sys
import argparse
import yaml
import datetime
import hal
import confHandler

# Formatters


class mdFormatter:
    def header(self, name, level):
        return "#" * level + " " + str(name) + "\n\n"

    def listStart(self, level=1):
        out = ""
        if level > 1:
            out += "\n"
        return out

    def listEnd(self, level=1):
        return "\n"

    def listItem(self, name, level=1):
        return "  " * (level - 1) + "* " + name + "\n"

    def eventListStart(self):
        return "\n"

    def eventListEnd(self):
        return "\n"

    def eventStart(self):
        return "* "

    def eventEnd(self):
        return "\n"

    def contribListStart(self):
        return "\n"

    def contribListEnd(self):
        return ""

    def contribStart(self):
        return "  * "

    def contribEnd(self):
        return "\n"

    def it(self, name):
        # This is the typical format for the title
        # Latex is correctly displayed, but when text representation is used instead of latex some characters have to be properly escaped
        name = name.replace("s_(NN)", "sNN")
        return "_" + name + "_"

    def link(self, ref, name):
        return "[" + name + "](" + ref + ")"


class htmlFormatter:
    def header(self, name, level):
        return "\n<h{}>{}</h{}>\n".format(level, name, level)

    def listStart(self, level=1):
        style = "circle"
        if level > 1:
            style = "disc"
        indent = "  " * (level - 1)
        return "\n" + indent + '<ul style="list-style-type: {};">\n'.format(style)

    def listEnd(self, level=1):
        return "  " * (level - 1) + "</ul>\n"

    def listItem(self, name, level=1):
        return "  " * level + "<li>" + name + "</li>\n"

    def eventListStart(self):
        return '<ul style="list-style-type: circle;">\n'

    def eventListEnd(self):
        return "</ul>\n"

    def eventStart(self):
        return "  <li>"

    def eventEnd(self):
        return "  </li>\n"

    def contribListStart(self):
        return '\n    <ul style="list-style-type: disc;">\n'

    def contribListEnd(self):
        return "    </ul>\n"

    def contribStart(self):
        return "      <li>"

    def contribEnd(self):
        return "</li>\n"

    def it(self, name):
        return "<em>" + name + "</em>"

    def link(self, ref, name):
        return '<a href="' + ref + '">' + name + "</a>"


def getFormatter(fmt):
    if fmt == "mdx":
        return mdFormatter()
    return htmlFormatter()


def getPageHeader(title):
    out = "---\n"
    out += 'title: "{}"\n'.format(title)
    out += 'date: "2011-12-16 14:01:22 +0000 UTC"\n'
    out += 'lastmod: "{} +0000 UTC"\n'.format(
        datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )
    out += "---\n\n"
    return out


def getOutFilename(group, fmt, name, subawebDir):
    grp = group.lower().replace("subatech-", "")
    if fmt == "html":
        return "{}_{}.html".format(grp, name)

    outDir = os.path.join(subawebDir, "content/recherche/equipes", grp)
    if name == "conferences":
        name = "presentations-de-conferences-seminaires-et-posters"
    name += ".xx.mdx"
    outFilename = os.path.join(outDir, name)
    if os.path.exists(outFilename):
        return outFilename
    return name


def generateTestPage(inFilename, outFilename):
    with open(inFilename) as inFile:
        with open(outFilename, "w") as outFile:
            print("Writing " + outFilename)
            outFile.write("<!DOCTYPE html>\n")
            outFile.write("<html>\n")
            outFile.write("<head>\n")
            outFile.write(
                '  <meta http-equiv="content-type" content="text/html; charset=utf-8;" />\n'
            )
            outFile.write("</head>\n")
            outFile.write("<body>\n")
            outFile.write(inFile.read())
            outFile.write("</body>\n")
            outFile.write("</html>\n")


def readMdx(filename):
    if not os.path.exists(filename):
        return [None, None]
    with open(filename) as inFile:
        fcontent = inFile.readlines()
        return ["".join(fcontent[0:6]), "".join(fcontent[6:])]


def dumpToFile(outFilename, title, txt, fmt):
    [header, body] = [None, None]
    if fmt == "mdx":
        [header, body] = readMdx(outFilename)
        if body:
            if body == txt:
                print("No changes in " + outFilename)
                return
        if not header:
            header = getPageHeader(title)
    with open(outFilename, "w") as outFile:
        print("Writing " + outFilename)
        if header:
            outFile.write(header)
        outFile.write(txt)

    if fmt == "html":
        generateTestPage(outFilename, "test_" + outFilename)


# Publications


def read_tagged_pub(group):
    scriptDir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(
        scriptDir, "groups/{}/selected_publications.yaml".format(group)
    )
    with open(filename) as inFile:
        return yaml.safe_load(inFile.read())


def getSelected(entries, group):
    tags = read_tagged_pub(group)
    filtered = []
    for entry in entries:
        checks = [hal.getEprint(entry.get("arxivId_s")), entry.get("doiId_s")]
        for val in checks:
            if val and val in tags:
                sel = entry
                sel["selected"] = tags[val]
                newtitle = tags.get(val + "_title")
                if newtitle:
                    sel["title_s"][0] = newtitle
                filtered.append(sel)
                break
    return filtered


def getAuthor(entry):
    authors = entry["authFullName_s"]
    if len(authors) > 5:
        return authors[0] + " et al."
    return " and ".join(authors)


def getJournal(entry, formatter):
    out = ""
    journal = entry.get("journalTitle_s")
    if journal:
        volume = entry.get("volume_s")
        if volume:
            journal += " " + volume
        journal += " ({})".format(entry["producedDateY_i"])
        pages = entry.get("page_s")
        if pages:
            journal += " " + pages
        out += journal
    doi = entry.get("doiId_s")
    if doi:
        out += " " + formatter.link("https://doi.org/" + doi, "doi:" + doi)

    arxiv = entry.get("arxivId_s")
    if arxiv:
        if out:
            out += " "
        out += (
            "["
            + formatter.link("https://arxiv.org/abs/" + arxiv, "arXiv:{}".format(arxiv))
            + "]"
        )
    return out


def toDate(dateStr):
    return datetime.datetime.strptime(dateStr, "%Y-%m-%d").date()


def generate_selected_pub(group, fmt, ymin, subawebDir):
    entries = hal.getParsed(
        "collCode_s:{} docType_s:ART".format(group),
        "halId_s,authFullName_s,collaboration_s,title_s,arxivId_s,doiId_s,journalTitle_s,volume_s,number_s,page_s,producedDateY_i",
        ymin,
    )

    selected = getSelected(entries, group)

    formatter = getFormatter(fmt)

    txt = formatter.header("ALICE publications", 2)
    txt += formatter.header(
        formatter.link(
            "http://aliceinfo.cern.ch/ArtSubmission/publications", "ALICE web page"
        ),
        3,
    )
    txt += formatter.header(
        formatter.link(
            "https://inspirehep.net/literature?sort=mostrecent&size=250&page=1&q=fin%20cn%20alice%20and%20a%20batigne%20and%20a%20germain%20and%20tc%20p%20not%20tc%20c",
            "INSPIRE-HEP",
        ),
        3,
    )
    txt += formatter.header(
        formatter.link(
            "https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=fin%20cn%20star%20and%20%28a%20Erazmus%20or%20a%20kabana%29%20and%20tc%20p%20not%20tc%20c",
            "STAR publications on INSPIRE-HEP",
        ),
        2,
    )
    txt += formatter.header(
        formatter.link(
            "https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=fin%20a%20Aphecetche%20and%20cn%20phenix%20and%20tc%20p%20not%20tc%20c",
            "PHENIX publications on INSPIRE-HEP",
        ),
        2,
    )
    txt += formatter.header(
        formatter.link(
            "https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=fin%20a%20schutz%20and%20cn%20wa98%20and%20tc%20p%20not%20tc%20c",
            "WA98 publications on INSPIRE-HEP",
        ),
        2,
    )
    txt += formatter.header(
        "Sélection des publications et autres publications / Selection of publications and other standalone publications ({}-{})".format(
            ymin, datetime.datetime.today().year
        ),
        2,
    )

    txt += formatter.listStart()
    selForSort = selected
    for sel in selected:
        if not sel.get("arxivId_s"):
            sel["arxivId_s"] = "0"

    for entry in sorted(
        selForSort,
        key=lambda sel: (sel["producedDateY_i"], sel.get("arxivId_s")),
        reverse=True,
    ):
        txt += formatter.listItem(
            "{}, {}".format(entry["title_s"][0], getJournal(entry, formatter))
        )
    txt += formatter.listEnd()

    outFilename = getOutFilename(group, fmt, "publications", subawebDir)
    dumpToFile(outFilename, "Publications", txt, fmt)

    return 0


def readTheses(group):
    scriptDir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(scriptDir, "groups/{}/theses.yaml".format(group))
    with open(filename) as inFile:
        inEntries = yaml.safe_load(inFile.read())
        entries = []
        for en in inEntries:
            entry = {}
            entry["title_s"] = [en["title"]]
            entry["authFirstName_s"] = [en["firstname"]]
            entry["authLastName_s"] = [en["lastname"]]
            defense = en.get("defense")
            if defense:
                entry["defenseDate_s"] = defense
            url = en.get("url")
            if url:
                entry["url"] = url
            entries.append(entry)
        return entries


def generate_theses(group, fmt, subawebDir):
    entries = hal.getParsed(
        "collCode_s:{} docType_s:THESE".format(group),
        "halId_s,authFirstName_s,authLastName_s,title_s,defenseDate_s",
        2003,
    )

    local = readTheses(group)
    ongoing = [entry for entry in local if not "defenseDate_s" in entry]
    done = [entry for entry in local if "defenseDate_s" in entry]

    entries += done

    formatter = getFormatter(fmt)
    txt = ""

    if ongoing:
        txt += formatter.header("En cours / In preparation", 2)
        for entry in ongoing:
            txt += formatter.listItem(
                "{}, {} {}".format(
                    entry["title_s"][0],
                    entry["authFirstName_s"][0],
                    entry["authLastName_s"][0].upper(),
                )
            )

    txt += formatter.header("Soutenues / Defended", 2)

    txt += formatter.listStart()
    for entry in sorted(entries, key=lambda sel: sel["defenseDate_s"], reverse=True):
        url = entry.get("url")
        if not url:
            id = entry.get("halId_s")
            if id:
                url = "https://theses.hal.science/" + id
        title = entry["title_s"][0]
        titleLink = title
        if url:
            titleLink = formatter.link(url, title)
        txt += formatter.listItem(
            "{}, {} {}, defended {}".format(
                titleLink,
                entry["authFirstName_s"][0],
                entry["authLastName_s"][0].upper(),
                entry["defenseDate_s"],
            )
        )
    txt += formatter.listEnd()

    outFilename = getOutFilename(group, fmt, "theses", subawebDir)
    dumpToFile(outFilename, "Thèses / PhD", txt, fmt)

    return 0


# Conferences


def formatContribution(conf, formatter):
    # Generates the code for the contributions
    if "contributions" not in conf:
        return ""
    contributions = conf["contributions"]

    level = 2
    out = formatter.listStart(level)
    for contrib in contributions:
        fmtContrib = ""
        if contrib.get("invited") and contrib["invited"] is True:
            fmtContrib += "Invited "
        fmtContrib += contrib["type"]
        contribDetails = ""
        if contrib.get("title"):
            contribDetails += formatter.it(contrib["title"]) + ","
        if contrib.get("firstname"):
            contribDetails += (
                " " + contrib["firstname"] + " " + contrib["lastname"].upper()
            )
        if contrib.get("nauthors") and contrib["nauthors"] > 1:
            contribDetails += " et al."
        if len(contribDetails) > 0:
            fmtContrib += ": " + contribDetails
        if contrib.get("proceedings"):
            fmtContrib += ". Proceedings " + formatter.link(
                contrib["proceedings"], "here"
            )
        out += formatter.listItem(fmtContrib, level)
    out += formatter.listEnd(level)
    return out


def formatEvent(event, formatter):
    # Generate the code for the event
    out = ""
    url = event.get("url")
    name = event["conference"]
    if event.get("alias"):
        name = event["alias"]
    if url:
        out += formatter.link(url, name)
    else:
        out += name

    out += (
        ", " + toDate(event["start"]).strftime("%d/%m/%y") + ", " + event["venue"] + "."
    )
    if event.get("type"):
        out += " " + event["type"] + "."
    if event.get("participants"):
        out += " " + str(event["participants"]) + " participants."
    out += formatContribution(event, formatter).rstrip()
    return formatter.listItem(out)


def generate_conferences(group, fmt, subawebDir):
    events = confHandler.getEvents(group)
    eventsYear = {}
    for evt in events:
        year = toDate(evt["start"]).year
        if not year in eventsYear:
            eventsYear[year] = []
        eventsYear[year].append(evt)

    formatter = getFormatter(fmt)
    txt = ""
    for year, mergedEvents in eventsYear.items():
        txt += formatter.header(year, 2)
        txt += formatter.listStart()
        for event in mergedEvents:
            txt += formatEvent(event, formatter)
        txt += formatter.listEnd()

    lastYear = max(eventsYear.keys())
    title = (
        "Présentations à des Conférences/ Contribution to Conferences (2008-{})".format(
            lastYear
        )
    )
    outFilename = getOutFilename(group, fmt, "conferences", subawebDir)
    dumpToFile(outFilename, title, txt, fmt)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utility for bibliography")
    parser.add_argument("--group", help="Subatech group", default="SUBATECH-PLASMA")
    parser.add_argument("--ymin", help="Minimum year", type=int, default=2007)
    parser.add_argument(
        "--subatech-next-dir",
        "-d",
        help="Directory containing the Subatech website source files",
        dest="subaweb",
        default=".",
    )
    parser.add_argument(
        "--format", help="Output format", choices=["html", "mdx"], default="mdx"
    )

    args = parser.parse_args()
    rc = 0
    rc += generate_selected_pub(args.group, args.format, args.ymin, args.subaweb)
    rc += generate_theses(args.group, args.format, args.subaweb)
    rc += generate_conferences(args.group, args.format, args.subaweb)
    sys.exit(rc)
