# Subatech bibliography

This repository contains a series of tool to check the bibliography of the Subatech laboratory via HAL and to generate some publication/conference highlights in the Subatech webpage

## check_hal_untagged.py

This script allows to check the contributions in HAL that are in the SUBATECH collection but are not flagged by the subatech groups.

```shell
python3 check_hal_untagged.py
```

### Configuration

The list of untagged files can be rather long.
To help people that handle the bibliography of just one group, a configuration file can be added in the form `groups/<group>/members.yaml`, where `<group>` is the name of the group collection in HAL.

The script will therefore provide more verbose information for the untagged contributions in HAL that match the last name of each group members.
This is useful to highlight the contributions that should be tagged for the specific group chosen and not for other groups.

## generate_webpage_files.py

This script combines information from HAL and local information in order to generate the list of selected publications and conference contributions of the group for the SUBATECH webpage

```shell
python3 generate_webpage_files.py
```

### Selected publications

The selected publication from one group can be tagged in the file: `groups/<group>/selected_publications.yaml`, where `<group>` is the name of the group collection in HAL.
Each contribution is in the form:
`ID: [list_of_tags]`
where:

* `ID` is either the arxiv id or the doi
* `list_of_tags` is a arbitrary list to help internally understand the criteria for the selection of the publication

Sometimes, the title of the publications is not correctly formatted for latex and this can lead to errors in the rendering of the generated files.
Is it therefore possible to specify a corrected title by writing a special entry in `selected_publications.yaml` in the form:
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

The information of the ongoing theses or of the theses that are not in the HAL archive can be specified in the file: `groups/<group>/theses.yaml`
