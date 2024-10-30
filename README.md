# Subatech bibliography

This repository contains a series of tool to check the bibliography of the Subatech laboratory via HAL and to generate some publication/conference highlights in the Subatech webpage.

## check_hal_untagged.py

This script allows to check the contributions in HAL that are in the Subatech collection but are not flagged by the Subatech groups.

```shell
python3 check_hal_untagged.py
```

The script retrieves the name of Subatech members and their group from ldap, and uses this information to sort the many contributions.
The matching is of course not perfect, but it allows a first sorting of publication per group.

## show_stats.py

This script shows the number of publications of the selected Subatech group separated by categories and per production year.

```shell
python3 show_stats.py
```

## show_papers_outside_collab.py

This script shows the publications of the selected Subatech group that do not belong to a collaboration.
This is helpful to highlight either review papers or publications with few authors.

```shell
python3 show_papers_outside_collab.py
```

## generate_webpage_files.py

This script combines information from HAL and local information in order to generate the list of selected publications and conference contributions of the group for the Subatech webpage.

Usage:

```shell
python3 generate_webpage_files.py
```

Notice that the script reads some local information written in yaml. Since the yaml parser is not part of the standard python distribution, it has to be installed with:

```shell
pip3 install --user PyYAML
```

### Selected publications

The selected publication from one group can be tagged in the file: `groups/<group>/selected_publications.yaml`, where `<group>` is the name of the group collection in HAL.
Each contribution is in the form:
`ID: [list_of_tags]`
where:

* `ID` is either the arxiv id or the doi
* `list_of_tags` is a arbitrary list to help internally understand the criteria for the selection of the publication

Sometimes, the title of the publications is not correctly formatted for latex and this can lead to errors in the rendering of the generated files.
It is therefore possible to specify a corrected title by writing a special entry in `selected_publications.yaml` in the form:

`ID_title: newtitle`

where:

* `ID` is the same as the one used for the entry, followed by the suffix: `_title`
* `newtitle` is the title that will be used when generating the output file, instead of the one obtained from HAL.

### Additional conference information

The systematic feeding of HAL has started relatively late.
Old contributions to conferences might therefore not be in the HAL archive.
Also, it might be useful to keep track of a specific contribution to a conference while waiting for the corresponding proceedings to be produced, thus triggering the automatic feed to HAL.
Such contributions can be specified in the file: `groups/<group>/conferences.yaml`, where `<group>` is the name of the group collection in HAL.

The automatic contributions in HAL might be incomplete.
For example, the conference url might not be added by default.
Also, old contributions were entered manually and might have some errors.
The fixes or addition of some information for the webpage, can be added in the special file: `groups/<group>/conferences_patch_hal.json`.

### Additional theses information

The information of the ongoing theses or of the theses that are not in the HAL archive can be specified in the file: `groups/<group>/theses.yaml`.
