Icon Resolution Extension
=================

Bigtree3DStore supports configuring export of specified size ICONS into GCode. In the initial file, there are four reference sizes, which are referenced according to the existing rules (width,height). Each behavior has one size data, and supports output of multiple sizes simultaneously.

Note:
1. Cura is suggested to run under administrative authority, that is, to run Cura with administrative authority.
2. This configuration file only supports dimension data, except for skipping lines starting with '#' symbol, other illegal characters may cause operation errors;Do not change the file encoding format, which is currently limited to UTF-8 file encoding format. The wrong format will cause the read configuration to fail.