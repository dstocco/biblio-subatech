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
