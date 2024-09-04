#!/usr/bin/env python3

"""Script to generate the subatech-next webpage files"""

import os
import sys
import argparse
import datetime
import yaml
import hal
import confHandler

# Formatters


class MDFormatter:
    """Class to format output in Markdown"""

    def header(self, name, level):
        """Header"""
        return "#" * level + " " + str(name) + "\n\n"

    def list_start(self, level=1):
        """Start list"""
        out = ""
        if level > 1:
            out += "\n"
        return out

    # pylint: disable-next=unused-argument
    def list_end(self, level=1):
        """End list"""
        return "\n"

    def list_item(self, name, level=1):
        """List item"""
        return "  " * (level - 1) + "* " + name + "\n"

    def event_list_start(self):
        """Start event list"""
        return "\n"

    def event_list_end(self):
        """End event list"""
        return "\n"

    def event_start(self):
        """Start event"""
        return "* "

    def event_end(self):
        """End event"""
        return "\n"

    def contrib_list_start(self):
        """Start contribution list"""
        return "\n"

    def contrib_list_end(self):
        """End contribution list"""
        return ""

    def contrib_start(self):
        """Start contribution"""
        return "  * "

    def contrib_end(self):
        """End contribution"""
        return "\n"

    def text_it(self, name):
        """Italics"""
        # This is the typical format for the title
        # Latex is correctly displayed, but when text representation is used instead of latex
        # some characters have to be properly escaped
        name = name.replace("s_(NN)", "sNN")
        return "_" + name + "_"

    def link(self, ref, name):
        """Format link"""
        return "[" + name + "](" + ref + ")"


class HTMLFormatter:
    """Class to format output in HTML"""

    def header(self, name, level):
        """Header"""
        return f"\n<h{level}>{name}</h{level}>\n"

    def list_start(self, level=1):
        """Start list"""
        style = "circle"
        if level > 1:
            style = "disc"
        indent = "  " * (level - 1)
        return f'\n{indent}<ul style="list-style-type: {style};">\n'

    def list_end(self, level=1):
        """End list"""
        return "  " * (level - 1) + "</ul>\n"

    def list_item(self, name, level=1):
        """List item"""
        return "  " * level + "<li>" + name + "</li>\n"

    def event_list_start(self):
        """Start event list"""
        return '<ul style="list-style-type: circle;">\n'

    def event_list_end(self):
        """End event list"""
        return "</ul>\n"

    def event_start(self):
        """Start event"""
        return "  <li>"

    def event_end(self):
        """End event"""
        return "  </li>\n"

    def contrib_list_start(self):
        """Start contribution list"""
        return '\n    <ul style="list-style-type: disc;">\n'

    def contrib_list_end(self):
        """End contribution list"""
        return "    </ul>\n"

    def contrib_start(self):
        """Start contribution"""
        return "      <li>"

    def contrib_end(self):
        """End contribution"""
        return "</li>\n"

    def text_it(self, name):
        """Italics"""
        return "<em>" + name + "</em>"

    def link(self, ref, name):
        """Format link"""
        return '<a href="' + ref + '">' + name + "</a>"


def get_formatter(fmt):
    """Return the formatter"""
    if fmt == "mdx":
        return MDFormatter()
    return HTMLFormatter()


def get_page_header_lines(title):
    """Returns the page header"""
    current_time = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    out = [
        "---\n",
        f"title: {title}\n",
        'date: "2011-12-16 14:01:22 +0000 UTC"\n',
        f'lastmod: "{current_time} +0000 UTC"\n',
        "---\n\n",
    ]
    return out


def get_out_filename(group, fmt, name, subaweb_dir, lang):
    """Returns the output filename"""
    grp = group.lower().replace("subatech-", "")
    if fmt == "html":
        return f"{grp}_{name}_{lang}.html"

    out_dir = os.path.join(subaweb_dir, "content/recherche/equipes", grp)
    if name == "conferences":
        name = "presentations-de-conferences-seminaires-et-posters"
    name += f".{lang}.mdx"
    out_filename = os.path.join(out_dir, name)
    if os.path.exists(out_filename):
        return out_filename
    return name


def generate_test_page(in_filename, out_filename):
    """Generate a test page"""
    with open(in_filename, encoding="utf-8") as in_file:
        with open(out_filename, "w", encoding="utf-8") as out_file:
            print("Writing " + out_filename)
            out_file.write("<!DOCTYPE html>\n")
            out_file.write("<html>\n")
            out_file.write("<head>\n")
            out_file.write(
                '  <meta http-equiv="content-type" content="text/html; charset=utf-8;" />\n'
            )
            out_file.write("</head>\n")
            out_file.write("<body>\n")
            out_file.write(in_file.read())
            out_file.write("</body>\n")
            out_file.write("</html>\n")


def read_mdx(filename):
    """Read markdown for javascript"""
    if not os.path.exists(filename):
        return {}
    with open(filename, encoding="utf-8") as in_file:
        fcontent = in_file.readlines()
        return {"header_lines": fcontent[0:6], "body_lines": fcontent[6:]}


def dump_to_file(out_filename, title, txt, fmt):
    """Dump content to file"""
    header_lines = []
    if fmt == "mdx":
        mdx_dict = read_mdx(out_filename)
        body_lines = mdx_dict.get("body_lines")
        if body_lines:
            body = "".join(body_lines)
            if body == txt:
                print("No changes in " + out_filename)
                return
        header_lines = mdx_dict.get("header_lines")
        header_update = get_page_header_lines(title)
        if header_lines:
            header_lines[1] = header_update[1]
        else:
            header_lines = header_update
    with open(out_filename, "w", encoding="utf-8") as out_file:
        print("Writing " + out_filename)
        if header_lines:
            out_file.write("".join(header_lines))
        out_file.write(txt)

    if fmt == "html":
        generate_test_page(out_filename, "test_" + out_filename)


# Publications


def read_tagged_pub(group):
    """Read file with selected publications"""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(script_dir, f"groups/{group}/selected_publications.yaml")
    with open(filename, encoding="utf-8") as in_file:
        return yaml.safe_load(in_file.read())


def get_selected(entries, group):
    """Returns the selected publications"""
    tags = read_tagged_pub(group)
    filtered = []
    for entry in entries:
        checks = [hal.get_eprint(entry.get("arxivId_s")), entry.get("doiId_s")]
        for val in checks:
            if val and val in tags:
                sel = entry
                sel["selected"] = tags[val]
                new_title = tags.get(val + "_title")
                if new_title:
                    sel["title_s"][0] = new_title
                filtered.append(sel)
                break
    return filtered


def get_author(entry):
    """Gets the author"""
    authors = entry["authFullName_s"]
    if len(authors) > 5:
        return authors[0] + " et al."
    return " and ".join(authors)


def get_journal(entry, formatter):
    """Returns the journal type"""
    out = ""
    journal = entry.get("journalTitle_s")
    if journal:
        volume = entry.get("volume_s")
        if volume:
            journal += " " + volume
        journal += f" ({entry['producedDateY_i']})"
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
            + formatter.link("https://arxiv.org/abs/" + arxiv, f"arXiv:{arxiv}")
            + "]"
        )
    return out


def to_date(date_str):
    """Convert string to date object"""
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()


def generate_selected_pub(group, fmt, ymin, subaweb_dir):
    """Generates the list of selected publications in the chosen language"""
    entries = hal.get_parsed(
        f"collCode_s:{group} docType_s:ART",
        "halId_s,authFullName_s,collaboration_s,title_s,arxivId_s,doiId_s,journalTitle_s,volume_s,number_s,page_s,producedDateY_i",
        ymin,
    )

    selected = get_selected(entries, group)

    formatter = get_formatter(fmt)

    langs = {"en": 0, "fr": 1}
    h1 = ["ALICE publications", "Publications d'ALICE"]
    h2 = ["ALICE web page", "Page web d'ALICE"]
    star = ["STAR publications on INSPIRE-HEP", "Publications de STAR sur INSPIRE-HEP"]
    phenix = [
        "PHENIX publications on INSPIRE-HEP",
        "Publications de PHENIX sur INSPIRE-HEP",
    ]
    wa98 = [
        "WA98 publications on INSPIRE-HEP",
        "Publications de WA98 sur INSPIRE-HEP",
    ]
    selection = [
        "Selection of publications and other standalone publications",
        "Sélection des publications et autres publications",
    ]

    for key, idx in langs.items():
        txt = formatter.header(h1[idx], 2)
        txt += formatter.header(
            formatter.link(
                "http://aliceinfo.cern.ch/ArtSubmission/publications", h2[idx]
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
                star[idx],
            ),
            2,
        )
        txt += formatter.header(
            formatter.link(
                "https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=fin%20a%20Aphecetche%20and%20cn%20phenix%20and%20tc%20p%20not%20tc%20c",
                phenix[idx],
            ),
            2,
        )
        txt += formatter.header(
            formatter.link(
                "https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=fin%20a%20schutz%20and%20cn%20wa98%20and%20tc%20p%20not%20tc%20c",
                wa98[idx],
            ),
            2,
        )
        txt += formatter.header(
            f"{selection[idx]} ({ymin}-{datetime.datetime.today().year})",
            2,
        )

        txt += formatter.list_start()
        sel_for_sort = selected
        for sel in selected:
            if not sel.get("arxivId_s"):
                sel["arxivId_s"] = "0"

        for entry in sorted(
            sel_for_sort,
            key=lambda sel: (sel["producedDateY_i"], sel.get("arxivId_s")),
            reverse=True,
        ):
            txt += formatter.list_item(
                f"{entry['title_s'][0]}, {get_journal(entry, formatter)}"
            )
        txt += formatter.list_end()

        out_filename = get_out_filename(group, fmt, "publications", subaweb_dir, key)
        dump_to_file(out_filename, "Publications", txt, fmt)

    return 0


def read_theses(group):
    """Read list of theses"""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(script_dir, f"groups/{group}/theses.yaml")
    with open(filename, encoding="utf-8") as in_file:
        in_entries = yaml.safe_load(in_file.read())
        entries = []
        for en in in_entries:
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


def generate_theses(group, fmt, subaweb_dir):
    """Generate list of theses"""
    entries = hal.get_parsed(
        f"collCode_s:{group} docType_s:THESE",
        "halId_s,authFirstName_s,authLastName_s,title_s,defenseDate_s",
        2003,
    )

    local = read_theses(group)
    ongoing = [entry for entry in local if not "defenseDate_s" in entry]
    done = [entry for entry in local if "defenseDate_s" in entry]

    entries += done

    formatter = get_formatter(fmt)

    langs = {"en": 0, "fr": 1}
    ong = ["Ongoing", "En cours"]
    defended = ["Defended", "Soutenues"]
    title = ["PhD", "Thèses"]

    for key, idx in langs.items():
        txt = ""
        if ongoing:
            txt += formatter.header(ong[idx], 2)
            txt += formatter.list_start()
            for entry in ongoing:
                txt += formatter.list_item(
                    f"{entry['title_s'][0]}, {entry['authFirstName_s'][0]} {entry['authLastName_s'][0].upper()}"
                )
            txt += formatter.list_end()

        txt += formatter.header(defended[idx], 2)

        txt += formatter.list_start()
        for entry in sorted(
            entries, key=lambda sel: sel["defenseDate_s"], reverse=True
        ):
            url = entry.get("url")
            if not url:
                entry_id = entry.get("halId_s")
                if entry_id:
                    url = "https://theses.hal.science/" + entry_id
            title = entry["title_s"][0]
            title_link = title
            if url:
                title_link = formatter.link(url, title)
            txt += formatter.list_item(
                f"{title_link}, {entry['authFirstName_s'][0]} {entry['authLastName_s'][0].upper()}, defended {entry['defenseDate_s']}"
            )
        txt += formatter.list_end()

        out_filename = get_out_filename(group, fmt, "theses", subaweb_dir, key)
        dump_to_file(out_filename, title[idx], txt, fmt)

    return 0


# Conferences


def format_contribution(conf, formatter):
    """Generates the code for the contributions"""
    if "contributions" not in conf:
        return ""
    contributions = conf["contributions"]

    level = 2
    out = formatter.list_start(level)
    for contrib in contributions:
        fmt_contrib = ""
        if contrib.get("invited") and contrib["invited"] is True:
            fmt_contrib += "Invited "
        fmt_contrib += contrib["type"]
        contrib_details = ""
        if contrib.get("title"):
            contrib_details += formatter.text_it(contrib["title"]) + ","
        if contrib.get("firstname"):
            contrib_details += (
                " " + contrib["firstname"] + " " + contrib["lastname"].upper()
            )
        if contrib.get("nauthors") and contrib["nauthors"] > 1:
            contrib_details += " et al."
        if len(contrib_details) > 0:
            fmt_contrib += ": " + contrib_details
        if contrib.get("proceedings"):
            fmt_contrib += ". Proceedings " + formatter.link(
                contrib["proceedings"], "here"
            )
        out += formatter.list_item(fmt_contrib, level)
    out += formatter.list_end(level)
    return out


def format_event(event, formatter):
    """Generate the code for the event"""
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
        ", "
        + to_date(event["start"]).strftime("%d/%m/%y")
        + ", "
        + event["venue"]
        + "."
    )
    if event.get("type"):
        out += " " + event["type"] + "."
    if event.get("participants"):
        out += " " + str(event["participants"]) + " participants."
    out += format_contribution(event, formatter).rstrip()
    return formatter.list_item(out)


def generate_conferences(group, fmt, subaweb_dir):
    """Generate the conferences"""
    events = confHandler.get_events(group)
    events_year = {}
    for evt in events:
        year = to_date(evt["start"]).year
        if not year in events_year:
            events_year[year] = []
        events_year[year].append(evt)

    formatter = get_formatter(fmt)
    langs = {"en": 0, "fr": 1}
    titles = ["Contribution to conferences", "Présentations à des Conférences"]

    for key, idx in langs.items():
        txt = ""
        for year, merged_events in events_year.items():
            txt += formatter.header(year, 2)
            txt += formatter.list_start()
            for event in merged_events:
                txt += format_event(event, formatter)
            txt += formatter.list_end()

        last_year = max(events_year.keys())
        title = f"{titles[idx]} (2008-{last_year})"
        out_filename = get_out_filename(group, fmt, "conferences", subaweb_dir, key)
        dump_to_file(out_filename, title, txt, fmt)

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
    ret_code = 0
    ret_code += generate_selected_pub(args.group, args.format, args.ymin, args.subaweb)
    if args.format == "html":
        ret_code += generate_theses(args.group, args.format, args.subaweb)
        ret_code += generate_conferences(args.group, args.format, args.subaweb)
    sys.exit(ret_code)
